"""Isolated Compose recovery ensemble; logical identities survive relocation."""
from dataclasses import replace
import json
from pathlib import Path

from ...topology import render_flat_topology
from ..container_scale import deployment
from ..container_scale.config import logical_topology


def relocated_topology(config, count, decision, base_port, placements=None):
    original = logical_topology(config, count)
    placements = dict(placements or {})
    placements[decision['source']] = decision['destination']
    slots = {}
    nodes = []
    for node in original.active_nodes:
        physical = config.topology.node(placements.get(node.node_id, node.node_id.rsplit('-c', 1)[0]))
        slot = slots.get(physical.node_id, 0)
        slots[physical.node_id] = slot + 1
        port = base_port + slot
        nodes.append(replace(node, host=physical.host, port=port,
            endpoint=f'http://{physical.host}:{port}', local=physical.local,
            latitude=physical.latitude, longitude=physical.longitude,
            altitude_m=physical.altitude_m, region=physical.region))
    if decision['source'] not in {n.node_id for n in nodes}:
        raise ValueError('Unknown source participant')
    return replace(original, nodes=tuple(nodes))


class RecoveryDeployment:
    def __init__(self, config, root, topology, directory, token, replica_owners=None):
        self.config, self.root, self.topology = config, root, topology
        self.directory, self.token = directory, token
        self.hosts = []
        self.replica_owners = replica_owners or {}

    def remote_directory(self, node):
        return (str(self.directory / node.node_id) if node.local else
            f"{self.config.deployment['remote_dir']}/recovery-{self.token}")

    def command(self, node, *args):
        dest = self.remote_directory(node)
        return deployment.execute(self.config, node, ['docker', 'compose',
            '--project-directory', dest, '-f', dest+'/compose.json', *args])

    def start(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        topology_path = render_flat_topology(self.topology, self.directory/'topology.toml')
        for physical in self.config.topology.active_nodes:
            participants = [n for n in self.topology.active_nodes if n.host == physical.host and (not self.replica_owners or n.node_id in self.replica_owners)]
            if not participants:
                continue
            # Reuse exactly the image and resource/security settings of the baseline.
            prototype = next(iter(deployment.compose_document(self.config, physical, 1)['services'].values()))
            services = {}
            for node in participants:
                service = dict(prototype)
                service.pop('build', None)
                service['ports'] = [f'{physical.host}:{node.port}:8080']
                service['command'] = ['--node-id', node.node_id, '--tier', node.tier,
                    '--topology-file', 'configs/container-topology.toml', '--topology-name', 'container-scale']
                if node.node_id in self.replica_owners:
                    service['command'] += ['--replica-of', self.replica_owners[node.node_id]]
                service['labels'] = {**prototype['labels'], 'continuum.recovery': self.token,
                    'continuum.logical_tier': node.tier}
                services[node.node_id] = service
            document = {'name': 'continuum-recovery-'+self.token, 'services': services}
            dest = self.remote_directory(physical)
            payload = json.dumps({'directory': dest, 'topology': topology_path.read_text(), 'compose': document})
            script = "import json,sys; from pathlib import Path; d=json.load(sys.stdin); p=Path(d['directory']); p.mkdir(parents=True,exist_ok=False); (p/'topology.toml').write_text(d['topology']); (p/'compose.json').write_text(json.dumps(d['compose']))"
            deployment.execute(self.config, physical, ['python3', '-c', script], input=payload)
            self.hosts.append(physical)
            self.command(physical, 'up', '-d', '--no-build', '--pull', 'never')
        deployment.wait_ready(self.config, self.topology, node_ids=set(self.replica_owners) if self.replica_owners else None)

    def close(self):
        errors = []
        for node in self.hosts:
            try:
                self.command(node, 'down', '--timeout', '10')
            except Exception as error:
                errors.append({'host': node.node_id, 'error': str(error)})
        (self.directory/'cleanup.json').write_text(json.dumps(errors, indent=2))
        return errors

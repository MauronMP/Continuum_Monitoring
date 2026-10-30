"""Bounded service-level samples alongside application benchmark evidence."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from threading import Event, Thread

from ..container_scale import deployment


class Sampler:
    def __init__(self, actuator, output, interval):
        self.actuator, self.output, self.interval = actuator, output, interval
        self.stop_event = Event()
        self.thread = Thread(target=self._run, name='continuum-service-observer', daemon=True)

    def sample(self, node):
        a = self.actuator
        directory = a.remote_directory(node)
        prefix = ['docker', 'compose', '--project-directory', directory,
                  '-f', directory+'/compose.json']
        result = dict(host=node.node_id, time=datetime.now(timezone.utc).isoformat())
        if getattr(a, 'replica_owners', {}):
            try:
                def parse(value):
                    if not value.strip(): return []
                    try:
                        data=json.loads(value);return data if isinstance(data,list) else [data]
                    except json.JSONDecodeError:
                        return [json.loads(line) for line in value.splitlines() if line.strip()]
                base = deployment.host_directory(a.config,a.root,node)
                services=parse(deployment.execute(a.config,node,['docker','compose','--project-directory',base,'-f',base+'/compose.json','ps','--all','--format','json'],timeout=10))
                if any(h.node_id==node.node_id for h in a.hosts):
                    services+=parse(deployment.execute(a.config,node,prefix+['ps','--all','--format','json'],timeout=10))
                ids=list(dict.fromkeys(s['ID'] for s in services if s.get('State')=='running' and s.get('ID')))
                result['services']=json.dumps(services)
                result['resources']=deployment.execute(a.config,node,['docker','stats','--no-stream','--format','{{json .}}',*ids],timeout=10) if ids else ''
            except Exception as error:
                result['error']=str(error)
            return result
        try:
            result['services'] = deployment.execute(a.config,node,prefix+['ps','--all','--format','json'],timeout=10)
            ids = deployment.execute(a.config,node,prefix+['ps','-q'],timeout=10).split()
            result['resources'] = deployment.execute(a.config,node,
                ['docker','stats','--no-stream','--format','{{json .}}',*ids],timeout=10) if ids else ''
        except Exception as error:
            result['error'] = str(error)
        return result

    def _run(self):
        while not self.stop_event.is_set():
            hosts=self.actuator.config.topology.active_nodes if getattr(self.actuator,'replica_owners',{}) else self.actuator.hosts
            with ThreadPoolExecutor(max_workers=max(1,len(hosts))) as pool:
                rows = list(pool.map(self.sample,hosts))
            with self.output.open('a') as handle:
                for row in rows:
                    handle.write(json.dumps(row)+'\n')
            self.stop_event.wait(self.interval)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.stop_event.set()
        self.thread.join()  # Each cycle has three bounded 10-second host operations.

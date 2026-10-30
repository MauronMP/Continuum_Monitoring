"""Observe, decide, actuate and verify at bounded scenario boundaries."""
from collections import Counter
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from time import monotonic
import uuid

from ...protocol import SOFTWARE_BUILD_ID
from ..container_scale import deployment
from ..container_scale.config import logical_topology
from ..container_scale.runner import run as baseline_run, workload, read_rows
from ..distributed_reasoning_scalability import run_distributed_reasoning_scalability
from .actuator import RecoveryDeployment
from .pools import expanded_topology, routing_coverage, progress_assessment
from .policy import choose_expansion as choose, evidence, trigger


def save(path, data):
    path.write_text(json.dumps(data, indent=2, default=str)+'\n')


def supervise(config, benchmark, policy, output_root, *, input_dir=None, execute=False, scenarios=None):
    output = output_root/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
    output.mkdir(parents=True)
    save(output/'policy.json', policy)
    save(output/'configuration.json', config.raw)
    decisions = []
    save(output/'decisions.json', decisions)
    if input_dir is None:
        if not execute:
            raise ValueError('plan requires --input-dir')
        input_dir = baseline_run(config, benchmark, output/'baseline', scenario_names=scenarios, keep_going=True)
    input_dir = Path(input_dir).resolve()
    campaign = json.loads((input_dir/'campaign.json').read_text())
    archived = json.loads((input_dir/'configuration.json').read_text())
    # Do not silently change the archived workload, deadline or reasoner matrix.
    if archived != config.raw:
        raise ValueError('Configuration differs from campaign; use the archived effective configuration')
    save(output/'provenance.json', dict(baseline=str(input_dir), scope='Synthetic origin-preserving replica expansion', adaptation_strategy='origin-preserving-pools-v2', execute=execute, selected_scenarios=scenarios, coordinator_build_id=SOFTWARE_BUILD_ID,
        ontology_sha256={str(p): hashlib.sha256(benchmark.resolve(p).read_bytes()).hexdigest() for p in benchmark.ontology_files}))
    lifecycle_raw = deepcopy(config.raw)
    lifecycle_raw['deployment']['operation_timeout_seconds'] = policy['supervisor']['operation_timeout_seconds']
    lifecycle = replace(config, raw=lifecycle_raw)
    steps = [s for s in campaign['steps'] if not scenarios or s['scenario'] in scenarios]
    if not steps or (scenarios and set(scenarios)-{s['scenario'] for s in steps}):
        raise ValueError('Unknown or empty scenario selection')
    for step in steps:
        count = step['containers_per_host']
        scenario = next(s for s in config.raw['scenarios'] if s['name'] == step['scenario'])
        baseline = input_dir/f'placement-{count}'/step['scenario']/'measured/distributed-reasoning-scalability'
        for layout in config.experiment['layouts']:
            observed = evidence(baseline, layout)
            if not observed['preparations']:
                decisions.append(dict(scenario=step['scenario'], layout=layout, attempt=0, containers_per_host=count,
                    status='abstained', before=observed, decision=dict(action='abstain', reason='No preparation evidence available')))
                save(output/'decisions.json', decisions)
                continue
            if not trigger(policy, observed):
                decisions.append(dict(scenario=step['scenario'], layout=layout, attempt=0,
                    containers_per_host=count, status='not_needed', before=observed,
                    decision=dict(action='none', reason='No configured failure threshold exceeded in this layout')))
                save(output/'decisions.json', decisions)
                continue
            placements = {f'{n.node_id}-c{i}': n.node_id for n in config.topology.active_nodes for i in range(1, count+1)}
            origin_topology = logical_topology(config, max(config.deployment['containers_per_host']))
            replicas = []
            tried = set()
            for attempt in range(1, policy['supervisor']['max_attempts']+1):
                token = uuid.uuid4().hex[:12]
                folder = output/f"{step['scenario']}-{layout}-{count}-{attempt}"
                folder.mkdir()
                row = dict(scenario=step['scenario'], layout=layout, attempt=attempt, containers_per_host=count,
                    idempotency_key=token, replication_version=attempt, before=observed,
                    status='observing', categories=['ADAPT','NODE','GOV','AUD','OPS'],
                    started_at=datetime.now(timezone.utc).isoformat())
                decisions.append(row)
                save(output/'decisions.json', decisions)
                actuator = None
                print(f"[adaptive-monitoring] scenario={step['scenario']} layout={layout} attempt={attempt}/{policy['supervisor']['max_attempts']} status=observing", flush=True)
                started = monotonic()
                try:
                    if execute:
                        # Start stopped baseline services, but never stop/restart a running origin.
                        for node in config.topology.active_nodes:
                            ids = [n.node_id for n in origin_topology.active_nodes if n.host==node.host]
                            deployment.compose(lifecycle, benchmark.root, node, 'start', *ids)
                        deployment.wait_ready(lifecycle, origin_topology)
                    probes = deployment.doctor(lifecycle, count)
                    save(folder/'probes.json', probes)
                    decision = choose(policy, config, probes, observed, layout, count, replicas=replicas, tried=tried)
                    row['decision'] = decision
                    row['status'] = 'abstained' if decision['action'] == 'abstain' else 'planned'
                    save(output/'decisions.json', decisions)
                    if decision['action'] == 'abstain' or not execute:
                        break
                    # The entire replacement topology must fit, not only the selected host.
                    if not all(p['ready'] for p in probes):
                        row.update(status='abstained', reason='Recovery ensemble cannot fit on all hosts')
                        break
                    tried.add((decision['source'], decision['destination']))
                    replica_id = f"{decision['source']}-r{attempt}"
                    proposed_replicas = [*replicas, dict(id=replica_id, owner=decision['source'], host=decision['destination'])]
                    proposed = {**placements, **{r['id']:r['host'] for r in proposed_replicas}}
                    # Reject an undersampled archived workload before deploying unused capacity.
                    pool_sizes = Counter(r['owner'] for r in proposed_replicas)
                    needed_requests = len(placements) * (1 + max(pool_sizes.values()))
                    if layout == 'distributed':
                        needed_requests = 1 + max(pool_sizes.values())
                    available_requests = scenario['query_rounds'] * min(scenario['concurrency'])
                    if available_requests < needed_requests:
                        row.update(status='abstained', stop_reason='Insufficient request budget for replica coverage; rerun baseline with more query_rounds',
                                   required_requests_per_stratum=needed_requests,
                                   configured_minimum_requests=available_requests)
                        break
                    occupancy = Counter(proposed.values())
                    insufficient = [p['host_id'] for p in probes if occupancy[p['host_id']] and (
                        p.get('memory_available_mib', 0) < occupancy[p['host_id']] * config.deployment['memory_mib_per_container'] + config.deployment['reserve_memory_mib']
                        or p.get('cpu_count', 0) < occupancy[p['host_id']] * config.deployment['cpu_per_container'])]
                    if insufficient:
                        row.update(status='abstained', stop_reason='Cumulative ensemble capacity insufficient', capacity_hosts=insufficient)
                        break
                    row['placements_before'] = {**placements, **{r['id']:r['host'] for r in replicas}}
                    row['replicas'] = proposed_replicas
                    owners = {r['id']:r['owner'] for r in proposed_replicas}
                    row['replica_owners'] = owners
                    row['placements_after'] = proposed
                    topology = expanded_topology(config, count, proposed_replicas, policy['supervisor']['recovery_port'])
                    actuator = RecoveryDeployment(lifecycle, benchmark.root, topology, folder/'deployment', token, replica_owners=owners)
                    row['status'] = 'deploying'
                    save(output/'decisions.json', decisions)
                    actuator.start()
                    row['deployment_seconds'] = monotonic()-started
                    row['status'] = 'verifying'
                    row['phase_times'] = dict(verification_started_at=datetime.now(timezone.utc).isoformat())
                    save(output/'decisions.json', decisions)
                    from .telemetry import Sampler
                    with Sampler(actuator, folder/'service-samples.jsonl', policy['supervisor']['telemetry_interval_seconds']):
                        # Same users, seed, request budgets, concurrency, repetitions and layouts.
                        if config.experiment['warmup']:
                            row['phase_times']['warmup_started_at'] = datetime.now(timezone.utc).isoformat()
                            run_distributed_reasoning_scalability(benchmark,
                                workload(config, scenario, len(placements), True),
                                'physical', folder/'warmup', topology.endpoints(), topology, replica_owners=owners, origin_topology=origin_topology)
                            row['phase_times']['warmup_finished_at'] = datetime.now(timezone.utc).isoformat()
                            deployment.wait_ready(config, origin_topology)
                            deployment.wait_ready(config, topology, node_ids=set(owners))
                        row['phase_times']['measured_started_at'] = datetime.now(timezone.utc).isoformat()
                        result = run_distributed_reasoning_scalability(benchmark,
                            workload(config, scenario, len(placements)), 'physical',
                            folder/'measured', topology.endpoints(), topology, query_each_repetition=True, replica_owners=owners, origin_topology=origin_topology)
                        row['phase_times']['measured_finished_at'] = datetime.now(timezone.utc).isoformat()
                    after = evidence(result, layout)
                    routing = read_rows(result/'replica-routing.csv')
                    origin_work = {r['logical_owner'] for r in routing if r['layout']==layout and r['is_origin'].lower()=='true' and r['status']=='completed' and float(r.get('process_cpu_ms') or 0)>0}
                    row['origins_with_observed_query_cpu'] = sorted(origin_work)
                    row['origin_work_verified'] = set(owners.values()) <= origin_work
                    row['routing_coverage'] = routing_coverage(routing, layout, proposed)
                    row['after'] = after
                    row['results'] = str(result.relative_to(output))
                    good = (after['preparations'] > 0 and after['preparation_failures'] == 0 and
                        after['requests'] > 0 and after['request_failures'] == 0 and row['origin_work_verified'] and row['routing_coverage']['complete'])
                    row['status'] = 'execution_recovered' if good else 'not_recovered'
                    row['semantic_validation'] = after['semantic_statuses']
                    # Preserve useful capacity if a new copy worsens completed work.
                    improved, regressed = progress_assessment(observed, after)
                    row['improved'] = improved
                    row['accepted'] = improved and row['routing_coverage']['complete']
                    if not row['routing_coverage']['complete']:
                        row['stop_reason'] = 'Insufficient routing coverage; increase query_rounds for both baseline and adaptive runs'
                    elif not improved:
                        row['stop_reason'] = 'No completion improvement; stop expansion and inspect request service time'
                    row['origin_preserved'] = all(topology.node(n).host == config.topology.node(host).host for n,host in placements.items())
                    if row['accepted']:
                        observed = after
                        replicas = proposed_replicas
                    else:
                        row['rollback_reason'] = 'No verified completion improvement; retain the preceding replica pool'
                    if not good and not row.get('stop_reason') and attempt == policy['supervisor']['max_attempts']:
                        row['stop_reason'] = 'Attempt budget exhausted; failures remain'
                except Exception as error:
                    import traceback
                    row.update(status='failed', error=str(error))
                    (folder/'failure.log').write_text(traceback.format_exc())
                finally:
                    cleanup_errors = []
                    if actuator:
                        try:
                            cleanup_errors = actuator.close()
                        except Exception as error:
                            cleanup_errors.append(dict(phase='recovery_cleanup', error=str(error)))
                    row['cleanup_errors'] = cleanup_errors
                    row['elapsed_seconds'] = monotonic()-started
                    row['finished_at'] = datetime.now(timezone.utc).isoformat()
                    save(output/'decisions.json', decisions)
                    if cleanup_errors:
                        raise RuntimeError('Cleanup/restore failed; inspect decisions.json before another recovery')
                    print(f"[adaptive-monitoring] scenario={step['scenario']} layout={layout} attempt={attempt} status={row['status']}", flush=True)
                if row['status'] != 'not_recovered' or row.get('stop_reason'):
                    break
    from .reporting import report
    report(output)
    return output

"""Fail-closed placement constraints and auditable ontology policy bindings."""

import json
import math
import tomllib
from collections import Counter, defaultdict
from pathlib import Path
import re

from ...ontology import load_graph
from ...synthetic import EX
from ..container_scale.runner import read_rows


def load_policy(path, benchmark):
    policy = tomllib.loads(Path(path).read_text())
    s = policy['supervisor']
    for key in ('telemetry_interval_seconds', 'max_attempts', 'minimum_failures', 'operation_timeout_seconds', 'recovery_port', 'max_replicas_per_authority', 'max_extra_containers_per_host'):
        if type(s[key]) is not int or s[key] < 1:
            raise ValueError(f'{key} must be a positive integer')
    if not 1024 <= s['recovery_port'] <= 65000:
        raise ValueError('Invalid recovery port')
    for key in ('max_failure_fraction', 'minimum_trust'):
        if not math.isfinite(s[key]) or not 0 <= s[key] <= 1:
            raise ValueError(f'{key} must be in [0, 1]')
    if policy['authorization']['workload'] != 'synthetic-container-scale':
        raise ValueError('Only synthetic experiment authorization is implemented')
    if type(policy['authorization']['allow_cross_tier']) is not bool:
        raise ValueError('allow_cross_tier must be boolean')
    if any(not math.isfinite(v) or not 0 <= v <= 1 for v in policy['trust'].values()):
        raise ValueError('Trust scores must be finite and in [0, 1]')
    graph = load_graph(benchmark.resolve(p) for p in benchmark.ontology_files)
    declared = {str(value): subject for subject, value in graph.subject_objects(EX.policyIdentifier)}
    required = {'P-ADAPT-01', 'P-ADAPT-04', 'P-ADAPT-06', 'P-ADAPT-07', 'P-ADAPT-08'}
    if not required <= set(s['policy_ids']) or set(s['policy_ids']) - declared.keys():
        raise ValueError('Missing required or unknown ontology policy bindings')
    policy['bindings'] = [dict(identifier=p, uri=str(declared[p]),
        facts=sorted((str(predicate), str(value)) for predicate, value in graph.predicate_objects(declared[p])))
        for p in s['policy_ids']]
    return policy


def evidence(directory, layout):
    """Keep preparation/service symptoms separate from application requests."""
    rows = [r for r in read_rows(directory/'distributed-reasoning-summary.csv') if r['layout'] == layout]
    queries = [r for r in read_rows(directory/'query-scalability.csv') if r['layout'] == layout]
    errors = [r.get('error', '') for r in rows if r['status'] != 'completed']
    sources = Counter()
    for message in errors:
        match = re.search(r'role=([\w-]+)', message)
        if match:
            sources[match.group(1)] += 1
    query_sources = Counter()
    strata = defaultdict(lambda: dict(requests=0, request_failures=0, query_source_counts=Counter()))
    for row in queries:
        group = strata[(row.get('reasoner', 'unknown'), int(row['concurrency']))]
        group['requests'] += int(row['client_requests'])
        group['request_failures'] += int(row['error_count'])
        for message in json.loads(row.get('error_details') or '[]'):
            match = re.search(r'role=([\w-]+)', message)
            if match:
                query_sources[match.group(1)] += 1
                group['query_source_counts'][match.group(1)] += 1
    attempts = sum(int(r['client_requests']) for r in queries)
    failures = sum(int(r['error_count']) for r in queries)
    return dict(preparations=len(rows), preparation_failures=len(errors),
        requests=attempts, request_failures=failures,
        failure_fraction=failures/attempts if attempts else None,
        source_counts=dict(sources), query_source_counts=dict(query_sources), errors=errors,
        query_strata=[dict(reasoner=k[0], concurrency=k[1], **v,
            failure_fraction=v['request_failures']/v['requests'] if v['requests'] else None)
            for k,v in sorted(strata.items())],
        semantic_statuses=sorted({r.get('semantic_equivalence_status', '') for r in rows}))


def trigger(policy, observations):
    """Evaluate each concurrency/reasoner independently; never dilute a failing stratum."""
    s = policy['supervisor']
    if observations['preparation_failures'] >= s['minimum_failures']:
        return dict(cause='preparation_failure', counts=observations['source_counts'], strata=[])
    groups = observations.get('query_strata') or [observations]
    breached = [g for g in groups if g['request_failures'] >= s['minimum_failures']
        and g.get('failure_fraction') is not None
        and g['failure_fraction'] > s['max_failure_fraction']]
    if breached:
        counts = Counter()
        for g in breached:
            counts.update(g.get('query_source_counts', {}))
        return dict(cause='application_request_failure', counts=dict(counts),
            strata=[{k:v for k,v in g.items() if k in
                ('reasoner','concurrency','requests','request_failures','failure_fraction')} for g in breached])
    return None


def choose(policy, config, probes, observations, layout, count, *, placements=None, tried=()):
    """Rank feasible cumulative placements; never repeat a tried source/destination."""
    s = policy['supervisor']
    signal = trigger(policy, observations)
    if not signal:
        return dict(action='abstain', reason='Configured failure threshold not reached')
    counts = signal['counts']
    if not counts:
        return dict(action='abstain', reason='Failure source is unavailable; fresh worker-attributed evidence is required')
    hosts = {n.node_id: n for n in config.topology.active_nodes}
    placements = placements or {f'{h}-c{i}':h for h in hosts for i in range(1,count+1)}
    occupancy = Counter(placements.values())
    rejected = []
    for source in sorted(counts, key=lambda k: (-counts[k], k)):
        source_host = placements.get(source)
        if source_host not in hosts:
            rejected.append(dict(source=source, reasons=['unknown failure source']))
            continue
        candidates = []
        for probe in probes:
            host_id = probe['host_id']
            node = hosts[host_id]
            slots = occupancy.get(host_id, 0) + 1
            ram = slots * config.deployment['memory_mib_per_container'] + config.deployment['reserve_memory_mib']
            cpu = slots * config.deployment['cpu_per_container']
            trust = policy['trust'].get(host_id, -1)
            allowed = host_id in policy['authorization']['allowed_destinations']
            allowed &= policy['authorization']['allow_cross_tier'] or node.tier == hosts[source_host].tier
            reasons = []
            if host_id == source_host: reasons.append('source host excluded')
            if (source, host_id) in tried: reasons.append('placement already attempted')
            if not allowed: reasons.append('destination not authorized')
            if trust < s['minimum_trust']: reasons.append('insufficient declared trust')
            if not probe.get('ready'): reasons.append('runtime/capacity probe failed')
            if probe.get('memory_available_mib', 0) < ram: reasons.append('insufficient residual RAM')
            if probe.get('cpu_count', 0) < cpu: reasons.append('insufficient CPU capacity')
            if reasons:
                rejected.append(dict(source=source, host=host_id, reasons=reasons))
            else:
                candidates.append(dict(host=host_id, trust=trust,
                    residual_ram_mib=probe['memory_available_mib']-ram,
                    residual_cpu=probe['cpu_count']-cpu))
        candidates.sort(key=lambda r: (-r['trust'], -r['residual_ram_mib'], -r['residual_cpu'], r['host']))
        if candidates:
            return dict(action='rebuild_fragment_service' if layout == 'distributed' else 'rebuild_replica_service',
                source=source, source_host=source_host, destination=candidates[0]['host'], cause=signal['cause'],
                trigger_strata=signal['strata'], candidates=candidates, rejected=rejected, policy_ids=s['policy_ids'],
                ranking='Failure count, declared trust, residual RAM, residual CPU, stable host ID')
    return dict(action='abstain', reason='No untried authorized destination with sufficient capacity', rejected=rejected)


def choose_expansion(policy, config, probes, observations, layout, count, *, replicas=(), tried=()):
    """Add read-only capacity while every original authority remains at its host."""
    signal=trigger(policy,observations)
    if not signal:return dict(action='abstain',reason='Configured failure threshold not reached')
    if observations['preparation_failures']:
        return dict(action='abstain',reason='Preparation failed: copying the same fragment cannot reduce its preparation cost; original authorities must remain active')
    counts=signal['counts']
    if not counts:return dict(action='abstain',reason='Failure source unavailable; worker-attributed evidence required')
    s=policy['supervisor'];hosts={n.node_id:n for n in config.topology.active_nodes}
    extras=Counter(r['host'] for r in replicas);copies=Counter(r['owner'] for r in replicas)
    rejected=[]
    for source in sorted(counts,key=lambda k:(-counts[k],k)):
        source_host=source.rsplit('-c',1)[0]
        if source_host not in hosts:continue
        if copies[source]>=s.get('max_replicas_per_authority',2):
            rejected.append(dict(source=source,reasons=['authority replica limit reached']));continue
        candidates=[]
        for p in probes:
            host=p['host_id'];node=hosts[host];slots=count+extras[host]+1
            reasons=[]
            if host==source_host:reasons.append('keep overload capacity on a different host')
            if (source,host) in tried or any(r['owner']==source and r['host']==host for r in replicas):reasons.append('destination already attempted for this authority')
            if host not in policy['authorization']['allowed_destinations']:reasons.append('destination not authorized')
            if not policy['authorization']['allow_cross_tier'] and node.tier!=hosts[source_host].tier:reasons.append('cross-tier placement not authorized')
            trust=policy['trust'].get(host,-1)
            if trust<s['minimum_trust']:reasons.append('insufficient declared trust')
            if not p.get('ready'):reasons.append('runtime probe failed')
            if extras[host]>=s.get('max_extra_containers_per_host',2):reasons.append('host expansion limit reached')
            ram=slots*config.deployment['memory_mib_per_container']+config.deployment['reserve_memory_mib']
            cpu=slots*config.deployment['cpu_per_container']
            if p.get('memory_available_mib',0)<ram:reasons.append('insufficient residual RAM')
            if p.get('cpu_count',0)<cpu:reasons.append('insufficient CPU capacity')
            if reasons:rejected.append(dict(source=source,host=host,reasons=reasons));continue
            candidates.append(dict(host=host,cloud=node.tier=='cloud',existing_extras=extras[host],trust=trust,
                residual_ram_mib=p['memory_available_mib']-ram,residual_cpu=p['cpu_count']-cpu))
        candidates.sort(key=lambda r:(r['cloud'],r['existing_extras'],-r['trust'],-r['residual_ram_mib'],-r['residual_cpu'],r['host']))
        if candidates:
            return dict(action='add_fragment_replica' if layout=='distributed' else 'add_service_replica',source=source,
                source_host=source_host,destination=candidates[0]['host'],cause=signal['cause'],trigger_strata=signal['strata'],
                origin_retained=True,candidates=candidates,rejected=rejected,policy_ids=s['policy_ids'],
                ranking='Eligible non-Cloud hosts first, fewer extra containers, trust, residual RAM/CPU, stable ID')
    return dict(action='abstain',reason='No eligible expansion destination within capacity and replica limits',rejected=rejected)

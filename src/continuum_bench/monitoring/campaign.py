"""Reproducible physical campaigns through infrastructure, reasoner and result ports."""
from __future__ import annotations
from .budget import unlimited_execution, wait_timeout, execution_metadata
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import time
import uuid

from ..core import ResultSink
from ..reasoners import get_reasoner
from .campaign_config import CampaignConfig
from .campaign_infrastructure import Infrastructure
from .campaign_results import StructuredResults
from .load_benchmark import _local_timeout
from .workloads import build_workload, query_for, result_keys, digest


def _percentile(values, fraction):
    values = sorted(values)
    return values[min(len(values)-1, int((len(values)-1)*fraction))] if values else None


def execute_campaign(config: CampaignConfig, infrastructure: Infrastructure, sink: ResultSink,
                     *, reasoners=get_reasoner) -> int:
    nodes = infrastructure.inventory()
    points = list(config.points())
    if max(w.physical_nodes for _, _, w in points) > len(nodes):
        raise ValueError('Requested physical node count exceeds the discovered inventory')
    for name in config.reasoners:
        reasoners(name)  # Fail before any worker mutation for unsupported engines.
    failures = 0
    for axis, value, workload in points:
        selected = nodes[:workload.physical_nodes]
        for reasoner in config.reasoners:
            # Canonical reference is shared across layouts. Its time is kept outside measurements.
            reference_start = time.perf_counter()
            reference_error = ""
            try:
                with _local_timeout(config.point_timeout_seconds):
                    reference_graph = reasoners(reasoner).materialize(build_workload(workload, config.seed)).graph
                    expected = [digest(result_keys(reference_graph, query_for(workload, i, config.policy_categories)))
                                for i in range(workload.query_count)]
            except Exception as exc:
                reference_error = f"{type(exc).__name__}: {exc}"
            reference_ms = (time.perf_counter()-reference_start)*1000
            for mode in config.modes:
                for repetition in range(config.repetitions):
                    token = uuid.uuid4().hex
                    started = time.perf_counter()
                    deadline = float("inf") if unlimited_execution() else started + config.point_timeout_seconds
                    common = {'execution_policy': execution_metadata(), 'execution_id': token, 'timestamp': datetime.now(timezone.utc).isoformat(),
                              'configuration_id': config.fingerprint, 'axis': axis, 'axis_value': value,
                              'reasoner': reasoner, 'mode': mode, 'repetition': repetition,
                              'seed': config.seed, 'workload': asdict(workload),
                              'policy_categories': config.policy_categories, 'nodes': selected,
                              'timeout_seconds': config.point_timeout_seconds, 'reference_ms': reference_ms}
                    if reference_error:
                        failures += 1
                        sink.write({**common, 'status': 'reference_failed', 'error': reference_error})
                        continue
                    prepared = []
                    events = []
                    status, error = 'completed', ''
                    executor = ThreadPoolExecutor(max_workers=max(workload.concurrency, len(selected)))
                    def remaining():
                        left = deadline-time.perf_counter()
                        if left <= 0:
                            raise TimeoutError('Campaign point budget exceeded')
                        return min(config.request_timeout_seconds, left)
                    def run_query(request):
                        queued = time.perf_counter()
                        index = request % workload.query_count
                        targets = [selected[request % len(selected)]] if mode == 'replicated' else selected
                        responses = [infrastructure.call(node, 'query', {'token': token, 'query_index': index}, remaining()) for node in targets]
                        keys = [key for response in responses for key in response['result_keys']]
                        elapsed = (time.perf_counter()-queued)*1000
                        return {'request': request, 'query_index': index, 'category': responses[0]['category'],
                                'policy_ids': responses[0]['policy_ids'], 'complexity': workload.query_complexity,
                                'latency_ms': elapsed, 'query_execution_ms': sum(r['execution_ms'] for r in responses),
                                'cpu_ms': sum(r['cpu_ms'] for r in responses),
                                'rss_mib': max((r['rss_mib'] for r in responses if r['rss_mib'] is not None), default=None),
                                'valid': digest(keys) == expected[index]}
                    try:
                        print(f'[campaign] axis={axis} value={value} reasoner={reasoner} mode={mode} repetition={repetition}', flush=True)
                        futures = [executor.submit(infrastructure.call, node, 'prepare', {
                            'workload': asdict(workload), 'seed': config.seed, 'reasoner': reasoner,
                            'policy_categories': config.policy_categories, 'token': token,
                            'owner': index if mode != 'replicated' else 0,
                            'owners': len(selected) if mode != 'replicated' else 1,
                        }, remaining()) for index, node in enumerate(selected)]
                        prepared = [future.result(timeout=wait_timeout(remaining())) for future in futures]
                        for i in range(config.warmup):
                            run_query(i)
                        query_started = time.perf_counter()
                        # Fixed-size batches bound submitted work and ensure concurrency is an actual limit.
                        for first in range(0, workload.requests, workload.concurrency):
                            futures = [executor.submit(run_query, i) for i in range(first, min(first+workload.concurrency, workload.requests))]
                            events.extend(f.result(timeout=wait_timeout(remaining())) for f in futures)
                        query_seconds = time.perf_counter()-query_started
                        if not all(event['valid'] for event in events):
                            status = 'invalid_results'
                    except Exception as exc:
                        error = f'{type(exc).__name__}: {exc}'
                        status = 'timeout' if isinstance(exc, TimeoutError) or 'timeout' in error.lower() or 'timed out' in error.lower() or '408' in error else 'failed'
                        query_seconds = None
                    finally:
                        # HTTP calls have their own deadline. Drain them before preparing the next point.
                        executor.shutdown(wait=True, cancel_futures=True)
                    if status != 'completed':
                        failures += 1
                    elapsed = (time.perf_counter()-started)*1000
                    latencies = [e['latency_ms'] for e in events]
                    cpu_ms = sum(p['cpu_ms'] for p in prepared)+sum(e['cpu_ms'] for e in events)
                    sink.write({**common, 'status': status, 'error': error,
                                'execution_ms': elapsed, 'reasoning_ms': sum(p['reasoning_ms'] for p in prepared),
                                'query_execution_ms': sum(e['query_execution_ms'] for e in events),
                                'cpu_ms': cpu_ms, 'cpu_percent_one_core_sum': 100*cpu_ms/elapsed if elapsed else None,
                                'rss_mib': max((p['rss_mib'] for p in [*prepared,*events] if p['rss_mib'] is not None), default=None),
                                'input_triples': sum(p['input_triples'] for p in prepared),
                                'output_triples': sum(p['output_triples'] for p in prepared),
                                'latency_p50_ms': _percentile(latencies, .5), 'latency_p95_ms': _percentile(latencies, .95),
                                'throughput_rps': len(events)/query_seconds if query_seconds else None,
                                'completed_requests': len(events), 'unobserved_requests': workload.requests-len(events),
                                'result_validation_rate': sum(e['valid'] for e in events)/len(events) if events else None,
                                'events': events})
    return failures


def run_campaign(config: CampaignConfig, infrastructure: Infrastructure, output: Path) -> tuple[Path, int]:
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    directory = output/run_id
    sink = StructuredResults(directory, {'execution_policy': execution_metadata(), 'run_id': run_id, 'configuration': config.public(),
        'configuration_id': config.fingerprint, 'python': platform.python_version(),
        'platform': platform.platform(), 'workload_kind': 'synthetic policy microbenchmark'})
    from .provenance import snapshot
    root = Path(__file__).resolve().parents[3]
    provenance = snapshot(root, directory)
    (directory/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    (directory/'campaign.toml').write_text(config.path.read_text())
    try:
        failures = execute_campaign(config, infrastructure, sink)
    except Exception as error:
        sink.write({'configuration_id': config.fingerprint, 'status': 'setup_failed',
                    'error': f'{type(error).__name__}: {error}'})
        raise
    finally:
        sink.close()
    return directory, failures

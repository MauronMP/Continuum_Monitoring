"""Worker-side workload execution through reasoner and metric ports."""
from dataclasses import asdict
from ..core import MetricCollector
from ..reasoners import get_reasoner
from .campaign_config import Workload
from .metrics import ProcessMetrics, measured
from .workloads import build_workload, query_for, result_keys, digest

class CampaignRuntime:
    def __init__(self, metrics: MetricCollector | None = None, reasoners=get_reasoner):
        self.metrics = metrics or ProcessMetrics()
        self.reasoners = reasoners
        self.graph = None

    def prepare(self, payload):
        self.graph = None
        workload = Workload(**payload['workload'])
        before = self.metrics.snapshot()
        source = build_workload(workload, int(payload['seed']), int(payload.get('owner', 0)), int(payload.get('owners', 1)))
        result = self.reasoners(payload['reasoner']).materialize(source)
        self.graph = result.graph
        self.workload = workload
        self.categories = tuple(payload['policy_categories'])
        self.token = payload['token']
        return {**measured(before, self.metrics.snapshot()), 'reasoning_ms': result.duration_ms,
                'input_triples': result.input_triples, 'output_triples': result.output_triples,
                'token': self.token}

    def execute(self, payload):
        if self.graph is None or payload['token'] != self.token:
            raise ValueError('Campaign state is absent or belongs to another execution')
        before = self.metrics.snapshot()
        query = query_for(self.workload, int(payload['query_index']), self.categories)
        keys = result_keys(self.graph, query)
        return {**measured(before, self.metrics.snapshot()), 'query_id': query.identifier,
                'category': query.category, 'policy_ids': query.policy_ids,
                'complexity': query.complexity, 'result_count': len(keys),
                'result_digest': digest(keys), 'result_keys': keys}

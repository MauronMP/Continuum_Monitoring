"""Unlimited execution must complete slow work, not hide failed work."""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from continuum_bench.monitoring.budget import (
    execution_policy, execution_metadata, local_phase_timeout,
    remaining_seconds, wait_timeout, PhaseBudgetTimeout,
)
from continuum_bench.monitoring.distributed import _request
from continuum_bench.monitoring.load_benchmark import _local_timeout
from continuum_bench.monitoring.suite import suite_plan


def test_unlimited_local_and_future_waits_exceed_budget():
    with execution_policy(True):
        for timer in (local_phase_timeout, _local_timeout):
            with timer(0.001):
                time.sleep(0.02)
        assert remaining_seconds(time.monotonic()-10, 0.001) == float('inf')
        with ThreadPoolExecutor() as executor:
            assert executor.submit(lambda: (time.sleep(0.02), 42)[1]).result(timeout=wait_timeout(0.001)) == 42
        assert execution_metadata()['configured_budgets_enforced'] is False
    with pytest.raises(PhaseBudgetTimeout):
        remaining_seconds(time.monotonic()-10, 0.001)


def test_unlimited_http_disables_worker_alarm_and_socket_deadline():
    received=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_POST(self):
            received.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            time.sleep(0.04)
            self.send_response(500 if self.path=='/failure' else 200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with execution_policy(True):
            url=f'http://127.0.0.1:{server.server_port}'
            assert _request(url,'/queries',{'phase_timeout_seconds':0.001},timeout=0.001)['status']=='ok'
            with pytest.raises(Exception):
                _request(url,'/failure',{},timeout=0.001)
        assert all(p['phase_timeout_seconds']==0 for p in received)
    finally:
        server.shutdown();server.server_close();thread.join()


def test_unlimited_suite_propagates_policy_to_all_physical_families(root,tmp_path):
    plan=suite_plan(root,root/'configs/benchmark.toml',tmp_path,unlimited=True)
    for step in plan:
        if step['name']!='software':
            assert '--unlimited' in step['command']
            assert '--keep-going' in step['command']

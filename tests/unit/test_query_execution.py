from threading import Barrier, Event, Lock

from continuum_bench import experiment
from continuum_bench.config import load_config
from continuum_bench.query_execution import _physical_query, execute_logical_query
from continuum_bench.topology import Host, Topology


def _hosts(count=3):
    return tuple(Host(f"edge{index}", "edge", f"p{index}", "127.0.0.1", 8400 + index) for index in range(count))


def _query(query_id="Q1", scope="authorities"):
    return {
        "id": query_id,
        "query": "SELECT ?s WHERE { ?s ?p ?o }",
        "execution_scope": scope,
        "merge_strategy": "set_union",
        "kind": "inventory",
    }


def _response(host):
    return {
        "outcome": {
            "duration_ms": 1.0,
            "result_count": 1,
            "result_digest": f"digest-{host}",
            "result_keys": [host],
            "ask_result": False,
        }
    }


def test_single_fanout_issues_one_request():
    calls = []

    def request(url, **_kwargs):
        calls.append(url)
        return _response(url)

    logical, physical = execute_logical_query(
        _hosts(),
        _query(scope="authority_key:user-a"),
        1,
        0,
        "distributed",
        physical_timeout=10,
        logical_timeout=10,
        request=request,
    )
    assert logical["fanout_size"] == 1
    assert logical["status"] == "completed"
    assert len(calls) == len(physical) == 1


def test_three_way_fanout_starts_all_requests_concurrently():
    barrier = Barrier(3)
    lock = Lock()
    active = 0
    maximum_active = 0

    def request(url, **_kwargs):
        nonlocal active, maximum_active
        with lock:
            active += 1
            maximum_active = max(maximum_active, active)
        barrier.wait(timeout=2)
        with lock:
            active -= 1
        return _response(url)

    logical, physical = execute_logical_query(
        _hosts(),
        _query(),
        1,
        0,
        "distributed",
        physical_timeout=10,
        logical_timeout=10,
        request=request,
    )
    assert logical["status"] == "completed"
    assert logical["fanout_size"] == 3
    assert logical["result_count"] == 3
    assert logical["result_digest"] is not None
    assert len(physical) == 3
    assert maximum_active == 3


def test_partial_failure_has_no_complete_logical_digest():
    def request(url, **_kwargs):
        if ":8401" in url:
            raise RuntimeError("worker failed")
        return _response(url)

    logical, physical = execute_logical_query(
        _hosts(),
        _query(),
        1,
        0,
        "distributed",
        physical_timeout=10,
        logical_timeout=10,
        request=request,
    )
    assert logical["status"] == "failed"
    assert logical["result_digest"] is None
    assert logical["result_count"] is None
    assert logical["failed_hosts"] == ["edge1"]
    assert len(logical["partial_results"]) == 2
    assert sum(row["status"] == "completed" for row in physical) == 2


def test_one_physical_timeout_marks_whole_logical_query_timed_out():
    def request(url, **_kwargs):
        if ":8402" in url:
            raise RuntimeError("worker request timed out")
        return _response(url)

    logical, physical = execute_logical_query(
        _hosts(),
        _query(),
        1,
        0,
        "distributed",
        physical_timeout=10,
        logical_timeout=20,
        request=request,
    )
    assert logical["status"] == "query_timeout"
    assert logical["result_digest"] is None
    assert logical["failed_hosts"] == ["edge2"]
    assert len(logical["partial_results"]) == 2
    assert [row["status"] for row in physical].count("query_timeout") == 1


def test_logical_deadline_marks_pending_fanout_and_preserves_hosts():
    release = Event()

    def request(url, **_kwargs):
        release.wait(timeout=2)
        return _response(url)

    def deadline_wait(futures, timeout):
        assert timeout <= 10
        return set(), set(futures)

    logical, physical = execute_logical_query(
        _hosts(),
        _query(),
        1,
        0,
        "distributed",
        physical_timeout=30,
        logical_timeout=10,
        request=request,
        wait_for_futures=deadline_wait,
    )
    release.set()
    assert logical["status"] == "query_timeout"
    assert logical["result_digest"] is None
    assert sorted(logical["pending_hosts"]) == ["edge0", "edge1", "edge2"]
    assert all(row["status"] == "query_timeout" for row in physical)


def test_completed_physical_request_cannot_make_an_expired_logical_query_valid():
    class ControlledClock:
        def __init__(self):
            self.value = 0.0
            self.lock = Lock()

        def __call__(self):
            with self.lock:
                return self.value

        def advance_to(self, value):
            with self.lock:
                self.value = value

    clock = ControlledClock()
    observed_timeouts = []

    def request(url, **kwargs):
        observed_timeouts.append(kwargs["timeout"])
        clock.advance_to(2.0)
        return _response(url)

    def completed_wait(futures, timeout):
        assert timeout <= 1.0
        for future in futures:
            future.result()
        return set(futures), set()

    logical, physical = execute_logical_query(
        _hosts(1),
        _query(scope="authority_key:user-a"),
        1,
        0,
        "distributed",
        physical_timeout=120,
        logical_timeout=1,
        request=request,
        clock=clock,
        wait_for_futures=completed_wait,
    )
    assert observed_timeouts == [1.0]
    assert physical[0]["status"] == "completed"
    assert logical["status"] == "query_timeout"
    assert logical["result_digest"] is None
    assert logical["partial_results"][0]["host"] == "edge0"


def test_physical_timeout_is_capped_by_remaining_logical_budget():
    observed = []
    times = iter([8.0, 8.5])

    def request(_url, **kwargs):
        observed.append(kwargs["timeout"])
        return _response("edge0")

    row = _physical_query(_hosts(1)[0], _query(), 1, 10.0, 120.0, request, lambda: next(times))
    assert observed == [2.0]
    assert row["status"] == "completed"


def test_catalog_round_aborts_after_first_logical_timeout(monkeypatch):
    calls = []

    def execute(_hosts, query, round_, *_args, **_kwargs):
        calls.append(query["id"])
        status = "query_timeout" if query["id"] == "Q2" else "completed"
        return (
            {
                "query_id": query["id"],
                "round": round_,
                "status": status,
                "failed_hosts": ["edge1"] if status == "query_timeout" else [],
            },
            [{"query_id": query["id"], "round": round_, "host": "edge1", "status": status}],
        )

    monkeypatch.setattr(experiment, "execute_logical_query", execute)
    queries = [_query("Q1"), _query("Q2"), _query("Q3")]
    logical, physical, aborted = experiment._catalog_round(_hosts(), queries, 1, "distributed", 10, 20)
    assert calls == ["Q1", "Q2"]
    assert [row["query_id"] for row in logical] == ["Q1", "Q2"]
    assert len(physical) == 2
    assert aborted == {"failed_round": 1, "failed_query_id": "Q2", "failed_hosts": ["edge1"]}


def test_catalog_rounds_do_not_start_next_round_after_timeout(monkeypatch):
    rounds = []

    def catalog_round(_hosts, queries, round_, _layout, _physical_timeout, _logical_timeout):
        rounds.append(round_)
        return (
            [
                {"query_id": queries[0]["id"], "round": round_, "status": "completed", "failed_hosts": []},
                {"query_id": queries[1]["id"], "round": round_, "status": "query_timeout", "failed_hosts": ["edge1"]},
            ],
            [{"query_id": queries[0]["id"], "round": round_, "host": "edge0", "status": "completed"}],
            {"failed_round": round_, "failed_query_id": queries[1]["id"], "failed_hosts": ["edge1"]},
        )

    monkeypatch.setattr(experiment, "_catalog_round", catalog_round)
    logical, _physical, catalog, aborted = experiment._catalog_rounds(
        _hosts(), [_query("Q1"), _query("Q2"), _query("Q3")], 18, "distributed", 10, 20, 100, 1
    )
    assert rounds == [1]
    assert [row["query_id"] for row in logical] == ["Q1", "Q2"]
    assert [row["round"] for row in catalog] == [1]
    assert aborted["failed_query_id"] == "Q2"


def test_timeout_recovery_uses_idle_workers_without_restart(root, monkeypatch):
    loaded = load_config(root / "configs/benchmark.toml")
    topology = Topology("test", _hosts())
    monkeypatch.setattr(experiment, "wait_ready", lambda *_args, **_kwargs: {"idle": True})
    monkeypatch.setattr(
        experiment, "restart_workers", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError())
    )
    result = experiment._recover_after_query_timeout(loaded, topology, {})
    assert result["recovered"] is True
    assert result["restart_required"] is False


def test_timeout_recovery_restarts_when_worker_remains_busy(root, monkeypatch):
    loaded = load_config(root / "configs/benchmark.toml")
    topology = Topology("test", _hosts())
    monkeypatch.setattr(experiment, "wait_ready", lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError()))
    monkeypatch.setattr(
        experiment,
        "restart_workers",
        lambda _config, _topology, host_ids: [
            {"host": host.id, "required": host.id in host_ids, "recovered": True} for host in topology.hosts
        ],
    )
    result = experiment._recover_after_query_timeout(loaded, topology, {})
    assert result["recovered"] is True
    assert result["restart_required"] is True
    assert {row["host"] for row in result["restart_evidence"]} == {host.id for host in topology.hosts}


def test_failed_restart_marks_timeout_recovery_unsuccessful(root, monkeypatch):
    loaded = load_config(root / "configs/benchmark.toml")
    topology = Topology("test", _hosts())
    monkeypatch.setattr(experiment, "wait_ready", lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError()))
    monkeypatch.setattr(
        experiment,
        "restart_workers",
        lambda _config, _topology, _host_ids: [
            {"host": host.id, "recovered": host.id != "edge1"} for host in topology.hosts
        ],
    )
    result = experiment._recover_after_query_timeout(loaded, topology, {})
    assert result["restart_required"] is True
    assert result["recovered"] is False


def test_worker_preparation_is_concurrent_for_ready_critical_path(monkeypatch):
    hosts = _hosts()
    barrier = Barrier(len(hosts))
    lock = Lock()
    active = 0
    maximum_active = 0

    def prepare(host, _payload, _timeout, _digest):
        nonlocal active, maximum_active
        with lock:
            active += 1
            maximum_active = max(maximum_active, active)
        barrier.wait(timeout=2)
        with lock:
            active -= 1
        return {"host": host.id}

    monkeypatch.setattr(experiment, "_prepare", prepare)
    fragments = {host.id: host.id.encode() for host in hosts}
    expected = {host.id: {"closure_digest": host.id} for host in hosts}
    prepared = experiment._prepare_workers(hosts, fragments, 10, expected)
    assert {row["host"] for row in prepared} == {host.id for host in hosts}
    assert maximum_active == len(hosts)

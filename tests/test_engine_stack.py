import pytest

from continuum_bench import engine_stack


def test_engine_stack_reuses_healthy_services(monkeypatch, tmp_path):
    compose_calls = []
    monkeypatch.setattr(engine_stack, "discover", lambda urls: [])
    monkeypatch.setattr(
        engine_stack,
        "_compose",
        lambda root, *arguments: compose_calls.append(arguments),
    )

    with engine_stack.semantic_engine_stack(tmp_path) as urls:
        assert urls == engine_stack.DEFAULT_ENGINE_URLS

    assert compose_calls == []


def test_engine_stack_starts_waits_and_stops_owned_services(
    monkeypatch,
    tmp_path,
):
    compose_calls = []
    discoveries = 0

    def discover_after_start(urls, **kwargs):
        nonlocal discoveries
        discoveries += 1
        if discoveries == 1:
            raise OSError("not running")
        return []

    monkeypatch.setattr(engine_stack, "discover", discover_after_start)
    monkeypatch.setattr(engine_stack, "preflight", lambda root: None)
    monkeypatch.setattr(
        engine_stack,
        "_compose",
        lambda root, *arguments: compose_calls.append(arguments),
    )

    with engine_stack.semantic_engine_stack(tmp_path):
        pass

    assert compose_calls == [
        ("build", "rdflib"),
        ("build", "jena"),
        ("up", "-d", "--no-build"),
        ("down",),
    ]


def _fake_started_stack(monkeypatch, calls):
    monkeypatch.setattr(
        engine_stack,
        "discover",
        lambda *a, **k: (_ for _ in ()).throw(OSError("offline")),
    )
    monkeypatch.setattr(engine_stack, "preflight", lambda root: None)
    monkeypatch.setattr(engine_stack, "_ready", lambda urls: [])
    monkeypatch.setattr(
        engine_stack, "_compose", lambda root, *args: calls.append(args)
    )


def test_startup_failure_keeps_original_error_and_collects_logs(monkeypatch, tmp_path):
    calls = []
    _fake_started_stack(monkeypatch, calls)
    original = RuntimeError("Jena unavailable")
    monkeypatch.setattr(
        engine_stack, "_ready", lambda urls: (_ for _ in ()).throw(original)
    )
    with pytest.raises(RuntimeError) as caught:
        with engine_stack.semantic_engine_stack(tmp_path):
            pytest.fail("A failed startup must not run benchmarks")
    assert caught.value is original
    assert ("ps", "-a") in calls
    assert ("logs", "--no-color", "--tail", "60") in calls
    assert ("down",) not in calls  # Do not delete diagnostics/unknown services.


def test_cleanup_failure_never_masks_query_error(monkeypatch, tmp_path):
    calls = []
    _fake_started_stack(monkeypatch, calls)

    def compose(root, *args):
        if args == ("down",):
            raise RuntimeError("socket permission denied")

    monkeypatch.setattr(engine_stack, "_compose", compose)
    with pytest.raises(AssertionError, match="EXT-Q68") as caught:
        with engine_stack.semantic_engine_stack(tmp_path):
            raise AssertionError("EXT-Q68")
    assert "socket permission denied" in caught.value.__notes__[0]


def test_cleanup_only_failure_is_explicit(monkeypatch, tmp_path):
    calls = []
    _fake_started_stack(monkeypatch, calls)

    def compose(root, *args):
        if args == ("down",):
            raise RuntimeError("shutdown failed")

    monkeypatch.setattr(engine_stack, "_compose", compose)
    with pytest.raises(RuntimeError, match="shutdown failed") as caught:
        with engine_stack.semantic_engine_stack(tmp_path):
            pass
    assert "Las pruebas finalizaron" in caught.value.__notes__[0]


def test_keep_running_does_not_stop_services(monkeypatch, tmp_path):
    calls = []
    _fake_started_stack(monkeypatch, calls)
    with engine_stack.semantic_engine_stack(tmp_path, keep_running=True):
        pass
    assert ("down",) not in calls

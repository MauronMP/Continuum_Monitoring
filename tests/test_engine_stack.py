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

    def discover_after_start(urls):
        nonlocal discoveries
        discoveries += 1
        if discoveries == 1:
            raise OSError("not running")
        return []

    monkeypatch.setattr(engine_stack, "discover", discover_after_start)
    monkeypatch.setattr(
        engine_stack,
        "_compose",
        lambda root, *arguments: compose_calls.append(arguments),
    )

    with engine_stack.semantic_engine_stack(tmp_path):
        pass

    assert compose_calls == [
        ("up", "-d", "--build"),
        ("down",),
    ]

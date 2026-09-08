import pytest
from continuum_bench import engine_stack

def test_reuses_native_services(monkeypatch, tmp_path):
    monkeypatch.setattr(engine_stack, "discover", lambda urls: [])
    with engine_stack.semantic_engine_stack(tmp_path) as urls:
        assert urls == engine_stack.DEFAULT_ENGINE_URLS

def test_missing_native_services_report_actionable_error(monkeypatch, tmp_path):
    def offline(urls):
        raise OSError("offline")
    monkeypatch.setattr(engine_stack, "discover", offline)
    with pytest.raises(RuntimeError, match="native services"):
        with engine_stack.semantic_engine_stack(tmp_path):
            pytest.fail("Unavailable services must fail before a benchmark")

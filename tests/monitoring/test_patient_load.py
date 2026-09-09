from dataclasses import replace
import pytest
from continuum_bench.monitoring import load_benchmark
from continuum_bench.monitoring.load_config import load_load_config
from continuum_bench.monitoring.distributed import Endpoint


@pytest.mark.parametrize('stop,expected',[(True,1),(False,2)])
def test_patient_load_attempts_later_profiles_after_prepare_timeout(config,tmp_path,monkeypatch,stop,expected):
    workload=load_load_config(config.root/'configs/load-smoke.toml')
    first=replace(workload.profiles[0],name='first',node_count=1)
    second=replace(first,name='second',events_per_second=first.events_per_second*2)
    workload=replace(workload,profiles=(first,second),repetitions=1,stop_after_timeout=stop)
    calls=[]
    monkeypatch.setattr(load_benchmark,'discover_load_endpoints',lambda *_:[Endpoint('http://worker:8391','cloud')])
    def timeout(*args,**kwargs):
        calls.append(args)
        raise TimeoutError('prepare timed out')
    monkeypatch.setattr(load_benchmark,'_parallel',timeout)
    load_benchmark.run_load_benchmark(replace(config,reasoners=('rdfs',)),workload,'physical',tmp_path)
    assert len(calls)==expected

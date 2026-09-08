"""Performance evaluation, experiment orchestration and result analysis."""

def export_physical_fragments(*args, **kwargs):
    from .physical_suite import export_physical_fragments as run
    return run(*args, **kwargs)

def run_physical_monitoring_suite(*args, **kwargs):
    from .physical_suite import run_physical_monitoring_suite as run
    return run(*args, **kwargs)

def run_distributed_monitoring_suite(*args, **kwargs):
    from .distributed_suite import run_distributed_monitoring_suite as run
    return run(*args, **kwargs)

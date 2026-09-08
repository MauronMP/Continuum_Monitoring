"""Fast workload-capacity checks performed before contacting any worker."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .config import BenchmarkConfig
from .experiment_config import ExperimentConfig, load_experiment_config
from .load_config import LoadBenchmarkConfig, load_load_config
from .ontology import load_graph
from .queries import load_catalog
from .synthetic import synthetic_triple_count


@dataclass(frozen=True)
class WorkloadTarget:
    source: str
    name: str
    users: int
    target_triples: int
    rule_count: int


def minimum_asserted_triples(base_triples: int, users: int, rules: int) -> int:
    """Exact graph size before optional neutral/semantic padding."""

    return (
        base_triples
        + synthetic_triple_count(users)
        + rules
        + (1 if rules else 0)
    )


def _targets_from_load(workload: LoadBenchmarkConfig) -> Iterable[WorkloadTarget]:
    for profile in workload.profiles:
        yield WorkloadTarget(
            source=str(workload.path),
            name=profile.name,
            users=profile.users,
            target_triples=profile.target_triples,
            rule_count=profile.rule_count,
        )


def _targets_from_experiment(
    workload: ExperimentConfig,
    source: str,
) -> Iterable[WorkloadTarget]:
    yield WorkloadTarget(
        source=source,
        name="scale_out",
        users=workload.scale_out_users,
        target_triples=workload.scale_out_target_triples,
        rule_count=workload.scale_out_rule_count,
    )
    for profile in workload.reasoning_profiles:
        yield WorkloadTarget(
            source=source,
            name=profile.name,
            users=profile.users,
            target_triples=profile.target_triples,
            rule_count=profile.rule_count,
        )


def validate_workload_targets(
    config: BenchmarkConfig,
    targets: Iterable[WorkloadTarget],
) -> dict[str, object]:
    """Reject target sizes that would require deleting asserted triples."""

    base_triples = len(
        load_graph(config.resolve(path) for path in config.ontology_files)
    )
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    configured_categories = set(config.category_order)
    catalog_categories = {spec.category for spec in specs}
    if configured_categories != catalog_categories:
        raise ValueError(
            "benchmark.category_order must cover the query catalog exactly; "
            f"missing={sorted(catalog_categories - configured_categories)}, "
            f"unknown={sorted(configured_categories - catalog_categories)}"
        )
    checked = 0
    errors: list[str] = []
    for target in targets:
        checked += 1
        minimum = minimum_asserted_triples(
            base_triples, target.users, target.rule_count
        )
        if target.target_triples and target.target_triples < minimum:
            errors.append(
                f"{Path(target.source).name}:{target.name}: "
                f"target_triples={target.target_triples} is below the asserted "
                f"minimum={minimum} (base={base_triples}, users={target.users}, "
                f"rules={target.rule_count})"
            )
    if errors:
        raise ValueError(
            "Invalid workload target(s); a benchmark may pad a graph but must "
            "not shrink it:\n- " + "\n- ".join(errors)
        )
    return {
        "ok": True,
        "base_triples": base_triples,
        "query_count": len(specs),
        "category_count": len(catalog_categories),
        "targets_checked": checked,
    }


def validate_load_workload(
    config: BenchmarkConfig,
    workload: LoadBenchmarkConfig,
) -> dict[str, object]:
    return validate_workload_targets(config, _targets_from_load(workload))


def validate_experiment_workload(
    config: BenchmarkConfig,
    workload: ExperimentConfig,
    source: str | Path,
) -> dict[str, object]:
    return validate_workload_targets(
        config, _targets_from_experiment(workload, str(source))
    )


def validate_default_workloads(
    config: BenchmarkConfig,
    load_path: str | Path,
    experiment_path: str | Path,
) -> dict[str, object]:
    load_workload = load_load_config(load_path)
    experiment_workload = load_experiment_config(experiment_path)
    load_report = validate_load_workload(config, load_workload)
    experiment_report = validate_experiment_workload(
        config, experiment_workload, experiment_path
    )
    return {"ok": True, "load": load_report, "experiments": experiment_report}

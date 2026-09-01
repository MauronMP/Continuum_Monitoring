from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class BenchmarkConfig:
    root: Path
    ontology_files: tuple[Path, ...]
    shape_files: tuple[Path, ...]
    query_catalog: Path
    topology_file: Path
    output_dir: Path
    reasoners: tuple[str, ...]
    category_order: tuple[str, ...]
    scale_users: tuple[int, ...]
    repetitions: int
    seed: int

    def resolve(self, path: Path) -> Path:
        return path if path.is_absolute() else self.root / path


def load_config(path: str | Path) -> BenchmarkConfig:
    config_path = Path(path).resolve()
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)
    root = config_path.parents[1]
    paths = raw["paths"]
    benchmark = raw["benchmark"]
    return BenchmarkConfig(
        root=root,
        ontology_files=tuple(Path(value) for value in paths["ontology_files"]),
        shape_files=tuple(Path(value) for value in paths["shape_files"]),
        query_catalog=Path(paths["query_catalog"]),
        topology_file=Path(paths.get("topology_file", "configs/topology.toml")),
        output_dir=Path(paths["output_dir"]),
        reasoners=tuple(benchmark["reasoners"]),
        category_order=tuple(benchmark["category_order"]),
        scale_users=tuple(int(value) for value in benchmark["scale_users"]),
        repetitions=int(benchmark["repetitions"]),
        seed=int(benchmark["seed"]),
    )

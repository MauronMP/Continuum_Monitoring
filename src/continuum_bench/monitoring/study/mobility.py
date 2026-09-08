"""Static positions and a registry for future mobility implementations."""
import random
from typing import Callable
from ...core.contracts import MobilityModel as MobilityStrategy
from .config import MobilityModel
from .models import MobilitySample

class StaticMobility:
    def __init__(self, config: MobilityModel):
        self.config = config
    def position_at(self, node_id: str, timestamp_s: float) -> MobilitySample:
        rng = random.Random(f"{self.config.seed}:{node_id}")
        return MobilitySample(timestamp_s, node_id,
            rng.uniform(0, self.config.area_width_m), rng.uniform(0, self.config.area_height_m),
            0, 0, 0, "static", "static")

_FACTORIES = {"static": StaticMobility}

def register_mobility_model(name: str, factory: Callable) -> None:
    if name in _FACTORIES:
        raise ValueError(f"Mobility model already registered: {name}")
    _FACTORIES[name] = factory

def build_mobility_strategy(config: MobilityModel) -> MobilityStrategy:
    if config.model not in _FACTORIES:
        raise ValueError(f"Mobility model {config.model!r} is reserved for a future plugin; only static positions are built in")
    return _FACTORIES[config.model](config)

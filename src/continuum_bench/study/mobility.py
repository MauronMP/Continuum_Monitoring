"""Deterministic, replayable mobility strategies for continuum experiments."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, degrees, hypot, pi, sin
import random
from typing import Protocol

from .config import MobilityModel
from .models import MobilitySample, Position


@dataclass
class MobilityState:
    position: Position
    destination: Position
    speed_mps: float
    direction_radians: float
    pause_remaining_s: float = 0.0


class MobilityStrategy(Protocol):
    def position_at(self, node_id: str, timestamp_s: float) -> MobilitySample:
        """Return deterministic mobility state for a node and timestamp."""


class DeterministicMobility:
    """Pure timestamp simulation: call order cannot alter a trajectory."""

    def __init__(self, config: MobilityModel) -> None:
        self.config = config

    def _rng(self, node_id: str) -> random.Random:
        return random.Random(f"{self.config.seed}:{node_id}")

    def _initial_state(self, node_id: str, rng: random.Random) -> MobilityState:
        position = Position(
            rng.uniform(0, self.config.area_width_m),
            rng.uniform(0, self.config.area_height_m),
        )
        return MobilityState(
            position=position,
            destination=self._destination(rng),
            speed_mps=self._speed(rng),
            direction_radians=rng.uniform(0, 2 * pi),
        )

    def _speed(self, rng: random.Random) -> float:
        minimum = max(0.0, self.config.min_speed_mps)
        maximum = max(minimum, self.config.max_speed_mps)
        return minimum if maximum == minimum else rng.uniform(minimum, maximum)

    def _destination(self, rng: random.Random) -> Position:
        return Position(
            rng.uniform(0, self.config.area_width_m),
            rng.uniform(0, self.config.area_height_m),
        )

    def _intervals(self, timestamp_s: float):
        remaining = max(0.0, timestamp_s)
        step = max(self.config.step_seconds, 0.001)
        while remaining > 0:
            delta = min(step, remaining)
            yield delta
            remaining -= delta

    def _move(
        self, position: Position, direction: float, distance: float
    ) -> tuple[Position, float]:
        x = position.x_m + cos(direction) * distance
        y = position.y_m + sin(direction) * distance
        width = self.config.area_width_m
        height = self.config.area_height_m
        if self.config.boundary == "wrap":
            return Position(x % width, y % height, position.z_m), direction
        dx = cos(direction)
        dy = sin(direction)
        while x < 0 or x > width:
            x = -x if x < 0 else 2 * width - x
            dx = -dx
        while y < 0 or y > height:
            y = -y if y < 0 else 2 * height - y
            dy = -dy
        return Position(x, y, position.z_m), atan2(dy, dx)

    def _sample(
        self,
        node_id: str,
        timestamp_s: float,
        state: MobilityState,
        label: str,
    ) -> MobilitySample:
        return MobilitySample(
            timestamp_s=timestamp_s,
            node_id=node_id,
            x_m=state.position.x_m,
            y_m=state.position.y_m,
            z_m=state.position.z_m,
            speed_mps=state.speed_mps,
            direction_degrees=(degrees(state.direction_radians) + 360) % 360,
            mobility_model=self.config.model,
            mobility_state=label,
        )


class StaticMobility(DeterministicMobility):
    def position_at(self, node_id: str, timestamp_s: float) -> MobilitySample:
        state = self._initial_state(node_id, self._rng(node_id))
        state.speed_mps = 0.0
        return self._sample(node_id, timestamp_s, state, "static")


class ConstantVelocityMobility(DeterministicMobility):
    def position_at(self, node_id: str, timestamp_s: float) -> MobilitySample:
        state = self._initial_state(node_id, self._rng(node_id))
        for delta in self._intervals(timestamp_s):
            state.position, state.direction_radians = self._move(
                state.position, state.direction_radians, state.speed_mps * delta
            )
        return self._sample(node_id, timestamp_s, state, "moving")


class RandomWalkMobility(DeterministicMobility):
    def position_at(self, node_id: str, timestamp_s: float) -> MobilitySample:
        rng = self._rng(node_id)
        state = self._initial_state(node_id, rng)
        for delta in self._intervals(timestamp_s):
            state.direction_radians = rng.uniform(0, 2 * pi)
            state.speed_mps = self._speed(rng)
            state.position, state.direction_radians = self._move(
                state.position, state.direction_radians, state.speed_mps * delta
            )
        return self._sample(node_id, timestamp_s, state, "walking")


class RandomWaypointMobility(DeterministicMobility):
    def position_at(self, node_id: str, timestamp_s: float) -> MobilitySample:
        rng = self._rng(node_id)
        state = self._initial_state(node_id, rng)
        label = "waypoint"
        for delta in self._intervals(timestamp_s):
            remaining = delta
            while remaining > 1e-12:
                if state.pause_remaining_s > 0:
                    consumed = min(remaining, state.pause_remaining_s)
                    state.pause_remaining_s -= consumed
                    remaining -= consumed
                    label = "paused"
                    if state.pause_remaining_s > 0:
                        continue
                    state.destination = self._destination(rng)
                    state.speed_mps = self._speed(rng)
                dx = state.destination.x_m - state.position.x_m
                dy = state.destination.y_m - state.position.y_m
                distance = hypot(dx, dy)
                if distance <= 1e-12 or state.speed_mps <= 0:
                    state.position = state.destination
                    state.pause_remaining_s = self.config.pause_seconds
                    if state.pause_remaining_s == 0:
                        state.destination = self._destination(rng)
                        state.speed_mps = self._speed(rng)
                    continue
                state.direction_radians = atan2(dy, dx)
                travel_time = distance / state.speed_mps
                consumed = min(remaining, travel_time)
                travelled = state.speed_mps * consumed
                state.position = Position(
                    state.position.x_m + cos(state.direction_radians) * travelled,
                    state.position.y_m + sin(state.direction_radians) * travelled,
                )
                remaining -= consumed
                label = "waypoint"
                if consumed >= travel_time - 1e-12:
                    state.position = state.destination
                    state.pause_remaining_s = self.config.pause_seconds
        if label == "paused":
            state.speed_mps = 0.0
        return self._sample(node_id, timestamp_s, state, label)


class ManhattanGridMobility(DeterministicMobility):
    def position_at(self, node_id: str, timestamp_s: float) -> MobilitySample:
        rng = self._rng(node_id)
        state = self._initial_state(node_id, rng)
        spacing = max(self.config.grid_spacing_m, 1.0)
        state.position = Position(
            round(state.position.x_m / spacing) * spacing,
            round(state.position.y_m / spacing) * spacing,
        )
        state.direction_radians = rng.choice((0.0, pi / 2, pi, 3 * pi / 2))
        for delta in self._intervals(timestamp_s):
            at_intersection = (
                abs(state.position.x_m / spacing - round(state.position.x_m / spacing))
                < 1e-9
                and abs(
                    state.position.y_m / spacing
                    - round(state.position.y_m / spacing)
                )
                < 1e-9
            )
            if at_intersection and rng.random() < self.config.turn_probability:
                state.direction_radians = (
                    state.direction_radians + rng.choice((-pi / 2, 0.0, pi / 2))
                ) % (2 * pi)
            state.position, state.direction_radians = self._move(
                state.position, state.direction_radians, state.speed_mps * delta
            )
        return self._sample(node_id, timestamp_s, state, "grid")


class GaussMarkovMobility(DeterministicMobility):
    def position_at(self, node_id: str, timestamp_s: float) -> MobilitySample:
        rng = self._rng(node_id)
        state = self._initial_state(node_id, rng)
        alpha = self.config.gauss_markov_alpha
        mean_direction = self.config.mean_direction_degrees * pi / 180
        for delta in self._intervals(timestamp_s):
            state.speed_mps = max(
                0.0,
                alpha * state.speed_mps
                + (1 - alpha) * self.config.mean_speed_mps
                + (1 - alpha) * rng.gauss(0, 0.5),
            )
            state.direction_radians = (
                alpha * state.direction_radians
                + (1 - alpha) * mean_direction
                + (1 - alpha) * rng.gauss(0, pi / 4)
            )
            state.position, state.direction_radians = self._move(
                state.position, state.direction_radians, state.speed_mps * delta
            )
        return self._sample(node_id, timestamp_s, state, "correlated")


def build_mobility_strategy(config: MobilityModel) -> MobilityStrategy:
    strategies: dict[str, type[DeterministicMobility]] = {
        "static": StaticMobility,
        "constant_velocity": ConstantVelocityMobility,
        "random_waypoint": RandomWaypointMobility,
        "random_walk": RandomWalkMobility,
        "manhattan_grid": ManhattanGridMobility,
        "gauss_markov": GaussMarkovMobility,
    }
    return strategies[config.model](config)

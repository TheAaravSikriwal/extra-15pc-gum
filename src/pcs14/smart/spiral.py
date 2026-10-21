"""The spiral descent (#34): down from height in a helix on low throttle, instead of straight
down, then straight down for the last few meters on the rangefinder.

Coming straight down fast is what puts a quad into the vortex ring state, where it sinks into
its own downwash and loses lift; moving sideways while it sinks keeps it flying in clean air.
Gazebo doesn't model the vortex ring state at all, so the sim checks the path only: that it
follows the helix and sinks at the rate asked. Whether the helix really keeps a real drone out of
it is on the unproven list.

The helix starts where the drone is: the center sits one radius to its east, and it circles
counterclockwise seen from above.
"""

import math
from dataclasses import dataclass

import numpy as np

STRAIGHT_SINK_MS = 0.7  # the last few meters, straight down, like a normal landing


@dataclass(frozen=True)
class Spiral:
    start_m: float  # height it starts from
    radius_m: float = 8.0
    sink_ms: float = 1.5
    speed_ms: float = 4.0  # around the circle
    straight_m: float = 4.0  # the last meters, straight down
    start_north: float = 0.0
    start_east: float = 0.0

    @property
    def center(self) -> tuple[float, float]:
        return self.start_north, self.start_east + self.radius_m

    @property
    def lap_s(self) -> float:
        return 2 * math.pi * self.radius_m / self.speed_ms

    @property
    def turning_s(self) -> float:
        return max(self.start_m - self.straight_m, 0.0) / self.sink_ms

    def at(self, t: float) -> tuple[float, float, float]:
        """(north, east, height) `t` s into the descent."""
        spin = min(t, self.turning_s)
        angle = math.pi + self.speed_ms / self.radius_m * spin  # starts due west of the center
        north = self.center[0] + self.radius_m * math.sin(angle) * -1
        east = self.center[1] + self.radius_m * math.cos(angle)
        if t <= self.turning_s:
            return north, east, self.start_m - self.sink_ms * t
        height = self.straight_m - STRAIGHT_SINK_MS * (t - self.turning_s)
        return north, east, max(height, 0.0)


@dataclass(frozen=True)
class Followed:
    radius_error_m: float  # the worst distance off the circle
    sink_ms: float  # the sink rate it held


def followed(t, north, east, height, spiral: Spiral) -> Followed:
    """How well a flown path followed the helix, over its turning part."""
    t, north, east, height = (np.asarray(x, dtype=float) for x in (t, north, east, height))
    turning = t <= spiral.turning_s
    cn, ce = spiral.center
    radius = np.hypot(north[turning] - cn, east[turning] - ce)
    sink = -np.polyfit(t[turning], height[turning], 1)[0]
    return Followed(float(np.max(np.abs(radius - spiral.radius_m))), float(sink))

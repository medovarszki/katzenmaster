"""The cat's behaviour: a GUI-free state machine.

Coordinates are screen coordinates in logical pixels. ``x`` is the left edge of the
cat sprite, which stays within ``[min_x, max_x]``; ``y`` is the (fixed) top edge.
"""

from __future__ import annotations

import math
import random
from enum import Enum

from . import config
from .animation import Animator
from .sprites import AnimationSpec


class State(Enum):
    SIT = "sit"
    BLINK = "blink"
    WALK = "walk"
    SLEEP = "sleep"
    CHASE = "chase"  # walking towards the cursor


ANIMATION_FOR_STATE = {
    State.SIT: "sit",
    State.BLINK: "blink",
    State.WALK: "walk",
    State.SLEEP: "sleep",
    State.CHASE: "walk",
}

RIGHT, LEFT = 1, -1


def ground_position(available: tuple[int, int, int, int], size: tuple[int, int]) -> tuple[int, int, int]:
    """Horizontal range and top y for a sprite standing on the bottom edge of ``available``.

    ``available`` is ``(x, y, width, height)`` as from ``QScreen.availableGeometry()``.
    Returns ``(min_x, max_x, y)``.
    """
    ax, ay, aw, ah = available
    w, h = size
    min_x = ax
    max_x = max(ax, ax + aw - w)
    y = ay + ah - h
    return min_x, max_x, y


class CatBrain:
    def __init__(
        self,
        specs: dict[str, AnimationSpec],
        size: tuple[int, int],
        ground: tuple[int, int, int],
        rng: random.Random | None = None,
        cfg=config,
    ) -> None:
        self.specs = specs
        self.width, self.height = size
        self.rng = rng or random.Random()
        self.cfg = cfg
        self.min_x, self.max_x, self.y = ground
        self.x = float(self.min_x + (self.max_x - self.min_x) / 2)
        self.facing = RIGHT
        self.state = State.SIT
        self.animator = Animator(specs["sit"])
        # timers
        self.awake = 0.0  # time since the last nap / cursor interaction
        self.action_timer = 0.0
        self.blink_timer = 0.0
        self.sleep_threshold = 0.0
        self.sleep_timer = 0.0
        self.walk_remaining = 0.0
        self.chase_target = self.x
        self.chase_time = 0.0
        self.cooldown = 0.0
        self._reset_awake()
        self._enter_sit()

    # ------------------------------------------------------------------ helpers
    def _uniform(self, rng_range: tuple[float, float]) -> float:
        return self.rng.uniform(*rng_range)

    def _set_state(self, state: State) -> None:
        self.state = state
        self.animator.restart(self.specs[ANIMATION_FOR_STATE[state]])

    def _reset_awake(self) -> None:
        self.awake = 0.0
        self.sleep_threshold = self._uniform(self.cfg.SLEEP_AFTER)

    def _enter_sit(self) -> None:
        self._set_state(State.SIT)
        self.action_timer = self._uniform(self.cfg.SIT_ACTION_INTERVAL)
        self.blink_timer = self._uniform(self.cfg.BLINK_INTERVAL)

    def _enter_walk(self) -> None:
        self.facing = self.rng.choice((LEFT, RIGHT))
        self.walk_remaining = self._uniform(self.cfg.WALK_DISTANCE)
        self._set_state(State.WALK)

    def _enter_sleep(self) -> None:
        self.sleep_timer = self._uniform(self.cfg.SLEEP_DURATION)
        self._set_state(State.SLEEP)

    def _enter_chase(self, cursor_x: float) -> None:
        self.chase_target = self._target_for_cursor(cursor_x)
        self.chase_time = 0.0
        self.facing = RIGHT if self.chase_target > self.x else LEFT
        self._set_state(State.CHASE)

    def _target_for_cursor(self, cursor_x: float) -> float:
        return self.clamp_x(cursor_x - self.width / 2)

    def clamp_x(self, x: float) -> float:
        return min(max(x, self.min_x), self.max_x)

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)

    def is_near(self, cursor: tuple[float, float] | None) -> bool:
        if cursor is None:
            return False
        cx, cy = self.center
        return math.hypot(cursor[0] - cx, cursor[1] - cy) <= self.cfg.CURSOR_NEAR_RADIUS

    # --------------------------------------------------------------- public API
    def set_ground(self, ground: tuple[int, int, int]) -> None:
        """Update the walkable range (e.g. the taskbar was resized)."""
        self.min_x, self.max_x, self.y = ground
        self.x = self.clamp_x(self.x)
        self.chase_target = self.clamp_x(self.chase_target)

    def force_state(self, state: State, facing: int = RIGHT) -> None:
        """Jump straight into a state (used by --snapshot)."""
        self.facing = facing
        if state is State.SIT:
            self._enter_sit()
        elif state is State.SLEEP:
            self._enter_sleep()
        elif state is State.WALK:
            self.walk_remaining = float("inf")
            self._set_state(State.WALK)
        elif state is State.CHASE:
            self.chase_target = self.max_x if facing == RIGHT else self.min_x
            self.chase_time = -float("inf")
            self._set_state(State.CHASE)
        else:
            self._set_state(state)

    @property
    def animation(self) -> str:
        return ANIMATION_FOR_STATE[self.state]

    @property
    def frame(self) -> int:
        return self.animator.frame

    @property
    def mirrored(self) -> bool:
        """Only the walk animation is directional; it faces right in the sheet."""
        return self.animation == "walk" and self.facing == LEFT

    @property
    def position(self) -> tuple[int, int]:
        return (round(self.x), self.y)

    def update(self, dt: float, cursor: tuple[float, float] | None = None) -> None:
        dt = min(max(dt, 0.0), self.cfg.MAX_DT)
        self.cooldown = max(0.0, self.cooldown - dt)
        near = self.is_near(cursor)
        self.animator.advance(dt)

        if self.state is State.SLEEP:
            self.sleep_timer -= dt
            if near:
                # woken up by the cursor: sit up, and don't react again immediately
                self.cooldown = self.cfg.REACT_COOLDOWN
                self._reset_awake()
                self._enter_sit()
            elif self.sleep_timer <= 0:
                self._reset_awake()
                self._enter_sit()
            return

        self.awake += dt
        if self.state in (State.SIT, State.BLINK):
            if near and self.cooldown <= 0:
                self._react_to_cursor(cursor[0])
                return
            if self.state is State.BLINK:
                if self.animator.finished:
                    self.state = State.SIT
                    self.animator.restart(self.specs["sit"])
                return
            self.action_timer -= dt
            self.blink_timer -= dt
            if self.action_timer <= 0:
                if self.awake >= self.sleep_threshold:
                    self._enter_sleep()
                elif self.rng.random() < self.cfg.WALK_PROBABILITY:
                    self._enter_walk()
                else:
                    self.action_timer = self._uniform(self.cfg.SIT_ACTION_INTERVAL)
            elif self.blink_timer <= 0:
                self.blink_timer = self._uniform(self.cfg.BLINK_INTERVAL)
                self._set_state(State.BLINK)

        elif self.state is State.WALK:
            step = self.cfg.WALK_SPEED * dt
            self._move(step)
            self.walk_remaining -= step
            if self.walk_remaining <= 0:
                self._enter_sit()

        elif self.state is State.CHASE:
            self.chase_time += dt
            if cursor is not None:
                self.chase_target = self._target_for_cursor(cursor[0])
            dx = self.chase_target - self.x
            if abs(dx) <= self.cfg.CHASE_ARRIVE_DISTANCE or self.chase_time >= self.cfg.CHASE_TIMEOUT:
                self.cooldown = self.cfg.REACT_COOLDOWN
                self._enter_sit()
                return
            self.facing = RIGHT if dx > 0 else LEFT
            step = min(abs(dx), self.cfg.CHASE_SPEED * dt)
            self.x = self.clamp_x(self.x + self.facing * step)

    def _react_to_cursor(self, cursor_x: float) -> None:
        self._reset_awake()  # playing with the cursor keeps the cat awake
        target = self._target_for_cursor(cursor_x)
        if abs(target - self.x) > self.cfg.CHASE_ARRIVE_DISTANCE:
            self._enter_chase(cursor_x)
        else:
            # cursor is right above the cat: acknowledge it with a blink
            self.cooldown = self.cfg.REACT_COOLDOWN
            self.blink_timer = self._uniform(self.cfg.BLINK_INTERVAL)
            self._set_state(State.BLINK)

    def _move(self, step: float) -> None:
        """Walk ``step`` px in the facing direction, turning around at the edges."""
        if self.max_x <= self.min_x:
            self.x = float(self.min_x)
            return
        x = self.x + self.facing * step
        while x < self.min_x or x > self.max_x:
            if x > self.max_x:
                x = 2 * self.max_x - x
                self.facing = LEFT
            elif x < self.min_x:
                x = 2 * self.min_x - x
                self.facing = RIGHT
        self.x = x

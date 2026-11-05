import random
import types

import pytest

from catpet import config
from catpet.brain import LEFT, RIGHT, CatBrain, State, ground_position

SIZE = (96, 96)
AVAILABLE = (0, 0, 1920, 1040)  # e.g. 1080p with a 40 px taskbar at the bottom
DT = 1 / 30


def make_brain(meta, seed=1, cfg=config, available=AVAILABLE):
    return CatBrain(meta.animations, SIZE, ground_position(available, SIZE), random.Random(seed), cfg)


def cfg_with(**overrides):
    values = {k: getattr(config, k) for k in dir(config) if k.isupper()}
    values.update(overrides)
    return types.SimpleNamespace(**values)


def run(brain, seconds, cursor=None, record=None):
    for _ in range(int(seconds / DT)):
        brain.update(DT, cursor)
        if record is not None:
            record.append((brain.state, brain.x, brain.facing))


# ------------------------------------------------------------------ geometry
def test_ground_position_bottom_of_available_geometry():
    assert ground_position((0, 0, 1920, 1040), SIZE) == (0, 1824, 944)
    # taskbar on top / multi-monitor offsets
    assert ground_position((100, 30, 800, 570), SIZE) == (100, 804, 504)


def test_ground_position_narrow_screen():
    min_x, max_x, _ = ground_position((10, 0, 50, 500), SIZE)
    assert min_x == max_x == 10


def test_starts_sitting_on_ground(meta):
    b = make_brain(meta)
    assert b.state is State.SIT
    assert b.y == 944
    assert 0 <= b.x <= 1824


# --------------------------------------------------------------- state flow
def test_visits_all_states_and_stays_in_bounds(meta):
    b = make_brain(meta, seed=3)
    rec = []
    run(b, 600, record=rec)
    states = {s for s, _, _ in rec}
    assert {State.SIT, State.BLINK, State.WALK, State.SLEEP} <= states
    assert State.CHASE not in states  # only the cursor triggers chasing
    assert all(b.min_x <= x <= b.max_x for _, x, _ in rec)


def test_transitions_follow_the_rules(meta):
    b = make_brain(meta, seed=5)
    rec = []
    run(b, 900, record=rec)
    allowed = {
        (State.SIT, State.BLINK), (State.BLINK, State.SIT),
        (State.SIT, State.WALK), (State.WALK, State.SIT),
        (State.SIT, State.SLEEP), (State.SLEEP, State.SIT),
    }
    for (a, _, _), (c, _, _) in zip(rec, rec[1:]):
        if a is not c:
            assert (a, c) in allowed, (a, c)


def test_blink_returns_to_sit(meta):
    b = make_brain(meta, cfg=cfg_with(BLINK_INTERVAL=(0.5, 0.5), SIT_ACTION_INTERVAL=(99, 99)))
    run(b, 0.6)
    assert b.state is State.BLINK and b.animation == "blink"
    run(b, meta.animations["blink"].duration + 0.1)
    assert b.state is State.SIT


def test_falls_asleep_after_long_awake_time_and_wakes_up(meta):
    cfg = cfg_with(WALK_PROBABILITY=0.0, SIT_ACTION_INTERVAL=(1, 1), SLEEP_AFTER=(10, 10),
                   SLEEP_DURATION=(5, 5))
    b = make_brain(meta, cfg=cfg)
    run(b, 9.5)
    assert b.state in (State.SIT, State.BLINK)
    run(b, 1.6)
    assert b.state is State.SLEEP and b.animation == "sleep"
    run(b, 5.2)
    assert b.state is State.SIT


def test_walking_cat_still_gets_sleepy(meta):
    """Awake time counts while walking too, so an active cat eventually naps."""
    cfg = cfg_with(WALK_PROBABILITY=1.0, SIT_ACTION_INTERVAL=(1, 1), SLEEP_AFTER=(20, 20))
    b = make_brain(meta, cfg=cfg)
    rec = []
    run(b, 60, record=rec)
    assert State.WALK in {s for s, _, _ in rec}
    first_sleep = next(i for i, (s, _, _) in enumerate(rec) if s is State.SLEEP)
    assert rec[first_sleep - 1][0] in (State.SIT, State.BLINK)  # only falls asleep from sitting
    assert first_sleep * DT >= 20


def test_cursor_interaction_keeps_cat_awake(meta):
    cfg = cfg_with(WALK_PROBABILITY=0.0, SIT_ACTION_INTERVAL=(1, 1), SLEEP_AFTER=(10, 10),
                   BLINK_INTERVAL=(99, 99))
    b = make_brain(meta, cfg=cfg)
    run(b, 8)
    b.update(DT, _cursor_near(b, 0))  # cursor right above -> blink, awake time reset
    assert b.awake < 1
    run(b, 8)
    assert b.state is not State.SLEEP
    run(b, 4)
    assert b.state is State.SLEEP


def test_walk_moves_and_mirrors(meta):
    cfg = cfg_with(WALK_PROBABILITY=1.0, SIT_ACTION_INTERVAL=(0.1, 0.1), WALK_DISTANCE=(300, 300))
    b = make_brain(meta, cfg=cfg)
    x0 = b.x
    run(b, 0.2)
    assert b.state is State.WALK and b.animation == "walk"
    assert b.mirrored == (b.facing == LEFT)
    run(b, 1.0)
    assert (b.x - x0) * b.facing > 0  # moved in the facing direction
    rec = []
    run(b, 300 / config.WALK_SPEED, record=rec)
    assert State.SIT in [s for s, _, _ in rec]  # the walk ended with sitting down


@pytest.mark.parametrize("start_x, facing, expected", [(1810.0, RIGHT, LEFT), (10.0, LEFT, RIGHT)])
def test_turns_around_at_edges(meta, start_x, facing, expected):
    b = make_brain(meta)
    b.force_state(State.WALK, facing)
    b.x = start_x
    run(b, 1.0)
    assert b.facing == expected
    assert b.min_x <= b.x <= b.max_x
    assert b.mirrored == (expected == LEFT)


def test_sit_and_sleep_are_never_mirrored(meta):
    b = make_brain(meta)
    for st in (State.SIT, State.SLEEP, State.BLINK):
        b.force_state(st, LEFT)
        assert not b.mirrored


def test_huge_dt_is_clamped(meta):
    b = make_brain(meta)
    b.force_state(State.WALK, RIGHT)
    x0 = b.x
    b.update(1000.0)
    assert abs(b.x - x0) <= config.WALK_SPEED * config.MAX_DT + 1e-6


def test_set_ground_clamps_position(meta):
    b = make_brain(meta)
    b.x = 1800
    b.set_ground(ground_position((0, 0, 1280, 700), SIZE))
    assert b.x == 1280 - 96 and b.y == 700 - 96


# -------------------------------------------------------------- cursor reaction
def _cursor_near(b, dx):
    cx, cy = b.center
    return (cx + dx, cy - 20)


def test_sleeping_cat_wakes_up_on_cursor(meta):
    b = make_brain(meta)
    b.force_state(State.SLEEP)
    b.update(DT, (b.center[0] + 1000, b.center[1]))  # far away: keeps sleeping
    assert b.state is State.SLEEP
    b.update(DT, _cursor_near(b, 50))
    assert b.state is State.SIT
    # cooldown: does not immediately run after the cursor
    b.update(DT, _cursor_near(b, 100))
    assert b.state is State.SIT


def test_sitting_cat_walks_to_cursor_then_sits(meta):
    b = make_brain(meta, cfg=cfg_with(SIT_ACTION_INTERVAL=(99, 99), BLINK_INTERVAL=(99, 99)))
    x0 = b.x
    cursor = _cursor_near(b, 120)
    b.update(DT, cursor)
    assert b.state is State.CHASE and b.facing == RIGHT and b.animation == "walk"
    run(b, 3.0, cursor)
    assert b.state is State.SIT
    assert b.x > x0
    assert abs(b.center[0] - cursor[0]) <= config.CHASE_ARRIVE_DISTANCE + 1


def test_chase_to_the_left_is_mirrored(meta):
    b = make_brain(meta)
    b.update(DT, _cursor_near(b, -120))
    assert b.state is State.CHASE and b.facing == LEFT and b.mirrored


def test_cursor_right_above_triggers_blink(meta):
    b = make_brain(meta)
    b.update(DT, _cursor_near(b, 0))
    assert b.state is State.BLINK


def test_reaction_cooldown(meta):
    b = make_brain(meta, cfg=cfg_with(SIT_ACTION_INTERVAL=(99, 99), BLINK_INTERVAL=(99, 99)))
    cursor = _cursor_near(b, 120)
    b.update(DT, cursor)
    while b.state is State.CHASE:  # chase and sit down next to the cursor
        b.update(DT, cursor)
    assert b.state is State.SIT
    cursor = (cursor[0] + 100, cursor[1])  # cursor moves a bit, still near
    waited = 0.0
    while b.state is State.SIT and waited < 60:
        b.update(DT, cursor)
        waited += DT
    assert b.state is State.CHASE
    assert config.REACT_COOLDOWN - 2 * DT <= waited <= config.REACT_COOLDOWN + 2 * DT


def test_chase_gives_up_after_timeout(meta):
    b = make_brain(meta, cfg=cfg_with(CHASE_SPEED=1.0, CHASE_TIMEOUT=1.0,
                                      SIT_ACTION_INTERVAL=(99, 99), BLINK_INTERVAL=(99, 99)))
    cursor = _cursor_near(b, 150)
    run(b, 1.2, cursor)
    assert b.state is State.SIT


def test_chase_target_is_clamped_to_screen(meta):
    b = make_brain(meta)
    b.x = 1800
    cursor = (1915, b.center[1])
    run(b, 2.0, cursor)
    assert b.x <= b.max_x


def test_walking_cat_ignores_cursor(meta):
    b = make_brain(meta)
    b.force_state(State.WALK, RIGHT)
    b.update(DT, _cursor_near(b, 0))
    assert b.state is State.WALK


def test_timings_are_random_but_seeded(meta):
    a1, a2, b1 = make_brain(meta, seed=7), make_brain(meta, seed=7), make_brain(meta, seed=8)
    ra, rb, rc = [], [], []
    run(a1, 120, record=ra)
    run(a2, 120, record=rb)
    run(b1, 120, record=rc)
    assert ra == rb
    assert ra != rc

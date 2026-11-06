import random
import types

import pytest

from katzenmaster import config
from katzenmaster.brain import LEFT, RIGHT, CatBrain, State, ground_position

SIZE = (96, 96)
AVAILABLE = (0, 0, 1920, 1040)  # e.g. 1080p with a 40 px taskbar at the bottom
DT = 1 / 30


def make_brain(meta, seed=1, cfg=config, available=AVAILABLE):
    return CatBrain(meta.animations, SIZE, ground_position(available, SIZE), random.Random(seed), cfg)


def cfg_with(**overrides):
    values = {k: getattr(config, k) for k in dir(config) if k.isupper()}
    values.update(overrides)
    return types.SimpleNamespace(**values)


NO_EXTRAS = dict(STRETCH_PROBABILITY=0.0, YAWN_PROBABILITY=0.0, GROOM_PROBABILITY=0.0)


def finish(brain, anim):
    """Run until a non-looping animation has played through."""
    run(brain, brain.specs[anim].duration + 0.1)


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
    assert {State.SIT, State.BLINK, State.WALK, State.SLEEP,
            State.STRETCH, State.YAWN, State.GROOM} <= states
    assert State.CHASE not in states  # only the cursor triggers chasing
    assert all(b.min_x <= x <= b.max_x for _, x, _ in rec)


def test_transitions_follow_the_rules(meta):
    b = make_brain(meta, seed=5)
    rec = []
    run(b, 900, record=rec)
    allowed = {
        (State.SIT, State.BLINK), (State.BLINK, State.SIT),
        (State.SIT, State.WALK), (State.WALK, State.SIT),
        (State.SIT, State.STRETCH), (State.STRETCH, State.SIT),
        (State.SIT, State.GROOM), (State.GROOM, State.SIT),
        (State.SIT, State.YAWN), (State.YAWN, State.SIT),
        (State.YAWN, State.SLEEP),  # only way to fall asleep
        (State.SLEEP, State.STRETCH),  # waking up on its own
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
                   SLEEP_DURATION=(5, 5), **NO_EXTRAS)
    b = make_brain(meta, cfg=cfg)
    run(b, 9.5)
    assert b.state in (State.SIT, State.BLINK)
    run(b, 1.6)
    assert b.state is State.YAWN and b.animation == "yawn"  # yawns before the nap
    finish(b, "yawn")
    assert b.state is State.SLEEP and b.animation == "sleep"
    run(b, 5.0)
    assert b.state is State.STRETCH  # stretches after waking up on its own
    finish(b, "stretch")
    assert b.state is State.SIT


def test_walking_cat_still_gets_sleepy(meta):
    """Awake time counts while walking too, so an active cat eventually naps."""
    cfg = cfg_with(WALK_PROBABILITY=1.0, SIT_ACTION_INTERVAL=(1, 1), SLEEP_AFTER=(20, 20))
    b = make_brain(meta, cfg=cfg)
    rec = []
    run(b, 60, record=rec)
    assert State.WALK in {s for s, _, _ in rec}
    first_sleep = next(i for i, (s, _, _) in enumerate(rec) if s is State.SLEEP)
    assert rec[first_sleep - 1][0] is State.YAWN  # always yawns right before the nap
    first_yawn = next(i for i in range(first_sleep, 0, -1) if rec[i - 1][0] is not State.YAWN)
    assert rec[first_yawn - 1][0] in (State.SIT, State.BLINK)  # ...and only from sitting
    assert first_yawn * DT >= 20


def test_cursor_interaction_keeps_cat_awake(meta):
    cfg = cfg_with(WALK_PROBABILITY=0.0, SIT_ACTION_INTERVAL=(1, 1), SLEEP_AFTER=(10, 10),
                   BLINK_INTERVAL=(99, 99), **NO_EXTRAS)
    b = make_brain(meta, cfg=cfg)
    run(b, 8)
    b.update(DT, _cursor_near(b, 0))  # cursor right above -> blink, awake time reset
    assert b.awake < 1
    run(b, 8)
    assert b.state not in (State.YAWN, State.SLEEP)
    run(b, 4 + meta.animations["yawn"].duration)
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


def test_front_views_are_never_mirrored(meta):
    b = make_brain(meta)
    for st in (State.SIT, State.SLEEP, State.BLINK, State.YAWN, State.GROOM):
        b.force_state(st, LEFT)
        assert not b.mirrored


@pytest.mark.parametrize("facing", [LEFT, RIGHT])
def test_stretch_is_mirrored_when_facing_left(meta, facing):
    b = make_brain(meta)
    b.force_state(State.STRETCH, facing)
    assert b.animation == "stretch"
    assert b.mirrored == (facing == LEFT)


# ------------------------------------------------------------ stretch / yawn / groom
def _only(**probabilities):
    p = dict(WALK_PROBABILITY=0.0, **NO_EXTRAS)
    p.update(probabilities)
    return cfg_with(SIT_ACTION_INTERVAL=(1, 1), BLINK_INTERVAL=(99, 99), **p)


def test_stretch_plays_once_in_place_then_sits(meta):
    b = make_brain(meta, cfg=_only(STRETCH_PROBABILITY=1.0))
    x0 = b.x
    run(b, 1.1)
    assert b.state is State.STRETCH and b.animation == "stretch"
    finish(b, "stretch")
    assert b.state is State.SIT
    assert b.x == x0  # stretching does not move the cat


def test_yawn_plays_once_then_sits(meta):
    b = make_brain(meta, cfg=_only(YAWN_PROBABILITY=1.0))
    run(b, 1.1)
    assert b.state is State.YAWN and b.animation == "yawn"
    finish(b, "yawn")
    assert b.state is State.SIT  # not sleepy yet: no nap after this yawn


def test_groom_loops_for_the_configured_time(meta):
    b = make_brain(meta, cfg=_only(GROOM_PROBABILITY=1.0, GROOM_DURATION=(3, 3)))
    run(b, 1.1)
    assert b.state is State.GROOM and b.animation == "groom"
    run(b, 2.8)
    assert b.state is State.GROOM
    run(b, 0.3)
    assert b.state is State.SIT


def test_action_probabilities_are_respected(meta):
    b = make_brain(meta, seed=11, cfg=_only(WALK_PROBABILITY=0.25, STRETCH_PROBABILITY=0.25,
                                            YAWN_PROBABILITY=0.25, GROOM_PROBABILITY=0.25,
                                            SLEEP_AFTER=(1e9, 1e9)))
    rec = []
    run(b, 900, record=rec)
    starts = [c for (a, _, _), (c, _, _) in zip(rec, rec[1:]) if a is not c and a is State.SIT]
    counts = {s: starts.count(s) for s in (State.WALK, State.STRETCH, State.YAWN, State.GROOM)}
    assert all(n >= 0.15 * len(starts) for n in counts.values()), counts
    assert State.SLEEP not in starts


def test_grooming_cat_reacts_to_cursor(meta):
    b = make_brain(meta, cfg=_only(GROOM_PROBABILITY=1.0, GROOM_DURATION=(99, 99)))
    run(b, 1.1)
    assert b.state is State.GROOM
    b.update(DT, _cursor_near(b, 120))
    assert b.state is State.CHASE


@pytest.mark.parametrize("state", [State.STRETCH, State.YAWN])
def test_stretching_or_yawning_cat_finishes_first(meta, state):
    b = make_brain(meta, cfg=cfg_with(SIT_ACTION_INTERVAL=(99, 99), BLINK_INTERVAL=(99, 99)))
    b.force_state(state, RIGHT)
    cursor = _cursor_near(b, 120)
    b.update(DT, cursor)
    assert b.state is state
    reacted = []
    run(b, meta.animations[state.value].duration + 0.2, cursor, record=reacted)
    assert State.CHASE in {s for s, _, _ in reacted}  # reacts right after sitting down


def test_woken_by_cursor_sits_without_stretching(meta):
    b = make_brain(meta)
    b.force_state(State.SLEEP)
    b.update(DT, _cursor_near(b, 50))
    assert b.state is State.SIT


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

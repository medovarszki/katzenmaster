from katzenmaster.animation import Animator
from katzenmaster.sprites import AnimationSpec

LOOP = AnimationSpec("walk", 0, 6, 10.0, True)
ONCE = AnimationSpec("blink", 1, 4, 12.0, False)


def test_frames_advance_with_time():
    a = Animator(LOOP)
    seen = []
    for _ in range(12):
        seen.append(a.frame)
        a.advance(0.1)
    assert seen == [0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5]


def test_loop_never_finishes():
    a = Animator(LOOP)
    a.advance(100)
    assert not a.finished
    assert 0 <= a.frame < 6


def test_non_loop_clamps_and_finishes():
    a = Animator(ONCE)
    assert not a.finished
    a.advance(ONCE.duration - 0.01)
    assert a.frame == 3 and not a.finished
    a.advance(0.02)
    assert a.finished
    a.advance(10)
    assert a.frame == 3


def test_restart_and_negative_dt():
    a = Animator(LOOP)
    a.advance(0.25)
    a.advance(-5)
    assert a.frame == 2
    a.restart(ONCE)
    assert a.spec is ONCE and a.frame == 0

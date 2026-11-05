"""Frame timing for a single animation (pure Python)."""

from __future__ import annotations

from .sprites import AnimationSpec


class Animator:
    """Tracks elapsed time in an animation and maps it to a frame index."""

    def __init__(self, spec: AnimationSpec) -> None:
        self.spec = spec
        self.elapsed = 0.0

    def restart(self, spec: AnimationSpec | None = None) -> None:
        if spec is not None:
            self.spec = spec
        self.elapsed = 0.0

    def advance(self, dt: float) -> None:
        self.elapsed += max(0.0, dt)

    @property
    def frame(self) -> int:
        idx = int(self.elapsed * self.spec.fps + 1e-9)  # tolerate float accumulation
        if self.spec.loop:
            return idx % self.spec.frames
        return min(idx, self.spec.frames - 1)

    @property
    def finished(self) -> bool:
        """True once a non-looping animation has shown its last frame for a full frame time."""
        return (not self.spec.loop) and self.elapsed + 1e-9 >= self.spec.duration

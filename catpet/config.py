"""All tunable constants in one place.

Times are in seconds, distances in logical (device-independent) screen pixels.
"""

import sys
from pathlib import Path


def assets_dir() -> Path:
    """Sprite folder: next to the package, or inside a PyInstaller bundle when frozen."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "assets" / "sprites"
    return Path(__file__).resolve().parent.parent / "assets" / "sprites"


# --- assets / rendering ----------------------------------------------------
ASSETS_DIR = assets_dir()
SPRITE_PNG = ASSETS_DIR / "sprites.png"
SPRITE_JSON = ASSETS_DIR / "sprites.json"

SCALE = 3  # integer nearest-neighbour scale factor (32 px -> 96 px)

TICK_MS = 33  # main loop interval (~30 fps)
MAX_DT = 0.1  # clamp for a single simulation step (e.g. after suspend)

# --- behaviour timings (min, max) ------------------------------------------
SIT_ACTION_INTERVAL = (3.0, 8.0)  # how long to sit before deciding what to do next
WALK_PROBABILITY = 0.4  # chance to start walking when a sit interval ends
BLINK_INTERVAL = (4.0, 10.0)  # time between blinks while sitting
# Awake time without any cursor interaction after which the cat, the next time it
# decides what to do while sitting, takes a nap instead.
SLEEP_AFTER = (60.0, 120.0)
SLEEP_DURATION = (30.0, 90.0)  # how long a nap lasts if nobody disturbs it
WALK_DISTANCE = (120.0, 600.0)  # how far a walk goes (px), turning at the edges
WALK_SPEED = 60.0  # px / s
CHASE_SPEED = 120.0  # px / s, when walking towards the cursor

# --- cursor reaction -------------------------------------------------------
CURSOR_NEAR_RADIUS = 160.0  # cursor counts as "near" within this distance of the cat centre
CHASE_ARRIVE_DISTANCE = 8.0  # stop chasing when this close (horizontally) to the cursor
CHASE_TIMEOUT = 6.0  # give up chasing after this long
REACT_COOLDOWN = 5.0  # ignore the cursor for this long after a reaction / wake-up

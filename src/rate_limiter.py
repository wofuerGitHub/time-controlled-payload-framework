"""
File: rate_limiter.py
Description: Minimal file-based rate limiter for throttling outbound API
    calls to a fixed number of queries per minute. The next-allowed
    timestamp is persisted to a control file, so the limit survives
    process restarts (e.g. a container that exits and gets restarted).
"""

import time

_config = {
    "speed": 60,                  # allowed queries per minute
    "control_file": "speed.ctl",  # file that persists the next-allowed timestamp
}


def configure(speed: float = None, control_file: str = None) -> None:
    """Update rate-limiter settings."""
    if speed is not None:
        _config["speed"] = speed
    if control_file is not None:
        _config["control_file"] = control_file


def wait_for_slot() -> None:
    """
    Block until the next query is allowed, then reserve the following slot.

    Call this immediately before every outbound request.
    """
    wait_time = 60 / _config["speed"]
    control_file = _config["control_file"]
    now = time.time()

    try:
        with open(control_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            next_allowed = float(lines[-1]) if lines else now
    except FileNotFoundError:
        next_allowed = now + wait_time

    if now < next_allowed:            # not allowed to query yet
        time_to_wait = next_allowed - now
        next_allowed += wait_time
    else:                              # allowed, but still enforce spacing
        time_to_wait = wait_time
        next_allowed = now + wait_time

    with open(control_file, "w", encoding="utf-8") as f:
        f.write(str(next_allowed))

    time.sleep(time_to_wait)

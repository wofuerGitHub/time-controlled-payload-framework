"""
Provide file-based request throttling for recurring or rate-limited jobs.

This module maintains a persistent throttle state containing the Unix timestamp
at which the next request is allowed. It calculates the required waiting time
based on a configured requests-per-minute limit and updates the throttle state
after each execution.

If the throttle state file is missing or invalid, it is recreated using the
current timestamp.

Main functions:
    throttle_file_rw():
        Read or write the persistent throttle state.

    timing_logic():
        Calculate the next allowed execution time and required waiting time.

    throttle():
        Apply the complete throttling workflow and return the required delay.

The module can also be executed directly to test the throttling behavior using
the application's configuration file.
"""

import json
from pathlib import Path
import time
from typing import Optional
import warnings

def throttle_file_rw(throttle_path: Path, mode: str = "r", \
                     next_allowed_at: Optional[float] = None) -> float:
    """
    Read or write the throttle state file.

    Parameters:
        throttle_path:
            Path to the throttle state file.

        mode : {"r", "w"}, default "r"
            "r" to read (default), "w" to write.

        next_allowed_at:
            Unix timestamp when the next request is allowed.
            Required if mode is "w".

    Returns:
        float:
            next_allowed_at Unix timestamp.
    """

    # Check mode validity
    if mode not in {"r", "w"}:
        raise ValueError(
            f"Invalid mode: {mode}. Use 'r' for read or 'w' for write."
        )

    # Check next_allowed_at validity
    if mode == "w" and next_allowed_at is None:
        raise ValueError(
            "next_allowed_at must be provided when writing to the throttle file"
        )

    # Check next_allowed_at validity
    if next_allowed_at is not None and next_allowed_at < 0:
        raise ValueError(
            "next_allowed_at must be a positive number"
        )

    # Throttle file does not exist -> generate it.
    if not throttle_path.is_file():
        warnings.warn(
            f"Throttle file not found: {throttle_path}. "
            "Creating a new throttle file.",
            RuntimeWarning,
        )

        if next_allowed_at is None:
            next_allowed_at = time.time()

        throttle = {
            "next_allowed_at": next_allowed_at
        }

        throttle_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with throttle_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(throttle, file, indent=4)

    # Throttle file exists, write next_allowed_at to it.
    elif mode == "w":
        if next_allowed_at is None:
            raise ValueError(
                "next_allowed_at must be provided when writing to the throttle file"
            )

        throttle = {
            "next_allowed_at": next_allowed_at
        }

        with throttle_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(throttle, file, indent=4)

    # Throttle file exists, read next_allowed_at from it as default.
    try:
        with throttle_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            throttle = json.load(file)

        next_allowed_at = float(
            throttle["next_allowed_at"]
        )

        if next_allowed_at < 0:
            raise ValueError(
                "next_allowed_at cannot be negative"
            )

        return next_allowed_at

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        warnings.warn(
            f"Throttle file missing or invalid: {throttle_path}. "
            f"Creating a new throttle file. Reason: {error}",
            RuntimeWarning,
        )

        return throttle_file_rw(
            throttle_path,
            "w",
            next_allowed_at=time.time()
        )

def timing_logic(next_allowed_at: float, requests_per_minute: float,) -> tuple[float, float]:
    """
    Calculate the next allowed execution time based on the request rate.

    Returns:
        tuple[float, float]:
            next_allowed_at:
                Unix timestamp when the following request is allowed.

            waiting_time:
                Seconds to wait before the current request is allowed.
                Returns 0.0 if execution is allowed immediately.
    """

    if requests_per_minute <= 0:
        raise ValueError(
            "requests_per_minute must be greater than 0"
        )

    if next_allowed_at < 0:
        raise ValueError(
            "next_allowed_at cannot be negative"
    )

    current_time = time.time()
    waiting_time = max(0.0, next_allowed_at - current_time)
    next_allowed_at = max(next_allowed_at, current_time) + (60 / requests_per_minute)
    return next_allowed_at, waiting_time

def throttle(throttle_path: Path, requests_per_minute: float) -> float:
    """
    Throttle the execution of a function based on the request rate.

    Parameters:
        throttle_path:
            Path to the throttle state file.

        requests_per_minute:
            Number of requests allowed per minute.

    Returns:
        float:
            Seconds to wait before the current request is allowed.
            Returns 0.0 if execution is allowed immediately.
    """

    next_allowed_at = throttle_file_rw(throttle_path, "r")
    next_allowed_at, waiting_time = timing_logic(next_allowed_at, requests_per_minute)
    throttle_file_rw(throttle_path, "w", next_allowed_at)
    return waiting_time

#---

def main() -> None:
    """
    For testing purposes only, run the throttle logic in a loop, printing the current timing 
    parameters, the next allowed execution time, and the waiting time before the next execution.

    Logic:
        1. Read next_allowed_at from throttle file and use requests_per_minute.
        2. Calculate waiting time and next_allowed_at.
        3. Write next_allowed_at back to throttle file.
        4. Sleep for waiting_time seconds before the next iteration.
    """

    config_file = "config/config.json"
    config_path = Path(config_file)
    project_root = config_path.parent.parent
    with config_path.open("r", encoding="utf-8") as file:
        config = json.load(file)
    speed_control = config["global"]["speed_control"]
    requests_per_minute = float(speed_control["requests_per_minute"])
    throttle_file = speed_control["throttle_file"]
    throttle_path = project_root / throttle_file

    print(f"Using throttle file: {throttle_path.resolve()}")
    print(f"Using requests_per_minute: {requests_per_minute}")
    print("Starting throttle loop. Press Ctrl+C to exit.")

    last_execution_time = time.time()

    while True:

        # Wait for the next allowed execution time based on the throttle logic
        time.sleep(throttle(throttle_path, requests_per_minute))
        print(
            f"Payload executed at {time.time()}. "
            f"Time since last execution: "
            f"{time.time() - last_execution_time:.6f} seconds."
        )
        last_execution_time = time.time()

if __name__ == "__main__":
    main()

### Throttle Function
# read timing parameters from a configuration file or environment variables
# calculate waiting time for the next execution
# write the next allowed execution time to a configuration file or environment variable
# return the waiting time for the next execution


import json
from pathlib import Path
import time


def read_timing_parameters(config_file: str = "config/config.json",) -> tuple[float, float]:
    """
    Read timing parameters from config.json and respective throttle-file.

    Paths inside config.json are interpreted relative to the
    project root.

    Returns:
        tuple[float, float]:
            next_allowed_at, requests_per_minute
    """

    config_path = Path(config_file)
    project_root = config_path.parent.parent

    # Read config.json
    with config_path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    # Read configured request limit
    requests_per_minute = float(
        config["speed_control"]["requests_per_minute"]
    )

    # Get throttle file path from config.json
    throttle_file = config["speed_control"]["throttle_file"]

    # Resolve relative to project root
    throttle_path = project_root / throttle_file

    # Read throttle.json
    with throttle_path.open("r", encoding="utf-8") as file:
        throttle = json.load(file)

    next_allowed_at = float(
        throttle["next_allowed_at"]
    )

    return next_allowed_at, requests_per_minute

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
    current_time = time.time()
    waiting_time = 0.0

    if current_time < next_allowed_at:
        waiting_time = next_allowed_at - current_time

    next_allowed_at = max(next_allowed_at, current_time) + (60 / requests_per_minute)

    return next_allowed_at, waiting_time

def write_timing_parameters(config_file: str, next_allowed_at: float,) -> None:
    """
    Write next_allowed_at to the throttle file specified in config.json.

    The throttle file path inside config.json is interpreted relative
    to the project root.

    Example config.json:

        "speed_control": {
            "throttle_file": "runtime/throttle.json"
        }

    Parameters:

        config_file:
            Path to the main configuration file.
            Defaults to "config/config.json".
    
        next_allowed_at:
            Unix timestamp when the next request is allowed.

    """

    config_path = Path(config_file)

    # Determine project root from:
    #
    # project/
    # ├── config/
    # │   └── config.json
    # └── runtime/
    #     └── throttle.json
    #
    project_root = config_path.parent.parent

    # Read main configuration.
    with config_path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    # Get throttle file path from config.json.
    throttle_file = config["speed_control"]["throttle_file"]

    # Resolve throttle file relative to project root.
    throttle_path = project_root / throttle_file

    # Read existing throttle state.
    with throttle_path.open("r", encoding="utf-8") as file:
        throttle = json.load(file)

    # Update only next_allowed_at.
    throttle["next_allowed_at"] = next_allowed_at

    # Write updated throttle state back to throttle.json.
    with throttle_path.open("w", encoding="utf-8") as file:
        json.dump(throttle, file, indent=4)

#---

def main() -> None:
    while True:
        next_allowed_at, requests_per_minute = read_timing_parameters()

        print(
            f"Current timing parameters: "
            f"{next_allowed_at}, {requests_per_minute}"
        )

        next_allowed_at, waiting_time = timing_logic(next_allowed_at, requests_per_minute,)

        print(f"Next allowed at: {next_allowed_at}")
        print(f"Waiting time: {waiting_time}")

        write_timing_parameters("config/config.json", next_allowed_at)

        time.sleep(waiting_time)


if __name__ == "__main__":
    main()
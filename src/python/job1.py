import json
import os
from pathlib import Path
from throttle import throttle
import time

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_PATH = Path(
    os.getenv(
        "APP_CONFIG",
        PROJECT_ROOT / "config" / "config.json",
    )
)

def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> None:
    """
    for testing purposes only, run the throttle logic in a loop, printing the current timing parameters,
    the next allowed execution time, and the waiting time before the next execution.

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
    requests_per_minute = float(config["speed_control"]["requests_per_minute"])
    throttle_file = config["speed_control"]["throttle_file"]
    throttle_path = project_root / throttle_file

    print(f"Using throttle file: {throttle_path.resolve()}")
    print(f"Using requests_per_minute: {requests_per_minute}")
    print("Starting throttle loop. Press Ctrl+C to exit.")

    last_execution_time = time.time()

    while True:

        # Wait for the next allowed execution time based on the throttle logic
        time.sleep(throttle(throttle_path, requests_per_minute))
        print(f"Payload executed at {time.time()}. Time since last execution: {time.time() - last_execution_time:.6f} seconds.")
        last_execution_time = time.time()

if __name__ == "__main__":
    main()
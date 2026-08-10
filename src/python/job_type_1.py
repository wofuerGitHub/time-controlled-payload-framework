import json
import os
from pathlib import Path
from common.throttle import throttle
import sys
import time

# Check for the required command-line argument
if len(sys.argv) < 2:
    raise ValueError(
        "Missing required argument: id. "
        "Usage: python job_type_1.py <id>"
    )

id = sys.argv[1]

# Determine the project root directory and configuration file path
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load the configuration file path from the environment variable or use the default path
CONFIG_PATH = Path(os.getenv("APP_CONFIG", PROJECT_ROOT / "config" / "config.json"))

# Function to load the configuration from the JSON file
def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)

# Main function to execute the job type 1 logic
def main() -> None:
    """
    Job Type 1: This job type executes a payload at a controlled rate defined by the configuration file. 
    It reads the throttle settings from the configuration and uses a throttle file to determine when to 
    execute the payload. The job runs indefinitely until interrupted by the user.
    """

    config = load_config()
    requests_per_minute = float(config["speed_control"]["requests_per_minute"])
    throttle_file = config["speed_control"]["throttle_file"]
    throttle_path = PROJECT_ROOT / throttle_file

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
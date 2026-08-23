import time
from pathlib import Path

from common.bootstrap import initialize
from common.throttle import throttle

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def main() -> None:
    """
    Job Type 1 executes one throttled payload and then exits after its cadence
    delay. A process manager can restart the process for the next execution.
    """
    config, job_config = initialize()

    requests_per_minute = float(config["speed_control"]["requests_per_minute"])
    throttle_file = config["speed_control"]["throttle_file"]
    throttle_path = PROJECT_ROOT / throttle_file
    delay_seconds = float(job_config.get("delay_seconds", 0))
    count = int(job_config.get("executions", 1))

    print(f"Using throttle file: {throttle_path.resolve()}")
    print(f"Using requests_per_minute: {requests_per_minute}")
    print(f"Starting {job_config['id']}.")

    last_execution_time = time.time()
    while count > 0:

        # Wait for the next allowed execution time based on the throttle logic
        time.sleep(throttle(throttle_path, requests_per_minute))
        print(f"Payload executed at {time.time()}. Time since last exec.: {time.time() - last_execution_time:.6f} seconds. Remaining: {count - 1}")
        last_execution_time = time.time()
        count -= 1

    print(f"Job {job_config['id']} completed. Exiting after {delay_seconds} seconds.")
    time.sleep(delay_seconds)

if __name__ == "__main__":
    main()
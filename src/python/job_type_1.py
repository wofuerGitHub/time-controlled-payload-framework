import logging
import random
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
    logger = logging.LoggerAdapter(
        logging.getLogger(__name__),
        {"job_id": job_config["id"]},
    )
    logger.info("Starting %s.", job_config["id"])
    logger.debug("Job configuration: %s", job_config)

    requests_per_minute = float(config["speed_control"]["requests_per_minute"])
    throttle_file = config["speed_control"]["throttle_file"]
    throttle_path = PROJECT_ROOT / throttle_file
    delay_seconds = float(job_config.get("delay_seconds", 0))
    count = int(job_config.get("executions", 1))

    # print(f"Using throttle file: {throttle_path.resolve()}")
    # print(f"Using requests_per_minute: {requests_per_minute}")
    # print(f"Starting {job_config['id']}.")
    logger.debug("Using throttle file: %s", throttle_path.resolve())
    logger.debug("Using requests_per_minute: %s", requests_per_minute)
    logger.debug("Starting %s.", job_config["id"])

    last_execution_time = time.time()
    while count > 0:

        # Wait for the next allowed execution time based on the throttle logic
        time.sleep(throttle(throttle_path, requests_per_minute))

        # print(f"Payload executed at {time.time()}. Time since last exec.: {time.time() - last_execution_time:.6f} seconds. Remaining: {count - 1}")
        logger.debug(
            "Payload executed at %.2f. Time since last exec.: %.2f seconds. Remaining: %d",
            time.time(),
            time.time() - last_execution_time,
            count - 1,
        )
        # Simulate some processing time for the payload execution
        time.sleep(random.uniform(0.001, 0.050))

        last_execution_time = time.time()
        count -= 1

    # print(f"Job {job_config['id']} completed. Exiting after {delay_seconds} seconds.")
    logger.debug(
        "Job %s completed. Exiting after %s seconds.",
        job_config["id"],
        delay_seconds,
    )
    time.sleep(delay_seconds)
    logger.info("Ending %s.", job_config["id"])

if __name__ == "__main__":
    main()
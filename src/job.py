"""
File: job.py
Description: Template for a "run once, sleep, exit" job. Pair this with a
    process manager that restarts the process when it exits (e.g. Docker's
    `restart: always`) to get a self-scheduling recurring job without cron
    or an in-process scheduler.
"""

import time
from urllib.request import urlopen

from config_loader import load_config
from rate_limiter import configure, wait_for_slot


def do_work(urls: list) -> None:
    """One iteration of the job's actual work."""
    for url in urls:
        wait_for_slot()  # respect the configured queries/min before each call
        with urlopen(url, timeout=10) as response:
            print(f"[{time.strftime('%X')}] {url} -> {response.status}")


def main() -> None:
    config = load_config("config.json")
    configure(speed=config["speed"], control_file=config["control_file"])

    do_work(config["urls"])

    delay = config["delay_seconds"]
    print(f"job done, sleeping {delay}s then exiting "
          f"(the process manager restarts the job to reschedule it)")
    time.sleep(delay)


if __name__ == "__main__":
    main()

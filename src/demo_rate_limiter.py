"""
File: demo_rate_limiter.py
Description: Standalone demo, no network or config file needed. Run it to
    watch the rate limiter space out calls to roughly one every 5 seconds
    (speed=12/min). Run it twice in a row to see the limit persist across
    process restarts via demo_speed.ctl.
"""

import time
from rate_limiter import configure, wait_for_slot

configure(speed=12, control_file="demo_speed.ctl")  # 12/min == 1 every 5s

for i in range(5):
    wait_for_slot()
    print(f"call {i + 1} at {time.strftime('%X')}")

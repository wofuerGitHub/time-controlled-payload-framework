# time-controlled-queries-demo

Minimal Python demo for two common patterns when polling a rate-limited REQUESTS on a recurring schedule, without using an external scheduler library or a MySQL event scheduler.

1. **Query throttling**  
   Limit outbound REQUESTS calls to `N` requests per minute using a small persisted control file that stores the next allowed request timestamp. Because the state is stored on disk, the throttle survives process restarts.

2. **Job cadence**  
   A job runs once, waits for a configured delay, then exits. A process manager restarts it after exit. In this demo, Docker uses `restart: always`, giving a simple "run every N seconds" execution model without scheduler-specific application code.

## Application Lifecycle

1. Container starts
2. `main.py` runs
3. `main.py` reads `config/config.json`
4. Configuration is validated
5. The job runs
6. REQUESTS are throttled as needed
7. The job completes
8. The process sleeps for the configured delay
9. The process exits
10. Docker restarts the container
11. The cycle repeats
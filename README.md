# time-controlled-queries-demo

Minimal starting point for two patterns commonly needed when polling a
rate-limited API on a recurring schedule, without any external scheduler
library or MySQL event scheduler:

1. **Query throttling** (`src/rate_limiter.py`) — cap outbound calls to
   N per minute using a small control file that persists the
   next-allowed timestamp, so the limit holds even across restarts.
2. **Job cadence** (`src/job.py`) — a job does its work once, sleeps for
   a configured delay, then exits. Paired with a process manager that
   restarts the process on exit (Docker's `restart: always` here), this
   is a full "run every N seconds" schedule with zero scheduler code.

## Layout

```
config.json              # speed (queries/min), delay_seconds, urls to poll
src/rate_limiter.py       # pattern 1: configure() + wait_for_slot()
src/job.py                # pattern 2: do_work() then sleep(delay) then exit
src/config_loader.py      # tiny JSON config loader
src/demo_rate_limiter.py  # standalone demo, no network/config needed
Dockerfile, docker-compose.yml
```

## Try the rate limiter alone

```bash
cd src
python demo_rate_limiter.py   # 5 calls, spaced ~5s apart (speed=12/min)
python demo_rate_limiter.py   # run again immediately: it still waits,
                               # because demo_speed.ctl persisted the state
```

## Run the job locally

```bash
pip install -r requirements.txt
mkdir -p state
cd src && python job.py       # fetches config.json's urls, then sleeps
```

## Run it as a self-scheduling service

```bash
docker compose up --build
```

The container runs `job.py` once, sleeps `delay_seconds`, and exits;
`restart: always` makes Docker relaunch it, so the job re-runs on that
interval indefinitely. The `job_state` volume keeps `state/speed.ctl`
around across restarts so the rate limit stays consistent.

## Adapting this for a real project

- Replace `do_work()` in `src/job.py` with your actual fetch/parse/store
  logic; call `wait_for_slot()` right before every outbound request.
- Give each distinct job its own `delay_seconds` in `config.json` (or its
  own config file) and its own Dockerfile/service in
  `docker-compose.yml` if you have several independent jobs.
- If several jobs share one upstream API's rate limit, point them at the
  same `control_file` (and mount it from the same volume) so they
  throttle against each other, not just themselves.

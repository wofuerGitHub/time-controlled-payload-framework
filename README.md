# time-controlled-payload-framework

A small Python and Docker demonstration of two related patterns:

- **File-backed rate throttling:** executions are spaced according to a configured requests-per-minute rate. The next permitted execution time is persisted in `runtime/throttle.json`.
- **Restart-driven job cadence:** a finite job batch waits for a configured delay, exits, and is restarted by Docker Compose.

The payload is simulated with a short random processing delay. This project does not make outbound HTTP requests or provide a production scheduler.

## How It Works

Each Compose service runs `src/python/job_type_1.py` with a configured job ID. The process:

1. Loads `config/config.json` and selects the matching enabled job.
2. Initializes logging, normally writing to `runtime/app.log`.
3. Reads the shared throttle state.
4. Waits until the next permitted execution, then updates the state for the following execution.
5. Simulates the payload and repeats until the job's `executions` count is exhausted.
6. Waits for `delay_seconds` and exits.
7. Is restarted by Docker because the service uses `restart: always`.

The `runtime` directory is mounted into each container, so logs and throttle state remain available on the host and survive container recreation.

## Prerequisites

- Python 3.12 or newer for local execution
- Docker with the Compose plugin for container execution

## Run With Docker Compose

From the repository root, build the image and start both configured jobs:

```bash
docker compose up --build
```

Run in the background and follow the service logs:

```bash
docker compose up --build -d
docker compose logs -f
```

Stop and remove the containers with:

```bash
docker compose down
```

The Compose file defines two services:

| Service | Job ID | Default executions | Delay before restart |
| --- | --- | ---: | ---: |
| `job1` | `id1` | 50 | 4.3 seconds |
| `job2` | `id2` | 7 | 3.1 seconds |

Both services mount `./runtime` at `/app/runtime` and `./config` at `/app/config`.

## Run Locally

Run these commands from the repository root. The source package is laid out so the job can be started directly:

```bash
python src/python/job_type_1.py id1
python src/python/job_type_1.py id2
```

The default configuration is `config/config.json`. Set `APP_CONFIG` to use another JSON configuration file:

```bash
APP_CONFIG=config/config.json python src/python/job_type_1.py id1
```

The configured paths are resolved relative to the project root when running the job locally or in the supplied Docker image.

## Configuration

The default configuration is in [config/config.json](config/config.json).

### Global Settings

| Key | Description | Current value |
| --- | --- | --- |
| `speed_control.throttle_file` | JSON file containing the next allowed Unix timestamp | `runtime/throttle.json` |
| `speed_control.requests_per_minute` | Rate used to space executions; must be greater than zero | `100` |
| `logging.file` | Log file path | `runtime/app.log` |
| `logging.level` | Global Python logging level | `INFO` |
| `logging.format` | Python logging format string | Includes timestamp, job ID, logger, level, and message |

### Job Settings

Each entry in `jobs` is selected by its `id` command-line argument:

| Key | Description |
| --- | --- |
| `id` | Identifier passed to `job_type_1.py` |
| `name` | Descriptive job name |
| `type` | Job type metadata; dispatch is currently not dynamic |
| `executions` | Number of simulated payloads in one process run |
| `delay_seconds` | Delay after the batch completes and before process exit |
| `enabled` | Whether the job is allowed to run |
| `logging` | Optional per-job logging overrides |

Changing `executions` changes the size of each batch. Changing `delay_seconds` changes the interval between a process exit and its Docker restart; it does not change the spacing enforced between individual executions.

## Throttle State

The throttle stores a single `next_allowed_at` Unix timestamp:

```json
{
    "next_allowed_at": 1787484697.7003608
}
```

The interval between executions is `60 / requests_per_minute` seconds. With the default rate of `100`, the target interval is `0.6` seconds. If the file is missing or contains invalid JSON, it is recreated using the current time and a `RuntimeWarning` is emitted.

## Tests

The tests use Python's standard-library `unittest` runner:

```bash
python -m unittest discover -s tests/unit -p 'test_*.py'
```

The current tests cover throttle file creation and repair, timestamp handling, argument validation, timing calculations, and persistence of the next allowed timestamp.

## Repository Layout

```text
config/config.json                 Application and job configuration
docker/Dockerfile                  Python 3.12 image definition
docker-compose.yml                 job1 and job2 services
runtime/throttle.json              Persisted throttle state
src/python/job_type_1.py           Job entry point
src/python/common/bootstrap.py     Configuration and logging setup
src/python/common/throttle.py      File-backed throttle implementation
tests/unit/test_throttle.py        Throttle unit tests
```

## Operational Notes

- The throttle state is shared by both Compose services. The implementation does not use file locking or atomic read-modify-write coordination, so concurrent processes can race when updating the JSON file.
- `restart: always` restarts a container after normal exit and after failure. Treat this as a simple demonstration of recurring execution, not a replacement for a production scheduler or supervisor policy.
- `name` and `type` are currently descriptive configuration fields. The executable is `job_type_1.py` for both configured jobs.
- Runtime logs and state are intentionally stored under `runtime/`. Review or clear that directory deliberately when resetting local execution state.

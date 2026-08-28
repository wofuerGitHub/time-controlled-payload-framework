"""
Common application bootstrap utilities.

Provides configuration loading, job selection, and logging initialization
for the application's job processes.
"""

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

# Determine the project root directory and configuration file path
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Load the configuration file path from the environment variable or use the default path
CONFIG_PATH = Path(os.getenv("APP_CONFIG", PROJECT_ROOT / "config" / "config.json"))

# Function to merge job settings over global settings without dropping nested defaults
def merge_config(global_config: dict[str, Any], job_config: dict[str, Any]) -> dict[str, Any]:
    """Merge job settings over global settings without dropping nested defaults."""
    merged_config = dict(global_config)

    for key, value in job_config.items():
        global_value = merged_config.get(key)
        if isinstance(global_value, dict) and isinstance(value, dict):
            merged_config[key] = merge_config(global_value, value)
        else:
            merged_config[key] = value

    return merged_config

# Function to load the configuration from the JSON file
def load_config(config_path: Path) -> dict[str, Any]:
    """
    Load configuration from a JSON file.

    Parameters:
        config_path:
            Path to the JSON configuration file.

    Returns:
        dict[str, Any]:
            Parsed configuration.

    Raises:
        FileNotFoundError:
            If the configuration file does not exist.

        PermissionError:
            If the configuration file cannot be read due to permissions.

        ValueError:
            If the file contains invalid JSON or the top-level
            JSON value is not an object.
    """

    # Check if configuration file exists
    if not config_path.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path.resolve()}"
        )

    # Read configuration file
    try:
        with config_path.open("r", encoding="utf-8") as file:
            config = json.load(file)

    except PermissionError as exc:
        raise PermissionError(
            f"Permission denied reading configuration file: "
            f"{config_path.resolve()}"
        ) from exc

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in configuration file "
            f"{config_path.resolve()}: "
            f"line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    # Configuration root must be a JSON object
    if not isinstance(config, dict):
        raise ValueError(
            f"Invalid configuration in {config_path.resolve()}: "
            "top-level JSON value must be an object."
        )

    return config

# Function initializing application by parsing command-line arguments and configuration loading
def initialize() -> dict[str, Any]:
    """
    Initialize the application.

    Parses the job ID from the command line, loads the configuration,
    selects the matching job configuration, and initializes logging.

    Returns:
        dict[str, Any]:
            Configuration of the selected job.

        Raises:
            ValueError:
                If the job ID does not exist or the job is disabled.
    """

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "id",
        help="ID of the job instance",
    )

    args = parser.parse_args()

    # Load complete application configuration
    config = load_config(CONFIG_PATH)

    # Find global configuration
    global_config = config.get("global", {})

    if not global_config:
        raise ValueError(
            f"Global configuration missing in {CONFIG_PATH.resolve()}"
        )

    # Find requested job configuration
    job_config = next(
        (
            job
            for job in config.get("jobs", [])
            if isinstance(job, dict)
            and job.get("id") == args.id
        ),
        {},
    )

    if not job_config:
        raise ValueError(f"Unknown job id: {args.id}")

    # job config overrides global config for all settings, including logging
    if not job_config.get("enabled", True):
        raise ValueError(f"Job {args.id} is disabled in configuration")

    # Merge job configuration over global configuration
    config = merge_config(global_config, job_config)

    # Setup logging configuration
    setup_logging(
        config=config,
    )

    return config

# Function to setup logging configuration based on the loaded configuration
def setup_logging(config: dict[str, Any]) -> None:
    """
    Setup logging using the initialized configuration.
    """

    logging_config = config.get("logging", {})

    # Read settings
    log_file = logging_config.get("file")
    log_level = logging_config.get("level", "INFO")
    log_format = logging_config.get(
        "format",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Convert logging level string to logging constant
    level = getattr(logging, str(log_level).upper(), None)

    if not isinstance(level, int):
        raise ValueError(
            f"Invalid logging level: {log_level}"
        )

    # Create log directory if necessary
    if log_file:
        log_path = PROJECT_ROOT / log_file
        log_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
    else:
        log_path = None

    # Configure logging
    logging.basicConfig(
        filename=log_path,
        level=level,
        format=log_format,
    )

# ---

def main() -> None:
    """
    For testing purposes only, get the job configuration and print it to the console.
    """
    config = initialize()

    logger = logging.LoggerAdapter(
        logging.getLogger(__name__),
        {"job_id": config["id"]},
    )

    logger.info("Application started")
    logger.debug("Job configuration: %s", config)

    print(json.dumps(config, indent=4))

if __name__ == "__main__":
    main()

import argparse
import json
import os
from pathlib import Path
from typing import Any

# Determine the project root directory and configuration file path
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Load the configuration file path from the environment variable or use the default path
CONFIG_PATH = Path(os.getenv("APP_CONFIG", PROJECT_ROOT / "config" / "config.json"))

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

# Function to setup logging configuration based on the loaded configuration
def setup_logging(config: dict[str, Any]) -> None:
    """
    Setup logging configuration based on the loaded configuration.

    Parameters:
        config:
            Loaded configuration dictionary.
    """

    import logging.config

    logging_config = config.get("logging", {})
    if logging_config:
        logging.config.dictConfig(logging_config)
    else:
        # Default logging configuration if not specified in the config
        logging.basicConfig(level=logging.INFO)

# Function to initialize the application by parsing command-line arguments and loading the configuration
def initialize():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "id",
        help="ID of the job instance",
    )

    args = parser.parse_args()

    config = load_config(CONFIG_PATH)
    return config

# ---

def main() -> None:
    print(json.dumps(initialize(), indent=4))
    
if __name__ == "__main__":
    main()
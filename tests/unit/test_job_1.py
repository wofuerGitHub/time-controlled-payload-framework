import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_PATH = Path(
    os.getenv(
        "APP_CONFIG",
        PROJECT_ROOT / "config" / "config.json",
    )
)

def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> None:
    config = load_config()
    print(config)


if __name__ == "__main__":
    main()


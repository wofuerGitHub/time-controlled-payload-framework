"""
File: config_loader.py
Description: Tiny JSON config loader shared by all jobs.
"""

import json


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

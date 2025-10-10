import json
import os

def load_config(path="config.json"):
    with open(path, "r") as f:
        config = json.load(f)
    for key, value in config["api_keys"].items():
        os.environ[key] = value
    return config

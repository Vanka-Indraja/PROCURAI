import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_FILE = PROJECT_ROOT / "data" / "standards.json"


def load_standards():

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        standards = json.load(file)

    return standards
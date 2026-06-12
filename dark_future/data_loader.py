from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = PROJECT_ROOT / "data" / "rules"


def load_rule_json(name: str) -> dict[str, Any]:
    path = RULES_DIR / name
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def vehicle_template(template_id: str) -> dict[str, Any]:
    vehicles = load_rule_json("vehicles.json")
    for template in vehicles["vehicleTemplates"]:
        if template["id"] == template_id:
            return template
    raise KeyError(f"Unknown vehicle template: {template_id}")


def speed_phase_rows() -> list[dict[str, Any]]:
    rules = load_rule_json("speed-phases.json")
    return rules["core"]["rows"] + rules["whiteLineFever"]["rows"]


def track_inventory() -> dict[str, Any]:
    return load_rule_json("track-piece-inventory.json")


def track_definitions() -> dict[str, Any]:
    return load_rule_json("track-definitions.json")

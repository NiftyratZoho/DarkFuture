from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import ceil
from types import MappingProxyType
from typing import Any, Mapping

from .data_loader import load_rule_json


Effect = Mapping[str, Any]


@dataclass(frozen=True)
class DamageIncrementPenalty:
    threshold: int
    max_mph_delta: int
    acceleration_mph_delta: int
    handling_delta: int


@dataclass(frozen=True)
class DamageResult:
    die: int
    damage_modifier: int
    armour: int
    ordinary_damage: int
    remaining_damage: int
    critical_triggered: bool
    terminal_damage: bool
    crossed_increment_thresholds: tuple[int, ...]
    increment_penalties: tuple[DamageIncrementPenalty, ...]
    ignored_ordinary_damage: bool = False
    hazard_safety_limit_mph: int | None = None


@dataclass(frozen=True)
class CriticalResult:
    table_id: str
    roll: int
    result_id: str
    effects: tuple[Effect, ...]
    confirmation_roll: Effect | None = None
    raw: Effect | None = None


@dataclass(frozen=True)
class HazardTestResult:
    kind: str
    roll: int | None
    total: int | None
    effect: str
    skipped: bool = False
    speed_loss_mph: int = 0
    control_lost: bool = False
    safety_limit_mph: int | None = None


@lru_cache(maxsize=1)
def damage_tables() -> dict[str, Any]:
    return load_rule_json("damage-tables.json")


@lru_cache(maxsize=1)
def hazard_tables() -> dict[str, Any]:
    return load_rule_json("hazard-results.json")


@lru_cache(maxsize=1)
def equipment_tables() -> dict[str, Any]:
    return load_rule_json("equipment.json")


@lru_cache(maxsize=1)
def bikes_three_wheelers_tables() -> dict[str, Any]:
    return load_rule_json("bikes-three-wheelers.json")


def _validate_d6(roll: int) -> None:
    if roll < 1 or roll > 6:
        raise ValueError(f"d6 roll must be between 1 and 6, got {roll}")


def _freeze_effect(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_effect(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_effect(item) for item in value)
    return value


def _matching_row(rows: list[dict[str, Any]], roll: int) -> dict[str, Any]:
    for row in rows:
        range_ = row.get("range", {})
        minimum = int(range_.get("min", -10**9))
        maximum = int(range_.get("max", 10**9))
        if minimum <= roll <= maximum:
            return row
    raise KeyError(f"No table row matches roll {roll}")


def vehicle_damage_profile(template_id: str) -> dict[str, Any]:
    for profile in damage_tables()["vehicleDamage"]:
        if profile["vehicleTemplateId"] == template_id:
            return profile
    raise KeyError(f"Unknown vehicle damage profile: {template_id}")


def weapon_damage_modifier(weapon_id: str) -> int:
    for weapon in damage_tables()["weaponDamageCharacteristics"]:
        if weapon["weaponId"] == weapon_id:
            return int(weapon["damageModifier"])
    raise KeyError(f"Unknown weapon damage characteristic: {weapon_id}")


def damage_increment_penalties(
    template_id: str,
    previous_damage: int,
    remaining_damage: int,
) -> tuple[DamageIncrementPenalty, ...]:
    profile = vehicle_damage_profile(template_id)
    effect = damage_tables()["damageIncrementEffect"]
    crossed = [
        int(threshold)
        for threshold in profile["damageIncrements"]
        if previous_damage >= int(threshold) and remaining_damage < int(threshold)
    ]
    return tuple(
        DamageIncrementPenalty(
            threshold=threshold,
            max_mph_delta=int(effect["maxMphDelta"]),
            acceleration_mph_delta=int(effect["accelerationMphDelta"]),
            handling_delta=int(effect["handlingDelta"]),
        )
        for threshold in crossed
    )


def resolve_damage(
    *,
    template_id: str,
    current_damage: int,
    die: int,
    damage_modifier: int,
    armour: int,
    tags: tuple[str, ...] = (),
) -> DamageResult:
    _validate_d6(die)
    critical_trigger = damage_tables()["coreDamageProcedure"]["criticalTrigger"]
    ignored_ordinary = current_damage <= 0
    ordinary_damage = 0
    remaining_damage = current_damage
    if not ignored_ordinary:
        ordinary_damage = max(0, die + damage_modifier - armour)
        remaining_damage = max(0, current_damage - ordinary_damage)

    penalties = damage_increment_penalties(template_id, current_damage, remaining_damage)
    hazard_limit = None
    if "HE" in tags:
        hazard_limit = 50 if damage_modifier <= 4 else 30

    return DamageResult(
        die=die,
        damage_modifier=damage_modifier,
        armour=armour,
        ordinary_damage=ordinary_damage,
        remaining_damage=remaining_damage,
        critical_triggered=die == int(critical_trigger["damageDieNatural"]),
        terminal_damage=current_damage > 0 and remaining_damage <= 0,
        crossed_increment_thresholds=tuple(penalty.threshold for penalty in penalties),
        increment_penalties=penalties,
        ignored_ordinary_damage=ignored_ordinary,
        hazard_safety_limit_mph=hazard_limit,
    )


def critical_result(table_id: str, roll: int) -> CriticalResult:
    _validate_d6(roll)
    table = damage_tables()["criticalResultTables"][table_id]
    if isinstance(table, dict):
        effects = tuple(_freeze_effect(effect) for effect in table.get("effects", ()))
        return CriticalResult(
            table_id=table_id,
            roll=roll,
            result_id=table_id,
            effects=effects,
            raw=_freeze_effect(table),
        )

    row = _matching_row(table, roll)
    return CriticalResult(
        table_id=table_id,
        roll=roll,
        result_id=str(row["resultId"]),
        effects=tuple(_freeze_effect(effect) for effect in row.get("effects", ())),
        confirmation_roll=_freeze_effect(row["confirmationRoll"])
        if "confirmationRoll" in row
        else None,
        raw=_freeze_effect(row),
    )


def speed_factor(mph: int) -> int:
    if mph <= 0:
        return 0
    return ceil(mph / 20)


def resolve_hazard_test(
    *,
    roll: int,
    mph: int,
    safety_limit_mph: int,
    handling: int,
    drive_skill: int,
    controlled: bool = True,
) -> HazardTestResult:
    _validate_d6(roll)
    if not controlled or mph <= safety_limit_mph:
        return HazardTestResult(
            kind="hazard",
            roll=None,
            total=None,
            effect="ok",
            skipped=True,
            safety_limit_mph=safety_limit_mph,
        )

    excess_speed = ceil(max(0, mph - safety_limit_mph) / 10)
    optimum_control = max(handling, drive_skill)
    total = roll + excess_speed - optimum_control
    row = _matching_row(hazard_tables()["hazardRoll"]["results"], total)
    effect = str(row["effect"])
    speed_loss = 5 * total if effect == "panicBrake" else 0
    return HazardTestResult(
        kind="hazard",
        roll=roll,
        total=total,
        effect=effect,
        speed_loss_mph=speed_loss,
        control_lost=effect == "controlLoss",
        safety_limit_mph=safety_limit_mph,
    )


def resolve_control_loss_test(
    *,
    roll: int,
    mph: int,
    handling: int,
    drive_skill: int | None,
) -> HazardTestResult:
    _validate_d6(roll)
    effective_drive = 0 if drive_skill is None else drive_skill
    total = roll + speed_factor(mph) - min(handling, effective_drive)
    if handling == 0 or drive_skill is None:
        total += 2
    row = _matching_row(hazard_tables()["controlLossTest"]["results"], total)
    return HazardTestResult(
        kind="controlLoss",
        roll=roll,
        total=total,
        effect=str(row["effect"]),
        control_lost=str(row["effect"]) != "regainControlAfterStraightMove",
    )


def spin_template_speed_loss(total: int, colour: str | None = None) -> int | None:
    template = hazard_tables()["advancedSpin"].get("alreadySpunSpinTemplate", {})
    rows_by_colour = template.get("rowsByColour", {})
    colour_key = colour or str(template.get("defaultColour", "redClockwise"))
    rows = rows_by_colour.get(colour_key)
    if rows is None:
        raise KeyError(f"Unknown spin template colour: {colour_key}")
    for row in rows:
        range_data = row["range"]
        minimum = int(range_data.get("min", -999))
        maximum = int(range_data.get("max", 999))
        if minimum <= total <= maximum:
            return int(row["speedLossMph"])
    return None


def safety_limit(safety_limit_id: str) -> int | None:
    for row in hazard_tables()["safetyLimits"]:
        if row["id"] == safety_limit_id:
            value = row["safetyLimitMph"]
            return int(value) if value is not None else None
    raise KeyError(f"Unknown safety limit: {safety_limit_id}")


def _missile_ammunition(ammo_id: str) -> dict[str, Any]:
    for row in equipment_tables()["ammunitionTypes"]:
        if row["id"] == ammo_id:
            return row
    raise KeyError(f"Unknown ammunition type: {ammo_id}")


def tgsm_submunition_count(roll: int) -> int:
    _validate_d6(roll)
    tgsm = _missile_ammunition("missile.tgsm")
    row = _matching_row(tgsm["resolution"]["submunitionCountTable"], roll)
    return int(row["submunitions"])


def tgsm_hit_location(roll: int) -> dict[str, Any]:
    _validate_d6(roll)
    tgsm = _missile_ammunition("missile.tgsm")
    return dict(_matching_row(tgsm["resolution"]["hitLocationTable"], roll))


def resolve_tgsm_hit(count_roll: int, location_rolls: tuple[int, ...]) -> tuple[dict[str, Any], ...]:
    count = tgsm_submunition_count(count_roll)
    if len(location_rolls) != count:
        raise ValueError(f"TGSM count roll requires {count} hit-location rolls")
    return tuple(tgsm_hit_location(roll) for roll in location_rolls)


def three_wheeler_hit_component(matrix_id: str, attack_arc: str, roll: int) -> str:
    _validate_d6(roll)
    matrix = bikes_three_wheelers_tables()[matrix_id]
    rows = matrix["attackArcs"][attack_arc]
    return str(_matching_row(rows, roll)["component"])

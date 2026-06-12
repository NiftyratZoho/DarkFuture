from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from .data_loader import track_definitions


LANE_COUNT = 8
VEHICLE_LANE_WIDTH = 2
MIN_LANE_PAIR = 1
MAX_LANE_PAIR = LANE_COUNT - VEHICLE_LANE_WIDTH + 1

TrackPieceType = Literal["straight", "curve30to60", "curve50to80"]
DriftDirection = Literal["left", "right", "inward", "outward"]


def lane_key(lane: int) -> str:
    validate_lane(lane)
    if lane == 1:
        return "lane1_inner"
    if lane == LANE_COUNT:
        return "lane8_outer"
    return f"lane{lane}"


def validate_lane(lane: int) -> None:
    if lane < 1 or lane > LANE_COUNT:
        raise ValueError(f"lane must be between 1 and {LANE_COUNT}: {lane}")


def validate_lane_pair(lane_pair: int) -> None:
    if not is_legal_lane_pair(lane_pair):
        raise ValueError(f"lane_pair must be one of {legal_lane_pairs()}: {lane_pair}")


def occupied_lanes(lane_pair: int) -> tuple[int, int]:
    validate_lane_pair(lane_pair)
    return lane_pair, lane_pair + 1


def legal_lane_pairs() -> tuple[int, ...]:
    rules = _rules()
    return tuple(int(pair) for pair in rules["implementationConventions"]["legalLanePairs"])


def is_legal_lane_pair(lane_pair: int) -> bool:
    return lane_pair in legal_lane_pairs()


def base_piece_type(piece_type: str) -> TrackPieceType:
    if piece_type.startswith("curve30to60"):
        return "curve30to60"
    if piece_type.startswith("curve50to80"):
        return "curve50to80"
    if piece_type == "straight":
        return "straight"
    raise KeyError(f"Unknown track piece type: {piece_type}")


def piece_definition(piece_type: str) -> dict[str, Any]:
    return _rules()["trackPieceTypes"][base_piece_type(piece_type)]


def straight_spaces() -> int:
    return int(piece_definition("straight")["sectionsPerLane"])


def lane_section_count(piece_type: str, lane: int) -> int:
    definition = piece_definition(piece_type)
    validate_lane(lane)
    if definition["type"] == "straight":
        return int(definition["sectionsPerLane"])
    return int(definition["sectionsByLane"][lane_key(lane)])


def lane_speed_limit(piece_type: str, lane: int) -> int | None:
    definition = piece_definition(piece_type)
    validate_lane(lane)
    if definition["type"] == "straight":
        return None
    return int(definition["speedByLane"][lane_key(lane)])


def lane_pair_section_count(piece_type: str, lane_pair: int) -> int:
    return max(lane_section_count(piece_type, lane) for lane in occupied_lanes(lane_pair))


def piece_max_spaces(piece_type: str) -> int:
    return max(lane_section_count(piece_type, lane) for lane in range(1, LANE_COUNT + 1))


def piece_angle_degrees(piece_type: str) -> int:
    definition = piece_definition(piece_type)
    return int(definition.get("angleDegrees", 0))


def piece_family(piece_type: str) -> str:
    definition = piece_definition(piece_type)
    return str(definition.get("family", definition["type"]))


def lane_pair_safety_limit(piece_type: str, lane_pair: int) -> int | None:
    definition = piece_definition(piece_type)
    if definition["type"] == "straight":
        validate_lane_pair(lane_pair)
        return None
    return min(
        int(definition["speedByLane"][lane_key(lane)])
        for lane in occupied_lanes(lane_pair)
    )


def is_valid_lane_space(piece_type: str, lane: int, space: int) -> bool:
    if space < 1:
        return False
    return space <= lane_section_count(piece_type, lane)


def is_valid_position(piece_type: str, lane_pair: int, space: int) -> bool:
    if not is_legal_lane_pair(lane_pair) or space < 1:
        return False
    return space <= lane_pair_section_count(piece_type, lane_pair)


def forward_position(
    track_piece_types: list[str] | tuple[str, ...],
    section: int,
    space: int,
    lane_pair: int,
    direction: int = 1,
) -> tuple[int, int] | None:
    if direction not in (-1, 1):
        raise ValueError(f"direction must be 1 or -1: {direction}")
    if section < 0 or section >= len(track_piece_types):
        raise IndexError(f"section out of range: {section}")

    current_piece = track_piece_types[section]
    if not is_valid_position(current_piece, lane_pair, space):
        raise ValueError(
            f"invalid position for {current_piece}: section={section}, space={space}, lane_pair={lane_pair}"
        )

    next_space = space + direction
    if is_valid_position(current_piece, lane_pair, next_space):
        return section, next_space

    next_section = section + direction
    if next_section < 0 or next_section >= len(track_piece_types):
        return None

    next_piece = track_piece_types[next_section]
    if direction == 1:
        return next_section, 1
    return next_section, lane_pair_section_count(next_piece, lane_pair)


def drift_lane_pair(
    piece_type: str,
    lane_pair: int,
    drift_direction: DriftDirection,
    *,
    allow_inward_curve_drift: bool = False,
) -> int | None:
    validate_lane_pair(lane_pair)
    offset = _drift_offset(piece_type, drift_direction, allow_inward_curve_drift)
    target = lane_pair + offset
    if not is_legal_lane_pair(target):
        return None
    return target


def can_drift(
    piece_type: str,
    lane_pair: int,
    drift_direction: DriftDirection,
    *,
    allow_inward_curve_drift: bool = False,
) -> bool:
    try:
        return drift_lane_pair(
            piece_type,
            lane_pair,
            drift_direction,
            allow_inward_curve_drift=allow_inward_curve_drift,
        ) is not None
    except ValueError:
        return False


def render_grid_data(piece_type: str) -> dict[str, Any]:
    definition = piece_definition(piece_type)
    max_spaces = piece_max_spaces(piece_type)
    cells = []
    for lane in range(1, LANE_COUNT + 1):
        for space in range(1, max_spaces + 1):
            cells.append(
                {
                    "lane": lane,
                    "space": space,
                    "valid": is_valid_lane_space(piece_type, lane, space),
                    "speedLimitMph": lane_speed_limit(piece_type, lane),
                }
            )
    return {
        "pieceType": base_piece_type(piece_type),
        "kind": definition["type"],
        "family": piece_family(piece_type),
        "angleDegrees": piece_angle_degrees(piece_type),
        "lanes": LANE_COUNT,
        "spaces": max_spaces,
        "cells": cells,
        "lanePairs": [
            {
                "lanePair": lane_pair,
                "lanes": occupied_lanes(lane_pair),
                "spaces": lane_pair_section_count(piece_type, lane_pair),
                "safetyLimitMph": lane_pair_safety_limit(piece_type, lane_pair),
            }
            for lane_pair in legal_lane_pairs()
        ],
    }


def _drift_offset(
    piece_type: str,
    drift_direction: DriftDirection,
    allow_inward_curve_drift: bool,
) -> int:
    kind = piece_definition(piece_type)["type"]
    if kind == "straight":
        if drift_direction in ("left", "inward"):
            return -1
        if drift_direction in ("right", "outward"):
            return 1
    else:
        if drift_direction == "outward":
            return 1
        if drift_direction == "inward" and allow_inward_curve_drift:
            return -1
        if drift_direction in ("left", "right"):
            raise ValueError("curve drift must use 'inward' or 'outward'")
    raise ValueError(f"illegal drift direction for {piece_type}: {drift_direction}")


@lru_cache(maxsize=1)
def _rules() -> dict[str, Any]:
    return track_definitions()

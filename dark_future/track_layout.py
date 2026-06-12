from __future__ import annotations

from dataclasses import dataclass
import math

from .track import (
    LANE_COUNT,
    lane_pair_section_count,
    lane_section_count,
    piece_angle_degrees,
    straight_spaces,
)


@dataclass(frozen=True)
class SectionPlacement:
    index: int
    piece_type: str
    entry: tuple[float, float]
    exit: tuple[float, float]
    heading_degrees: float
    exit_heading_degrees: float
    center: tuple[float, float] | None
    radius: float | None
    turn_direction: int
    lane_direction: int


def layout_track_sections(
    piece_types: list[str] | tuple[str, ...],
    *,
    lane_width: float,
    car_length: float,
    start: tuple[float, float] = (0.0, 0.0),
    heading_degrees: float = 0.0,
) -> tuple[SectionPlacement, ...]:
    placements: list[SectionPlacement] = []
    entry = start
    heading = heading_degrees
    lane_direction = 1
    for index, piece_type in enumerate(piece_types):
        placement = place_section(
            index,
            piece_type,
            entry=entry,
            heading_degrees=heading,
            lane_width=lane_width,
            car_length=car_length,
            lane_direction=lane_direction,
        )
        placements.append(placement)
        entry = placement.exit
        heading = placement.exit_heading_degrees
        lane_direction = placement.lane_direction
    return tuple(placements)


def place_section(
    index: int,
    piece_type: str,
    *,
    entry: tuple[float, float],
    heading_degrees: float,
    lane_width: float,
    car_length: float,
    lane_direction: int = 1,
) -> SectionPlacement:
    angle_degrees = piece_angle_degrees(piece_type)
    if angle_degrees == 0:
        length = straight_spaces() * car_length
        exit_point = _advance(entry, heading_degrees, length)
        return SectionPlacement(
            index=index,
            piece_type=piece_type,
            entry=entry,
            exit=exit_point,
            heading_degrees=heading_degrees,
            exit_heading_degrees=heading_degrees,
            center=None,
            radius=None,
            turn_direction=0,
            lane_direction=lane_direction,
        )

    turn = -1 if piece_type.endswith("_right") else 1
    road_width = LANE_COUNT * lane_width
    boundaries = curve_lane_boundary_radii(
        piece_type,
        lane_width=lane_width,
        car_length=car_length,
    )
    inner_edge_radius = boundaries[0]
    outer_edge_radius = boundaries[-1]
    inner_entry = entry
    if turn == 1:
        inner_entry = _advance(entry, heading_degrees + 90, road_width)
    center = _advance(inner_entry, heading_degrees + turn * 90, inner_edge_radius)
    exit_heading = heading_degrees + turn * angle_degrees
    radial_from_center = heading_degrees - turn * 90
    exit_radial = radial_from_center + turn * angle_degrees
    exit_radius = outer_edge_radius if turn == 1 else inner_edge_radius
    exit_point = _advance(center, exit_radial, exit_radius)
    return SectionPlacement(
        index=index,
        piece_type=piece_type,
        entry=entry,
        exit=exit_point,
        heading_degrees=heading_degrees,
        exit_heading_degrees=exit_heading,
        center=center,
        radius=inner_edge_radius,
        turn_direction=turn,
        lane_direction=-1 if turn == 1 else 1,
    )


def point_on_straight(
    placement: SectionPlacement,
    *,
    space: int,
    lane_pair: float,
    lane_width: float,
    car_length: float,
) -> tuple[float, float]:
    along = (space - 0.5) * car_length
    lateral = lane_offset(placement, lane_pair, lane_width)
    point = _advance(placement.entry, placement.heading_degrees, along)
    return _advance(point, placement.heading_degrees + 90, lateral)


def point_on_curve(
    placement: SectionPlacement,
    *,
    space: int,
    lane_pair: int,
    lane_width: float,
    car_length: float,
    spaces: int | None = None,
) -> tuple[float, float]:
    if placement.center is None or placement.radius is None:
        raise ValueError("curve placement requires center and radius")
    count = lane_pair_section_count(placement.piece_type, lane_pair)
    angle_step = (placement.exit_heading_degrees - placement.heading_degrees) / count
    radial = placement.heading_degrees - placement.turn_direction * 90
    radial += angle_step * (space - 0.5)
    centers = curve_lane_center_radii(placement.piece_type, car_length=car_length)
    radius = (centers[lane_pair - 1] + centers[lane_pair]) / 2
    return _advance(placement.center, radial, radius)


def point_on_curve_lane(
    placement: SectionPlacement,
    *,
    space: int,
    lane: int,
    car_length: float,
) -> tuple[float, float]:
    if placement.center is None:
        raise ValueError("curve placement requires center")
    count = lane_section_count(placement.piece_type, lane)
    angle_step = (placement.exit_heading_degrees - placement.heading_degrees) / count
    radial = placement.heading_degrees - placement.turn_direction * 90
    radial += angle_step * (space - 0.5)
    radius = curve_lane_center_radii(placement.piece_type, car_length=car_length)[lane - 1]
    return _advance(placement.center, radial, radius)


def curve_lane_center_radii(piece_type: str, *, car_length: float) -> tuple[float, ...]:
    theta = math.radians(piece_angle_degrees(piece_type))
    if theta <= 0:
        raise ValueError(f"{piece_type} is not a curve")
    return tuple(
        lane_section_count(piece_type, lane) * car_length / theta
        for lane in range(1, LANE_COUNT + 1)
    )


def curve_lane_boundary_radii(
    piece_type: str,
    *,
    lane_width: float,
    car_length: float,
) -> tuple[float, ...]:
    centers = curve_lane_center_radii(piece_type, car_length=car_length)
    inner_edge = centers[0] - lane_width / 2
    return tuple(inner_edge + lane_width * index for index in range(LANE_COUNT + 1))


def lane_offset(
    placement: SectionPlacement,
    lane_position: float,
    lane_width: float,
) -> float:
    if placement.lane_direction == -1:
        return (LANE_COUNT - lane_position) * lane_width
    return lane_position * lane_width


def _advance(
    point: tuple[float, float],
    heading_degrees: float,
    distance: float,
) -> tuple[float, float]:
    radians = math.radians(heading_degrees)
    return (
        point[0] + math.cos(radians) * distance,
        point[1] + math.sin(radians) * distance,
    )

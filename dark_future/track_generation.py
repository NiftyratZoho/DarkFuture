from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Literal, Protocol


CurveFamily = Literal["broadBend", "tightCorner"]
CurveDirection = Literal["left", "right"]
SectionKind = Literal["straight", "curve50to80", "curve30to60"]

MAX_CONTINUOUS_SECTIONS = 7
INITIAL_STARTING_STRAIGHTS = 3
INITIAL_TARGET_SECTIONS = 10


class DiceSource(Protocol):
    def roll(self) -> int:
        ...


@dataclass
class SequenceDice:
    values: list[int]
    index: int = 0

    def __init__(self, values: Iterable[int]) -> None:
        self.values = list(values)
        self.index = 0

    def roll(self) -> int:
        if self.index >= len(self.values):
            raise IndexError("dice sequence exhausted")
        value = int(self.values[self.index])
        self.index += 1
        if value < 1 or value > 6:
            raise ValueError(f"dice value must be 1-6: {value}")
        return value


@dataclass(frozen=True)
class GeneratedSection:
    kind: SectionKind
    direction: CurveDirection | None = None
    automatic: bool = False

    @property
    def is_curve(self) -> bool:
        return self.kind != "straight"

    @property
    def piece_type(self) -> str:
        if self.direction is None:
            return self.kind
        return f"{self.kind}_{self.direction}"


@dataclass
class TrackInventory:
    straights: int | None = None
    broad_bends: int | None = None
    tight_corners: int | None = None

    @classmethod
    def unlimited(cls) -> "TrackInventory":
        return cls()

    @classmethod
    def from_rule_inventory(cls, data: dict[str, object]) -> "TrackInventory":
        visible = data.get("visibleInventory")
        if not isinstance(visible, dict):
            return cls.unlimited()
        return cls(
            straights=_inventory_count(visible.get("straight")),
            broad_bends=_inventory_count(visible.get("broadBends")),
            tight_corners=_inventory_count(visible.get("tightCorners")),
        )

    def available(self, section: GeneratedSection, sections: list[GeneratedSection]) -> bool:
        limit = self._limit_for(section)
        if limit is None:
            return True
        return sum(1 for placed in sections if self._same_component_family(placed, section)) < limit

    def has_family_available(self, family: CurveFamily, sections: list[GeneratedSection]) -> bool:
        limit = self._family_limit(family)
        if limit is None:
            return True
        return sum(1 for section in sections if curve_family_for_kind(section.kind) == family) < limit

    def has_straight_available(self, sections: list[GeneratedSection]) -> bool:
        return self.available(GeneratedSection("straight"), sections)

    def _limit_for(self, section: GeneratedSection) -> int | None:
        if section.kind == "straight":
            return self.straights
        return self._family_limit(curve_family_for_kind(section.kind))

    def _family_limit(self, family: CurveFamily | None) -> int | None:
        if family == "broadBend":
            return self.broad_bends
        if family == "tightCorner":
            return self.tight_corners
        return None

    @staticmethod
    def _same_component_family(a: GeneratedSection, b: GeneratedSection) -> bool:
        if a.kind == "straight" or b.kind == "straight":
            return a.kind == b.kind
        return curve_family_for_kind(a.kind) == curve_family_for_kind(b.kind)


@dataclass
class RollingTrack:
    sections: list[GeneratedSection] = field(default_factory=list)
    removed_sections: list[GeneratedSection] = field(default_factory=list)
    pending_mandatory_straight_after_curve_index: int | None = None
    ended: bool = False

    @classmethod
    def starting_straights(cls, count: int = INITIAL_STARTING_STRAIGHTS) -> "RollingTrack":
        return cls(sections=[GeneratedSection("straight", automatic=True) for _ in range(count)])

    @property
    def piece_types(self) -> list[str]:
        return [section.piece_type for section in self.sections]


def generated_curve_family(roll: int) -> CurveFamily:
    _validate_die(roll)
    return "tightCorner" if roll >= 5 else "broadBend"


def generated_curve_direction(roll: int) -> CurveDirection:
    _validate_die(roll)
    return "left" if roll % 2 else "right"


def generated_section_is_curve(roll: int) -> bool:
    _validate_die(roll)
    return roll >= 5


def curve_kind_for_family(family: CurveFamily) -> SectionKind:
    return "curve30to60" if family == "tightCorner" else "curve50to80"


def curve_family_for_kind(kind: SectionKind) -> CurveFamily | None:
    if kind == "curve30to60":
        return "tightCorner"
    if kind == "curve50to80":
        return "broadBend"
    return None


def build_initial_track(
    dice: DiceSource,
    *,
    inventory: TrackInventory | None = None,
    target_sections: int = INITIAL_TARGET_SECTIONS,
) -> RollingTrack:
    track = RollingTrack.starting_straights()
    inventory = inventory or TrackInventory.unlimited()
    while len(track.sections) < target_sections and not track.ended:
        section = _roll_next_generated_section(dice, track.sections, inventory)
        if section is None:
            track.ended = True
            break
        _append_section(track, section, inventory)
        if section.is_curve and len(track.sections) < target_sections:
            _append_mandatory_straight(track, inventory)
    return track


def generate_for_lead(
    track: RollingTrack,
    lead_section_index: int,
    dice: DiceSource,
    *,
    inventory: TrackInventory | None = None,
    max_sections: int = MAX_CONTINUOUS_SECTIONS,
) -> RollingTrack:
    if track.ended:
        return track
    if lead_section_index < 0 or lead_section_index >= len(track.sections):
        raise IndexError(f"lead section out of range: {lead_section_index}")

    inventory = inventory or TrackInventory.unlimited()
    current = track.sections[lead_section_index]

    if current.is_curve:
        _place_pending_mandatory_straight(track, lead_section_index, inventory, max_sections)
        return track

    if _is_mandatory_straight_after_curve(track, lead_section_index):
        _clear_satisfied_pending_straight(track, lead_section_index)

    while _lead_needs_more_line_of_sight(track, lead_section_index) and not track.ended:
        section = _roll_next_generated_section(dice, track.sections, inventory)
        if section is None:
            track.ended = True
            break
        _append_section(track, section, inventory)
        lead_section_index -= _trim_to_max_sections(track, max_sections)
        if section.is_curve:
            track.pending_mandatory_straight_after_curve_index = len(track.sections) - 1
            break
    return track


def _roll_next_generated_section(
    dice: DiceSource,
    sections: list[GeneratedSection],
    inventory: TrackInventory,
) -> GeneratedSection | None:
    section_roll = dice.roll()
    if not generated_section_is_curve(section_roll):
        straight = GeneratedSection("straight")
        if not inventory.available(straight, sections):
            return None
        return straight

    family = _available_curve_family(generated_curve_family(dice.roll()), sections, inventory)
    if family is None:
        return None
    direction = _curve_direction_with_one_eighty_rule(dice.roll(), sections)
    return GeneratedSection(curve_kind_for_family(family), direction)


def _available_curve_family(
    wanted: CurveFamily,
    sections: list[GeneratedSection],
    inventory: TrackInventory,
) -> CurveFamily | None:
    if inventory.has_family_available(wanted, sections):
        return wanted
    other: CurveFamily = "tightCorner" if wanted == "broadBend" else "broadBend"
    if inventory.has_family_available(other, sections):
        return other
    return None


def _curve_direction_with_one_eighty_rule(
    direction_roll: int,
    sections: list[GeneratedSection],
) -> CurveDirection:
    rolled = generated_curve_direction(direction_roll)
    previous_directions = [section.direction for section in sections if section.is_curve]
    if len(previous_directions) >= 2 and previous_directions[-1] == previous_directions[-2]:
        return "right" if previous_directions[-1] == "left" else "left"
    return rolled


def _append_section(
    track: RollingTrack,
    section: GeneratedSection,
    inventory: TrackInventory,
) -> bool:
    if not inventory.available(section, track.sections):
        if section.kind == "straight":
            track.ended = True
        return False
    track.sections.append(section)
    return True


def _append_mandatory_straight(track: RollingTrack, inventory: TrackInventory) -> bool:
    return _append_section(track, GeneratedSection("straight", automatic=True), inventory)


def _place_pending_mandatory_straight(
    track: RollingTrack,
    lead_section_index: int,
    inventory: TrackInventory,
    max_sections: int,
) -> None:
    expected_index = lead_section_index + 1
    if expected_index < len(track.sections) and track.sections[expected_index].kind == "straight":
        _clear_satisfied_pending_straight(track, expected_index)
        return
    if _append_mandatory_straight(track, inventory):
        track.pending_mandatory_straight_after_curve_index = lead_section_index
        _trim_to_max_sections(track, max_sections)


def _lead_needs_more_line_of_sight(track: RollingTrack, lead_section_index: int) -> bool:
    ahead = track.sections[lead_section_index + 1 :]
    visible_straights = 0
    for section in ahead:
        if section.is_curve:
            return False
        visible_straights += 1
        if visible_straights >= 3:
            return False
    return True


def _trim_to_max_sections(track: RollingTrack, max_sections: int) -> int:
    removed_count = 0
    while len(track.sections) > max_sections:
        removed = track.sections.pop(0)
        track.removed_sections.append(removed)
        removed_count += 1
        if track.pending_mandatory_straight_after_curve_index is not None:
            track.pending_mandatory_straight_after_curve_index -= 1
            if track.pending_mandatory_straight_after_curve_index < 0:
                track.pending_mandatory_straight_after_curve_index = None
    return removed_count


def _is_mandatory_straight_after_curve(track: RollingTrack, section_index: int) -> bool:
    if section_index <= 0:
        return False
    return track.sections[section_index].kind == "straight" and track.sections[section_index - 1].is_curve


def _clear_satisfied_pending_straight(track: RollingTrack, straight_index: int) -> None:
    if track.pending_mandatory_straight_after_curve_index == straight_index - 1:
        track.pending_mandatory_straight_after_curve_index = None


def _validate_die(value: int) -> None:
    if value < 1 or value > 6:
        raise ValueError(f"dice value must be 1-6: {value}")


def _inventory_count(entry: object) -> int | None:
    if not isinstance(entry, dict):
        return None
    count = entry.get("count")
    return int(count) if isinstance(count, int) else None

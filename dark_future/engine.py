from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from math import ceil
import random
from pathlib import Path
from typing import Literal

from .combat_tables import (
    critical_result,
    resolve_control_loss_test,
    resolve_damage as table_resolve_damage,
    resolve_hazard_test,
)
from .data_loader import speed_phase_rows, track_inventory, vehicle_template
from .track import (
    LANE_COUNT,
    MAX_LANE_PAIR,
    MIN_LANE_PAIR,
    drift_lane_pair,
    forward_position as track_forward_position,
    lane_pair_safety_limit,
    lane_pair_section_count,
    piece_max_spaces,
)
from .track_generation import TrackInventory, build_initial_track


Side = Literal["agency", "outlaw"]
Direction = Literal[1, -1]
MarkerKind = Literal["oil", "smoke", "spikes", "mines"]


@dataclass(frozen=True)
class SourceRef:
    book: str
    pages: tuple[int, ...]
    note: str


@dataclass
class LogEntry:
    message: str
    kind: str = "rule"
    source: SourceRef | None = None


@dataclass
class Dice:
    seed: int = 124
    queue: list[int] = field(default_factory=list)
    rng: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self.rng = random.Random(self.seed)

    def d6(self) -> int:
        if self.queue:
            return self.queue.pop(0)
        return self.rng.randint(1, 6)

    def roll(self) -> int:
        return self.d6()


@dataclass
class Vehicle:
    id: str
    label: str
    side: Side
    template_id: str
    section: int
    space: int
    lane_pair: int
    direction: Direction
    mph: int
    max_mph: int
    acceleration_mph: int
    braking_mph: int
    handling: int
    damage: int
    armour: int
    weapon_label: str
    weapon_accuracy: int
    weapon_damage_modifier: int
    acted_this_phase: bool = False
    destroyed: bool = False
    control_state: str = "controlled"
    driver_skill: int = 3
    hazard_mod: int = 0
    weapon_disabled: bool = False
    critical_notes: list[str] = field(default_factory=list)
    rocket_booster_type: str | None = None
    rocket_booster_shots: int = 0
    rocket_booster_mode: str | None = None
    rocket_booster_cruise_mph: int | None = None
    rocket_booster_disabled: bool = False
    action_cancelled_this_phase: bool = False

    @property
    def lane_rows(self) -> tuple[int, int]:
        return self.lane_pair, self.lane_pair + 1


@dataclass
class CampaignState:
    name: str = "Roadside Sanction"
    player_kind: str = "Sanctioned Op agency"
    funds: int = 100000
    roster: list[str] = field(default_factory=lambda: ["Alex Decker", "Mara Voss"])
    garage: list[str] = field(default_factory=lambda: ["agency-1"])
    kudos: int = 0
    contracts_completed: int = 0
    repairs_pending: int = 0
    settlement_pending: bool = False
    recruits_hired: int = 0
    current_scenario: str = "intercept"
    objective: str = "Agency vehicle must exit the road or destroy the outlaw opposition."
    last_save_path: str = "dark_future_save.json"


@dataclass
class PassiveMarker:
    id: str
    kind: MarkerKind
    section: int
    space: int
    lane_pair: int
    owner_side: Side
    trigger_on_exit_vehicle_id: str | None = None


@dataclass
class GameState:
    turn: int
    phase: int
    track_sections: int
    vehicles: list[Vehicle]
    track_section_types: list[str]
    passive_markers: list[PassiveMarker]
    active_vehicle_id: str | None
    logs: list[LogEntry]
    campaign: CampaignState = field(default_factory=CampaignState)
    dice: Dice = field(default_factory=Dice)
    mode: str = "tactical"
    game_over: bool = False
    winner: Side | None = None
    next_marker_id: int = 1
    scenario_id: str = "intercept"
    objective: str = "Agency vehicle must exit the road or destroy the outlaw opposition."
    save_path: str = "dark_future_save.json"


@dataclass(frozen=True)
class Action:
    id: str
    label: str
    kind: str
    details: str = ""


PHASE_SOURCE = SourceRef(
    "Dark Future Rulebook",
    (9, 11, 12),
    "Speed factor activation from extracted speed phase table.",
)
MOVE_SOURCE = SourceRef(
    "Dark Future Rulebook",
    (10, 12, 13),
    "Straight track movement uses explicit section/space/lane state.",
)
SHOOT_SOURCE = SourceRef(
    "Dark Future Rulebook",
    (25, 27, 28, 29),
    "Rough direct-fire implementation using extracted weapon accuracy and damage procedure.",
)
RAM_SOURCE = SourceRef(
    "Dark Future Rulebook",
    (52, 54, 56, 57),
    "Rough ram classification and speed-factor damage from extracted ram rules.",
)
HAZARD_SOURCE = SourceRef(
    "Dark Future Rulebook",
    (30, 31, 38, 43, 44, 45),
    "Rough hazard/control-loss implementation using extracted safety-limit concepts.",
)
CAMPAIGN_SOURCE = SourceRef(
    "White Dwarf 124/125 Dead Man's Curve",
    (18, 19, 20, 68, 69, 70),
    "Rough campaign settlement loop for agency/gang persistence.",
)
CURVE_SOURCE = SourceRef(
    "Dark Future Rulebook",
    (10, 13, 74, 78),
    "Provisional curve section placeholder; exact curve atlas still needs trace.",
)
MANOEUVRE_SOURCE = SourceRef(
    "Dark Future Rulebook",
    (13, 14, 15),
    "Manoeuvres are declared before movement; drifts happen after the forward move, and U-turns use speed bands plus curve-edge restrictions.",
)


DEFAULT_WEAPONS = {
    "interceptor": ("15mm Autocannon", 1, 3),
    "renegade": ("6mm MG", 2, 1),
    "bike": ("4.2mm MG", 2, 1),
}

ROCKET_BOOSTER_SOURCE = SourceRef(
    "White Line Fever",
    (22,),
    "Rocket boosters use pulse/cruise modes, passive-space restrictions, shot ratings, and the WLF p.22 pulse table.",
)

ROCKET_BOOSTER_PULSE_ROWS = (
    (0, 800, 60, 210, 80, 240),
    (801, 1000, 50, 200, 70, 230),
    (1001, 1200, 45, 190, 65, 225),
    (1201, 1400, 40, 180, 60, 220),
    (1401, 1600, 36, 170, 55, 210),
    (1601, 1800, 32, 160, 50, 200),
    (1801, 2000, 30, 150, 45, 190),
    (2001, 2200, 26, 140, 40, 180),
    (2201, 2400, 24, 130, 36, 170),
    (2401, 2600, 22, 125, 32, 160),
    (2601, 2800, 20, 120, 30, 155),
    (2801, 3000, 18, 115, 28, 150),
    (3001, 3200, 16, 110, 24, 145),
    (3201, 3400, 14, 100, 20, 140),
)

SCENARIOS = {
    "intercept": {
        "label": "Intercept",
        "objective": "Agency vehicle must exit the far road edge or destroy the outlaw opposition.",
        "reward": 12000,
        "loss": -5000,
    },
    "ambush": {
        "label": "Ambush",
        "objective": "Agency must survive and destroy or outrun the ambushing outlaw.",
        "reward": 15000,
        "loss": -8000,
    },
    "pursuit": {
        "label": "Pursuit",
        "objective": "Agency must catch and disable the fleeing outlaw before it exits.",
        "reward": 18000,
        "loss": -10000,
    },
}
SCENARIO_ORDER = ("intercept", "ambush", "pursuit")


def make_vehicle(
    vehicle_id: str,
    label: str,
    side: Side,
    template_id: str,
    section: int,
    space: int,
    lane_pair: int,
    direction: Direction,
    mph: int,
) -> Vehicle:
    template = vehicle_template(template_id)
    stats = template["coreStats"]
    weapon_label, weapon_accuracy, weapon_damage_modifier = DEFAULT_WEAPONS.get(
        template_id, ("6mm MG", 2, 1)
    )
    vehicle = Vehicle(
        id=vehicle_id,
        label=label,
        side=side,
        template_id=template_id,
        section=section,
        space=space,
        lane_pair=lane_pair,
        direction=direction,
        mph=mph,
        max_mph=stats["maximumSpeedMph"],
        acceleration_mph=stats["accelerationMph"],
        braking_mph=stats["brakingMph"],
        handling=stats["handling"],
        damage=stats["damage"],
        armour=stats["armour"],
        weapon_label=weapon_label,
        weapon_accuracy=weapon_accuracy,
        weapon_damage_modifier=weapon_damage_modifier,
    )
    if template_id == "interceptor":
        vehicle.rocket_booster_type = "twin"
        vehicle.rocket_booster_shots = 36
    elif template_id == "renegade":
        vehicle.rocket_booster_type = "single"
        vehicle.rocket_booster_shots = 24
    return vehicle


def new_game(scenario_id: str = "intercept", campaign: CampaignState | None = None) -> GameState:
    scenario_id = scenario_id if scenario_id in SCENARIOS else "intercept"
    track_types = provisional_track_layout()
    agency_section, agency_space, agency_lane, agency_mph = 1, 1, 4, 60
    outlaw_section, outlaw_space, outlaw_lane, outlaw_direction, outlaw_mph = 6, 3, 4, -1, 40
    if scenario_id == "ambush":
        agency_section, agency_space, agency_lane, agency_mph = 2, 1, 4, 50
        outlaw_section, outlaw_space, outlaw_lane, outlaw_direction, outlaw_mph = 3, 2, 3, -1, 60
    elif scenario_id == "pursuit":
        agency_section, agency_space, agency_lane, agency_mph = 1, 1, 4, 70
        outlaw_section, outlaw_space, outlaw_lane, outlaw_direction, outlaw_mph = 4, 2, 4, 1, 50
    state = GameState(
        turn=1,
        phase=1,
        track_sections=len(track_types),
        vehicles=[
            make_vehicle("agency-1", "Interceptor", "agency", "interceptor", agency_section, agency_space, agency_lane, 1, agency_mph),
            make_vehicle("outlaw-1", "Renegade", "outlaw", "renegade", outlaw_section, outlaw_space, outlaw_lane, outlaw_direction, outlaw_mph),
        ],
        track_section_types=track_types,
        passive_markers=[],
        active_vehicle_id=None,
        campaign=campaign or CampaignState(current_scenario=scenario_id, objective=SCENARIOS[scenario_id]["objective"]),
        logs=[
            LogEntry(
                f"{SCENARIOS[scenario_id]['label']} contract begins. {SCENARIOS[scenario_id]['objective']}",
                "setup",
                CAMPAIGN_SOURCE,
            )
        ],
        scenario_id=scenario_id,
        objective=SCENARIOS[scenario_id]["objective"],
    )
    state.campaign.current_scenario = scenario_id
    state.campaign.objective = state.objective
    start_phase(state)
    return state


def provisional_track_layout() -> list[str]:
    inventory = track_inventory()["visibleInventory"]
    straight_count = int(inventory["straight"]["count"])
    curve_count = int(inventory["curvesTotal"]["count"])
    layout = ["straight", "straight", "straight"]
    if curve_count >= 1:
        layout.extend(["curve50to80_left", "straight"])
    if curve_count >= 2:
        layout.extend(["curve30to60_right", "straight"])
    return layout[: min(7, straight_count + curve_count)]


def generate_track_layout(state: GameState) -> None:
    inventory = TrackInventory.from_rule_inventory(track_inventory())
    track = build_initial_track(state.dice, inventory=inventory, target_sections=7)
    if not track.sections:
        state.logs.append(LogEntry("Track generation failed: no sections available.", "track", CURVE_SOURCE))
        return
    state.track_section_types = track.piece_types
    state.track_sections = len(track.piece_types)
    for vehicle in state.vehicles:
        vehicle.section = min(max(vehicle.section, 0), state.track_sections - 1)
        vehicle.space = min(vehicle.space, lane_pair_section_count(state.track_section_types[vehicle.section], vehicle.lane_pair))
    state.logs.append(LogEntry(f"Generated track: {', '.join(state.track_section_types)}.", "track", CURVE_SOURCE))


def speed_factor(mph: int) -> int:
    if mph <= 0:
        return 0
    return ceil(mph / 20)


def phase_moves(mph: int, phase: int) -> int:
    factor = speed_factor(mph)
    if factor == 0:
        return 0
    for row in speed_phase_rows():
        if row["speedFactor"] == factor:
            return int(row["phaseMoves"][phase - 1])
    return 1 if phase <= min(factor, 6) else 0


def vehicle_acts_in_phase(vehicle: Vehicle, phase: int) -> bool:
    if vehicle.mph <= 0:
        return phase == 1
    return phase_moves(vehicle.mph, phase) > 0


def vehicle_by_id(state: GameState, vehicle_id: str) -> Vehicle:
    for vehicle in state.vehicles:
        if vehicle.id == vehicle_id:
            return vehicle
    raise KeyError(vehicle_id)


def active_vehicle(state: GameState) -> Vehicle | None:
    if state.active_vehicle_id is None:
        return None
    return vehicle_by_id(state, state.active_vehicle_id)


def start_phase(state: GameState) -> None:
    for vehicle in state.vehicles:
        vehicle.acted_this_phase = False
        vehicle.action_cancelled_this_phase = False
    state.logs.append(LogEntry(f"Turn {state.turn}, phase {state.phase} starts.", "phase", PHASE_SOURCE))
    choose_next_actor(state)


def choose_next_actor(state: GameState) -> None:
    eligible = [
        vehicle
        for vehicle in state.vehicles
        if not vehicle.destroyed
        and not vehicle.acted_this_phase
        and vehicle_acts_in_phase(vehicle, state.phase)
    ]
    if not eligible:
        state.active_vehicle_id = None
        return
    eligible.sort(key=lambda vehicle: (-vehicle.mph, vehicle.section * -vehicle.direction))
    state.active_vehicle_id = eligible[0].id
    state.logs.append(
        LogEntry(
            f"{eligible[0].label} is active at {eligible[0].mph} mph.",
            "activation",
            PHASE_SOURCE,
        )
    )


def advance_phase(state: GameState) -> None:
    for vehicle in state.vehicles:
        apply_rocket_booster_phase_update(state, vehicle)
    if state.phase >= 6:
        state.phase = 1
        state.turn += 1
        state.logs.append(LogEntry(f"Turn {state.turn - 1} ends.", "turn", PHASE_SOURCE))
    else:
        state.phase += 1
    start_phase(state)


def rocket_booster_pulse_values(vehicle: Vehicle) -> tuple[int, int]:
    if vehicle.rocket_booster_type not in {"single", "twin"}:
        raise ValueError("vehicle has no rocket boosters")
    total_weight = 1000
    if vehicle.template_id == "interceptor":
        total_weight += 225
    elif vehicle.template_id == "renegade":
        total_weight += 150
    for min_weight, max_weight, single_acc, single_max, twin_acc, twin_max in ROCKET_BOOSTER_PULSE_ROWS:
        if min_weight <= total_weight <= max_weight:
            if vehicle.rocket_booster_type == "single":
                return single_acc, single_max
            return twin_acc, twin_max
    raise ValueError(f"no rocket booster pulse row for weight {total_weight}")


def apply_rocket_booster_phase_update(state: GameState, vehicle: Vehicle) -> None:
    if vehicle.destroyed:
        return
    if vehicle.rocket_booster_mode == "cruise":
        if vehicle.rocket_booster_shots <= 0:
            vehicle.rocket_booster_mode = None
            vehicle.rocket_booster_cruise_mph = None
            state.logs.append(LogEntry(f"{vehicle.label}'s rocket boosters cut out: no shots remain.", "rocket", ROCKET_BOOSTER_SOURCE))
            return
        vehicle.mph = vehicle.rocket_booster_cruise_mph or vehicle.mph
        vehicle.rocket_booster_shots -= 1
        state.logs.append(LogEntry(f"{vehicle.label}'s rocket boosters cruise at {vehicle.mph} mph ({vehicle.rocket_booster_shots} shots left).", "rocket", ROCKET_BOOSTER_SOURCE))
    elif vehicle.mph > vehicle.max_mph:
        old = vehicle.mph
        vehicle.mph = max(vehicle.max_mph, vehicle.mph - 5)
        if vehicle.mph != old:
            state.logs.append(LogEntry(f"{vehicle.label} decelerates toward normal maximum: {old} -> {vehicle.mph} mph.", "rocket", ROCKET_BOOSTER_SOURCE))


def legal_actions(state: GameState, vehicle: Vehicle | None = None) -> list[Action]:
    actor = vehicle or active_vehicle(state)
    if state.game_over:
        actions = []
        if state.campaign.settlement_pending:
            actions.append(Action("settle_campaign", "Settle Campaign", "campaign", "Apply reward, repair bill, and contract result."))
        actions.append(Action("new_contract", "New Contract", "campaign", "Start another tactical engagement."))
        actions.extend(_campaign_management_actions())
        return actions
    if state.mode == "campaign":
        return _campaign_management_actions()
    if actor is None:
        return [Action("next_phase", "Next Phase", "phase", "Advance to the next phase."), *_system_state_actions()]
    if actor.control_state != "controlled":
        return [
            Action("regain_control", "Regain Control", "hazard", "Roll to recover control."),
            Action("wait", "Hold", "action", "Skip this activation."),
        ]
    if actor.mph <= 0:
        actions = [
            Action("accelerate", "Move Off", "speed", f"Move one space and accelerate up to +{min(20, actor.acceleration_mph)} mph."),
            Action("shoot", "Shoot", "shoot", f"Fire {actor.weapon_label} while stationary."),
            Action("drop_smoke", "Drop Smoke", "passive", "Place smoke behind the stationary vehicle."),
            Action("wait", "Hold", "action", "Skip this activation."),
        ]
        if actor.weapon_disabled:
            actions = [action for action in actions if action.id != "shoot"]
        return actions
    actions = [
        Action("steady", "Steady Forward", "move", "Move one space forward."),
        Action("shoot", "Shoot", "shoot", f"Fire {actor.weapon_label} at a target ahead."),
        Action("drop_oil", "Drop Oil", "passive", "Place oil behind the vehicle."),
        Action("drop_smoke", "Drop Smoke", "passive", "Place smoke behind the vehicle."),
        Action("wait", "Hold", "action", "Skip this activation."),
    ]
    if actor.rocket_booster_mode == "cruise":
        actions.insert(1, Action("rocket_off", "Boosters Off", "rocket", "Switch rocket boosters off after moving."))
    else:
        actions.insert(1, Action("accelerate", "Accelerate", "speed", f"+{min(20, actor.acceleration_mph)} mph after moving."))
        actions.insert(2, Action("brake", "Brake", "speed", f"-{min(20, actor.braking_mph)} mph after moving."))
    if actor.rocket_booster_type and not actor.rocket_booster_disabled and actor.rocket_booster_shots > 0:
        actions.insert(3, Action("rocket_pulse", "Rocket Pulse", "rocket", "Move, then spend 2 shots for one WLF booster pulse."))
        if actor.mph >= 120:
            actions.insert(4, Action("rocket_cruise", "Rocket Cruise", "rocket", "Move, then lock boosters to maintain current speed."))
    next_position = _forward_position_in_state(state, actor)
    if next_position is not None:
        for action_id, label in (("drift_left", "Drift Left"), ("drift_right", "Drift Right")):
            _, blocked_reason = _legal_drift_lane_pair(state, actor, action_id, next_position[0])
            if blocked_reason is None:
                actions.insert(3, Action(action_id, label, "move", "Move forward, then shift one lane pair."))
    if _can_offer_u_turn(state, actor):
        actions.insert(5, Action("u_turn", "U-Turn", "move", "Turn through 180 degrees using the U-turn speed bands."))
    if actor.weapon_disabled:
        actions = [action for action in actions if action.id != "shoot"]
    return actions


def _campaign_management_actions() -> list[Action]:
    return [
        Action("generate_track", "Generate Track", "track", "Roll a fresh connected track layout."),
        Action("recruit_driver", "Recruit Driver", "campaign", "Hire a novice for $5,000."),
        Action("repair_agency", "Repair Agency", "campaign", "Spend funds to repair the agency vehicle."),
        Action("cycle_scenario", "Cycle Scenario", "campaign", "Switch the next contract type."),
        *_system_state_actions(),
    ]


def _system_state_actions() -> list[Action]:
    return [
        Action("save_game", "Save", "system", "Write campaign and tactical state to disk."),
        Action("load_game", "Load", "system", "Load the saved campaign and tactical state."),
    ]


def _forward_position(vehicle: Vehicle) -> tuple[int, int]:
    layout = provisional_track_layout()
    result = track_forward_position(
        layout,
        vehicle.section,
        vehicle.space,
        vehicle.lane_pair,
        vehicle.direction,
    )
    if result is None:
        return vehicle.section + vehicle.direction, 1
    return result


def _forward_position_in_state(state: GameState, vehicle: Vehicle) -> tuple[int, int] | None:
    return track_forward_position(
        state.track_section_types,
        vehicle.section,
        vehicle.space,
        vehicle.lane_pair,
        vehicle.direction,
    )


def _overlap(a: Vehicle, section: int, space: int, lane_pair: int, other: Vehicle) -> bool:
    if other.id == a.id:
        return False
    if other.destroyed:
        return False
    if other.section != section or other.space != space:
        return False
    lanes = {lane_pair, lane_pair + 1}
    return bool(lanes.intersection(other.lane_rows))


def _finish_activation(state: GameState, vehicle: Vehicle) -> None:
    vehicle.acted_this_phase = True
    check_victory(state)
    if state.game_over:
        state.active_vehicle_id = None
        return
    choose_next_actor(state)


def current_section_type(state: GameState, vehicle: Vehicle) -> str:
    if 0 <= vehicle.section < len(state.track_section_types):
        return state.track_section_types[vehicle.section]
    return "offroad"


def _section_type_at(state: GameState, section: int) -> str:
    if 0 <= section < len(state.track_section_types):
        return state.track_section_types[section]
    return "offroad"


def _is_curve_section(section_type: str) -> bool:
    return section_type.startswith("curve")


def _is_straight_section(section_type: str) -> bool:
    return section_type == "straight"


def section_space_limit(section: int, lane_pair: int, state: GameState | None = None) -> int:
    section_type = "straight"
    if state is not None and 0 <= section < len(state.track_section_types):
        section_type = state.track_section_types[section]
    elif 0 <= section < len(provisional_track_layout()):
        section_type = provisional_track_layout()[section]
    return lane_pair_section_count(section_type, lane_pair)


def section_space_limit_for_vehicle(vehicle: Vehicle, state: GameState | None = None) -> int:
    return section_space_limit(vehicle.section, vehicle.lane_pair, state)


def curve_safety_limit(state: GameState, vehicle: Vehicle) -> int | None:
    section_type = current_section_type(state, vehicle)
    return lane_pair_safety_limit(section_type, vehicle.lane_pair)


def _drift_direction_for_action(action_id: str) -> str:
    if action_id == "drift_left":
        return "left"
    if action_id == "drift_right":
        return "right"
    raise ValueError(f"not a drift action: {action_id}")


def _legal_drift_lane_pair(
    state: GameState,
    vehicle: Vehicle,
    action_id: str,
    forward_section: int,
) -> tuple[int | None, str | None]:
    current_piece = current_section_type(state, vehicle)
    forward_piece = _section_type_at(state, forward_section)
    drift_direction = _drift_direction_for_action(action_id)

    if _is_curve_section(current_piece) and not _is_straight_section(forward_piece):
        curve_direction = "outward" if drift_direction == "right" else "inward"
        if curve_direction == "inward":
            return None, "Core rules allow voluntary curve drifts only outward unless the forward move enters a straight."
        target = drift_lane_pair(current_piece, vehicle.lane_pair, "outward")
    else:
        target = drift_lane_pair(current_piece if _is_straight_section(current_piece) else "straight", vehicle.lane_pair, drift_direction)

    if target is None:
        return None, "Drift contact zone reaches the road edge."
    return target, None


def _u_turn_geometry_status(state: GameState, vehicle: Vehicle) -> tuple[bool, str | None]:
    section_type = current_section_type(state, vehicle)
    adjacent_types = {
        _section_type_at(state, vehicle.section - 1),
        _section_type_at(state, vehicle.section + 1),
    }
    if _is_curve_section(section_type):
        if vehicle.lane_pair in {MIN_LANE_PAIR, MAX_LANE_PAIR} and "straight" in adjacent_types:
            return False, "Curve-edge U-turn needs traced six-lane contact-zone geometry before it can be resolved."
        return False, "U-turns are prohibited on ordinary curved track spaces."
    if _is_straight_section(section_type) and any(_is_curve_section(piece) for piece in adjacent_types):
        return False, "Straight-next-to-curve U-turn needs traced six-lane contact-zone geometry before it can be resolved."
    return True, None


def _u_turn_contact_zone_clear(state: GameState, vehicle: Vehicle) -> tuple[bool, str | None]:
    for other in state.vehicles:
        if other.id == vehicle.id or other.destroyed:
            continue
        if other.section == vehicle.section and other.space == vehicle.space and set(vehicle.lane_rows).intersection(other.lane_rows):
            return False, "U-turn contact zone overlaps another vehicle."
        if other.section == vehicle.section and abs(other.space - vehicle.space) <= 1:
            return False, "U-turn six-lane contact zone needs traced diagram geometry to judge nearby vehicles."
    return True, None


def _can_offer_u_turn(state: GameState, vehicle: Vehicle) -> bool:
    geometry_ok, _ = _u_turn_geometry_status(state, vehicle)
    if not geometry_ok:
        return False
    contact_ok, _ = _u_turn_contact_zone_clear(state, vehicle)
    return contact_ok


def take_hazard_test(state: GameState, vehicle: Vehicle, safety_limit_mph: int, reason: str) -> bool:
    if vehicle.destroyed:
        return True
    roll = state.dice.d6()
    result = resolve_hazard_test(
        roll=roll,
        mph=vehicle.mph,
        safety_limit_mph=safety_limit_mph,
        handling=vehicle.handling + vehicle.hazard_mod,
        drive_skill=vehicle.driver_skill,
        controlled=vehicle.control_state == "controlled",
    )
    if result.skipped:
        return True
    state.logs.append(
        LogEntry(
            f"{vehicle.label} hazard test for {reason}: table total {result.total} gives {result.effect}.",
            "hazard",
            HAZARD_SOURCE,
        )
    )
    if result.speed_loss_mph:
        vehicle.mph = max(0, vehicle.mph - result.speed_loss_mph)
        vehicle.action_cancelled_this_phase = True
        state.logs.append(
            LogEntry(
                f"{vehicle.label} panic brakes to {vehicle.mph} mph.",
                "hazard",
                HAZARD_SOURCE,
            )
        )
    if result.control_lost:
        vehicle.control_state = "out_of_control"
        vehicle.action_cancelled_this_phase = True
        state.logs.append(
            LogEntry(
                f"{vehicle.label} loses control.",
                "control-loss",
                HAZARD_SOURCE,
            )
        )
    return not result.control_lost


def check_movement_hazards(
    state: GameState,
    vehicle: Vehicle,
    action_id: str,
    *,
    old_section: int | None = None,
    old_lane_pair: int | None = None,
) -> None:
    curve_hazards: list[tuple[int, str]] = []
    old_position_changed = old_section != vehicle.section or old_lane_pair != vehicle.lane_pair
    if old_position_changed and old_section is not None and old_lane_pair is not None and 0 <= old_section < state.track_sections:
        old_limit = lane_pair_safety_limit(state.track_section_types[old_section], old_lane_pair)
        if old_limit is not None:
            curve_hazards.append((old_limit, f"exiting curve safety limit {old_limit} mph"))
    safety_limit = curve_safety_limit(state, vehicle)
    if safety_limit is not None:
        curve_hazards.append((safety_limit, f"curve safety limit {safety_limit} mph"))
    seen_curve_hazards: set[tuple[int, str]] = set()
    for limit, reason in sorted(curve_hazards, reverse=True):
        key = (limit, reason)
        if key in seen_curve_hazards:
            continue
        seen_curve_hazards.add(key)
        take_hazard_test(state, vehicle, limit, reason)
    if action_id.startswith("drift") and vehicle.mph > 80:
        take_hazard_test(state, vehicle, 80, "drift over 80 mph")
    hit_markers = [
        marker
        for marker in state.passive_markers
        if marker.section == vehicle.section
        and marker.space == vehicle.space
        and bool(set((marker.lane_pair, marker.lane_pair + 1)).intersection(vehicle.lane_rows))
    ]
    for marker in hit_markers:
        resolve_marker_hit(state, vehicle, marker)


def check_passive_markers_on_exit(
    state: GameState,
    vehicle: Vehicle,
    old_section: int,
    old_space: int,
    old_lane_pair: int,
) -> None:
    old_lanes = {old_lane_pair, old_lane_pair + 1}
    hit_markers = [
        marker
        for marker in state.passive_markers
        if marker.trigger_on_exit_vehicle_id == vehicle.id
        and marker.section == old_section
        and marker.space == old_space
        and bool({marker.lane_pair, marker.lane_pair + 1}.intersection(old_lanes))
    ]
    for marker in hit_markers:
        resolve_marker_hit(state, vehicle, marker)


def resolve_marker_hit(state: GameState, vehicle: Vehicle, marker: PassiveMarker) -> None:
    state.logs.append(LogEntry(f"{vehicle.label} hits {marker.kind}.", "passive", HAZARD_SOURCE))
    if marker.kind == "oil":
        vehicle.hazard_mod -= 1
        take_hazard_test(state, vehicle, 30, "oil")
    elif marker.kind == "smoke":
        take_hazard_test(state, vehicle, 60, "smoke")
    elif marker.kind == "spikes":
        if vehicle.mph > 20 and state.dice.d6() == 6:
            apply_critical_hit(state, vehicle, HAZARD_SOURCE, "spikes")
    elif marker.kind == "mines":
        apply_damage(state, vehicle, state.dice.d6(), 3, HAZARD_SOURCE, "pattern mine")
        if vehicle.mph > 50:
            take_hazard_test(state, vehicle, 50, "mine blast")
    state.passive_markers.remove(marker)


def marker_position_behind(state: GameState, vehicle: Vehicle) -> tuple[int, int]:
    section = vehicle.section
    space = vehicle.space - vehicle.direction
    if space > section_space_limit(section, vehicle.lane_pair, state):
        section += 1
        space = 1
    elif space < 1:
        section -= 1
        space = section_space_limit(section, vehicle.lane_pair, state)
    return section, space


def drop_marker(state: GameState, vehicle: Vehicle, kind: MarkerKind) -> None:
    section, space = marker_position_behind(state, vehicle)
    if section < 0 or section >= state.track_sections:
        state.logs.append(LogEntry(f"{vehicle.label} cannot drop {kind}; rear space is off road.", "passive"))
        _finish_activation(state, vehicle)
        return
    trigger_vehicle = next(
        (
            other
            for other in state.vehicles
            if _overlap(vehicle, section, space, vehicle.lane_pair, other)
        ),
        None,
    )
    marker = PassiveMarker(
        id=f"marker-{state.next_marker_id}",
        kind=kind,
        section=section,
        space=space,
        lane_pair=vehicle.lane_pair,
        owner_side=vehicle.side,
        trigger_on_exit_vehicle_id=trigger_vehicle.id if trigger_vehicle is not None else None,
    )
    state.next_marker_id += 1
    state.passive_markers.append(marker)
    tailgater = f" under {trigger_vehicle.label}" if trigger_vehicle is not None else ""
    state.logs.append(LogEntry(f"{vehicle.label} drops {kind} at section {section + 1}, space {space}, LP{vehicle.lane_pair}{tailgater}.", "passive"))
    _finish_activation(state, vehicle)


def apply_rocket_booster_action(state: GameState, vehicle: Vehicle, action_id: str) -> None:
    if action_id == "rocket_off":
        vehicle.rocket_booster_mode = None
        vehicle.rocket_booster_cruise_mph = None
        state.logs.append(LogEntry(f"{vehicle.label} switches rocket boosters off.", "rocket", ROCKET_BOOSTER_SOURCE))
        return
    if not vehicle.rocket_booster_type:
        state.logs.append(LogEntry(f"{vehicle.label} has no rocket boosters.", "illegal-action", ROCKET_BOOSTER_SOURCE))
        return
    if vehicle.rocket_booster_disabled:
        state.logs.append(LogEntry(f"{vehicle.label}'s rocket boosters are disabled.", "illegal-action", ROCKET_BOOSTER_SOURCE))
        return
    if action_id == "rocket_cruise":
        if vehicle.mph < 120:
            state.logs.append(LogEntry(f"{vehicle.label} cannot set rocket cruise below 120 mph.", "illegal-action", ROCKET_BOOSTER_SOURCE))
            return
        if vehicle.rocket_booster_shots < 1:
            state.logs.append(LogEntry(f"{vehicle.label} has no rocket booster shots left.", "illegal-action", ROCKET_BOOSTER_SOURCE))
            return
        vehicle.rocket_booster_mode = "cruise"
        vehicle.rocket_booster_cruise_mph = vehicle.mph
        vehicle.rocket_booster_shots -= 1
        state.logs.append(LogEntry(f"{vehicle.label} locks rocket boosters in cruise at {vehicle.mph} mph ({vehicle.rocket_booster_shots} shots left).", "rocket", ROCKET_BOOSTER_SOURCE))
        return
    if action_id == "rocket_pulse":
        if vehicle.rocket_booster_shots < 2:
            state.logs.append(LogEntry(f"{vehicle.label} needs 2 rocket booster shots for a pulse.", "illegal-action", ROCKET_BOOSTER_SOURCE))
            return
        acc, max_mph = rocket_booster_pulse_values(vehicle)
        old = vehicle.mph
        vehicle.mph = min(max_mph, vehicle.mph + acc)
        vehicle.rocket_booster_mode = "pulse"
        vehicle.rocket_booster_cruise_mph = None
        vehicle.rocket_booster_shots -= 2
        state.logs.append(LogEntry(f"{vehicle.label} rocket pulse: {old} -> {vehicle.mph} mph, pulse max {max_mph} ({vehicle.rocket_booster_shots} shots left).", "rocket", ROCKET_BOOSTER_SOURCE))


def apply_rocket_booster_critical(
    state: GameState,
    vehicle: Vehicle,
    *,
    explodes: bool,
) -> None:
    if not vehicle.rocket_booster_type or vehicle.rocket_booster_disabled:
        state.logs.append(LogEntry(f"Rocket booster critical on {vehicle.label} is wasted.", "critical", ROCKET_BOOSTER_SOURCE))
        return
    vehicle.rocket_booster_disabled = True
    vehicle.rocket_booster_mode = None
    vehicle.rocket_booster_cruise_mph = None
    vehicle.critical_notes.append("rocket boosters disabled")
    if vehicle.rocket_booster_type == "twin":
        state.logs.append(LogEntry(f"{vehicle.label}'s linked twin rocket boosters are disabled as a pair.", "critical", ROCKET_BOOSTER_SOURCE))
    else:
        state.logs.append(LogEntry(f"{vehicle.label}'s rocket booster is disabled.", "critical", ROCKET_BOOSTER_SOURCE))
    if explodes:
        apply_damage(state, vehicle, state.dice.d6(), 8, ROCKET_BOOSTER_SOURCE, "rocket booster explosion")
        take_hazard_test(state, vehicle, 30, "rocket booster explosion")


def critical_table_for_roll(roll: int) -> str:
    if roll <= 1:
        return "driver"
    if roll <= 3:
        return "engine"
    if roll == 4:
        return "wheels"
    if roll == 5:
        return "bodywork"
    return "weapons"


def apply_critical_effect(state: GameState, target: Vehicle, effect) -> None:
    kind = effect.get("kind") if hasattr(effect, "get") else None
    if kind == "driveSkillDelta":
        target.driver_skill = max(0, target.driver_skill + int(effect["value"]))
    elif kind == "setDriveSkill":
        target.driver_skill = max(0, int(effect["value"]))
    elif kind == "handlingDelta":
        target.handling += int(effect["value"])
    elif kind == "setHandling":
        target.handling = int(effect["value"])
    elif kind == "setAccelerationMph":
        target.acceleration_mph = max(0, int(effect["value"]))
    elif kind == "setBrakingMph":
        target.braking_mph = max(0, int(effect["value"]))
    elif kind == "halveCurrentAcceleration":
        target.acceleration_mph = max(0, target.acceleration_mph // 2)
    elif kind == "halveCurrentBraking":
        target.braking_mph = max(0, target.braking_mph // 2)
    elif kind == "maxMphBecomesLowerOf":
        target.max_mph = min(target.max_mph - 10, 60)
        target.mph = min(target.mph, target.max_mph)
    elif kind == "engineDisabled":
        target.acceleration_mph = 0
        target.max_mph = min(target.max_mph, target.mph)
    elif kind in {"selectedWeaponOutOfAction", "weaponCannotBeOperated", "weaponDestroyed"}:
        target.weapon_disabled = True
    elif kind == "weaponAccuracyDelta":
        target.weapon_accuracy += int(effect["value"])
    elif kind == "automaticControlLoss":
        target.control_state = "out_of_control"
    elif kind == "hazardEvent":
        safety = int(effect.get("safetyLimitMph", effect.get("ifMphGreaterThan", 0)) or 0)
        if safety:
            take_hazard_test(state, target, safety, "critical hazard")


def apply_critical_hit(state: GameState, target: Vehicle, source: SourceRef, reason: str) -> None:
    table_roll = state.dice.d6()
    result_roll = state.dice.d6()
    table_id = critical_table_for_roll(table_roll)
    result = critical_result(table_id, result_roll)
    for effect in result.effects:
        apply_critical_effect(state, target, effect)
    if result.confirmation_roll is not None:
        confirmation_total = state.dice.d6() + max(0, target.weapon_damage_modifier)
        success_if = int(result.confirmation_roll.get("successIfGte", 99))
        success_effect = result.confirmation_roll.get("successEffect")
        if confirmation_total >= success_if:
            if isinstance(success_effect, dict):
                apply_critical_effect(state, target, success_effect)
            elif success_effect == "engineDisabled":
                target.acceleration_mph = 0
            elif success_effect == "brokenAxle":
                target.handling -= 2
                target.acceleration_mph = 0
    note = f"{table_id}: {result.result_id}"
    target.critical_notes.append(note)
    state.logs.append(LogEntry(f"{reason} critical on {target.label}: {note}.", "critical", source))


def _section_start_distance(state: GameState, section: int) -> int:
    return sum(piece_max_spaces(piece) for piece in state.track_section_types[:section])


def _track_distance_position(state: GameState, section: int, space: int) -> int:
    return _section_start_distance(state, section) + space


def _vehicle_distance_position(state: GameState, vehicle: Vehicle) -> int:
    return _track_distance_position(state, vehicle.section, vehicle.space)


def _distance_spaces(state: GameState, a: Vehicle, b: Vehicle) -> int:
    return abs(_vehicle_distance_position(state, a) - _vehicle_distance_position(state, b))


def _lane_overlap(a: Vehicle, b: Vehicle) -> bool:
    return bool(set(a.lane_rows).intersection(b.lane_rows))


def _ahead_of(state: GameState, shooter: Vehicle, target: Vehicle) -> bool:
    shooter_pos = _vehicle_distance_position(state, shooter)
    target_pos = _vehicle_distance_position(state, target)
    return (target_pos - shooter_pos) * shooter.direction > 0


def _line_of_fire_blocked(state: GameState, shooter: Vehicle, target: Vehicle) -> bool:
    shooter_pos = _vehicle_distance_position(state, shooter)
    target_pos = _vehicle_distance_position(state, target)
    low, high = sorted((shooter_pos, target_pos))
    for other in state.vehicles:
        if other.id in {shooter.id, target.id} or other.destroyed:
            continue
        other_pos = _vehicle_distance_position(state, other)
        if low < other_pos < high and _lane_overlap(shooter, other):
            return True
    for marker in state.passive_markers:
        marker_pos = _track_distance_position(state, marker.section, marker.space)
        if marker.kind == "smoke" and low < marker_pos < high:
            marker_lanes = {marker.lane_pair, marker.lane_pair + 1}
            if marker_lanes.intersection(shooter.lane_rows):
                return True
    return False


def shoot_targets(state: GameState, shooter: Vehicle) -> list[Vehicle]:
    return [
        target
        for target in state.vehicles
        if target.side != shooter.side
        and not target.destroyed
        and abs(target.lane_pair - shooter.lane_pair) <= 1
        and _ahead_of(state, shooter, target)
        and _distance_spaces(state, shooter, target) <= 8
        and not _line_of_fire_blocked(state, shooter, target)
    ]


def _objective_target(state: GameState, vehicle: Vehicle) -> Vehicle | None:
    enemies = [target for target in state.vehicles if target.side != vehicle.side and not target.destroyed]
    if not enemies:
        return None
    if state.scenario_id == "pursuit" and vehicle.side == "outlaw":
        return None
    return min(enemies, key=lambda target: _distance_spaces(state, vehicle, target))


def _lane_pair_hits_marker(
    state: GameState,
    section: int,
    space: int,
    lane_pair: int,
    kind: MarkerKind | None = None,
) -> bool:
    lanes = {lane_pair, lane_pair + 1}
    return any(
        marker.section == section
        and marker.space == space
        and (kind is None or marker.kind == kind)
        and bool(lanes.intersection({marker.lane_pair, marker.lane_pair + 1}))
        for marker in state.passive_markers
    )


def _drift_action_toward_lane(state: GameState, vehicle: Vehicle, target_lane_pair: int) -> str | None:
    if vehicle.lane_pair == target_lane_pair:
        return None
    next_position = _forward_position_in_state(state, vehicle)
    if next_position is None:
        return None
    section, space = next_position
    if vehicle.lane_pair > target_lane_pair:
        action_id = "drift_left"
        target_pair = vehicle.lane_pair - 1
    else:
        action_id = "drift_right"
        target_pair = vehicle.lane_pair + 1
    legal_target, blocked_reason = _legal_drift_lane_pair(state, vehicle, action_id, section)
    if blocked_reason is not None or legal_target is None:
        return None
    if legal_target != target_pair:
        return None
    if _lane_pair_hits_marker(state, section, space, target_pair):
        return None
    return action_id


def _curve_limit_after_forward(state: GameState, vehicle: Vehicle) -> int | None:
    next_position = _forward_position_in_state(state, vehicle)
    if next_position is None:
        return None
    next_section, _ = next_position
    if next_section < 0 or next_section >= state.track_sections:
        return None
    return lane_pair_safety_limit(state.track_section_types[next_section], vehicle.lane_pair)


def apply_damage(
    state: GameState,
    target: Vehicle,
    damage_roll: int,
    damage_modifier: int,
    source: SourceRef,
    reason: str,
) -> int:
    result = table_resolve_damage(
        template_id=target.template_id,
        current_damage=target.damage,
        die=damage_roll,
        damage_modifier=damage_modifier,
        armour=target.armour,
    )
    damage = result.ordinary_damage
    target.damage = result.remaining_damage
    state.logs.append(
        LogEntry(
            f"{reason}: d6 {damage_roll} + {damage_modifier} - armour {target.armour} = {damage}; {target.label} has {target.damage} damage left.",
            "damage",
            source,
        )
    )
    for penalty in result.increment_penalties:
        target.max_mph = max(20, target.max_mph + penalty.max_mph_delta)
        target.acceleration_mph = max(0, target.acceleration_mph + penalty.acceleration_mph_delta)
        target.handling += penalty.handling_delta
        target.mph = min(target.mph, target.max_mph)
        note = f"damage below {penalty.threshold}"
        target.critical_notes.append(note)
        state.logs.append(
            LogEntry(
                f"{target.label} crosses damage increment {penalty.threshold}: max {target.max_mph}, accel {target.acceleration_mph}, handling {target.handling}.",
                "damage",
                source,
            )
        )
    if result.critical_triggered:
        apply_critical_hit(state, target, source, reason)
    if result.terminal_damage and not target.destroyed:
        target.destroyed = True
        target.mph = 0
        state.logs.append(LogEntry(f"{target.label} is destroyed.", "destroyed", source))
    return damage


def apply_shoot(state: GameState, shooter: Vehicle, *, finish_activation: bool = True) -> None:
    targets = shoot_targets(state, shooter)
    if not targets:
        state.logs.append(LogEntry(f"{shooter.label} has no target in its forward corridor.", "shoot", SHOOT_SOURCE))
        if finish_activation:
            _finish_activation(state, shooter)
        return
    target = min(targets, key=lambda item: _distance_spaces(state, shooter, item))
    hit_roll = state.dice.d6()
    range_penalty = 1 if _distance_spaces(state, shooter, target) > 4 else 0
    total = hit_roll + shooter.weapon_accuracy - range_penalty
    state.logs.append(
        LogEntry(
            f"{shooter.label} fires {shooter.weapon_label} at {target.label}: d6 {hit_roll} + accuracy {shooter.weapon_accuracy} - range {range_penalty} = {total}.",
            "shoot",
            SHOOT_SOURCE,
        )
    )
    if total >= 6:
        apply_damage(
            state,
            target,
            state.dice.d6(),
            shooter.weapon_damage_modifier,
            SHOOT_SOURCE,
            shooter.weapon_label,
        )
    else:
        state.logs.append(LogEntry(f"{shooter.label} misses.", "shoot", SHOOT_SOURCE))
    if finish_activation:
        _finish_activation(state, shooter)


def resolve_ram(state: GameState, rammer: Vehicle, target: Vehicle) -> None:
    rammer_sf = speed_factor(rammer.mph)
    target_sf = speed_factor(target.mph)
    if rammer.direction != target.direction:
        ram_type = "head-on"
        modifier = rammer_sf + target_sf
        rammer.mph = 0
        target.mph = 0
        apply_damage(state, rammer, state.dice.d6(), modifier, RAM_SOURCE, f"{ram_type} ram")
        apply_damage(state, target, state.dice.d6(), modifier, RAM_SOURCE, f"{ram_type} ram")
    else:
        ram_type = "shunt"
        modifier = abs(rammer_sf - target_sf)
        if modifier == 0:
            state.logs.append(LogEntry(f"{rammer.label} shunts {target.label}; equal speed factors cause no damage.", "ram", RAM_SOURCE))
        else:
            apply_damage(state, rammer, state.dice.d6(), modifier, RAM_SOURCE, f"{ram_type} ram")
            apply_damage(state, target, state.dice.d6(), modifier, RAM_SOURCE, f"{ram_type} ram")
        diff = abs(rammer.mph - target.mph)
        change = ceil(diff / 2)
        if rammer.mph >= target.mph:
            rammer.mph -= change
            target.mph += change
        else:
            rammer.mph += change
            target.mph -= change
    state.logs.append(LogEntry(f"{rammer.label} resolves a {ram_type} ram with {target.label}.", "ram", RAM_SOURCE))


def recruit_driver(state: GameState) -> None:
    cost = 5000
    if state.campaign.funds < cost:
        state.logs.append(LogEntry("Recruitment failed: not enough funds.", "campaign", CAMPAIGN_SOURCE))
        return
    state.campaign.funds -= cost
    state.campaign.recruits_hired += 1
    name = f"Novice {state.campaign.recruits_hired}"
    state.campaign.roster.append(name)
    state.logs.append(LogEntry(f"Recruited {name} for ${cost}.", "campaign", CAMPAIGN_SOURCE))


def repair_agency_vehicle(state: GameState) -> None:
    agency_vehicles = [vehicle for vehicle in state.vehicles if vehicle.side == "agency"]
    if not agency_vehicles:
        return
    spent = 0
    for vehicle in agency_vehicles:
        missing = max(0, vehicle_template(vehicle.template_id)["coreStats"]["damage"] - vehicle.damage)
        affordable_points = min(missing, state.campaign.funds // 250)
        if affordable_points <= 0:
            continue
        vehicle.damage += affordable_points
        spent += affordable_points * 250
        state.campaign.funds -= affordable_points * 250
        if vehicle.damage > 0:
            vehicle.destroyed = False
        vehicle.critical_notes.clear()
    state.campaign.repairs_pending = max(0, state.campaign.repairs_pending - spent)
    state.logs.append(LogEntry(f"Repair action spent ${spent}; funds ${state.campaign.funds}.", "campaign", CAMPAIGN_SOURCE))


def cycle_scenario(state: GameState) -> None:
    index = SCENARIO_ORDER.index(state.campaign.current_scenario)
    next_scenario = SCENARIO_ORDER[(index + 1) % len(SCENARIO_ORDER)]
    state.campaign.current_scenario = next_scenario
    state.campaign.objective = SCENARIOS[next_scenario]["objective"]
    state.logs.append(LogEntry(f"Next contract set to {SCENARIOS[next_scenario]['label']}.", "campaign", CAMPAIGN_SOURCE))


def game_state_to_dict(state: GameState) -> dict:
    return {
        "turn": state.turn,
        "phase": state.phase,
        "trackSections": state.track_sections,
        "trackSectionTypes": list(state.track_section_types),
        "vehicles": [asdict(vehicle) for vehicle in state.vehicles],
        "passiveMarkers": [asdict(marker) for marker in state.passive_markers],
        "activeVehicleId": state.active_vehicle_id,
        "campaign": asdict(state.campaign),
        "mode": state.mode,
        "gameOver": state.game_over,
        "winner": state.winner,
        "nextMarkerId": state.next_marker_id,
        "scenarioId": state.scenario_id,
        "objective": state.objective,
        "savePath": state.save_path,
        "logs": [asdict(entry) for entry in state.logs[-80:]],
    }


def game_state_from_dict(data: dict) -> GameState:
    campaign = CampaignState(**data.get("campaign", {}))
    logs = [
        LogEntry(
            message=entry["message"],
            kind=entry.get("kind", "rule"),
            source=SourceRef(**entry["source"]) if entry.get("source") else None,
        )
        for entry in data.get("logs", [])
    ]
    return GameState(
        turn=int(data["turn"]),
        phase=int(data["phase"]),
        track_sections=int(data["trackSections"]),
        vehicles=[Vehicle(**vehicle) for vehicle in data["vehicles"]],
        track_section_types=list(data["trackSectionTypes"]),
        passive_markers=[PassiveMarker(**marker) for marker in data.get("passiveMarkers", [])],
        active_vehicle_id=data.get("activeVehicleId"),
        logs=logs,
        campaign=campaign,
        mode=data.get("mode", "tactical"),
        game_over=bool(data.get("gameOver", False)),
        winner=data.get("winner"),
        next_marker_id=int(data.get("nextMarkerId", 1)),
        scenario_id=data.get("scenarioId", "intercept"),
        objective=data.get("objective", SCENARIOS["intercept"]["objective"]),
        save_path=data.get("savePath", "dark_future_save.json"),
    )


def save_game(state: GameState, path: str | Path | None = None) -> Path:
    save_path = Path(path or state.save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text(json.dumps(game_state_to_dict(state), indent=2), encoding="utf-8")
    state.campaign.last_save_path = str(save_path)
    state.logs.append(LogEntry(f"Saved game to {save_path}.", "system"))
    return save_path


def load_game(path: str | Path = "dark_future_save.json") -> GameState:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    state = game_state_from_dict(data)
    state.logs.append(LogEntry(f"Loaded game from {path}.", "system"))
    return state


def copy_state(target: GameState, source: GameState) -> None:
    target.turn = source.turn
    target.phase = source.phase
    target.track_sections = source.track_sections
    target.vehicles = source.vehicles
    target.track_section_types = source.track_section_types
    target.passive_markers = source.passive_markers
    target.active_vehicle_id = source.active_vehicle_id
    target.logs = source.logs
    target.campaign = source.campaign
    target.mode = source.mode
    target.game_over = source.game_over
    target.winner = source.winner
    target.next_marker_id = source.next_marker_id
    target.scenario_id = source.scenario_id
    target.objective = source.objective
    target.save_path = source.save_path


def apply_action(state: GameState, action_id: str) -> None:
    if action_id == "recruit_driver":
        recruit_driver(state)
        return
    if action_id == "repair_agency":
        repair_agency_vehicle(state)
        return
    if action_id == "cycle_scenario":
        cycle_scenario(state)
        return
    if action_id == "generate_track":
        generate_track_layout(state)
        return
    if action_id == "save_game":
        save_game(state)
        return
    if action_id == "load_game":
        try:
            copy_state(state, load_game(state.save_path))
        except FileNotFoundError:
            state.logs.append(LogEntry("Load failed: no save file exists yet.", "system"))
        return
    if state.game_over and action_id == "settle_campaign":
        settle_campaign(state)
        return
    if state.game_over and action_id == "new_contract":
        start_new_contract(state)
        return
    if state.game_over and action_id != "next_phase":
        return
    if action_id == "next_phase":
        advance_phase(state)
        return

    vehicle = active_vehicle(state)
    if vehicle is None:
        advance_phase(state)
        return
    if action_id == "wait":
        state.logs.append(LogEntry(f"{vehicle.label} holds position.", "action"))
        _finish_activation(state, vehicle)
        return
    if action_id == "regain_control":
        roll = state.dice.d6()
        result = resolve_control_loss_test(
            roll=roll,
            mph=vehicle.mph,
            handling=vehicle.handling,
            drive_skill=vehicle.driver_skill,
        )
        if not result.control_lost:
            vehicle.control_state = "controlled"
            state.logs.append(LogEntry(f"{vehicle.label} regains control: table total {result.total} gives {result.effect}.", "hazard", HAZARD_SOURCE))
        else:
            vehicle.mph = max(0, vehicle.mph - 10)
            state.logs.append(LogEntry(f"{vehicle.label} remains out of control ({result.effect}) and slows to {vehicle.mph} mph.", "control-loss", HAZARD_SOURCE))
        _finish_activation(state, vehicle)
        return
    if action_id == "drop_oil":
        drop_marker(state, vehicle, "oil")
        return
    if action_id == "drop_smoke":
        drop_marker(state, vehicle, "smoke")
        return
    if vehicle.mph <= 0 and action_id == "shoot":
        apply_shoot(state, vehicle)
        return
    if action_id == "u_turn":
        geometry_ok, geometry_reason = _u_turn_geometry_status(state, vehicle)
        if not geometry_ok:
            state.logs.append(LogEntry(f"{vehicle.label} cannot U-turn: {geometry_reason}", "illegal-action", MANOEUVRE_SOURCE))
            _finish_activation(state, vehicle)
            return
        contact_ok, contact_reason = _u_turn_contact_zone_clear(state, vehicle)
        if not contact_ok:
            state.logs.append(LogEntry(f"{vehicle.label} cannot U-turn: {contact_reason}", "illegal-action", MANOEUVRE_SOURCE))
            _finish_activation(state, vehicle)
            return
        if vehicle.mph >= 31:
            roll = state.dice.d6()
            result = resolve_control_loss_test(
                roll=roll,
                mph=vehicle.mph,
                handling=vehicle.handling,
                drive_skill=vehicle.driver_skill,
            )
            vehicle.control_state = "out_of_control" if result.control_lost else "controlled"
            state.logs.append(
                LogEntry(
                    f"{vehicle.label} is too fast for a U-turn at {vehicle.mph} mph; immediate control-loss test total {result.total} gives {result.effect}.",
                    "control-loss",
                    MANOEUVRE_SOURCE,
                )
            )
            _finish_activation(state, vehicle)
            return
        old_direction = vehicle.direction
        vehicle.direction = -vehicle.direction
        state.logs.append(
            LogEntry(
                f"{vehicle.label} completes a U-turn and reverses facing from {old_direction} to {vehicle.direction}.",
                "move",
                MANOEUVRE_SOURCE,
            )
        )
        if vehicle.mph > 10:
            take_hazard_test(state, vehicle, 10, "U-turn at 11-30 mph")
        _finish_activation(state, vehicle)
        return

    lane_pair = vehicle.lane_pair
    next_position = _forward_position_in_state(state, vehicle)
    if next_position is None:
        section = vehicle.section + vehicle.direction
        space = 1
    else:
        section, space = next_position
    speed_change = 0

    if action_id == "accelerate":
        speed_change = min(20, vehicle.acceleration_mph, vehicle.max_mph - vehicle.mph)
    elif action_id == "brake":
        speed_change = -min(20, vehicle.braking_mph, vehicle.mph)
    elif action_id in {"drift_left", "drift_right"}:
        if next_position is None:
            state.logs.append(LogEntry(f"{vehicle.label} cannot drift while leaving the road.", "illegal-action", MANOEUVRE_SOURCE))
            _finish_activation(state, vehicle)
            return
        drift_lane, blocked_reason = _legal_drift_lane_pair(state, vehicle, action_id, section)
        if blocked_reason is not None or drift_lane is None:
            state.logs.append(
                LogEntry(
                    f"{vehicle.label} cannot {action_id.replace('_', ' ')}: {blocked_reason}",
                    "illegal-action",
                    MANOEUVRE_SOURCE,
                )
            )
            _finish_activation(state, vehicle)
            return
        lane_pair = drift_lane

    old = (vehicle.section, vehicle.space, vehicle.lane_pair)

    if section < 0 or section >= state.track_sections:
        check_passive_markers_on_exit(state, vehicle, old[0], old[1], old[2])
        state.logs.append(LogEntry(f"{vehicle.label} exits the test road.", "scenario"))
        vehicle.acted_this_phase = True
        if vehicle.side == "agency" and state.scenario_id in {"intercept", "ambush"}:
            state.game_over = True
            state.winner = "agency"
            state.campaign.settlement_pending = True
            state.logs.append(LogEntry("Agency vehicle exits successfully.", "victory"))
        elif vehicle.side == "outlaw" and state.scenario_id == "pursuit":
            state.game_over = True
            state.winner = "outlaw"
            state.campaign.settlement_pending = True
            state.logs.append(LogEntry("Outlaw escapes the pursuit.", "victory"))
        choose_next_actor(state)
        return

    for other in state.vehicles:
        if _overlap(vehicle, section, space, lane_pair, other):
            check_passive_markers_on_exit(state, vehicle, old[0], old[1], old[2])
            resolve_ram(state, vehicle, other)
            _finish_activation(state, vehicle)
            return

    vehicle.section = section
    vehicle.space = space
    vehicle.lane_pair = lane_pair
    if speed_change:
        vehicle.mph += speed_change
    if action_id in {"rocket_pulse", "rocket_cruise", "rocket_off"}:
        apply_rocket_booster_action(state, vehicle, action_id)
    state.logs.append(
        LogEntry(
            f"{vehicle.label}: {old[0]+1}.{old[1]} LP{old[2]} -> {section+1}.{space} LP{lane_pair}, speed {vehicle.mph} mph.",
            "move",
            MOVE_SOURCE,
        )
    )
    check_passive_markers_on_exit(state, vehicle, old[0], old[1], old[2])
    check_movement_hazards(state, vehicle, action_id, old_section=old[0], old_lane_pair=old[2])
    if action_id == "shoot":
        if vehicle.control_state == "controlled" and not vehicle.action_cancelled_this_phase:
            apply_shoot(state, vehicle, finish_activation=False)
        else:
            state.logs.append(LogEntry(f"{vehicle.label}'s shooting action is cancelled by hazards.", "shoot", SHOOT_SOURCE))
    _finish_activation(state, vehicle)


def ai_choose_action(state: GameState, vehicle: Vehicle) -> str:
    if vehicle.control_state != "controlled":
        return "regain_control"

    next_position = _forward_position_in_state(state, vehicle)
    if next_position is not None:
        next_section, next_space = next_position
        if 0 <= next_section < state.track_sections and _lane_pair_hits_marker(
            state, next_section, next_space, vehicle.lane_pair, "smoke"
        ):
            target = _objective_target(state, vehicle)
            preferred_lane = target.lane_pair if target is not None else vehicle.lane_pair
            for lane in (preferred_lane, vehicle.lane_pair - 1, vehicle.lane_pair + 1):
                if MIN_LANE_PAIR <= lane <= MAX_LANE_PAIR and lane != vehicle.lane_pair:
                    action_id = _drift_action_toward_lane(state, vehicle, lane)
                    if action_id is not None:
                        return action_id
            return "brake" if vehicle.mph > 20 else "steady"

    current_limit = curve_safety_limit(state, vehicle)
    next_limit = _curve_limit_after_forward(state, vehicle)
    curve_limits = [limit for limit in (current_limit, next_limit) if limit is not None]
    if curve_limits and vehicle.mph > min(curve_limits):
        return "brake"

    if shoot_targets(state, vehicle):
        return "shoot"

    next_section = -1 if next_position is None else next_position[0]
    if next_section < 0 or next_section >= state.track_sections:
        if state.scenario_id == "pursuit" and vehicle.side == "outlaw":
            return "steady"
        return "brake" if vehicle.mph > 20 else "steady"

    agency = next((v for v in state.vehicles if v.side == "agency" and not v.destroyed), None)
    if agency is None:
        return "steady"

    if state.scenario_id == "ambush" and _ahead_of(state, vehicle, agency):
        return "brake" if vehicle.mph > agency.mph else "steady"

    if state.scenario_id == "pursuit" and vehicle.side == "outlaw":
        return "accelerate" if vehicle.mph < vehicle.max_mph else "steady"

    target = _objective_target(state, vehicle) or agency
    if vehicle.lane_pair != target.lane_pair and abs(vehicle.section - target.section) <= 3:
        action_id = _drift_action_toward_lane(state, vehicle, target.lane_pair)
        if action_id is not None:
            return action_id

    return "steady"


def apply_ai_turn_if_needed(state: GameState) -> bool:
    vehicle = active_vehicle(state)
    if vehicle is None or vehicle.side != "outlaw":
        return False
    action = ai_choose_action(state, vehicle)
    state.logs.append(LogEntry(f"Computer chooses {action.replace('_', ' ')} for {vehicle.label}.", "ai"))
    apply_action(state, action)
    return True


def settle_campaign(state: GameState) -> None:
    if not state.campaign.settlement_pending:
        state.logs.append(LogEntry("No campaign settlement is pending.", "campaign", CAMPAIGN_SOURCE))
        return
    if state.winner == "agency":
        reward = int(SCENARIOS[state.scenario_id]["reward"])
        kudos = 2
    else:
        reward = int(SCENARIOS[state.scenario_id]["loss"])
        kudos = -1
    repair_bill = sum((24 - vehicle.damage) * 250 for vehicle in state.vehicles if vehicle.side == "agency")
    state.campaign.funds += reward - repair_bill
    state.campaign.kudos += kudos
    state.campaign.contracts_completed += 1
    state.campaign.repairs_pending = repair_bill
    state.campaign.settlement_pending = False
    state.logs.append(
        LogEntry(
            f"Campaign settled: reward {reward}, repairs {repair_bill}, funds {state.campaign.funds}, kudos {state.campaign.kudos}.",
            "campaign",
            CAMPAIGN_SOURCE,
        )
    )


def start_new_contract(state: GameState) -> None:
    campaign = state.campaign
    new_state = new_game(campaign.current_scenario, campaign)
    copy_state(state, new_state)
    state.logs.append(LogEntry("New contract started from campaign state.", "campaign", CAMPAIGN_SOURCE))


def check_victory(state: GameState) -> None:
    living_sides = {vehicle.side for vehicle in state.vehicles if not vehicle.destroyed}
    if len(living_sides) == 1:
        state.game_over = True
        state.winner = next(iter(living_sides))
        state.campaign.settlement_pending = True
        state.logs.append(LogEntry(f"{state.winner.title()} side wins the engagement.", "victory"))
    elif not living_sides:
        state.game_over = True
        state.winner = None
        state.campaign.settlement_pending = True
        state.logs.append(LogEntry("Both sides are destroyed. No winner.", "victory"))

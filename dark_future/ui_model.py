from __future__ import annotations

from dataclasses import dataclass

from .data_loader import load_rule_json, vehicle_template
from .engine import (
    LANE_COUNT,
    GameState,
    active_vehicle,
    curve_safety_limit,
    legal_actions,
    phase_moves,
    section_space_limit,
    shoot_targets,
    speed_factor,
)
from .track import (
    is_valid_lane_space,
    lane_speed_limit,
    piece_angle_degrees,
    piece_family,
    piece_max_spaces,
)


@dataclass(frozen=True)
class SourceModel:
    book: str
    pages: tuple[int, ...]
    note: str


@dataclass(frozen=True)
class SectionModel:
    index: int
    label: str
    kind: str
    spaces: int
    lane_count: int
    is_curve: bool
    family: str
    angle_degrees: int


@dataclass(frozen=True)
class TrackCellModel:
    section: int
    lane: int
    space: int
    valid: bool
    speed_limit_mph: int | None


@dataclass(frozen=True)
class VehicleTokenModel:
    id: str
    label: str
    side: str
    template_id: str
    section: int
    space: int
    lane_pair: int
    lane_rows: tuple[int, int]
    occupied_lanes: tuple[int, ...]
    direction: int
    spin_facing_degrees: int | None
    mph: int
    active: bool
    destroyed: bool
    control_state: str


@dataclass(frozen=True)
class MarkerTokenModel:
    id: str
    kind: str
    section: int
    space: int
    lane_pair: int
    owner_side: str


@dataclass(frozen=True)
class TacticalBoardModel:
    turn: int
    phase: int
    track_sections: tuple[SectionModel, ...]
    cells: tuple[TrackCellModel, ...]
    vehicles: tuple[VehicleTokenModel, ...]
    markers: tuple[MarkerTokenModel, ...]
    active_vehicle_id: str | None
    game_over: bool
    winner: str | None


@dataclass(frozen=True)
class VehicleRecordModel:
    id: str
    label: str
    side: str
    template_id: str
    status: str
    position: str
    speed: str
    max_mph: int
    acceleration_mph: int
    braking_mph: int
    handling: int
    damage: int
    armour: int
    weapon: str
    weapon_accuracy: int
    weapon_damage_modifier: int
    control_state: str
    driver_skill: int
    hazard_mod: int
    weapon_disabled: bool
    critical_notes: tuple[str, ...]


@dataclass(frozen=True)
class VehicleRecordsModel:
    records: tuple[VehicleRecordModel, ...]


@dataclass(frozen=True)
class DesignCatalogItemModel:
    id: str
    label: str
    category: str
    cost: int | None
    weight: int | None
    status: str
    details: str
    icon_id: str | None = None


@dataclass(frozen=True)
class DesignVehicleModel:
    id: str
    label: str
    template_id: str
    template_label: str
    kind: str
    installed_items: tuple[str, ...]
    payload_used: int | None
    payload_limit: int | None
    total_cost: int | None
    stat_lines: tuple[str, ...]


@dataclass(frozen=True)
class VehicleDesignModel:
    title: str
    selected_vehicle_id: str | None
    vehicles: tuple[DesignCatalogItemModel, ...]
    chassis: tuple[DesignCatalogItemModel, ...]
    equipment: tuple[DesignCatalogItemModel, ...]
    selected_vehicle: DesignVehicleModel | None
    summary_lines: tuple[str, ...]
    validation_messages: tuple[str, ...]


@dataclass(frozen=True)
class MountSlotModel:
    id: str
    label: str
    kind: str
    location: str
    allowed_classes: tuple[str, ...]
    allowed_facings: tuple[str, ...]
    capacity: int
    installed_label: str | None
    installed_weapon_id: str | None
    icon_weapon_id: str | None
    status: str


@dataclass(frozen=True)
class GarageLoadoutModel:
    vehicle_id: str | None
    label: str
    template_id: str | None
    template_label: str
    kind: str
    mounts: tuple[MountSlotModel, ...]
    payload_used: int | None
    payload_limit: int | None
    cost_estimate: int | None
    weight_estimate: int | None
    stat_lines: tuple[str, ...]
    validation_messages: tuple[str, ...]


@dataclass(frozen=True)
class CampaignSummaryModel:
    name: str
    player_kind: str
    scenario: str
    objective: str
    funds: int
    kudos: int
    contracts_completed: int
    repairs_pending: int
    settlement_pending: bool
    recruits_hired: int
    save_path: str
    roster: tuple[str, ...]
    garage: tuple[str, ...]
    placeholder: str


@dataclass(frozen=True)
class ActionButtonModel:
    id: str
    label: str
    kind: str
    details: str
    hotkey: str
    enabled: bool


@dataclass(frozen=True)
class ActionPanelModel:
    title: str
    actor_id: str | None
    actor_label: str
    actor_lines: tuple[str, ...]
    actions: tuple[ActionButtonModel, ...]


@dataclass(frozen=True)
class LogLineModel:
    message: str
    kind: str
    source: SourceModel | None


@dataclass(frozen=True)
class LogModel:
    title: str
    entries: tuple[LogLineModel, ...]
    total_entries: int


@dataclass(frozen=True)
class DebugVehicleMovementModel:
    vehicle_id: str
    label: str
    speed_factor: int
    phase_moves: int
    current: str
    forward: str | None


@dataclass(frozen=True)
class DebugHazardModel:
    vehicle_id: str
    label: str
    curve_safety_limit_mph: int | None
    hazard_mod: int
    control_state: str
    notes: tuple[str, ...]


@dataclass(frozen=True)
class DebugContactModel:
    shooter_id: str
    shooter_label: str
    target_ids: tuple[str, ...]
    placeholder: str


@dataclass(frozen=True)
class DebugOverlayModel:
    movement: tuple[DebugVehicleMovementModel, ...]
    hazards: tuple[DebugHazardModel, ...]
    contacts: tuple[DebugContactModel, ...]
    placeholders: tuple[str, ...]


def build_tactical_board_model(state: GameState) -> TacticalBoardModel:
    sections = tuple(
        SectionModel(
            index=index,
            label=str(index + 1),
            kind=section_type,
            spaces=piece_max_spaces(section_type),
            lane_count=LANE_COUNT,
            is_curve=section_type != "straight",
            family=piece_family(section_type),
            angle_degrees=piece_angle_degrees(section_type),
        )
        for index, section_type in enumerate(state.track_section_types)
    )
    cells = tuple(
        TrackCellModel(
            section=index,
            lane=lane,
            space=space,
            valid=is_valid_lane_space(section_type, lane, space),
            speed_limit_mph=lane_speed_limit(section_type, lane),
        )
        for index, section_type in enumerate(state.track_section_types)
        for lane in range(1, LANE_COUNT + 1)
        for space in range(1, piece_max_spaces(section_type) + 1)
    )
    vehicles = tuple(
        VehicleTokenModel(
            id=vehicle.id,
            label=vehicle.label,
            side=vehicle.side,
            template_id=vehicle.template_id,
            section=vehicle.section,
            space=vehicle.space,
            lane_pair=vehicle.lane_pair,
            lane_rows=vehicle.lane_rows,
            occupied_lanes=vehicle.occupied_lanes,
            direction=vehicle.direction,
            spin_facing_degrees=vehicle.spin_facing_degrees,
            mph=vehicle.mph,
            active=vehicle.id == state.active_vehicle_id,
            destroyed=vehicle.destroyed,
            control_state=vehicle.control_state,
        )
        for vehicle in state.vehicles
    )
    markers = tuple(
        MarkerTokenModel(
            id=marker.id,
            kind=marker.kind,
            section=marker.section,
            space=marker.space,
            lane_pair=marker.lane_pair,
            owner_side=marker.owner_side,
        )
        for marker in state.passive_markers
    )
    return TacticalBoardModel(
        turn=state.turn,
        phase=state.phase,
        track_sections=sections,
        cells=cells,
        vehicles=vehicles,
        markers=markers,
        active_vehicle_id=state.active_vehicle_id,
        game_over=state.game_over,
        winner=state.winner,
    )


def build_vehicle_records_model(state: GameState) -> VehicleRecordsModel:
    records = tuple(
        VehicleRecordModel(
            id=vehicle.id,
            label=vehicle.label,
            side=vehicle.side,
            template_id=vehicle.template_id,
            status="destroyed" if vehicle.destroyed else "active",
            position=f"section {vehicle.section + 1}, space {vehicle.space}, LP{vehicle.lane_pair}",
            speed=f"{vehicle.mph} mph",
            max_mph=vehicle.max_mph,
            acceleration_mph=vehicle.acceleration_mph,
            braking_mph=vehicle.braking_mph,
            handling=vehicle.handling,
            damage=vehicle.damage,
            armour=vehicle.armour,
            weapon=vehicle.weapon_label,
            weapon_accuracy=vehicle.weapon_accuracy,
            weapon_damage_modifier=vehicle.weapon_damage_modifier,
            control_state=vehicle.control_state,
            driver_skill=vehicle.driver_skill,
            hazard_mod=vehicle.hazard_mod,
            weapon_disabled=vehicle.weapon_disabled,
            critical_notes=tuple(vehicle.critical_notes),
        )
        for vehicle in state.vehicles
    )
    return VehicleRecordsModel(records=records)


def build_vehicle_design_model(state: GameState, selected_vehicle_id: str | None = None) -> VehicleDesignModel:
    vehicle_rows = _vehicle_template_items()
    chassis_rows = _advanced_chassis_items()
    equipment_rows = _equipment_catalog_items()
    selected_id = selected_vehicle_id
    if selected_id is None and state.campaign.garage:
        selected_id = state.campaign.garage[0]
    selected = _selected_design_vehicle(state, selected_id)
    messages = list(_design_validation_messages(state, selected))
    if selected is None and selected_id is not None:
        messages.append(f"Selected vehicle {selected_id} is not present in the current tactical state.")
    return VehicleDesignModel(
        title="Vehicle Design / Garage",
        selected_vehicle_id=selected.id if selected is not None else selected_id,
        vehicles=vehicle_rows,
        chassis=chassis_rows,
        equipment=equipment_rows,
        selected_vehicle=selected,
        summary_lines=_design_summary_lines(selected),
        validation_messages=tuple(messages),
    )


def build_garage_loadout_model(state: GameState, selected_vehicle_id: str | None = None) -> GarageLoadoutModel:
    if selected_vehicle_id is None:
        selected_vehicle_id = state.active_vehicle_id
    vehicle = next((item for item in state.vehicles if item.id == selected_vehicle_id), None)
    if vehicle is None:
        return GarageLoadoutModel(
            vehicle_id=selected_vehicle_id,
            label="No Vehicle Selected",
            template_id=None,
            template_label="None",
            kind="unknown",
            mounts=(),
            payload_used=None,
            payload_limit=None,
            cost_estimate=None,
            weight_estimate=None,
            stat_lines=("Select a tactical or campaign garage vehicle.",),
            validation_messages=(f"Selected vehicle {selected_vehicle_id} is not present in tactical state.",),
        )

    template = vehicle_template(vehicle.template_id)
    stats = template.get("coreStats", {})
    payload_limit = _optional_int(stats.get("payload"))
    weapon = _weapon_row_for_label(vehicle.weapon_label)
    installed_weapon_id = str(weapon["id"]) if weapon is not None else None
    installed_weight = _optional_int(weapon.get("weight")) if weapon is not None else None
    installed_cost = _optional_int(weapon.get("cost")) if weapon is not None else None
    mounts = tuple(
        _mount_slot_model(row, vehicle.weapon_label, installed_weapon_id, row.get("id") == "hood")
        for row in template.get("coreMounts", [])
    )
    messages = [
        "Hardpoint layout is data-driven from vehicle mount ids; WLF sheet images can be attached to these ids.",
        "Runtime vehicles currently expose one fitted weapon, projected onto the hood slot for display.",
    ]
    if payload_limit is not None and installed_weight is not None and installed_weight > payload_limit:
        messages.append("Installed weapon exceeds this vehicle payload.")
    if vehicle.id not in state.campaign.garage:
        messages.append("Selected vehicle is not listed in the lightweight campaign garage.")
    return GarageLoadoutModel(
        vehicle_id=vehicle.id,
        label=vehicle.label,
        template_id=vehicle.template_id,
        template_label=str(template.get("label", vehicle.template_id)),
        kind=str(template.get("kind", "vehicle")),
        mounts=mounts,
        payload_used=installed_weight,
        payload_limit=payload_limit,
        cost_estimate=installed_cost,
        weight_estimate=installed_weight,
        stat_lines=(
            f"Damage {vehicle.damage} | Armour {vehicle.armour}",
            f"Max {vehicle.max_mph} mph | Accel {vehicle.acceleration_mph} | Brake {vehicle.braking_mph}",
            f"Handling {vehicle.handling} | Driver {vehicle.driver_skill}",
            f"Control {vehicle.control_state} | Status {'destroyed' if vehicle.destroyed else 'roadworthy'}",
        ),
        validation_messages=tuple(messages),
    )


def build_campaign_summary_model(state: GameState) -> CampaignSummaryModel:
    campaign = state.campaign
    return CampaignSummaryModel(
        name=campaign.name,
        player_kind=campaign.player_kind,
        scenario=campaign.current_scenario,
        objective=campaign.objective,
        funds=campaign.funds,
        kudos=campaign.kudos,
        contracts_completed=campaign.contracts_completed,
        repairs_pending=campaign.repairs_pending,
        settlement_pending=campaign.settlement_pending,
        recruits_hired=campaign.recruits_hired,
        save_path=campaign.last_save_path,
        roster=tuple(campaign.roster),
        garage=tuple(campaign.garage),
        placeholder="Campaign actions are live: recruit, repair, scenario cycle, save, and load.",
    )


def _vehicle_template_items() -> tuple[DesignCatalogItemModel, ...]:
    rows = load_rule_json("vehicles.json").get("vehicleTemplates", [])
    items = []
    for row in rows:
        stats = row.get("coreStats", {})
        items.append(
            DesignCatalogItemModel(
                id=str(row["id"]),
                label=str(row.get("label", row["id"])),
                category=str(row.get("kind", "vehicle")),
                cost=None,
                weight=None,
                status=str(row.get("status", "cleanedDraft")),
                details=(
                    f"Dmg {stats.get('damage', '?')} Arm {stats.get('armour', '?')} "
                    f"Payload {stats.get('payload', '?')}"
                ),
            )
        )
    return tuple(items)


def _advanced_chassis_items() -> tuple[DesignCatalogItemModel, ...]:
    rows = load_rule_json("vehicles.json").get("advancedChassis", [])
    items = []
    for row in rows:
        items.append(
            DesignCatalogItemModel(
                id=str(row["id"]),
                label=f"{row.get('vehicleTemplateId', 'vehicle')} {row.get('engineSize', '')}".strip(),
                category="chassis",
                cost=_optional_int(row.get("cost")),
                weight=_optional_int(row.get("weight")),
                status=str(row.get("status", "cleanedDraft")),
                details=f"Template {row.get('vehicleTemplateId', '?')} | Engine {row.get('engineSize', '?')}",
            )
        )
    return tuple(items)


def _equipment_catalog_items() -> tuple[DesignCatalogItemModel, ...]:
    data = load_rule_json("equipment.json")
    categories = (
        "weapons",
        "mountUpgrades",
        "engineAddOns",
        "drivingSystems",
        "fireControlComputers",
        "safetyDevices",
    )
    items: list[DesignCatalogItemModel] = []
    for category in categories:
        for row in data.get(category, []):
            cost = _optional_int(row.get("cost"))
            weight = _optional_int(row.get("weight"))
            details_parts = []
            if "class" in row:
                details_parts.append(f"Class {row['class']}")
            if row.get("sanctioned"):
                details_parts.append("Sanctioned")
            if cost is None:
                details_parts.append("Cost pending")
            if weight is None:
                details_parts.append("Weight pending")
            items.append(
                DesignCatalogItemModel(
                    id=str(row["id"]),
                    label=str(row.get("label", row["id"])),
                    category=category,
                    cost=cost,
                    weight=weight,
                    status=str(row.get("status", "cleanedDraft" if cost is not None and weight is not None else "needsProofread")),
                    details=" | ".join(details_parts) or category,
                    icon_id=str(row["id"]) if category == "weapons" else None,
                )
            )
    return tuple(items)


def _mount_slot_model(row, weapon_label: str, weapon_id: str | None, installed: bool) -> MountSlotModel:
    allowed_classes = tuple(str(item) for item in row.get("allowedWeaponClasses", ()))
    allowed_facings = tuple(str(item) for item in row.get("allowedFacings", ()))
    return MountSlotModel(
        id=str(row.get("id", "mount")),
        label=_humanize_mount_id(str(row.get("id", "mount"))),
        kind=str(row.get("kind", "ordinary")),
        location=str(row.get("location", row.get("id", "mount"))),
        allowed_classes=allowed_classes,
        allowed_facings=allowed_facings,
        capacity=_optional_int(row.get("capacity")) or 1,
        installed_label=weapon_label if installed else None,
        installed_weapon_id=weapon_id if installed else None,
        icon_weapon_id=weapon_id if installed else None,
        status="fitted" if installed else "empty",
    )


def _weapon_row_for_label(label: str):
    normalized = _normalize_label(label)
    aliases = {
        "6mmmg": "6mmmachinegun",
        "15mmautocannon": "15mmautocannon",
    }
    wanted = aliases.get(normalized, normalized)
    for row in load_rule_json("equipment.json").get("weapons", []):
        if _normalize_label(str(row.get("label", ""))) == wanted:
            return row
    return None


def _normalize_label(label: str) -> str:
    return "".join(ch for ch in label.lower() if ch.isalnum())


def _humanize_mount_id(value: str) -> str:
    out = []
    for char in value:
        if char.isupper() and out:
            out.append(" ")
        out.append(char)
    return "".join(out).title()


def _selected_design_vehicle(state: GameState, selected_vehicle_id: str | None) -> DesignVehicleModel | None:
    if selected_vehicle_id is None:
        return None
    vehicle = next((item for item in state.vehicles if item.id == selected_vehicle_id), None)
    if vehicle is None:
        return None
    template = vehicle_template(vehicle.template_id)
    stats = template.get("coreStats", {})
    payload_limit = _optional_int(stats.get("payload"))
    installed = (f"{vehicle.weapon_label} (runtime weapon)",)
    return DesignVehicleModel(
        id=vehicle.id,
        label=vehicle.label,
        template_id=vehicle.template_id,
        template_label=str(template.get("label", vehicle.template_id)),
        kind=str(template.get("kind", "vehicle")),
        installed_items=installed,
        payload_used=None,
        payload_limit=payload_limit,
        total_cost=None,
        stat_lines=(
            f"Damage {vehicle.damage} | Armour {vehicle.armour}",
            f"Max {vehicle.max_mph} mph | Accel {vehicle.acceleration_mph} | Brake {vehicle.braking_mph}",
            f"Handling {vehicle.handling} | Driver {vehicle.driver_skill}",
            f"Control {vehicle.control_state} | Status {'destroyed' if vehicle.destroyed else 'roadworthy'}",
        ),
    )


def _design_summary_lines(selected: DesignVehicleModel | None) -> tuple[str, ...]:
    if selected is None:
        return ("No vehicle selected.", "Select a tactical vehicle or campaign garage entry to inspect.")
    payload_used = "pending" if selected.payload_used is None else str(selected.payload_used)
    payload_limit = "pending" if selected.payload_limit is None else str(selected.payload_limit)
    total_cost = "pending campaign record" if selected.total_cost is None else f"${selected.total_cost}"
    return (
        f"Selected: {selected.label} ({selected.template_label})",
        f"Payload: {payload_used} / {payload_limit}",
        f"Cost: {total_cost}",
        f"Installed items: {len(selected.installed_items)}",
    )


def _design_validation_messages(state: GameState, selected: DesignVehicleModel | None) -> tuple[str, ...]:
    messages = [
        "Design screen is read-only until campaign garage actions are connected to runtime state.",
        "Fitting validation is delegated to the campaign backend; this view does not duplicate mount rules.",
    ]
    if selected is not None and selected.payload_used is None:
        messages.append("Selected tactical vehicle has no campaign payload ledger yet.")
    if selected is not None and selected.id not in state.campaign.garage:
        messages.append("Selected vehicle is not listed in the lightweight campaign garage.")
    return tuple(messages)


def _optional_int(value) -> int | None:
    if value is None:
        return None
    return int(value)


def build_action_panel_model(state: GameState) -> ActionPanelModel:
    actor = active_vehicle(state)
    if actor is None:
        actor_lines = ("No active vehicle.", "Advance phase when ready.")
        actor_label = "None"
        actor_id = None
    else:
        actor_lines = (
            f"{actor.label} ({actor.side})",
            f"Speed: {actor.mph} mph  Handling: {actor.handling}",
            f"Damage: {actor.damage}  Armour: {actor.armour}",
            f"Control: {actor.control_state}  Driver: {actor.driver_skill}",
            f"Weapon: {actor.weapon_label}",
            f"Position: section {actor.section + 1}, space {actor.space}, lane pair {actor.lane_pair}",
            f"Objective: {state.objective}",
        )
        actor_label = actor.label
        actor_id = actor.id
    actions = tuple(
        ActionButtonModel(
            id=action.id,
            label=action.label,
            kind=action.kind,
            details=action.details,
            hotkey=str(index),
            enabled=True,
        )
        for index, action in enumerate(legal_actions(state), start=1)
    )
    return ActionPanelModel(
        title="Action Panel",
        actor_id=actor_id,
        actor_label=actor_label,
        actor_lines=actor_lines,
        actions=actions,
    )


def build_log_model(state: GameState, limit: int = 10) -> LogModel:
    entries = tuple(
        LogLineModel(
            message=entry.message,
            kind=entry.kind,
            source=(
                SourceModel(entry.source.book, entry.source.pages, entry.source.note)
                if entry.source is not None
                else None
            ),
        )
        for entry in state.logs[-limit:]
    )
    return LogModel(
        title="Rule / Combat Log",
        entries=entries,
        total_entries=len(state.logs),
    )


def build_debug_overlay_model(state: GameState) -> DebugOverlayModel:
    movement = tuple(_debug_movement_for_vehicle(state, vehicle) for vehicle in state.vehicles)
    hazards = tuple(
        DebugHazardModel(
            vehicle_id=vehicle.id,
            label=vehicle.label,
            curve_safety_limit_mph=curve_safety_limit(state, vehicle),
            hazard_mod=vehicle.hazard_mod,
            control_state=vehicle.control_state,
            notes=tuple(vehicle.critical_notes),
        )
        for vehicle in state.vehicles
    )
    contacts = tuple(
        DebugContactModel(
            shooter_id=vehicle.id,
            shooter_label=vehicle.label,
            target_ids=tuple(target.id for target in shoot_targets(state, vehicle)),
            placeholder="Forward-corridor direct fire and ram contacts are provisional.",
        )
        for vehicle in state.vehicles
        if not vehicle.destroyed
    )
    return DebugOverlayModel(
        movement=movement,
        hazards=hazards,
        contacts=contacts,
        placeholders=(
            "Movement graph: forward means same-lane next space; uneven curve lanes use the outside divider.",
            "Hazards: curve, drift, and passive marker checks expose rough safety-limit payloads.",
            "Contacts: forward corridor includes adjacent lane pairs, range cap, vehicle blocking, and smoke blocking.",
        ),
    )


def _debug_movement_for_vehicle(state: GameState, vehicle) -> DebugVehicleMovementModel:
    current = f"{vehicle.section + 1}.{vehicle.space} LP{vehicle.lane_pair}"
    next_section = vehicle.section
    next_space = vehicle.space + vehicle.direction
    limit = section_space_limit(vehicle.section, vehicle.lane_pair, state)
    if next_space > limit:
        next_section += 1
        next_space = 1
    elif next_space < 1:
        next_section -= 1
        if 0 <= next_section < state.track_sections:
            next_space = section_space_limit(next_section, vehicle.lane_pair, state)
    if 0 <= next_section < state.track_sections:
        forward = f"{next_section + 1}.{next_space} LP{vehicle.lane_pair}"
    else:
        forward = None
    return DebugVehicleMovementModel(
        vehicle_id=vehicle.id,
        label=vehicle.label,
        speed_factor=speed_factor(vehicle.mph),
        phase_moves=phase_moves(vehicle.mph, state.phase),
        current=current,
        forward=forward,
    )

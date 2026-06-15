from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import uuid4

from .data_loader import load_rule_json


DesignMode = Literal["corePayload", "advancedWeight"]
Facing = Literal["front", "rear", "leftSide", "rightSide", "floor", "roof"]

FACINGS: tuple[Facing, ...] = (
    "front",
    "rear",
    "leftSide",
    "rightSide",
    "floor",
    "roof",
)


class VehicleDesignError(ValueError):
    pass


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


@dataclass
class ArmourFacing:
    points: int
    material: str = "carbonSteel"


@dataclass
class MagazineLoad:
    kind: str
    shots: int | str
    source: str = "included"
    cost: int = 0
    weight: int = 0


@dataclass
class DesignMount:
    id: str
    kind: str
    location: str
    allowed_weapon_classes: list[str]
    allowed_facings: list[str]
    capacity: int = 1
    source_id: str = ""
    cost: int = 0
    weight: int = 0


@dataclass
class InstalledItem:
    id: str
    source_id: str
    label: str
    category: str
    cost: int
    weight: int
    item_class: str = ""
    mount_id: str | None = None
    facing: str | None = None
    linked_group_id: str | None = None
    magazines: list[MagazineLoad] = field(default_factory=list)
    double_load: bool = False


@dataclass
class VehicleStats:
    damage: int
    armour: int
    maximum_speed_mph: int
    acceleration_mph: int
    braking_mph: int
    handling: int
    non_he_handling: int | None = None
    he_hit_handling: int | None = None


@dataclass
class VehicleDesign:
    id: str
    label: str
    template_id: str
    design_mode: DesignMode
    chassis_id: str | None = None
    engine_size: str | None = None
    mounts: dict[str, DesignMount] = field(default_factory=dict)
    installed_items: list[InstalledItem] = field(default_factory=list)
    armour: dict[Facing, ArmourFacing] = field(default_factory=dict)
    base_cost: int = 0
    base_weight: int = 0
    linked_groups: dict[str, list[str]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def template(self) -> dict[str, Any]:
        return template_by_id(self.template_id)

    @property
    def kind(self) -> str:
        return str(self.template["kind"])


@dataclass(frozen=True)
class DesignSummary:
    total_cost: int
    total_weight: int
    payload_used: int
    payload_limit: int
    stats: VehicleStats
    armour: dict[Facing, ArmourFacing]
    legal: bool
    errors: tuple[str, ...] = ()


def vehicles_data() -> dict[str, Any]:
    return load_rule_json("vehicles.json")


def equipment_data() -> dict[str, Any]:
    return load_rule_json("equipment.json")


def proofread_data() -> dict[str, Any]:
    return load_rule_json("wlf-vehicle-tables-proofread.json")


def template_by_id(template_id: str) -> dict[str, Any]:
    for template in vehicles_data()["vehicleTemplates"]:
        if template["id"] == template_id:
            return template
    raise ValueError(f"unknown vehicle template {template_id}")


def vehicle_template(template_id: str) -> dict[str, Any]:
    return template_by_id(template_id)


def load_vehicle_design_rules() -> dict[str, Any]:
    return {
        "vehicles": vehicles_data(),
        "equipment": equipment_data(),
        "proofreadTables": proofread_data(),
    }


def chassis_by_id(chassis_id: str) -> dict[str, Any]:
    for chassis in vehicles_data()["advancedChassis"]:
        if chassis["id"] == chassis_id:
            return chassis
    raise ValueError(f"unknown chassis {chassis_id}")


def catalog_item(source_id: str) -> dict[str, Any]:
    data = equipment_data()
    for category in (
        "weapons",
        "mountUpgrades",
        "engineAddOns",
        "drivingSystems",
        "fireControlComputers",
        "safetyDevices",
    ):
        for row in data.get(category, []):
            if row["id"] == source_id:
                item = dict(row)
                item["_category"] = category
                return item
    raise ValueError(f"unknown equipment item {source_id}")


def available_catalog() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for category in (
        "weapons",
        "mountUpgrades",
        "engineAddOns",
        "drivingSystems",
        "fireControlComputers",
        "safetyDevices",
    ):
        for row in equipment_data().get(category, []):
            enriched = dict(row)
            enriched["_category"] = category
            rows.append(enriched)
    return rows


def create_core_design(template_id: str, label: str | None = None) -> VehicleDesign:
    template = template_by_id(template_id)
    stats = template["coreStats"]
    design = VehicleDesign(
        id=_new_id("design"),
        label=label or str(template["label"]),
        template_id=template_id,
        design_mode="corePayload",
    )
    design.mounts = _core_mounts(template)
    design.armour = {
        facing: ArmourFacing(int(stats["armour"]), "carbonSteel") for facing in FACINGS
    }
    return design


def create_advanced_design(chassis_id: str, label: str | None = None) -> VehicleDesign:
    chassis = chassis_by_id(chassis_id)
    template = template_by_id(str(chassis["vehicleTemplateId"]))
    stats = template["coreStats"]
    design = VehicleDesign(
        id=_new_id("design"),
        label=label or f"{template['label']} {chassis['engineSize'].upper()}",
        template_id=str(chassis["vehicleTemplateId"]),
        design_mode="advancedWeight",
        chassis_id=chassis_id,
        engine_size=str(chassis["engineSize"]),
        base_cost=int(chassis["cost"]),
        base_weight=int(chassis["weight"]),
    )
    design.mounts = _core_mounts(template)
    design.armour = {
        facing: ArmourFacing(int(stats["armour"]), "carbonSteel") for facing in FACINGS
    }
    return design


def create_advanced_bike_design(label: str = "Bike") -> VehicleDesign:
    template = template_by_id("bike")
    bike_row = next(row for row in proofread_data()["vehicles"] if row["vehicle"] == "Bike")
    stats = template["coreStats"]
    design = VehicleDesign(
        id=_new_id("design"),
        label=label,
        template_id="bike",
        design_mode="advancedWeight",
        base_cost=int(bike_row["cost"]),
        base_weight=int(bike_row["weight"]),
    )
    design.mounts = _core_mounts(template)
    design.armour = {
        facing: ArmourFacing(int(stats["armour"]), "carbonSteel") for facing in FACINGS
    }
    return design


def _core_mounts(template: dict[str, Any]) -> dict[str, DesignMount]:
    return {
        row["id"]: DesignMount(
            id=row["id"],
            kind=row["kind"],
            location=row["location"],
            allowed_weapon_classes=list(row.get("allowedWeaponClasses", [])),
            allowed_facings=list(row.get("allowedFacings", [])),
            capacity=int(row.get("capacity", 1)),
        )
        for row in template.get("coreMounts", [])
    }


def install_item(
    design: VehicleDesign,
    source_id: str,
    mount_id: str | None = None,
    facing: str | None = None,
    installed_id: str | None = None,
) -> InstalledItem:
    item = catalog_item(source_id)
    _require_known_cost_weight(item)
    _validate_vehicle_restrictions(design, item)
    category = item["_category"]
    if category == "mountUpgrades":
        return _add_mount_upgrade(design, item, installed_id)
    installed = InstalledItem(
        id=installed_id or _new_id("installed"),
        source_id=source_id,
        label=str(item.get("label", source_id)),
        category=category,
        cost=int(item["cost"]),
        weight=int(item["weight"]),
        item_class=str(item.get("class", "")),
        mount_id=mount_id,
        facing=facing,
    )
    if category == "weapons":
        _install_weapon(design, installed, item)
    elif category == "fireControlComputers":
        _validate_fire_control_install(design, installed, item)
    elif mount_id is not None:
        raise ValueError(f"{source_id} does not fit in weapon mounts")
    _validate_system_dependencies(design, item)
    design.installed_items.append(installed)
    _validate_conflicts(design)
    _raise_if_over_payload(design)
    return installed


def _add_mount_upgrade(
    design: VehicleDesign,
    item: dict[str, Any],
    installed_id: str | None,
) -> InstalledItem:
    source_id = str(item["id"])
    if source_id not in design.template.get("optionalMounts", []):
        raise ValueError(f"{design.template_id} cannot take {source_id}")
    if source_id == "turret" and any(mount.kind == "turret" for mount in design.mounts.values()):
        raise ValueError("cars may add only one turret")
    if source_id in design.mounts:
        raise ValueError(f"{source_id} is already fitted")
    if source_id == "turret":
        allowed_classes = ["medium", "heavy"]
        capacity = 2
        kind = "turret"
        allowed_facings = ["turret"]
    elif source_id == "outrigger":
        allowed_classes = ["lightweight"]
        capacity = 2
        kind = "outrigger"
        allowed_facings = ["front"]
    elif source_id == "cupola":
        allowed_classes = ["lightweight", "medium"]
        capacity = 1
        kind = "cupola"
        allowed_facings = ["rear"]
    elif source_id == "pintle":
        allowed_classes = ["lightweight", "medium"]
        capacity = 1
        kind = "pintle"
        allowed_facings = ["rear"]
    elif source_id in {"rearLeftWing", "tailgate", "rearRightWing"}:
        allowed_classes = list(item.get("allowedWeaponClasses", ["lightweightAsMedium", "medium", "heavy"]))
        capacity = int(item.get("capacity", 1))
        kind = "ordinary"
        allowed_facings = _mount_upgrade_facings(design, item)
    else:
        raise ValueError(f"{source_id} mount rules need proofread before use")
    design.mounts[source_id] = DesignMount(
        id=source_id,
        kind=kind,
        location=source_id,
        allowed_weapon_classes=allowed_classes,
        allowed_facings=allowed_facings,
        capacity=capacity,
        source_id=source_id,
        cost=int(item["cost"]),
        weight=int(item["weight"]),
    )
    installed = InstalledItem(
        id=installed_id or _new_id("installed"),
        source_id=source_id,
        label=str(item.get("label", source_id)),
        category="mountUpgrades",
        cost=int(item["cost"]),
        weight=int(item["weight"]),
        mount_id=source_id,
    )
    design.installed_items.append(installed)
    _raise_if_over_payload(design)
    return installed


def _mount_upgrade_facings(design: VehicleDesign, item: dict[str, Any]) -> list[str]:
    by_template = item.get("facingByVehicleTemplate", {})
    if design.template_id in by_template:
        return list(by_template[design.template_id])
    return list(item.get("allowedFacings", ["front"]))


def _install_weapon(
    design: VehicleDesign,
    installed: InstalledItem,
    item: dict[str, Any],
) -> None:
    if installed.mount_id is None:
        raise ValueError("weapon installation requires a mount id")
    if installed.mount_id not in design.mounts:
        raise ValueError(f"unknown mount {installed.mount_id}")
    mount = design.mounts[installed.mount_id]
    item_class = _item_class_for_mount(design, str(item.get("class", "")))
    if item_class not in mount.allowed_weapon_classes:
        if item.get("class") == "heavy" and "Wing" in mount.id:
            raise ValueError(f"heavy weapon {installed.source_id} cannot be fitted to wing mount {mount.id}")
        if mount.kind == "passive":
            raise ValueError(f"ordinary weapon {installed.source_id} cannot be fitted to passive mount {mount.id}")
        if item.get("class") in {"passive", "lightweightPassive"} and mount.kind != "passive":
            raise ValueError(f"passive weapon {installed.source_id} cannot be fitted to ordinary mount {mount.id}")
        if design.kind == "bike":
            raise ValueError(f"bike mount {mount.id} accepts lightweight weapons only")
        raise ValueError(f"{installed.source_id} cannot be fitted to {mount.id}")
    if item.get("coreTurretAllowed") is False and mount.kind == "turret":
        raise ValueError(f"{installed.source_id} cannot be fitted to a core turret")
    if installed.source_id in catalog_item_for_mount_forbidden(mount):
        raise ValueError(f"{installed.source_id} cannot be fitted to {mount.id}")
    if not installed.facing:
        installed.facing = mount.allowed_facings[0] if mount.allowed_facings else "front"
    if installed.facing not in mount.allowed_facings and mount.kind != "turret":
        raise ValueError(f"{mount.id} cannot face {installed.facing}")
    current = [row for row in design.installed_items if row.mount_id == mount.id and row.category == "weapons"]
    if mount.kind == "turret":
        classes = [row.item_class for row in current] + [installed.item_class]
        if "heavy" in classes and len(classes) > 1:
            raise ValueError("turret capacity exceeded: one heavy weapon or two medium weapons")
        if len(classes) > mount.capacity:
            raise ValueError("turret capacity exceeded")
    elif len(current) >= mount.capacity:
        raise ValueError(f"{mount.id} mount is already full")
    starting = item.get("startingLoad")
    if starting:
        installed.magazines.append(
            MagazineLoad(
                kind=str(starting["kind"]),
                shots=starting["shots"],
                source="included",
            )
        )


def catalog_item_for_mount_forbidden(mount: DesignMount) -> set[str]:
    if mount.source_id:
        try:
            return set(catalog_item(mount.source_id).get("forbiddenWeaponIds", []))
        except ValueError:
            return set()
    return set()


def _item_class_for_mount(design: VehicleDesign, item_class: str) -> str:
    if item_class == "lightweight" and design.kind == "car":
        return "lightweightAsMedium"
    return item_class


def _validate_fire_control_install(
    design: VehicleDesign,
    installed: InstalledItem,
    item: dict[str, Any],
) -> None:
    if installed.source_id == "turretFireComputer":
        if installed.mount_id is None:
            raise ValueError("turret fire computer requires a turret or cupola mount id")
        mount = design.mounts.get(installed.mount_id)
        if mount is None or mount.kind not in item.get("compatibleMountKinds", []):
            raise ValueError("turret fire computer requires a compatible turret or cupola")
    if installed.source_id == "missileFireComputer":
        if installed.mount_id is None:
            raise ValueError("missile fire computer requires a missile pod mount id")
        weapon = _installed_by_id(design, installed.mount_id)
        if weapon.source_id not in item.get("compatibleWeaponIds", []):
            raise ValueError("missile fire computer requires a missile pod")


def _validate_system_dependencies(design: VehicleDesign, item: dict[str, Any]) -> None:
    requires = set(item.get("requires", []))
    if "activeSuspension" in requires and not _has_system(design, "activeSuspension"):
        raise ValueError(f"{item['id']} requires active suspension")
    includes = set(item.get("includes", []))
    if "activeSuspension" in includes:
        return


def _has_system(design: VehicleDesign, system: str) -> bool:
    for item in design.installed_items:
        try:
            raw = catalog_item(item.source_id)
        except ValueError:
            continue
        if raw.get("system") == system or system in raw.get("includes", []):
            return True
    return False


def _validate_conflicts(design: VehicleDesign) -> None:
    installed = {item.source_id for item in design.installed_items}
    for item in design.installed_items:
        raw = catalog_item(item.source_id)
        for conflict in raw.get("conflictsWith", []):
            if conflict in installed:
                raise ValueError(f"{item.source_id} conflicts with {conflict}")
    if sum(1 for item in design.installed_items if item.source_id == "charger") > 1:
                raise ValueError("charger only one may be fitted")


def _validate_vehicle_restrictions(design: VehicleDesign, item: dict[str, Any]) -> None:
    kinds = item.get("allowedVehicleKinds")
    if kinds and design.kind not in kinds:
        raise ValueError(f"{item['id']} cannot be fitted to {design.kind}")
    templates = item.get("allowedVehicleTemplates")
    if templates and design.template_id not in templates:
        raise ValueError(f"{item['id']} cannot be fitted to {design.template_id}")


def _require_known_cost_weight(item: dict[str, Any]) -> None:
    if item.get("cost") is None:
        raise ValueError(f"{item['id']} has no proofread purchase cost")
    if item.get("weight") is None:
        raise ValueError(f"{item['id']} has no proofread weight")
    if item.get("status") == "needsProofread" and (item.get("cost") is None or item.get("weight") is None):
        raise ValueError(f"{item['id']} needs proofread")


def add_reload(design: VehicleDesign, installed_item_id: str, kind: str) -> MagazineLoad:
    weapon = _installed_by_id(design, installed_item_id)
    if weapon.category != "weapons":
        raise ValueError("reloads can only be added to weapons")
    reload_row = _reload_for_weapon(weapon.source_id, kind)
    load = MagazineLoad(
        kind=kind,
        shots=int(reload_row["shots"]),
        source="reload",
        cost=int(reload_row["cost"]),
        weight=int(reload_row.get("weight", 0)),
    )
    weapon.magazines.append(load)
    _raise_if_over_payload(design)
    return load


def add_special_ammo(design: VehicleDesign, installed_item_id: str, ammo_id: str) -> MagazineLoad:
    weapon = _installed_by_id(design, installed_item_id)
    ammo = _ammo_type(ammo_id)
    if weapon.source_id not in ammo.get("compatibleWeapons", [weapon.source_id]):
        raise ValueError(f"{ammo_id} is not compatible with {weapon.source_id}")
    cost = ammo.get("cost")
    weight = ammo.get("weight")
    if cost is None:
        proofread = _proofread_reload_for_weapon(weapon.source_id, ammo_id)
        cost = proofread.get("cost")
        weight = 0 if weight is None else weight
    if cost is None:
        raise ValueError(f"{ammo_id} has no proofread purchase cost")
    if weight is None:
        raise ValueError(f"{ammo_id} has no proofread weight")
    load = MagazineLoad(
        kind=ammo_id,
        shots=1,
        source="specialAmmo",
        cost=int(cost),
        weight=int(weight),
    )
    weapon.magazines.append(load)
    _raise_if_over_payload(design)
    return load


def add_double_load(design: VehicleDesign, installed_item_id: str) -> None:
    weapon = _installed_by_id(design, installed_item_id)
    if weapon.double_load:
        raise ValueError("double-load facility already fitted")
    row = _double_load_for_weapon(weapon.source_id)
    added_weight = row.get("additionalWeight", row.get("addWeight"))
    if added_weight is None:
        raise ValueError(f"{weapon.source_id} double-load weight needs proofread")
    weapon.double_load = True
    weapon.cost += int(row["cost"])
    weapon.weight += int(added_weight)
    _raise_if_over_payload(design)


def _reload_for_weapon(weapon_id: str, kind: str) -> dict[str, Any]:
    for row in equipment_data().get("reloads", []):
        if row["weaponId"] == weapon_id and row["kind"] == kind:
            return row
    if kind.startswith("missile."):
        ammo = _ammo_type(kind)
        if ammo.get("cost") is None or ammo.get("weight") is None:
            raise ValueError(f"{kind} needsProofread")
        return {
            "weaponId": weapon_id,
            "kind": kind,
            "shots": 1,
            "cost": int(ammo["cost"]),
            "weight": int(ammo["weight"]),
        }
    raise ValueError(f"{weapon_id} has no {kind} reload row")


def _proofread_reload_for_weapon(weapon_id: str, kind: str) -> dict[str, Any]:
    aliases = {
        "depletedUranium": "depletedUranium",
        "shapedPlastic": "shapedPlastic",
        "phosphor": "phosphor",
        "gp": "gp",
        "he": "highExplosive",
    }
    proofread_kind = aliases.get(kind, kind)
    sections = proofread_data()["weaponsAndReloads"]
    for section_rows in sections.values():
        for weapon in section_rows:
            if weapon["id"] != weapon_id:
                continue
            for reload_row in weapon.get("reloads", []):
                if reload_row["id"] == proofread_kind:
                    return reload_row
    raise ValueError(f"{weapon_id} has no proofread {kind} reload row")


def _ammo_type(ammo_id: str) -> dict[str, Any]:
    for row in equipment_data().get("ammunitionTypes", []):
        if row["id"] == ammo_id:
            return row
    raise ValueError(f"unknown ammunition type {ammo_id}")


def _double_load_for_weapon(weapon_id: str) -> dict[str, Any]:
    for row in equipment_data().get("doubleLoadFacilities", []):
        if row["weaponId"] == weapon_id:
            return row
    raise ValueError(f"{weapon_id} has no double-load facility")


def link_weapons(
    design: VehicleDesign,
    installed_item_ids: list[str],
    group_id: str | None = None,
) -> str:
    if len(installed_item_ids) < 2:
        raise ValueError("linked groups require at least two weapons")
    weapons = [_installed_by_id(design, item_id) for item_id in installed_item_ids]
    if any(weapon.category != "weapons" for weapon in weapons):
        raise ValueError("only weapons can be linked")
    source_ids = {weapon.source_id for weapon in weapons}
    if len(source_ids) != 1:
        raise ValueError("linked weapons must be identical")
    turret_states = {_is_turret_mounted(design, weapon) for weapon in weapons}
    if len(turret_states) != 1:
        raise ValueError("turret weapons cannot be linked with fixed weapons")
    facings = {_link_facing(design, weapon) for weapon in weapons}
    if len(facings) != 1:
        raise ValueError("linked weapons must face the same direction")
    if {"front", "rear"}.issubset(facings):
        raise ValueError("front-facing and rear-facing weapons cannot be linked")
    linked_id = group_id or _new_id("link")
    design.linked_groups[linked_id] = [weapon.id for weapon in weapons]
    for weapon in weapons:
        weapon.linked_group_id = linked_id
    return linked_id


def _link_facing(design: VehicleDesign, weapon: InstalledItem) -> str:
    if _is_turret_mounted(design, weapon):
        return "turret"
    return weapon.facing or "front"


def _is_turret_mounted(design: VehicleDesign, weapon: InstalledItem) -> bool:
    mount = design.mounts.get(weapon.mount_id or "")
    return mount is not None and mount.kind == "turret"


def set_armour(
    design: VehicleDesign,
    facing: Facing,
    points: int,
    material: str = "carbonSteel",
) -> None:
    if facing not in FACINGS:
        raise ValueError(f"unknown armour facing {facing}")
    caps = equipment_data()["armour"]["caps"][design.kind]
    if points > int(caps[facing]):
        raise ValueError(f"{design.kind} {facing} armour cannot exceed {caps[facing]}")
    if material not in {"carbonSteel", "carbonPlastic"}:
        raise ValueError(f"unknown armour material {material}")
    design.armour[facing] = ArmourFacing(points, material)
    _raise_if_over_payload(design)


def armour_adjustment_cost_weight(design: VehicleDesign) -> tuple[int, int]:
    base = int(design.template["coreStats"]["armour"])
    total_cost = 0
    total_weight = 0
    side_pair: list[ArmourFacing] = []
    for facing, armour in design.armour.items():
        if design.kind == "car" and facing in {"leftSide", "rightSide"}:
            side_pair.append(armour)
            continue
        if armour.points < base:
            continue
        added = armour.points - base
        if added == 0 and armour.material == "carbonSteel":
            continue
        if armour.material == "carbonPlastic" and armour.points == base:
            conversion = _carbon_plastic_conversion(design)
            total_cost += int(conversion["cost"]) // len(FACINGS)
            total_weight += int(conversion["weightModifier"]) // len(FACINGS)
            continue
        row = _armour_row(design.kind, facing, armour.material)
        total_cost += int(row["cost"]) * added
        total_weight += int(row["weight"]) * added
    if side_pair:
        materials = {armour.material for armour in side_pair}
        added_points = {max(0, armour.points - base) for armour in side_pair}
        if len(materials) == 1 and len(added_points) == 1:
            material = next(iter(materials))
            added = next(iter(added_points))
            if added:
                row = _armour_row(design.kind, "leftSide", material)
                total_cost += int(row["cost"]) * added
                total_weight += int(row["weight"]) * added
        else:
            for armour in side_pair:
                added = max(0, armour.points - base)
                if added:
                    row = _armour_row(design.kind, "leftSide", armour.material)
                    total_cost += (int(row["cost"]) * added) // 2
                    total_weight += (int(row["weight"]) * added) // 2
    return total_cost, total_weight


def _armour_row(kind: str, facing: str, material: str) -> dict[str, Any]:
    table_name = "additionalCarbonSteel" if material == "carbonSteel" else "additionalCarbonPlastic"
    rows = proofread_data()["armour"][table_name][kind]
    target = _armour_target(kind, facing)
    for row in rows:
        if row["targetZone"] in {target, "any"}:
            return row
    raise ValueError(f"no proofread armour cost for {kind} {facing} {material}")


def _armour_target(kind: str, facing: str) -> str:
    if kind == "car" and facing in {"leftSide", "rightSide"}:
        return "sides"
    return facing


def _carbon_plastic_conversion(design: VehicleDesign) -> dict[str, Any]:
    label = str(design.template["label"])
    for row in proofread_data()["armour"]["carbonPlasticConversions"]:
        if row["vehicle"] == label:
            return row
    raise ValueError(f"no proofread carbon plastic conversion for {label}")


def summarize_design(design: VehicleDesign) -> DesignSummary:
    errors: list[str] = []
    try:
        _raise_if_over_payload(design)
    except ValueError as exc:
        errors.append(str(exc))
    armour_cost, armour_weight = armour_adjustment_cost_weight(design)
    item_cost = sum(item.cost + sum(load.cost for load in item.magazines) for item in design.installed_items)
    item_weight = sum(item.weight + sum(load.weight for load in item.magazines) for item in design.installed_items)
    total_cost = design.base_cost + item_cost + armour_cost
    total_weight = design.base_weight + item_weight + armour_weight
    try:
        stats = derived_stats(design, total_weight)
    except ValueError as exc:
        errors.append(str(exc))
        core = design.template["coreStats"]
        stats = VehicleStats(
            damage=int(core["damage"]),
            armour=int(core["armour"]),
            maximum_speed_mph=int(core["maximumSpeedMph"]),
            acceleration_mph=int(core["accelerationMph"]),
            braking_mph=int(core["brakingMph"]),
            handling=int(core["handling"]),
        )
    return DesignSummary(
        total_cost=total_cost,
        total_weight=total_weight,
        payload_used=item_weight + armour_weight,
        payload_limit=int(design.template["coreStats"]["payload"]) if design.design_mode == "corePayload" else 0,
        stats=stats,
        armour=dict(design.armour),
        legal=not errors,
        errors=tuple(errors),
    )


def derived_stats(design: VehicleDesign, total_weight: int | None = None) -> VehicleStats:
    core = design.template["coreStats"]
    if design.design_mode == "advancedWeight":
        weight = total_weight if total_weight is not None else summarize_design(design).total_weight
        if design.kind == "bike":
            stats = _bike_stats(weight)
            base_handling = int(core["handling"]) + int(stats["handlingModifier"])
            vehicle_stats = VehicleStats(
                damage=int(core["damage"]),
                armour=int(core["armour"]),
                maximum_speed_mph=int(stats["maximumSpeedMph"]),
                acceleration_mph=int(stats["accelerationMph"]),
                braking_mph=int(stats["brakingMph"]),
                handling=base_handling,
            )
        else:
            speed = _speed_stats(weight, design.engine_size or "")
            handling = _braking_handling_stats(weight, design.template_id)
            base_handling = int(core["handling"]) + int(handling["nonHeHandlingModifier"])
            vehicle_stats = VehicleStats(
                damage=int(core["damage"]),
                armour=int(core["armour"]),
                maximum_speed_mph=int(speed["maximumSpeedMph"]),
                acceleration_mph=int(speed["accelerationMph"]),
                braking_mph=int(handling["brakingMph"]),
                handling=base_handling,
                non_he_handling=base_handling,
                he_hit_handling=int(core["handling"]) + int(handling["heHitHandlingModifier"]),
            )
    else:
        vehicle_stats = VehicleStats(
            damage=int(core["damage"]),
            armour=int(core["armour"]),
            maximum_speed_mph=int(core["maximumSpeedMph"]),
            acceleration_mph=int(core["accelerationMph"]),
            braking_mph=int(core["brakingMph"]),
            handling=int(core["handling"]),
        )
    return _apply_system_effects(design, vehicle_stats)


def _speed_stats(weight: int, engine_size: str) -> dict[str, Any]:
    max_by_engine = proofread_data()["characteristics"]["maximumWeightByEngine"]
    if weight > int(max_by_engine[engine_size]):
        raise ValueError(f"{engine_size} cannot support total weight {weight}")
    for row in proofread_data()["characteristics"]["accelerationAndMaximumSpeed"]:
        if _weight_in_range(weight, row["weightRange"]):
            value = row[engine_size]
            if value is None:
                raise ValueError(f"no {engine_size} characteristics for total weight {weight}")
            return value
    raise ValueError(f"no acceleration/max-speed row for total weight {weight}")


def _braking_handling_stats(weight: int, template_id: str) -> dict[str, Any]:
    for row in proofread_data()["characteristics"]["brakingAndHandling"]:
        if _weight_in_range(weight, row["weightRange"]):
            return row[template_id]
    raise ValueError(f"no braking/handling row for total weight {weight}")


def _bike_stats(weight: int) -> dict[str, Any]:
    for row in proofread_data()["characteristics"]["bikes"]:
        if _weight_in_range(weight, row["weightRange"]):
            return row
    raise ValueError(f"no bike characteristics row for total weight {weight}")


def _weight_in_range(weight: int, weight_range: dict[str, Any]) -> bool:
    return weight >= int(weight_range.get("min", 0)) and weight <= int(weight_range["max"])


def _apply_system_effects(design: VehicleDesign, stats: VehicleStats) -> VehicleStats:
    acceleration = stats.acceleration_mph
    maximum = stats.maximum_speed_mph
    braking = stats.braking_mph
    handling_bonus = 0
    robotic_handling: int | None = None
    for installed in design.installed_items:
        raw = catalog_item(installed.source_id)
        effects = raw.get("effects", {})
        acceleration += int(effects.get("accelerationMph", 0))
        maximum += int(effects.get("maximumSpeedMph", 0))
        braking += int(effects.get("brakingMph", 0))
        if raw.get("system") == "roboticDrive":
            robotic_handling = int(effects.get("handling", 3))
        elif raw.get("system") == "activeSuspension":
            handling_bonus = max(handling_bonus, int(effects.get("handling", 0)))
        elif "handling" in effects:
            handling_bonus += int(effects["handling"])
    if robotic_handling is not None:
        handling_bonus = robotic_handling
    return VehicleStats(
        damage=stats.damage,
        armour=stats.armour,
        maximum_speed_mph=maximum,
        acceleration_mph=acceleration,
        braking_mph=braking,
        handling=stats.handling + handling_bonus,
        non_he_handling=None if stats.non_he_handling is None else stats.non_he_handling + handling_bonus,
        he_hit_handling=None if stats.he_hit_handling is None else stats.he_hit_handling + handling_bonus,
    )


def nox_active_stats(design: VehicleDesign) -> VehicleStats:
    stats = summarize_design(design).stats
    if not any(item.source_id == "nox" for item in design.installed_items):
        raise ValueError("nox is not fitted")
    max_bonus = 40 if design.kind == "car" else 10
    return VehicleStats(
        damage=stats.damage,
        armour=stats.armour,
        maximum_speed_mph=stats.maximum_speed_mph + max_bonus,
        acceleration_mph=stats.acceleration_mph * 2,
        braking_mph=stats.braking_mph,
        handling=stats.handling,
        non_he_handling=stats.non_he_handling,
        he_hit_handling=stats.he_hit_handling,
    )


def _raise_if_over_payload(design: VehicleDesign) -> None:
    if design.design_mode != "corePayload":
        return
    payload = summarize_design_no_validate(design).payload_used
    limit = int(design.template["coreStats"]["payload"])
    if payload > limit:
        raise ValueError("fitted equipment exceeds core payload")


def summarize_design_no_validate(design: VehicleDesign) -> DesignSummary:
    armour_cost, armour_weight = armour_adjustment_cost_weight(design)
    item_cost = sum(item.cost + sum(load.cost for load in item.magazines) for item in design.installed_items)
    item_weight = sum(item.weight + sum(load.weight for load in item.magazines) for item in design.installed_items)
    core = design.template["coreStats"]
    stats = VehicleStats(
        damage=int(core["damage"]),
        armour=int(core["armour"]),
        maximum_speed_mph=int(core["maximumSpeedMph"]),
        acceleration_mph=int(core["accelerationMph"]),
        braking_mph=int(core["brakingMph"]),
        handling=int(core["handling"]),
    )
    return DesignSummary(
        total_cost=design.base_cost + item_cost + armour_cost,
        total_weight=design.base_weight + item_weight + armour_weight,
        payload_used=item_weight + armour_weight,
        payload_limit=int(core["payload"]) if design.design_mode == "corePayload" else 0,
        stats=stats,
        armour=dict(design.armour),
        legal=True,
    )


def _installed_by_id(design: VehicleDesign, installed_item_id: str) -> InstalledItem:
    for item in design.installed_items:
        if item.id == installed_item_id:
            return item
    raise ValueError(f"unknown installed item {installed_item_id}")


def to_campaign_vehicle_kwargs(design: VehicleDesign) -> dict[str, Any]:
    summary = summarize_design(design)
    if not summary.legal:
        raise ValueError("; ".join(summary.errors))
    return {
        "label": design.label,
        "template_id": design.template_id,
        "value": summary.total_cost,
        "max_damage": summary.stats.damage,
    }


def validate_vehicle_design(spec: dict[str, Any]) -> dict[str, Any]:
    try:
        build_vehicle_design(spec)
    except VehicleDesignError as exc:
        return {"valid": False, "errors": [{"message": str(exc)}]}
    return {"valid": True, "errors": []}


def build_vehicle_design(spec: dict[str, Any]) -> dict[str, Any]:
    try:
        design = _design_from_spec(spec)
        summary = summarize_design(design)
        if not summary.legal:
            raise VehicleDesignError("; ".join(summary.errors))
        active_stats = None
        active_addons = set(spec.get("activeEngineAddOns", []))
        if "nox" in active_addons:
            active_stats = nox_active_stats(design)
        return _record_from_design(design, summary, active_stats)
    except VehicleDesignError:
        raise
    except ValueError as exc:
        raise VehicleDesignError(str(exc)) from exc


def _design_from_spec(spec: dict[str, Any]) -> VehicleDesign:
    mode = spec.get("designMode", "corePayload")
    template_id = str(spec.get("templateId", "interceptor"))
    if mode == "advancedWeight":
        if template_id == "bike":
            design = create_advanced_bike_design(str(spec.get("vehicleId", "Bike")))
        else:
            engine_size = str(spec.get("engineSize") or "v6")
            chassis_id = _chassis_id_for_template_engine(template_id, engine_size)
            design = create_advanced_design(chassis_id, str(spec.get("vehicleId", chassis_id)))
    else:
        design = create_core_design(template_id, str(spec.get("vehicleId", template_id)))
    for facing, armour in spec.get("armour", {}).items():
        set_armour(
            design,
            facing,
            int(armour["points"]),
            str(armour.get("material", "carbonSteel")),
        )
    for source_id in spec.get("mountUpgrades", []):
        install_item(design, str(source_id))
    for source_id in spec.get("engineAddOns", []):
        install_item(design, str(source_id))
    for source_id in spec.get("drivingSystems", []):
        install_item(design, str(source_id))
    for source_id in spec.get("safetyDevices", []):
        install_item(design, str(source_id))
    for row in spec.get("installedWeapons", []):
        weapon = install_item(
            design,
            str(row["weaponId"]),
            mount_id=str(row["mountId"]),
            facing=str(row.get("facing") or "front"),
            installed_id=str(row.get("id") or _new_id("weapon")),
        )
        _apply_weapon_ammo_spec(design, weapon, row)
    for row in spec.get("fireControlComputers", []):
        install_item(
            design,
            str(row["computerId"]),
            mount_id=str(row["mountId"]),
            installed_id=str(row.get("id") or _new_id("firecontrol")),
        )
    for group in spec.get("linkedGroups", []):
        link_weapons(
            design,
            [str(item_id) for item_id in group["weaponInstanceIds"]],
            str(group["id"]),
        )
    return design


def _chassis_id_for_template_engine(template_id: str, engine_size: str) -> str:
    for chassis in vehicles_data()["advancedChassis"]:
        if chassis["vehicleTemplateId"] == template_id and chassis["engineSize"] == engine_size:
            return str(chassis["id"])
    raise ValueError(f"no chassis for {template_id} {engine_size}")


def _apply_weapon_ammo_spec(
    design: VehicleDesign,
    weapon: InstalledItem,
    row: dict[str, Any],
) -> None:
    special_loads: list[MagazineLoad] = []
    for special in row.get("specialAmmo", []):
        for _ in range(int(special.get("count", 1))):
            special_loads.append(add_special_ammo(design, weapon.id, str(special["kind"])))
    if special_loads and weapon.magazines:
        starting = weapon.magazines[0]
        if isinstance(starting.shots, int) and starting.kind == "gp":
            remaining = max(0, starting.shots - len(special_loads))
            weapon.magazines = special_loads + [
                MagazineLoad(kind="gp", shots=remaining, source="included")
            ]
        else:
            weapon.magazines = special_loads + weapon.magazines
    for reload_row in row.get("reloads", []):
        for _ in range(int(reload_row.get("count", 1))):
            add_reload(design, weapon.id, str(reload_row["kind"]))
    if row.get("doubleLoad"):
        add_double_load(design, weapon.id)
    linked_group_id = row.get("linkedGroupId")
    if linked_group_id:
        weapon.linked_group_id = str(linked_group_id)


def _record_from_design(
    design: VehicleDesign,
    summary: DesignSummary,
    active_stats: VehicleStats | None,
) -> dict[str, Any]:
    stats = summary.stats
    record = {
        "vehicleId": design.id,
        "templateId": design.template_id,
        "designMode": design.design_mode,
        "engineSize": design.engine_size,
        "totalCost": summary.total_cost,
        "totalWeight": summary.total_weight,
        "payloadUsed": summary.payload_used,
        "payloadLimit": summary.payload_limit,
        "damageMax": stats.damage,
        "armour": stats.armour,
        "maximumSpeedMph": stats.maximum_speed_mph,
        "accelerationMph": stats.acceleration_mph,
        "brakingMph": stats.braking_mph,
        "baseHandling": _base_handling_for_record(design, summary.total_weight),
        "handling": stats.handling,
        "nonHeHandling": stats.non_he_handling if stats.non_he_handling is not None else stats.handling,
        "heHandling": stats.he_hit_handling if stats.he_hit_handling is not None else stats.handling,
        "armourByFacing": {
            facing: {"points": armour.points, "material": armour.material}
            for facing, armour in summary.armour.items()
        },
        "mounts": _record_mounts(design),
        "linkedGroups": [
            {"id": group_id, "weaponInstanceIds": list(item_ids)}
            for group_id, item_ids in design.linked_groups.items()
        ],
        "ammunitionMagazines": _record_magazines(design),
    }
    if active_stats is not None:
        record["activeAccelerationMph"] = active_stats.acceleration_mph
        record["activeMaximumSpeedMph"] = active_stats.maximum_speed_mph
    if any(item.source_id == "nox" for item in design.installed_items):
        record["noxExplosionRolls2d6"] = _nox_rolls(design)
    return record


def _base_handling_for_record(design: VehicleDesign, total_weight: int) -> int:
    stats = derived_stats(_copy_without_handling_systems(design), total_weight)
    return stats.handling


def _copy_without_handling_systems(design: VehicleDesign) -> VehicleDesign:
    copied = VehicleDesign(
        id=design.id,
        label=design.label,
        template_id=design.template_id,
        design_mode=design.design_mode,
        chassis_id=design.chassis_id,
        engine_size=design.engine_size,
        mounts=design.mounts,
        installed_items=[
            item
            for item in design.installed_items
            if catalog_item(item.source_id).get("system") not in {"activeSuspension", "roboticDrive"}
        ],
        armour=design.armour,
        base_cost=design.base_cost,
        base_weight=design.base_weight,
        linked_groups=design.linked_groups,
        notes=design.notes,
    )
    return copied


def _record_mounts(design: VehicleDesign) -> list[dict[str, Any]]:
    rows = []
    for mount in design.mounts.values():
        weapons = []
        for item in design.installed_items:
            if item.category == "weapons" and item.mount_id == mount.id:
                double_row = _double_load_row_or_none(item.source_id)
                weapons.append(
                    {
                        "id": item.id,
                        "weaponId": item.source_id,
                        "facing": item.facing,
                        "linkedGroupId": item.linked_group_id,
                        "doubleLoad": item.double_load,
                        "doubleLoadFacilityCost": int(double_row["cost"]) if item.double_load and double_row else 0,
                        "doubleLoadAdditionalWeight": int(double_row.get("additionalWeight", double_row.get("addWeight", 0))) if item.double_load and double_row else 0,
                    }
                )
        rows.append(
            {
                "mountId": mount.id,
                "kind": mount.kind,
                "installedWeapons": weapons,
            }
        )
    return rows


def _double_load_row_or_none(weapon_id: str) -> dict[str, Any] | None:
    try:
        return _double_load_for_weapon(weapon_id)
    except ValueError:
        return None


def _record_magazines(design: VehicleDesign) -> list[dict[str, Any]]:
    rows = []
    for item in design.installed_items:
        if item.category != "weapons":
            continue
        capacity = 0
        loads = []
        for load in item.magazines:
            if isinstance(load.shots, int):
                capacity += load.shots
            entry = {"kind": load.kind, "shots": load.shots}
            if load.source == "reload":
                entry["source"] = load.source
            loads.append(entry)
        rows.append(
            {
                "weaponInstanceId": item.id,
                "loads": loads,
                "capacityShots": capacity,
            }
        )
    return rows


def _nox_rolls(design: VehicleDesign) -> list[int]:
    has_charger = any(item.source_id == "charger" for item in design.installed_items)
    has_oil = any(item.source_id == "oilInjection" for item in design.installed_items)
    if has_charger and has_oil:
        return [2, 3, 11, 12]
    if has_charger:
        return [2, 11, 12]
    if has_oil:
        return [2, 3, 12]
    return [2, 12]

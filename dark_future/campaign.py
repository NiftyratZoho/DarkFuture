from __future__ import annotations

import json
from dataclasses import dataclass, field
from math import floor
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4


UnitKind = Literal["independentOp", "agency", "outlawGang", "renegadeOp"]
DriverRole = Literal["sanctioned", "outlaw", "renegade"]
InjuryState = Literal["unhurt", "hurt", "injured", "limbDisabled", "dead"]
EngagementType = Literal["intercept", "ambush", "pursuit"]
BountyResult = Literal["killed", "terminal_or_crashed"]

REPAIR_COST_PER_DAMAGE_POINT = 250
CRITICAL_REPAIR_COST = 250
HACK_REPAIR_COST = 500
STRIP_OWN_EQUIPMENT_COST = 250
AGENCY_NOVICE_LICENSE_COST = 5_000
AGENCY_RUNNING_COST = 10_000
EXPERIENCED_DRIVER_UPKEEP_RATE = 0.10
DATA_ROOT = Path(__file__).resolve().parent.parent / "data" / "rules"
STARTING_FUNDS = 100_000
STARTING_DRIVER_SKILL = 2

# Extracted from docs/rules/clean/campaign.md; still marked needsProofread there.
OUTLAW_BOUNTY_BY_DRIVE_SKILL = {
    2: 8_000,
    3: 12_000,
    4: 20_000,
    5: 40_000,
    6: 80_000,
    7: 120_000,
    8: 250_000,
    9: 500_000,
    10: 1_000_000,
}

MILEAGE_THRESHOLDS = (
    (200, 10),
    (120, 9),
    (60, 8),
    (40, 6),
    (20, 5),
    (10, 4),
    (5, 3),
    (0, 2),
)


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def drive_skill_for_mileage(mileage_points: int) -> int:
    for threshold, skill in MILEAGE_THRESHOLDS:
        if mileage_points >= threshold:
            return skill
    return 2


def media_visibility_for_kudos(kudos_points: int) -> str:
    if kudos_points <= 5:
        return "obscure"
    if kudos_points <= 10:
        return "known"
    if kudos_points <= 15:
        return "respected"
    if kudos_points <= 20:
        return "famous"
    if kudos_points <= 25:
        return "star"
    return "livingLegend"


@dataclass
class StoreItem:
    id: str
    label: str
    category: str
    value: int = 0
    source_id: str = ""
    purchase_cost: int = 0
    weight: int = 0
    mount_id: str | None = None
    damaged: bool = False
    status: str = "cleanedDraft"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "category": self.category,
            "value": self.value,
            "sourceId": self.source_id,
            "purchaseCost": self.purchase_cost,
            "weight": self.weight,
            "mountId": self.mount_id,
            "damaged": self.damaged,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StoreItem:
        return cls(
            id=str(data["id"]),
            label=str(data["label"]),
            category=str(data["category"]),
            value=int(data.get("value", 0)),
            source_id=str(data.get("sourceId", "")),
            purchase_cost=int(data.get("purchaseCost", data.get("value", 0))),
            weight=int(data.get("weight", 0)),
            mount_id=data.get("mountId"),
            damaged=bool(data.get("damaged", False)),
            status=str(data.get("status", "cleanedDraft")),
        )


@dataclass
class Driver:
    id: str
    name: str
    unit_id: str
    role: DriverRole
    drive_skill: int = 2
    mileage_points: int = 0
    psychosis_points: int = 0
    kudos_points: int = 0
    media_visibility: str = "obscure"
    injury_state: InjuryState = "unhurt"
    disorders: list[str] = field(default_factory=list)
    vehicle_ids: list[str] = field(default_factory=list)
    funds: int = 0
    experienced: bool = False
    own_vehicle_value: int = 0
    pending_media_psychosis: int = 0
    missed_sequences: int = 0
    temporary_effects: list[str] = field(default_factory=list)
    retired: bool = False

    def recalculate_progression(self) -> None:
        self.drive_skill = max(self.drive_skill, drive_skill_for_mileage(self.mileage_points))
        self.kudos_points = floor(self.mileage_points / 10)
        self.media_visibility = media_visibility_for_kudos(self.kudos_points)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "unitId": self.unit_id,
            "role": self.role,
            "driveSkill": self.drive_skill,
            "mileagePoints": self.mileage_points,
            "psychosisPoints": self.psychosis_points,
            "kudosPoints": self.kudos_points,
            "mediaVisibility": self.media_visibility,
            "injuryState": self.injury_state,
            "disorders": list(self.disorders),
            "vehicleIds": list(self.vehicle_ids),
            "funds": self.funds,
            "experienced": self.experienced,
            "ownVehicleValue": self.own_vehicle_value,
            "pendingMediaPsychosis": self.pending_media_psychosis,
            "missedSequences": self.missed_sequences,
            "temporaryEffects": list(self.temporary_effects),
            "retired": self.retired,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Driver:
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            unit_id=str(data["unitId"]),
            role=data.get("role", "sanctioned"),
            drive_skill=int(data.get("driveSkill", 2)),
            mileage_points=int(data.get("mileagePoints", 0)),
            psychosis_points=int(data.get("psychosisPoints", 0)),
            kudos_points=int(data.get("kudosPoints", 0)),
            media_visibility=str(data.get("mediaVisibility", "obscure")),
            injury_state=data.get("injuryState", "unhurt"),
            disorders=list(data.get("disorders", [])),
            vehicle_ids=list(data.get("vehicleIds", [])),
            funds=int(data.get("funds", 0)),
            experienced=bool(data.get("experienced", False)),
            own_vehicle_value=int(data.get("ownVehicleValue", 0)),
            pending_media_psychosis=int(data.get("pendingMediaPsychosis", 0)),
            missed_sequences=int(data.get("missedSequences", 0)),
            temporary_effects=list(data.get("temporaryEffects", [])),
            retired=bool(data.get("retired", False)),
        )


@dataclass
class VehicleRecord:
    id: str
    label: str
    unit_id: str
    owner_driver_id: str | None = None
    template_id: str = ""
    value: int = 0
    max_damage: int = 24
    current_damage: int = 24
    critical_hits: list[str] = field(default_factory=list)
    hack_damage_count: int = 0
    equipment: list[str] = field(default_factory=list)
    installed_items: list[StoreItem] = field(default_factory=list)
    payload_limit: int = 0
    payload_used: int = 0
    design_mode: str = "corePayload"
    roadworthy: bool = True
    written_off: bool = False

    @property
    def missing_damage(self) -> int:
        return max(0, self.max_damage - self.current_damage)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "unitId": self.unit_id,
            "ownerDriverId": self.owner_driver_id,
            "templateId": self.template_id,
            "value": self.value,
            "maxDamage": self.max_damage,
            "currentDamage": self.current_damage,
            "criticalHits": list(self.critical_hits),
            "hackDamageCount": self.hack_damage_count,
            "equipment": list(self.equipment),
            "installedItems": [item.to_dict() for item in self.installed_items],
            "payloadLimit": self.payload_limit,
            "payloadUsed": self.payload_used,
            "designMode": self.design_mode,
            "roadworthy": self.roadworthy,
            "writtenOff": self.written_off,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VehicleRecord:
        return cls(
            id=str(data["id"]),
            label=str(data["label"]),
            unit_id=str(data["unitId"]),
            owner_driver_id=data.get("ownerDriverId"),
            template_id=str(data.get("templateId", "")),
            value=int(data.get("value", 0)),
            max_damage=int(data.get("maxDamage", 24)),
            current_damage=int(data.get("currentDamage", 24)),
            critical_hits=list(data.get("criticalHits", [])),
            hack_damage_count=int(data.get("hackDamageCount", 0)),
            equipment=list(data.get("equipment", [])),
            installed_items=[
                StoreItem.from_dict(item) for item in data.get("installedItems", [])
            ],
            payload_limit=int(data.get("payloadLimit", 0)),
            payload_used=int(data.get("payloadUsed", 0)),
            design_mode=str(data.get("designMode", "corePayload")),
            roadworthy=bool(data.get("roadworthy", True)),
            written_off=bool(data.get("writtenOff", False)),
        )


@dataclass(frozen=True)
class CatalogItem:
    source_id: str
    label: str
    category: str
    cost: int
    weight: int
    item_class: str = ""
    sanctioned: bool = False
    status: str = "cleanedDraft"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class GarageReport:
    unit_id: str
    vehicle_id: str | None = None
    item_id: str | None = None
    spent: int = 0
    received: int = 0
    payload_used: int = 0
    payload_limit: int = 0


@dataclass
class RecruitmentLock:
    reason: str
    sequences_remaining: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "reason": self.reason,
            "sequencesRemaining": self.sequences_remaining,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecruitmentLock:
        return cls(
            reason=str(data["reason"]),
            sequences_remaining=int(data.get("sequencesRemaining", 1)),
        )


@dataclass
class UnitState:
    id: str
    name: str
    kind: UnitKind
    player_id: str
    funds: int = 100_000
    driver_ids: list[str] = field(default_factory=list)
    vehicle_ids: list[str] = field(default_factory=list)
    store: list[StoreItem] = field(default_factory=list)
    banked_funds: int = 0
    kudos_points: int = 0
    contracts_completed: int = 0
    failed_engagement_objective_count: int = 0
    active_this_sequence: bool = False
    pending_media_psychosis: int = 0
    recruitment_locks: list[RecruitmentLock] = field(default_factory=list)
    expenses_due: int = 0
    retired: bool = False

    def is_sanctioned(self) -> bool:
        return self.kind in ("independentOp", "agency")

    def is_outlaw(self) -> bool:
        return self.kind in ("outlawGang", "renegadeOp")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "playerId": self.player_id,
            "funds": self.funds,
            "driverIds": list(self.driver_ids),
            "vehicleIds": list(self.vehicle_ids),
            "store": [item.to_dict() for item in self.store],
            "bankedFunds": self.banked_funds,
            "kudosPoints": self.kudos_points,
            "contractsCompleted": self.contracts_completed,
            "failedEngagementObjectiveCount": self.failed_engagement_objective_count,
            "activeThisSequence": self.active_this_sequence,
            "pendingMediaPsychosis": self.pending_media_psychosis,
            "recruitmentLocks": [lock.to_dict() for lock in self.recruitment_locks],
            "expensesDue": self.expenses_due,
            "retired": self.retired,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UnitState:
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            kind=data["kind"],
            player_id=str(data["playerId"]),
            funds=int(data.get("funds", 100_000)),
            driver_ids=list(data.get("driverIds", [])),
            vehicle_ids=list(data.get("vehicleIds", [])),
            store=[StoreItem.from_dict(item) for item in data.get("store", [])],
            banked_funds=int(data.get("bankedFunds", 0)),
            kudos_points=int(data.get("kudosPoints", 0)),
            contracts_completed=int(data.get("contractsCompleted", 0)),
            failed_engagement_objective_count=int(data.get("failedEngagementObjectiveCount", 0)),
            active_this_sequence=bool(data.get("activeThisSequence", False)),
            pending_media_psychosis=int(data.get("pendingMediaPsychosis", 0)),
            recruitment_locks=[
                RecruitmentLock.from_dict(lock) for lock in data.get("recruitmentLocks", [])
            ],
            expenses_due=int(data.get("expensesDue", 0)),
            retired=bool(data.get("retired", False)),
        )


@dataclass(frozen=True)
class BountyClaim:
    unit_id: str
    enemy_drive_skill: int
    result: BountyResult

    def value(self) -> int:
        base = OUTLAW_BOUNTY_BY_DRIVE_SKILL[max(2, min(10, self.enemy_drive_skill))]
        if self.result == "terminal_or_crashed":
            return base // 2
        return base

    def to_dict(self) -> dict[str, Any]:
        return {
            "unitId": self.unit_id,
            "enemyDriveSkill": self.enemy_drive_skill,
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BountyClaim:
        return cls(
            unit_id=str(data["unitId"]),
            enemy_drive_skill=int(data["enemyDriveSkill"]),
            result=data["result"],
        )


@dataclass
class ContractOutcome:
    id: str
    attacker_unit_id: str
    defender_unit_id: str
    winner_unit_id: str | None = None
    engagement_type: EngagementType = "intercept"
    objective_satisfied: bool = True
    deliberate_objective_failure: bool = False
    participating_driver_ids: list[str] = field(default_factory=list)
    participating_vehicle_ids: list[str] = field(default_factory=list)
    surviving_driver_ids: list[str] = field(default_factory=list)
    killed_driver_ids: list[str] = field(default_factory=list)
    destroyed_vehicle_ids: list[str] = field(default_factory=list)
    terminal_vehicle_ids: list[str] = field(default_factory=list)
    bounty_claims: list[BountyClaim] = field(default_factory=list)
    loot_awards: dict[str, int] = field(default_factory=dict)
    mileage_awards: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "attackerUnitId": self.attacker_unit_id,
            "defenderUnitId": self.defender_unit_id,
            "winnerUnitId": self.winner_unit_id,
            "engagementType": self.engagement_type,
            "objectiveSatisfied": self.objective_satisfied,
            "deliberateObjectiveFailure": self.deliberate_objective_failure,
            "participatingDriverIds": list(self.participating_driver_ids),
            "participatingVehicleIds": list(self.participating_vehicle_ids),
            "survivingDriverIds": list(self.surviving_driver_ids),
            "killedDriverIds": list(self.killed_driver_ids),
            "destroyedVehicleIds": list(self.destroyed_vehicle_ids),
            "terminalVehicleIds": list(self.terminal_vehicle_ids),
            "bountyClaims": [claim.to_dict() for claim in self.bounty_claims],
            "lootAwards": dict(self.loot_awards),
            "mileageAwards": dict(self.mileage_awards),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContractOutcome:
        return cls(
            id=str(data["id"]),
            attacker_unit_id=str(data["attackerUnitId"]),
            defender_unit_id=str(data["defenderUnitId"]),
            winner_unit_id=data.get("winnerUnitId"),
            engagement_type=data.get("engagementType", "intercept"),
            objective_satisfied=bool(data.get("objectiveSatisfied", True)),
            deliberate_objective_failure=bool(data.get("deliberateObjectiveFailure", False)),
            participating_driver_ids=list(data.get("participatingDriverIds", [])),
            participating_vehicle_ids=list(data.get("participatingVehicleIds", [])),
            surviving_driver_ids=list(data.get("survivingDriverIds", [])),
            killed_driver_ids=list(data.get("killedDriverIds", [])),
            destroyed_vehicle_ids=list(data.get("destroyedVehicleIds", [])),
            terminal_vehicle_ids=list(data.get("terminalVehicleIds", [])),
            bounty_claims=[
                BountyClaim.from_dict(claim) for claim in data.get("bountyClaims", [])
            ],
            loot_awards={str(key): int(value) for key, value in data.get("lootAwards", {}).items()},
            mileage_awards={
                str(key): int(value) for key, value in data.get("mileageAwards", {}).items()
            },
        )


@dataclass
class SettlementReport:
    outcome_id: str
    funds_by_unit: dict[str, int] = field(default_factory=dict)
    mileage_by_driver: dict[str, int] = field(default_factory=dict)
    killed_driver_ids: list[str] = field(default_factory=list)
    written_off_vehicle_ids: list[str] = field(default_factory=list)
    objective_penalties: list[str] = field(default_factory=list)


@dataclass
class RepairEstimate:
    vehicle_id: str
    damage_points: int
    critical_hits: int
    hack_damage_count: int
    total_cost: int


@dataclass
class RepairReport:
    vehicle_id: str
    unit_id: str
    spent: int
    current_damage: int
    remaining_critical_hits: list[str]
    remaining_hack_damage_count: int


@dataclass
class CampaignState:
    sequence_number: int = 1
    units: dict[str, UnitState] = field(default_factory=dict)
    drivers: dict[str, Driver] = field(default_factory=dict)
    vehicles: dict[str, VehicleRecord] = field(default_factory=dict)
    contracts: list[ContractOutcome] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequenceNumber": self.sequence_number,
            "units": {unit_id: unit.to_dict() for unit_id, unit in self.units.items()},
            "drivers": {
                driver_id: driver.to_dict() for driver_id, driver in self.drivers.items()
            },
            "vehicles": {
                vehicle_id: vehicle.to_dict() for vehicle_id, vehicle in self.vehicles.items()
            },
            "contracts": [contract.to_dict() for contract in self.contracts],
            "logs": list(self.logs),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CampaignState:
        return cls(
            sequence_number=int(data.get("sequenceNumber", 1)),
            units={
                str(unit_id): UnitState.from_dict(unit)
                for unit_id, unit in data.get("units", {}).items()
            },
            drivers={
                str(driver_id): Driver.from_dict(driver)
                for driver_id, driver in data.get("drivers", {}).items()
            },
            vehicles={
                str(vehicle_id): VehicleRecord.from_dict(vehicle)
                for vehicle_id, vehicle in data.get("vehicles", {}).items()
            },
            contracts=[
                ContractOutcome.from_dict(contract) for contract in data.get("contracts", [])
            ],
            logs=list(data.get("logs", [])),
        )


def _load_rule_json(file_name: str) -> dict[str, Any]:
    with (DATA_ROOT / file_name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _vehicle_data() -> dict[str, Any]:
    return _load_rule_json("vehicles.json")


def _equipment_data() -> dict[str, Any]:
    return _load_rule_json("equipment.json")


def _template_by_id(template_id: str) -> dict[str, Any]:
    for template in _vehicle_data()["vehicleTemplates"]:
        if template["id"] == template_id:
            return template
    raise ValueError(f"unknown vehicle template {template_id}")


def _advanced_chassis_by_id(chassis_id: str) -> dict[str, Any]:
    for chassis in _vehicle_data()["advancedChassis"]:
        if chassis["id"] == chassis_id:
            return chassis
    raise ValueError(f"unknown chassis {chassis_id}")


def _equipment_catalog() -> dict[str, CatalogItem]:
    data = _equipment_data()
    catalog: dict[str, CatalogItem] = {}
    for category in (
        "weapons",
        "mountUpgrades",
        "engineAddOns",
        "drivingSystems",
        "fireControlComputers",
        "safetyDevices",
    ):
        for row in data.get(category, []):
            cost = row.get("cost")
            weight = row.get("weight")
            if cost is None or weight is None:
                status = row.get("status", "needsProofread")
            else:
                status = row.get("status", "cleanedDraft")
            catalog[row["id"]] = CatalogItem(
                source_id=row["id"],
                label=row.get("label", row["id"]),
                category=category,
                cost=-1 if cost is None else int(cost),
                weight=-1 if weight is None else int(weight),
                item_class=row.get("class", ""),
                sanctioned=bool(row.get("sanctioned", False)),
                status=status,
                raw=row,
            )
    for row in data.get("reloads", []):
        item_id = f"reload:{row['weaponId']}:{row['kind']}"
        catalog[item_id] = CatalogItem(
            source_id=item_id,
            label=f"{row['weaponId']} {row['kind']} reload",
            category="reloads",
            cost=int(row["cost"]),
            weight=0,
            status=row.get("status", "cleanedDraft"),
            raw=row,
        )
    for row in data.get("ammunitionTypes", []):
        if row.get("cost") is None:
            continue
        if row.get("weight") is None:
            status = row.get("status", "needsProofread")
            weight = -1
        else:
            status = row.get("status", "cleanedDraft")
            weight = int(row["weight"])
        catalog[f"ammo:{row['id']}"] = CatalogItem(
            source_id=f"ammo:{row['id']}",
            label=row.get("label", row["id"]),
            category="ammunitionTypes",
            cost=int(row["cost"]),
            weight=weight,
            status=status,
            raw=row,
        )
    return catalog


def _catalog_item(source_id: str) -> CatalogItem:
    catalog = _equipment_catalog()
    if source_id not in catalog:
        raise ValueError(f"unknown equipment item {source_id}")
    item = catalog[source_id]
    if item.cost < 0:
        raise ValueError(f"{source_id} has no proofread purchase cost")
    return item


def _require_known_weight(item: CatalogItem) -> None:
    if item.weight < 0:
        raise ValueError(f"{item.source_id} has no proofread weight")


def _outlaw_purchase_surcharge_percent() -> int:
    return int(_equipment_data().get("campaignPurchaseRules", {}).get(
        "outlawSanctionedItemSurchargePercent",
        0,
    ))


def campaign_purchase_price(unit: UnitState, item: CatalogItem) -> int:
    if unit.is_outlaw() and item.sanctioned:
        return item.cost + (item.cost * _outlaw_purchase_surcharge_percent() // 100)
    return item.cost


def _core_mount(template_id: str, mount_id: str) -> dict[str, Any]:
    template = _template_by_id(template_id)
    for mount in template.get("coreMounts", []):
        if mount["id"] == mount_id:
            return mount
    raise ValueError(f"{template_id} has no core mount {mount_id}")


def _vehicle_kind(template_id: str) -> str:
    return str(_template_by_id(template_id)["kind"])


def _item_class_for_mount(item: CatalogItem, template_id: str) -> str:
    if item.item_class == "lightweight" and _vehicle_kind(template_id) == "car":
        return "lightweightAsMedium"
    return item.item_class


def _validate_mount_fit(vehicle: VehicleRecord, item: CatalogItem, mount_id: str) -> None:
    if vehicle.written_off:
        raise ValueError("written-off vehicles cannot be re-equipped")
    if item.category != "weapons":
        return
    mount = _core_mount(vehicle.template_id, mount_id)
    item_class = _item_class_for_mount(item, vehicle.template_id)
    if item_class not in mount.get("allowedWeaponClasses", []):
        raise ValueError(f"{item.source_id} cannot be fitted to {mount_id}")
    if item.raw.get("coreTurretAllowed") is False and mount.get("kind") == "turret":
        raise ValueError(f"{item.source_id} cannot be fitted to a core turret")
    used_on_mount = sum(1 for installed in vehicle.installed_items if installed.mount_id == mount_id)
    if used_on_mount >= int(mount.get("capacity", 1)):
        raise ValueError(f"{mount_id} mount is already full")


def _validate_payload_after_fit(vehicle: VehicleRecord, extra_weight: int) -> None:
    if vehicle.design_mode != "corePayload":
        return
    if vehicle.payload_limit <= 0:
        raise ValueError("vehicle has no payload limit; recreate it from extracted vehicle data")
    if vehicle.payload_used + extra_weight > vehicle.payload_limit:
        raise ValueError("fitted equipment exceeds core payload")


def create_unit(
    campaign: CampaignState,
    unit_id: str,
    name: str,
    kind: UnitKind,
    player_id: str,
    funds: int = STARTING_FUNDS,
) -> UnitState:
    unit = UnitState(id=unit_id, name=name, kind=kind, player_id=player_id, funds=funds)
    campaign.units[unit.id] = unit
    campaign.logs.append(f"Created {kind} unit {name}.")
    return unit


def create_starting_unit(
    campaign: CampaignState,
    unit_id: str,
    name: str,
    kind: UnitKind,
    player_id: str,
) -> UnitState:
    unit = create_unit(campaign, unit_id, name, kind, player_id, STARTING_FUNDS)
    free_drivers = 2 if kind == "outlawGang" else 1 if kind in {"independentOp", "renegadeOp"} else 0
    for index in range(free_drivers):
        role: DriverRole = "outlaw" if unit.is_outlaw() else "sanctioned"
        driver = Driver(
            id=f"{unit_id}-driver-{index + 1}",
            name=f"{name} Driver {index + 1}",
            unit_id=unit.id,
            role=role,
            drive_skill=STARTING_DRIVER_SKILL,
        )
        campaign.drivers[driver.id] = driver
        unit.driver_ids.append(driver.id)
    if free_drivers:
        campaign.logs.append(f"{unit.name} starts with {free_drivers} free drive-skill {STARTING_DRIVER_SKILL} driver(s).")
    return unit


def add_vehicle(
    campaign: CampaignState,
    unit_id: str,
    label: str,
    vehicle_id: str | None = None,
    owner_driver_id: str | None = None,
    template_id: str = "",
    value: int = 0,
    max_damage: int = 24,
) -> VehicleRecord:
    unit = campaign.units[unit_id]
    payload_limit = 0
    if template_id:
        template = _template_by_id(template_id)
        core_stats = template["coreStats"]
        max_damage = int(core_stats["damage"])
        payload_limit = int(core_stats["payload"])
    vehicle = VehicleRecord(
        id=vehicle_id or _new_id("vehicle"),
        label=label,
        unit_id=unit_id,
        owner_driver_id=owner_driver_id,
        template_id=template_id,
        value=value,
        max_damage=max_damage,
        current_damage=max_damage,
        payload_limit=payload_limit,
    )
    campaign.vehicles[vehicle.id] = vehicle
    unit.vehicle_ids.append(vehicle.id)
    if owner_driver_id:
        campaign.drivers[owner_driver_id].vehicle_ids.append(vehicle.id)
    return vehicle


def purchase_chassis(
    campaign: CampaignState,
    unit_id: str,
    chassis_id: str,
    label: str,
    vehicle_id: str | None = None,
    owner_driver_id: str | None = None,
) -> VehicleRecord:
    chassis = _advanced_chassis_by_id(chassis_id)
    unit = campaign.units[unit_id]
    cost = int(chassis["cost"])
    if unit.funds < cost:
        raise ValueError("unit cannot afford chassis")
    unit.funds -= cost
    vehicle = add_vehicle(
        campaign,
        unit_id,
        label,
        vehicle_id=vehicle_id,
        owner_driver_id=owner_driver_id,
        template_id=str(chassis["vehicleTemplateId"]),
        value=cost,
    )
    vehicle.design_mode = "corePayload"
    campaign.logs.append(f"Purchased {chassis_id} chassis {label} for ${cost}.")
    return vehicle


def purchase_equipment_to_store(
    campaign: CampaignState,
    unit_id: str,
    source_id: str,
    store_item_id: str | None = None,
) -> StoreItem:
    unit = campaign.units[unit_id]
    item = _catalog_item(source_id)
    price = campaign_purchase_price(unit, item)
    if unit.funds < price:
        raise ValueError("unit cannot afford equipment")
    unit.funds -= price
    stored = StoreItem(
        id=store_item_id or _new_id("item"),
        label=item.label,
        category=item.category,
        value=item.cost,
        source_id=item.source_id,
        purchase_cost=price,
        weight=max(0, item.weight),
        status=item.status,
    )
    unit.store.append(stored)
    campaign.logs.append(f"Purchased {item.label} for {unit.name} at ${price}.")
    return stored


def fit_store_item_to_vehicle(
    campaign: CampaignState,
    unit_id: str,
    vehicle_id: str,
    store_item_id: str,
    mount_id: str | None = None,
) -> GarageReport:
    unit = campaign.units[unit_id]
    vehicle = campaign.vehicles[vehicle_id]
    if vehicle.unit_id != unit_id:
        raise ValueError("vehicle does not belong to unit")
    stored = next((item for item in unit.store if item.id == store_item_id), None)
    if stored is None:
        raise ValueError("item is not in the unit store")
    catalog_item = _catalog_item(stored.source_id)
    _require_known_weight(catalog_item)
    if catalog_item.category == "weapons":
        if mount_id is None:
            raise ValueError("weapon fitting requires a mount id")
        _validate_mount_fit(vehicle, catalog_item, mount_id)
    _validate_payload_after_fit(vehicle, catalog_item.weight)
    unit.store.remove(stored)
    stored.mount_id = mount_id
    vehicle.installed_items.append(stored)
    vehicle.equipment.append(stored.source_id)
    vehicle.payload_used += catalog_item.weight
    vehicle.value += stored.purchase_cost
    campaign.logs.append(f"Fitted {stored.label} to {vehicle.label}.")
    return GarageReport(
        unit_id=unit.id,
        vehicle_id=vehicle.id,
        item_id=stored.id,
        payload_used=vehicle.payload_used,
        payload_limit=vehicle.payload_limit,
    )


def strip_vehicle_item_to_store(
    campaign: CampaignState,
    unit_id: str,
    vehicle_id: str,
    installed_item_id: str,
) -> GarageReport:
    unit = campaign.units[unit_id]
    vehicle = campaign.vehicles[vehicle_id]
    if vehicle.unit_id != unit_id:
        raise ValueError("vehicle does not belong to unit")
    if unit.funds < STRIP_OWN_EQUIPMENT_COST:
        raise ValueError("unit cannot afford stripping cost")
    installed = next((item for item in vehicle.installed_items if item.id == installed_item_id), None)
    if installed is None:
        raise ValueError("item is not fitted to vehicle")
    unit.funds -= STRIP_OWN_EQUIPMENT_COST
    vehicle.installed_items.remove(installed)
    if installed.source_id in vehicle.equipment:
        vehicle.equipment.remove(installed.source_id)
    vehicle.payload_used = max(0, vehicle.payload_used - installed.weight)
    installed.mount_id = None
    unit.store.append(installed)
    campaign.logs.append(f"Stripped {installed.label} from {vehicle.label} for $250.")
    return GarageReport(
        unit_id=unit.id,
        vehicle_id=vehicle.id,
        item_id=installed.id,
        spent=STRIP_OWN_EQUIPMENT_COST,
        payload_used=vehicle.payload_used,
        payload_limit=vehicle.payload_limit,
    )


def sell_store_item(
    campaign: CampaignState,
    unit_id: str,
    store_item_id: str,
    die_roll: int,
) -> GarageReport:
    if not 1 <= die_roll <= 6:
        raise ValueError("sale die roll must be 1-6")
    unit = campaign.units[unit_id]
    stored = next((item for item in unit.store if item.id == store_item_id), None)
    if stored is None:
        raise ValueError("item is not in the unit store")
    catalog_item = _catalog_item(stored.source_id)
    if stored.category not in ("weapons", "mountUpgrades", "engineAddOns", "reloads"):
        raise ValueError("this equipment category cannot be sold from stores with current extracted rules")
    base = catalog_item.cost
    if unit.is_outlaw() and catalog_item.sanctioned:
        base = campaign_purchase_price(unit, catalog_item)
    offer = (base * (die_roll + 3)) // 10
    unit.store.remove(stored)
    unit.funds += offer
    campaign.logs.append(f"Sold {stored.label} for ${offer}.")
    return GarageReport(unit_id=unit.id, item_id=stored.id, received=offer)


def recruit_novice_driver(
    campaign: CampaignState,
    unit_id: str,
    name: str,
    driver_id: str | None = None,
) -> Driver:
    unit = campaign.units[unit_id]
    if unit.recruitment_locks:
        raise ValueError(f"{unit.name} cannot recruit while recruitment is locked")
    if unit.kind == "agency":
        if unit.funds < AGENCY_NOVICE_LICENSE_COST:
            raise ValueError("agency cannot afford novice licence")
        unit.funds -= AGENCY_NOVICE_LICENSE_COST
    role: DriverRole = "outlaw" if unit.is_outlaw() else "sanctioned"
    driver = Driver(
        id=driver_id or _new_id("driver"),
        name=name,
        unit_id=unit_id,
        role=role,
        drive_skill=2,
    )
    campaign.drivers[driver.id] = driver
    unit.driver_ids.append(driver.id)
    campaign.logs.append(f"Recruited novice driver {name} for {unit.name}.")
    return driver


def recruit_experienced_driver_stub(
    campaign: CampaignState,
    unit_id: str,
    name: str,
    drive_skill: int,
    own_vehicle_value: int,
    driver_id: str | None = None,
) -> Driver:
    if not 3 <= drive_skill <= 10:
        raise ValueError("experienced driver drive skill must be 3-10")
    unit = campaign.units[unit_id]
    if unit.recruitment_locks:
        raise ValueError(f"{unit.name} cannot recruit while recruitment is locked")
    role: DriverRole = "outlaw" if unit.is_outlaw() else "sanctioned"
    driver = Driver(
        id=driver_id or _new_id("driver"),
        name=name,
        unit_id=unit_id,
        role=role,
        drive_skill=drive_skill,
        mileage_points=_minimum_mileage_for_skill(drive_skill),
        funds=2_000 * drive_skill,
        experienced=True,
        own_vehicle_value=own_vehicle_value,
    )
    driver.recalculate_progression()
    campaign.drivers[driver.id] = driver
    unit.driver_ids.append(driver.id)
    unit.expenses_due += experienced_driver_upkeep(driver)
    campaign.logs.append(f"Generated experienced driver {name} for {unit.name}.")
    return driver


def experienced_driver_upkeep(driver: Driver) -> int:
    if not driver.experienced:
        return 0
    return int(driver.own_vehicle_value * EXPERIENCED_DRIVER_UPKEEP_RATE)


def _minimum_mileage_for_skill(drive_skill: int) -> int:
    candidates = [threshold for threshold, skill in MILEAGE_THRESHOLDS if skill == drive_skill]
    if candidates:
        return min(candidates)
    lower = [threshold for threshold, skill in MILEAGE_THRESHOLDS if skill < drive_skill]
    return max(lower) if lower else 0


def repair_cost(
    vehicle: VehicleRecord,
    damage_points: int | None = None,
    critical_hits: int | None = None,
    hack_damage_count: int | None = None,
) -> RepairEstimate:
    if vehicle.written_off:
        return RepairEstimate(vehicle.id, 0, 0, 0, 0)
    points = vehicle.missing_damage if damage_points is None else max(0, damage_points)
    crits = len(vehicle.critical_hits) if critical_hits is None else max(0, critical_hits)
    hacks = vehicle.hack_damage_count if hack_damage_count is None else max(0, hack_damage_count)
    points = min(points, vehicle.missing_damage)
    crits = min(crits, len(vehicle.critical_hits))
    hacks = min(hacks, vehicle.hack_damage_count)
    total = (
        points * REPAIR_COST_PER_DAMAGE_POINT
        + crits * CRITICAL_REPAIR_COST
        + hacks * HACK_REPAIR_COST
    )
    return RepairEstimate(vehicle.id, points, crits, hacks, total)


def repair_vehicle(
    campaign: CampaignState,
    unit_id: str,
    vehicle_id: str,
    damage_points: int | None = None,
    critical_hits: int | None = None,
    hack_damage_count: int | None = None,
) -> RepairReport:
    unit = campaign.units[unit_id]
    vehicle = campaign.vehicles[vehicle_id]
    if vehicle.unit_id != unit_id:
        raise ValueError("vehicle does not belong to unit")
    if vehicle.written_off:
        raise ValueError("written-off vehicles cannot be repaired")
    estimate = repair_cost(vehicle, damage_points, critical_hits, hack_damage_count)
    if unit.funds < estimate.total_cost:
        raise ValueError("unit cannot afford repair")
    unit.funds -= estimate.total_cost
    vehicle.current_damage = min(vehicle.max_damage, vehicle.current_damage + estimate.damage_points)
    del vehicle.critical_hits[: estimate.critical_hits]
    vehicle.hack_damage_count -= estimate.hack_damage_count
    vehicle.roadworthy = vehicle.current_damage > 0 and not vehicle.critical_hits
    campaign.logs.append(f"Repaired {vehicle.label} for ${estimate.total_cost}.")
    return RepairReport(
        vehicle_id=vehicle.id,
        unit_id=unit.id,
        spent=estimate.total_cost,
        current_damage=vehicle.current_damage,
        remaining_critical_hits=list(vehicle.critical_hits),
        remaining_hack_damage_count=vehicle.hack_damage_count,
    )


def settle_post_engagement(
    campaign: CampaignState,
    outcome: ContractOutcome,
) -> SettlementReport:
    report = SettlementReport(outcome_id=outcome.id)
    campaign.contracts.append(outcome)
    involved_unit_ids = {outcome.attacker_unit_id, outcome.defender_unit_id}

    objective_forfeits = (
        outcome.deliberate_objective_failure and not outcome.objective_satisfied
    )
    if objective_forfeits:
        attacker = campaign.units[outcome.attacker_unit_id]
        attacker.failed_engagement_objective_count += 1
        report.objective_penalties.append(outcome.attacker_unit_id)
        campaign.logs.append(f"{attacker.name} failed its engagement objective deliberately.")

    for driver_id in outcome.killed_driver_ids:
        driver = campaign.drivers[driver_id]
        driver.injury_state = "dead"
        driver.retired = True
        report.killed_driver_ids.append(driver_id)

    for vehicle_id in outcome.destroyed_vehicle_ids:
        vehicle = campaign.vehicles[vehicle_id]
        vehicle.roadworthy = False
        vehicle.current_damage = 0

    for vehicle_id in outcome.terminal_vehicle_ids:
        vehicle = campaign.vehicles[vehicle_id]
        vehicle.roadworthy = False
        vehicle.written_off = True
        report.written_off_vehicle_ids.append(vehicle_id)

    if not objective_forfeits:
        for claim in outcome.bounty_claims:
            unit = campaign.units[claim.unit_id]
            value = claim.value()
            unit.funds += value
            report.funds_by_unit[unit.id] = report.funds_by_unit.get(unit.id, 0) + value

        for unit_id, value in outcome.loot_awards.items():
            unit = campaign.units[unit_id]
            unit.funds += value
            report.funds_by_unit[unit.id] = report.funds_by_unit.get(unit.id, 0) + value

        for driver_id in outcome.surviving_driver_ids:
            driver = campaign.drivers[driver_id]
            if driver_id in outcome.participating_driver_ids:
                mileage = outcome.mileage_awards.get(driver_id, 1)
                driver.mileage_points += mileage
                driver.recalculate_progression()
                report.mileage_by_driver[driver_id] = mileage

    for unit_id in involved_unit_ids:
        unit = campaign.units[unit_id]
        unit.contracts_completed += 1
        unit.active_this_sequence = True
        unit.kudos_points = sum(campaign.drivers[driver_id].kudos_points for driver_id in unit.driver_ids)

    campaign.logs.append(f"Settled contract {outcome.id}.")
    return report


def pay_sequence_expenses(campaign: CampaignState, unit_id: str) -> int:
    unit = campaign.units[unit_id]
    due = unit.expenses_due
    if unit.kind == "agency" and len(unit.driver_ids) > 1:
        due += AGENCY_RUNNING_COST
    for driver_id in unit.driver_ids:
        due += experienced_driver_upkeep(campaign.drivers[driver_id])
    if due > unit.funds:
        raise ValueError("unit cannot afford sequence expenses")
    unit.funds -= due
    unit.expenses_due = 0
    return due

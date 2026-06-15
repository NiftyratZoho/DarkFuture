import dataclasses
import unittest

try:
    from dark_future import vehicle_design
except ImportError as exc:
    vehicle_design = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


REQUIRED_API = (
    "VehicleDesignError",
    "build_vehicle_design",
    "validate_vehicle_design",
    "vehicle_template",
    "load_vehicle_design_rules",
)


def plain(value):
    if dataclasses.is_dataclass(value):
        return plain(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if hasattr(value, "__dict__"):
        return plain(vars(value))
    return value


def by_id(rows, row_id):
    if isinstance(rows, dict):
        return rows[row_id]
    for row in rows:
        if row.get("id") == row_id or row.get("mountId") == row_id:
            return row
    raise AssertionError(f"Could not find row id {row_id!r} in {rows!r}")


def weapon_entry(record, weapon_id):
    for mount in record["mounts"]:
        for installed in mount.get("installedWeapons", []):
            if installed["weaponId"] == weapon_id:
                return installed
    raise AssertionError(f"Could not find installed weapon {weapon_id!r}")


def magazine(record, weapon_instance_id):
    for row in record["ammunitionMagazines"]:
        if row["weaponInstanceId"] == weapon_instance_id:
            return row
    raise AssertionError(f"Could not find magazine for {weapon_instance_id!r}")


@unittest.skipIf(vehicle_design is not None, "backend import succeeded")
class MissingVehicleDesignBackendTests(unittest.TestCase):
    def test_expected_vehicle_design_backend_api_names_are_explicit(self):
        self.fail(
            "Expected backend module dark_future.vehicle_design with API: "
            + ", ".join(REQUIRED_API)
            + f". Import failed with: {IMPORT_ERROR!r}"
        )


@unittest.skipIf(vehicle_design is None, "dark_future.vehicle_design backend is not present yet")
class VehicleDesignBackendTests(unittest.TestCase):
    def assert_invalid(self, spec, message_pattern):
        with self.assertRaisesRegex(vehicle_design.VehicleDesignError, message_pattern):
            vehicle_design.build_vehicle_design(spec)

    def build(self, spec):
        return plain(vehicle_design.build_vehicle_design(spec))

    def core_spec(self, template_id="interceptor", **overrides):
        spec = {
            "vehicleId": "test-car",
            "templateId": template_id,
            "designMode": "corePayload",
            "ownerSide": "agency",
            "installedWeapons": [],
            "mountUpgrades": [],
            "engineAddOns": [],
            "drivingSystems": [],
            "safetyDevices": [],
            "armour": {},
            "linkedGroups": [],
        }
        spec.update(overrides)
        return spec

    def advanced_spec(self, template_id="interceptor", engine_size="v12", **overrides):
        spec = self.core_spec(template_id, **overrides)
        spec["designMode"] = "advancedWeight"
        spec["engineSize"] = engine_size
        return spec

    def test_required_backend_api_is_available(self):
        missing = [name for name in REQUIRED_API if not hasattr(vehicle_design, name)]
        self.assertEqual(missing, [])

    def test_core_template_stats_payload_and_mounts_are_loaded(self):
        renegade = plain(vehicle_design.vehicle_template("renegade"))
        interceptor = plain(vehicle_design.vehicle_template("interceptor"))
        bike = plain(vehicle_design.vehicle_template("bike"))

        self.assertEqual(renegade["coreStats"]["damage"], 18)
        self.assertEqual(renegade["coreStats"]["armour"], 3)
        self.assertEqual(renegade["coreStats"]["maximumSpeedMph"], 100)
        self.assertEqual(renegade["coreStats"]["accelerationMph"], 20)
        self.assertEqual(renegade["coreStats"]["brakingMph"], 30)
        self.assertEqual(renegade["coreStats"]["handling"], 4)
        self.assertEqual(renegade["coreStats"]["payload"], 650)

        self.assertEqual(len([m for m in interceptor["coreMounts"] if m["kind"] == "ordinary"]), 6)
        self.assertEqual(len([m for m in interceptor["coreMounts"] if m["kind"] == "passive"]), 2)
        self.assertEqual(len([m for m in bike["coreMounts"] if m["kind"] == "ordinary"]), 2)
        self.assertEqual(len([m for m in bike["coreMounts"] if m["kind"] == "passive"]), 1)

    def test_core_payload_tracks_exact_limit_and_rejects_excess(self):
        legal = self.build(
            self.core_spec(
                installedWeapons=[
                    {"id": "chain-1", "weaponId": "chainGun", "mountId": "hood", "facing": "front"},
                    {"id": "laser-1", "weaponId": "heavyLaser", "mountId": "roof", "facing": "front"},
                    {"id": "smoke-1", "weaponId": "smokeLayer", "mountId": "passiveLeft", "facing": "rear"},
                    {"id": "oil-1", "weaponId": "oilLayer", "mountId": "passiveRight", "facing": "rear"},
                    {"id": "laser-2", "weaponId": "combatLaser", "mountId": "leftSide", "facing": "front"},
                    {"id": "laser-3", "weaponId": "combatLaser", "mountId": "rightSide", "facing": "front"},
                ],
            )
        )

        self.assertEqual(legal["payloadLimit"], 850)
        self.assertEqual(legal["payloadUsed"], 825)

        self.assert_invalid(
            self.core_spec(
                installedWeapons=[
                    {"id": "chain-1", "weaponId": "chainGun", "mountId": "hood", "facing": "front"},
                    {"id": "missile-1", "weaponId": "missilePod", "mountId": "roof", "facing": "front"},
                    {"id": "chain-2", "weaponId": "chainGun", "mountId": "leftSide", "facing": "front"},
                ],
            ),
            "exceeds core payload",
        )

    def test_proofread_missile_cost_weight_rows_are_usable_for_loadout(self):
        record = self.build(
            self.advanced_spec(
                installedWeapons=[
                    {
                        "id": "missile-1",
                        "weaponId": "missilePod",
                        "mountId": "hood",
                        "facing": "front",
                        "reloads": [
                            {"kind": "missile.cannister", "count": 1},
                            {"kind": "missile.smoke", "count": 1},
                            {"kind": "missile.tgsm", "count": 1},
                        ],
                    }
                ],
            )
        )
        ammo = magazine(record, "missile-1")
        self.assertEqual(
            ammo["loads"],
            [
                {"kind": "missile.he", "shots": 6},
                {"kind": "missile.cannister", "shots": 1, "source": "reload"},
                {"kind": "missile.smoke", "shots": 1, "source": "reload"},
                {"kind": "missile.tgsm", "shots": 1, "source": "reload"},
            ],
        )
        self.assertEqual(record["totalCost"], 139_500)
        self.assertEqual(record["totalWeight"], 1390)

    def test_proofread_wlf_bike_safety_and_drive_systems_are_usable(self):
        record = self.build(
            self.advanced_spec(
                template_id="bike",
                engine_size=None,
                safetyDevices=["crashBars"],
                drivingSystems=["twoWheelDrive", "computerDrive"],
            )
        )

        self.assertEqual(record["totalCost"], 20_500)
        self.assertEqual(record["totalWeight"], 200)
        self.assertEqual(record["accelerationMph"], 65)
        self.assertEqual(record["brakingMph"], 65)
        self.assertEqual(record["handling"], 9)

    def test_mount_legality_for_heavy_passive_and_bike_weapons(self):
        heavy_side = self.build(
            self.core_spec(
                installedWeapons=[
                    {"id": "chain-1", "weaponId": "chainGun", "mountId": "leftSide", "facing": "front"}
                ]
            )
        )
        self.assertEqual(by_id(heavy_side["mounts"], "leftSide")["installedWeapons"][0]["weaponId"], "chainGun")

        self.assert_invalid(
            self.core_spec(
                installedWeapons=[
                    {"id": "chain-1", "weaponId": "chainGun", "mountId": "leftWing", "facing": "front"}
                ]
            ),
            "heavy.*wing|leftWing.*heavy",
        )
        self.assert_invalid(
            self.core_spec(
                installedWeapons=[
                    {"id": "smoke-1", "weaponId": "smokeLayer", "mountId": "hood", "facing": "rear"}
                ]
            ),
            "passive.*ordinary|hood.*passive",
        )
        self.assert_invalid(
            self.core_spec(
                installedWeapons=[
                    {"id": "mg-1", "weaponId": "machineGun6mm", "mountId": "passiveLeft", "facing": "rear"}
                ]
            ),
            "ordinary.*passive|passiveLeft.*ordinary",
        )
        self.assert_invalid(
            self.core_spec(
                template_id="bike",
                installedWeapons=[
                    {"id": "mg-1", "weaponId": "machineGun6mm", "mountId": "leftFairing", "facing": "front"}
                ],
            ),
            "bike.*lightweight|leftFairing.*lightweight",
        )

    def test_turret_capacity_and_missile_exclusion(self):
        two_medium = self.build(
            self.core_spec(
                mountUpgrades=["turret"],
                installedWeapons=[
                    {"id": "mg-1", "weaponId": "machineGun6mm", "mountId": "turret", "facing": "front"},
                    {"id": "laser-1", "weaponId": "combatLaser", "mountId": "turret", "facing": "front"},
                ],
            )
        )
        self.assertEqual(len(by_id(two_medium["mounts"], "turret")["installedWeapons"]), 2)

        self.assert_invalid(
            self.core_spec(
                mountUpgrades=["turret"],
                installedWeapons=[
                    {"id": "chain-1", "weaponId": "chainGun", "mountId": "turret", "facing": "front"},
                    {"id": "mg-1", "weaponId": "machineGun6mm", "mountId": "turret", "facing": "front"},
                ],
            ),
            "turret.*capacity|capacity.*turret",
        )
        self.assert_invalid(
            self.core_spec(
                mountUpgrades=["turret"],
                installedWeapons=[
                    {"id": "missile-1", "weaponId": "missilePod", "mountId": "turret", "facing": "front"}
                ],
            ),
            "turret.*missile|missile.*turret",
        )

    def test_cupola_pintle_and_fire_computer_validation_uses_wlf_text_rules(self):
        cupola = self.build(
            self.core_spec(
                mountUpgrades=["cupola"],
                installedWeapons=[
                    {"id": "mg-1", "weaponId": "machineGun6mm", "mountId": "cupola", "facing": "rear"}
                ],
                fireControlComputers=[
                    {"id": "tfc-1", "computerId": "turretFireComputer", "mountId": "cupola"}
                ],
            )
        )
        cupola_mount = by_id(cupola["mounts"], "cupola")
        self.assertEqual(cupola_mount["installedWeapons"][0]["weaponId"], "machineGun6mm")

        self.assert_invalid(
            self.core_spec(
                mountUpgrades=["pintle"],
                installedWeapons=[
                    {"id": "mg-1", "weaponId": "machineGun6mm", "mountId": "pintle", "facing": "rear"}
                ],
                fireControlComputers=[
                    {"id": "tfc-1", "computerId": "turretFireComputer", "mountId": "pintle"}
                ],
            ),
            "turret fire computer.*turret or cupola|compatible turret or cupola",
        )
        self.assert_invalid(
            self.core_spec(
                mountUpgrades=["turret"],
                installedWeapons=[
                    {"id": "missile-1", "weaponId": "missilePod", "mountId": "turret", "facing": "front"}
                ],
                fireControlComputers=[
                    {"id": "tfc-1", "computerId": "turretFireComputer", "mountId": "missile-1"}
                ],
            ),
            "missile.*turret|turret.*missile",
        )

    def test_rear_hardpoints_use_proofread_capacity_and_facing_rules(self):
        interceptor = self.build(
            self.core_spec(
                mountUpgrades=["rearLeftWing", "tailgate", "rearRightWing"],
                installedWeapons=[
                    {"id": "chain-1", "weaponId": "chainGun", "mountId": "rearLeftWing", "facing": "front"},
                    {"id": "mg-1", "weaponId": "machineGun6mm", "mountId": "tailgate", "facing": "rear"},
                    {"id": "chain-2", "weaponId": "chainGun", "mountId": "rearRightWing", "facing": "rear"},
                ],
            )
        )
        self.assertEqual(by_id(interceptor["mounts"], "rearLeftWing")["installedWeapons"][0]["facing"], "front")
        self.assertEqual(by_id(interceptor["mounts"], "tailgate")["installedWeapons"][0]["facing"], "rear")
        self.assertEqual(by_id(interceptor["mounts"], "rearRightWing")["installedWeapons"][0]["facing"], "rear")

        self.assert_invalid(
            self.core_spec(
                mountUpgrades=["rearLeftWing"],
                template_id="renegade",
                installedWeapons=[
                    {"id": "mg-1", "weaponId": "machineGun6mm", "mountId": "rearLeftWing", "facing": "front"}
                ],
            ),
            "rearLeftWing.*cannot face front|cannot face front",
        )
        self.assert_invalid(
            self.core_spec(
                mountUpgrades=["tailgate"],
                installedWeapons=[
                    {"id": "mg-1", "weaponId": "machineGun6mm", "mountId": "tailgate", "facing": "front"}
                ],
            ),
            "tailgate.*cannot face front|cannot face front",
        )

    def test_engine_add_ons_apply_charger_nox_and_oil_effects(self):
        base = self.build(self.advanced_spec(engine_size="v12"))
        charger = self.build(self.advanced_spec(engine_size="v12", engineAddOns=["charger"]))
        oil = self.build(self.advanced_spec(engine_size="v12", engineAddOns=["oilInjection"]))
        nox = self.build(self.advanced_spec(engine_size="v12", engineAddOns=["nox"], activeEngineAddOns=["nox"]))
        all_addons = self.build(
            self.advanced_spec(
                engine_size="v12",
                engineAddOns=["charger", "nox", "oilInjection"],
                activeEngineAddOns=["nox", "oilInjection"],
            )
        )

        self.assertEqual(charger["accelerationMph"], base["accelerationMph"] + 4)
        self.assertEqual(charger["maximumSpeedMph"], base["maximumSpeedMph"] + 16)
        self.assertEqual(oil["accelerationMph"], base["accelerationMph"] - 2)
        self.assertEqual(oil["maximumSpeedMph"], base["maximumSpeedMph"] - 4)
        self.assertEqual(nox["activeAccelerationMph"], base["accelerationMph"] * 2)
        self.assertEqual(nox["activeMaximumSpeedMph"], base["maximumSpeedMph"] + 40)
        self.assertEqual(all_addons["noxExplosionRolls2d6"], [2, 3, 11, 12])

        self.assert_invalid(self.advanced_spec(engineAddOns=["charger", "charger"]), "charger.*only one|singleCharger")

    def test_active_suspension_and_robotic_drive_handling_do_not_stack(self):
        active = self.build(self.advanced_spec(drivingSystems=["activeSuspensionInterceptor"]))
        complete_robotic = self.build(self.advanced_spec(drivingSystems=["roboticDriveInterceptorComplete"]))
        upgraded_robotic = self.build(
            self.advanced_spec(drivingSystems=["activeSuspensionInterceptor", "roboticDriveInterceptorUpgrade"])
        )

        self.assertEqual(active["handling"], active["baseHandling"] + 2)
        self.assertEqual(complete_robotic["handling"], complete_robotic["baseHandling"] + 3)
        self.assertEqual(upgraded_robotic["handling"], upgraded_robotic["baseHandling"] + 3)

        self.assert_invalid(
            self.advanced_spec(drivingSystems=["roboticDriveInterceptorUpgrade"]),
            "roboticDrive.*requires.*activeSuspension|active suspension",
        )

    def test_armour_caps_materials_and_known_odyssey_example(self):
        armour = {
            facing: {"material": "carbonSteel", "points": 6}
            for facing in ("front", "rear", "leftSide", "rightSide", "floor", "roof")
        }
        record = self.build(self.advanced_spec(armour=armour))

        self.assertEqual(record["armourByFacing"]["front"], {"material": "carbonSteel", "points": 6})
        self.assertEqual(record["armourByFacing"]["roof"], {"material": "carbonSteel", "points": 6})

        self.assert_invalid(
            self.advanced_spec(armour={"front": {"material": "carbonSteel", "points": 7}}),
            "armour.*cap|front.*6",
        )
        self.assert_invalid(
            self.advanced_spec(
                template_id="bike",
                engine_size=None,
                armour={"leftSide": {"material": "carbonSteel", "points": 5}},
            ),
            "leftSide.*4|bike.*armour",
        )

        odyssey = self.build(
            self.advanced_spec(
                vehicleId="odyssey-4",
                engine_size="v12",
                armour=armour,
                safetyDevices=["passengerCage", "ejectorSeat"],
                installedWeapons=[
                    {"id": "mine-1", "weaponId": "patternMineLayer", "mountId": "passiveLeft", "facing": "rear"},
                    {"id": "smoke-1", "weaponId": "smokeLayer", "mountId": "passiveRight", "facing": "rear"},
                    {
                        "id": "auto-1",
                        "weaponId": "autocannon15mm",
                        "mountId": "leftWing",
                        "facing": "front",
                        "linkedGroupId": "front-autocannons",
                    },
                    {
                        "id": "auto-2",
                        "weaponId": "autocannon15mm",
                        "mountId": "rightWing",
                        "facing": "front",
                        "linkedGroupId": "front-autocannons",
                    },
                ],
                linkedGroups=[{"id": "front-autocannons", "weaponInstanceIds": ["auto-1", "auto-2"]}],
            )
        )
        self.assertEqual(odyssey["totalCost"], 143_500)
        self.assertEqual(odyssey["totalWeight"], 2080)
        self.assertEqual(odyssey["maximumSpeedMph"], 112)
        self.assertEqual(odyssey["accelerationMph"], 20)
        self.assertEqual(odyssey["brakingMph"], 20)
        self.assertEqual(odyssey["nonHeHandling"], 4)
        self.assertEqual(odyssey["heHandling"], 5)

    def test_linked_weapon_rules_require_identical_facing_and_turret_scope(self):
        legal = self.build(
            self.core_spec(
                installedWeapons=[
                    {
                        "id": "auto-1",
                        "weaponId": "autocannon15mm",
                        "mountId": "leftWing",
                        "facing": "front",
                        "linkedGroupId": "front-autocannons",
                    },
                    {
                        "id": "auto-2",
                        "weaponId": "autocannon15mm",
                        "mountId": "rightWing",
                        "facing": "front",
                        "linkedGroupId": "front-autocannons",
                    },
                ],
                linkedGroups=[{"id": "front-autocannons", "weaponInstanceIds": ["auto-1", "auto-2"]}],
            )
        )
        self.assertEqual(legal["linkedGroups"][0]["weaponInstanceIds"], ["auto-1", "auto-2"])

        self.assert_invalid(
            self.core_spec(
                installedWeapons=[
                    {"id": "mg-1", "weaponId": "machineGun6mm", "mountId": "leftWing", "facing": "front", "linkedGroupId": "mixed"},
                    {"id": "auto-1", "weaponId": "autocannon15mm", "mountId": "rightWing", "facing": "front", "linkedGroupId": "mixed"},
                ],
                linkedGroups=[{"id": "mixed", "weaponInstanceIds": ["mg-1", "auto-1"]}],
            ),
            "linked.*identical|identical.*linked",
        )
        self.assert_invalid(
            self.advanced_spec(
                installedWeapons=[
                    {"id": "mg-1", "weaponId": "machineGun6mm", "mountId": "hood", "facing": "front", "linkedGroupId": "mixed-facing"},
                    {"id": "mg-2", "weaponId": "machineGun6mm", "mountId": "tailgate", "facing": "rear", "linkedGroupId": "mixed-facing"},
                ],
                mountUpgrades=["tailgate"],
                linkedGroups=[{"id": "mixed-facing", "weaponInstanceIds": ["mg-1", "mg-2"]}],
            ),
            "linked.*same direction|front-facing.*rear-facing",
        )
        self.assert_invalid(
            self.core_spec(
                mountUpgrades=["turret"],
                installedWeapons=[
                    {"id": "mg-1", "weaponId": "machineGun6mm", "mountId": "turret", "facing": "front", "linkedGroupId": "turret-fixed"},
                    {"id": "mg-2", "weaponId": "machineGun6mm", "mountId": "hood", "facing": "front", "linkedGroupId": "turret-fixed"},
                ],
                linkedGroups=[{"id": "turret-fixed", "weaponInstanceIds": ["mg-1", "mg-2"]}],
            ),
            "turret.*linked|linked.*turret",
        )

    def test_ammo_starting_loads_reloads_special_replacement_and_double_loads(self):
        record = self.build(
            self.core_spec(
                installedWeapons=[
                    {
                        "id": "auto-1",
                        "weaponId": "autocannon15mm",
                        "mountId": "hood",
                        "facing": "front",
                        "specialAmmo": [{"kind": "depletedUranium", "count": 2}],
                        "reloads": [{"kind": "gp", "count": 1}],
                        "doubleLoad": True,
                    }
                ]
            )
        )
        auto = weapon_entry(record, "autocannon15mm")
        self.assertTrue(auto["doubleLoad"])
        self.assertEqual(auto["doubleLoadFacilityCost"], 2000)
        self.assertEqual(auto["doubleLoadAdditionalWeight"], 125)

        ammo = magazine(record, "auto-1")
        self.assertEqual(
            ammo["loads"],
            [
                {"kind": "depletedUranium", "shots": 1},
                {"kind": "depletedUranium", "shots": 1},
                {"kind": "gp", "shots": 6},
                {"kind": "gp", "shots": 8, "source": "reload"},
            ],
        )
        self.assertEqual(ammo["capacityShots"], 16)

        self.assert_invalid(
            self.core_spec(
                installedWeapons=[
                    {
                        "id": "laser-1",
                        "weaponId": "combatLaser",
                        "mountId": "hood",
                        "facing": "front",
                        "doubleLoad": True,
                    }
                ]
            ),
            "double.*combatLaser|combatLaser.*double",
        )
        self.assert_invalid(
            self.core_spec(
                installedWeapons=[
                    {
                        "id": "mg-1",
                        "weaponId": "machineGun6mm",
                        "mountId": "hood",
                        "facing": "front",
                        "specialAmmo": [{"kind": "phosphor", "count": 1}],
                    }
                ]
            ),
            "phosphor.*machineGun6mm|machineGun6mm.*phosphor",
        )

    def test_minigun_double_load_uses_proofread_added_weight(self):
        record = self.build(
            self.core_spec(
                installedWeapons=[
                    {
                        "id": "mini-1",
                        "weaponId": "minigun62mm",
                        "mountId": "hood",
                        "facing": "front",
                        "doubleLoad": True,
                    }
                ]
            )
        )
        mini = weapon_entry(record, "minigun62mm")
        self.assertTrue(mini["doubleLoad"])
        self.assertEqual(mini["doubleLoadFacilityCost"], 2000)
        self.assertEqual(mini["doubleLoadAdditionalWeight"], 75)

    def test_validate_vehicle_design_returns_errors_without_building_record(self):
        report = plain(
            vehicle_design.validate_vehicle_design(
                self.core_spec(
                    installedWeapons=[
                        {"id": "chain-1", "weaponId": "chainGun", "mountId": "leftWing", "facing": "front"}
                    ]
                )
            )
        )

        self.assertFalse(report["valid"])
        self.assertTrue(any("chainGun" in error["message"] and "leftWing" in error["message"] for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()

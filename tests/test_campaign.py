import unittest

from dark_future.campaign import (
    BountyClaim,
    CampaignState,
    ContractOutcome,
    add_vehicle,
    create_unit,
    fit_store_item_to_vehicle,
    purchase_chassis,
    purchase_equipment_to_store,
    recruit_experienced_driver_stub,
    recruit_novice_driver,
    repair_cost,
    repair_vehicle,
    sell_store_item,
    settle_post_engagement,
    strip_vehicle_item_to_store,
)


class CampaignBackendTests(unittest.TestCase):
    def make_campaign(self):
        campaign = CampaignState()
        agency = create_unit(campaign, "agency", "Eagle Security", "agency", "player-1", 20_000)
        gang = create_unit(campaign, "gang", "Dust Saints", "outlawGang", "player-2", 5_000)
        op_driver = recruit_novice_driver(campaign, agency.id, "Mara Voss", "driver-op")
        outlaw_driver = recruit_novice_driver(campaign, gang.id, "Raze", "driver-outlaw")
        car = add_vehicle(campaign, agency.id, "Interceptor", "car-op", owner_driver_id=op_driver.id)
        add_vehicle(campaign, gang.id, "Renegade", "car-outlaw", owner_driver_id=outlaw_driver.id)
        return campaign, agency, gang, op_driver, outlaw_driver, car

    def test_settlement_applies_bounty_mileage_kudos_and_losses(self):
        campaign, agency, gang, op_driver, outlaw_driver, _ = self.make_campaign()
        outcome = ContractOutcome(
            id="contract-1",
            attacker_unit_id=agency.id,
            defender_unit_id=gang.id,
            winner_unit_id=agency.id,
            participating_driver_ids=[op_driver.id, outlaw_driver.id],
            surviving_driver_ids=[op_driver.id],
            killed_driver_ids=[outlaw_driver.id],
            destroyed_vehicle_ids=["car-outlaw"],
            bounty_claims=[
                BountyClaim(unit_id=agency.id, enemy_drive_skill=3, result="killed")
            ],
            mileage_awards={op_driver.id: 10},
        )

        report = settle_post_engagement(campaign, outcome)

        self.assertEqual(report.funds_by_unit[agency.id], 12_000)
        self.assertEqual(campaign.units[agency.id].funds, 27_000)
        self.assertEqual(campaign.drivers[op_driver.id].mileage_points, 10)
        self.assertEqual(campaign.drivers[op_driver.id].drive_skill, 4)
        self.assertEqual(campaign.drivers[op_driver.id].kudos_points, 1)
        self.assertTrue(campaign.drivers[outlaw_driver.id].retired)
        self.assertFalse(campaign.vehicles["car-outlaw"].roadworthy)
        self.assertEqual(campaign.units[agency.id].contracts_completed, 1)
        self.assertEqual(campaign.units[gang.id].contracts_completed, 1)

    def test_deliberate_objective_failure_forfeits_pay_and_mileage(self):
        campaign, agency, gang, op_driver, _, _ = self.make_campaign()
        outcome = ContractOutcome(
            id="contract-2",
            attacker_unit_id=agency.id,
            defender_unit_id=gang.id,
            objective_satisfied=False,
            deliberate_objective_failure=True,
            participating_driver_ids=[op_driver.id],
            surviving_driver_ids=[op_driver.id],
            bounty_claims=[
                BountyClaim(unit_id=agency.id, enemy_drive_skill=4, result="terminal_or_crashed")
            ],
            mileage_awards={op_driver.id: 10},
        )

        report = settle_post_engagement(campaign, outcome)

        self.assertEqual(report.funds_by_unit, {})
        self.assertEqual(report.mileage_by_driver, {})
        self.assertEqual(campaign.units[agency.id].funds, 15_000)
        self.assertEqual(campaign.drivers[op_driver.id].mileage_points, 0)
        self.assertEqual(campaign.units[agency.id].failed_engagement_objective_count, 1)

    def test_repair_cost_counts_damage_criticals_and_hack_damage(self):
        campaign, agency, _, _, _, car = self.make_campaign()
        car.current_damage = 18
        car.critical_hits = ["engine damaged", "weapon disabled"]
        car.hack_damage_count = 1

        estimate = repair_cost(car)
        report = repair_vehicle(
            campaign,
            agency.id,
            car.id,
            damage_points=4,
            critical_hits=1,
            hack_damage_count=0,
        )

        self.assertEqual(estimate.total_cost, 2_500)
        self.assertEqual(report.spent, 1_250)
        self.assertEqual(car.current_damage, 22)
        self.assertEqual(car.critical_hits, ["weapon disabled"])
        self.assertEqual(car.hack_damage_count, 1)
        self.assertEqual(campaign.units[agency.id].funds, 13_750)

    def test_recruitment_creates_novice_and_experienced_driver_obligation(self):
        campaign = CampaignState()
        agency = create_unit(campaign, "agency", "Eagle Security", "agency", "player-1", 30_000)

        novice = recruit_novice_driver(campaign, agency.id, "Alex Decker", "novice")
        experienced = recruit_experienced_driver_stub(
            campaign,
            agency.id,
            "Cass Vale",
            drive_skill=5,
            own_vehicle_value=40_000,
            driver_id="experienced",
        )

        self.assertEqual(novice.drive_skill, 2)
        self.assertEqual(campaign.units[agency.id].funds, 25_000)
        self.assertTrue(experienced.experienced)
        self.assertEqual(experienced.funds, 10_000)
        self.assertEqual(experienced.mileage_points, 20)
        self.assertEqual(campaign.units[agency.id].expenses_due, 4_000)

    def test_campaign_serializes_to_plain_dict_and_loads_back(self):
        campaign, agency, gang, op_driver, _, car = self.make_campaign()
        car.current_damage = 20
        car.critical_hits.append("engine damaged")
        stored = purchase_equipment_to_store(campaign, agency.id, "machineGun6mm", "store-mg")
        car.template_id = "interceptor"
        car.payload_limit = 850
        fit_store_item_to_vehicle(campaign, agency.id, car.id, stored.id, "hood")
        outcome = ContractOutcome(
            id="contract-3",
            attacker_unit_id=agency.id,
            defender_unit_id=gang.id,
            winner_unit_id=agency.id,
            participating_driver_ids=[op_driver.id],
            surviving_driver_ids=[op_driver.id],
            mileage_awards={op_driver.id: 1},
        )
        settle_post_engagement(campaign, outcome)

        loaded = CampaignState.from_dict(campaign.to_dict())

        self.assertEqual(loaded.sequence_number, campaign.sequence_number)
        self.assertEqual(loaded.units[agency.id].name, "Eagle Security")
        self.assertEqual(loaded.drivers[op_driver.id].vehicle_ids, ["car-op"])
        self.assertEqual(loaded.vehicles[car.id].critical_hits, ["engine damaged"])
        self.assertEqual(loaded.vehicles[car.id].installed_items[0].source_id, "machineGun6mm")
        self.assertEqual(loaded.vehicles[car.id].payload_used, 175)
        self.assertEqual(loaded.contracts[0].id, "contract-3")

    def test_purchase_uses_extracted_costs_and_outlaw_surcharge(self):
        campaign = CampaignState()
        gang = create_unit(campaign, "gang", "Dust Saints", "outlawGang", "player-2", 40_000)

        item = purchase_equipment_to_store(campaign, gang.id, "chainGun", "chain-gun")

        self.assertEqual(item.value, 22_000)
        self.assertEqual(item.purchase_cost, 33_000)
        self.assertEqual(campaign.units[gang.id].funds, 7_000)

    def test_purchase_chassis_uses_extracted_vehicle_cost_and_template_payload(self):
        campaign = CampaignState()
        agency = create_unit(campaign, "agency", "Eagle Security", "agency", "player-1", 80_000)

        vehicle = purchase_chassis(campaign, agency.id, "interceptorV6", "Odyssey", "car-1")

        self.assertEqual(campaign.units[agency.id].funds, 30_000)
        self.assertEqual(vehicle.template_id, "interceptor")
        self.assertEqual(vehicle.value, 50_000)
        self.assertEqual(vehicle.max_damage, 24)
        self.assertEqual(vehicle.payload_limit, 850)

    def test_fitting_equipment_validates_mount_class_and_payload(self):
        campaign = CampaignState()
        agency = create_unit(campaign, "agency", "Eagle Security", "agency", "player-1", 100_000)
        vehicle = purchase_chassis(campaign, agency.id, "interceptorV6", "Odyssey", "car-1")
        chain_gun = purchase_equipment_to_store(campaign, agency.id, "chainGun", "chain-gun")

        with self.assertRaisesRegex(ValueError, "cannot be fitted"):
            fit_store_item_to_vehicle(campaign, agency.id, vehicle.id, chain_gun.id, "leftWing")

        report = fit_store_item_to_vehicle(campaign, agency.id, vehicle.id, chain_gun.id, "hood")

        self.assertEqual(report.payload_used, 300)
        self.assertEqual(vehicle.equipment, ["chainGun"])
        self.assertEqual(vehicle.installed_items[0].mount_id, "hood")

    def test_fitting_accepts_zero_cost_mount_and_rejects_over_payload(self):
        campaign = CampaignState()
        agency = create_unit(campaign, "agency", "Eagle Security", "agency", "player-1", 100_000)
        vehicle = purchase_chassis(campaign, agency.id, "interceptorV6", "Odyssey", "car-1")

        tailgate = purchase_equipment_to_store(campaign, agency.id, "tailgate", "tailgate")
        report = fit_store_item_to_vehicle(campaign, agency.id, vehicle.id, tailgate.id, "tailgate")
        self.assertEqual(tailgate.value, 0)
        self.assertEqual(report.payload_used, 0)

        vehicle.payload_used = 700
        chain_gun = purchase_equipment_to_store(campaign, agency.id, "chainGun", "chain-gun")
        with self.assertRaisesRegex(ValueError, "exceeds core payload"):
            fit_store_item_to_vehicle(campaign, agency.id, vehicle.id, chain_gun.id, "hood")

    def test_strip_and_sell_store_item_follow_campaign_resale_rule(self):
        campaign = CampaignState()
        agency = create_unit(campaign, "agency", "Eagle Security", "agency", "player-1", 80_000)
        vehicle = purchase_chassis(campaign, agency.id, "interceptorV6", "Odyssey", "car-1")
        item = purchase_equipment_to_store(campaign, agency.id, "machineGun6mm", "mg")
        fit_store_item_to_vehicle(campaign, agency.id, vehicle.id, item.id, "hood")

        strip_report = strip_vehicle_item_to_store(campaign, agency.id, vehicle.id, item.id)
        sell_report = sell_store_item(campaign, agency.id, item.id, die_roll=4)

        self.assertEqual(strip_report.spent, 250)
        self.assertEqual(strip_report.payload_used, 0)
        self.assertEqual(sell_report.received, 3_500)
        self.assertEqual(campaign.units[agency.id].funds, 28_250)


if __name__ == "__main__":
    unittest.main()

import unittest

from dark_future.combat_tables import (
    critical_result,
    damage_increment_penalties,
    resolve_control_loss_test,
    resolve_damage,
    resolve_tgsm_hit,
    resolve_hazard_test,
    safety_limit,
    tgsm_hit_location,
    tgsm_submunition_count,
    three_wheeler_hit_component,
    weapon_damage_modifier,
)


class CombatTableTests(unittest.TestCase):
    def test_damage_uses_extracted_weapon_modifier_and_armour(self):
        result = resolve_damage(
            template_id="interceptor",
            current_damage=24,
            die=2,
            damage_modifier=weapon_damage_modifier("15mmAutocannon"),
            armour=4,
        )

        self.assertEqual(result.ordinary_damage, 1)
        self.assertEqual(result.remaining_damage, 23)
        self.assertFalse(result.critical_triggered)
        self.assertFalse(result.terminal_damage)

    def test_natural_six_triggers_critical_even_when_armour_stops_damage(self):
        result = resolve_damage(
            template_id="interceptor",
            current_damage=24,
            die=6,
            damage_modifier=1,
            armour=10,
        )

        self.assertEqual(result.ordinary_damage, 0)
        self.assertEqual(result.remaining_damage, 24)
        self.assertTrue(result.critical_triggered)

    def test_damage_crossing_multiple_increments_returns_penalties(self):
        result = resolve_damage(
            template_id="interceptor",
            current_damage=19,
            die=6,
            damage_modifier=10,
            armour=0,
        )

        self.assertEqual(result.remaining_damage, 3)
        self.assertEqual(result.crossed_increment_thresholds, (18, 12, 6))
        self.assertEqual(
            [(penalty.max_mph_delta, penalty.acceleration_mph_delta, penalty.handling_delta) for penalty in result.increment_penalties],
            [(-10, -3, -1), (-10, -3, -1), (-10, -3, -1)],
        )

    def test_damage_increment_helper_does_not_treat_starting_damage_as_threshold(self):
        penalties = damage_increment_penalties(
            template_id="renegade",
            previous_damage=18,
            remaining_damage=17,
        )

        self.assertEqual(penalties, ())

    def test_terminal_damage_is_reported_once_current_damage_reaches_zero(self):
        result = resolve_damage(
            template_id="bike",
            current_damage=2,
            die=5,
            damage_modifier=3,
            armour=2,
        )

        self.assertEqual(result.remaining_damage, 0)
        self.assertTrue(result.terminal_damage)

    def test_already_zero_damage_ignores_ordinary_damage_but_keeps_critical_check(self):
        result = resolve_damage(
            template_id="renegade",
            current_damage=0,
            die=6,
            damage_modifier=8,
            armour=0,
        )

        self.assertTrue(result.ignored_ordinary_damage)
        self.assertEqual(result.ordinary_damage, 0)
        self.assertTrue(result.critical_triggered)
        self.assertFalse(result.terminal_damage)

    def test_he_damage_reports_extracted_hazard_limit_band(self):
        light_he = resolve_damage(
            template_id="renegade",
            current_damage=18,
            die=3,
            damage_modifier=2,
            armour=3,
            tags=("HE",),
        )
        heavy_he = resolve_damage(
            template_id="renegade",
            current_damage=18,
            die=3,
            damage_modifier=8,
            armour=3,
            tags=("HE",),
        )

        self.assertEqual(light_he.hazard_safety_limit_mph, 50)
        self.assertEqual(heavy_he.hazard_safety_limit_mph, 30)

    def test_critical_result_uses_named_component_table_ranges(self):
        result = critical_result("driver", 4)

        self.assertEqual(result.result_id, "driverInjured")
        self.assertEqual(result.effects[0]["kind"], "driveSkillDelta")
        self.assertEqual(result.effects[0]["value"], -1)

    def test_critical_result_exposes_confirmation_roll_rows(self):
        result = critical_result("engine", 1)

        self.assertEqual(result.result_id, "engineBlock")
        self.assertEqual(result.confirmation_roll["kind"], "d6PlusHitDamage")
        self.assertEqual(result.confirmation_roll["successIfGte"], 7)

    def test_hazard_at_or_below_safety_limit_is_skipped(self):
        result = resolve_hazard_test(
            roll=6,
            mph=60,
            safety_limit_mph=60,
            handling=0,
            drive_skill=0,
        )

        self.assertTrue(result.skipped)
        self.assertEqual(result.effect, "ok")

    def test_hazard_roll_can_panic_brake_from_table_total(self):
        result = resolve_hazard_test(
            roll=1,
            mph=70,
            safety_limit_mph=60,
            handling=1,
            drive_skill=1,
        )

        self.assertEqual(result.total, 1)
        self.assertEqual(result.effect, "panicBrake")
        self.assertEqual(result.speed_loss_mph, 5)
        self.assertFalse(result.control_lost)

    def test_hazard_roll_can_cause_control_loss_from_table_total(self):
        result = resolve_hazard_test(
            roll=6,
            mph=90,
            safety_limit_mph=60,
            handling=2,
            drive_skill=2,
        )

        self.assertEqual(result.total, 7)
        self.assertEqual(result.effect, "controlLoss")
        self.assertTrue(result.control_lost)

    def test_control_loss_test_uses_speed_factor_and_adverse_control(self):
        result = resolve_control_loss_test(
            roll=1,
            mph=60,
            handling=5,
            drive_skill=3,
        )

        self.assertEqual(result.total, 1)
        self.assertEqual(result.effect, "regainControlAfterStraightMove")
        self.assertFalse(result.control_lost)

    def test_control_loss_test_adds_zero_handling_or_no_driver_modifier(self):
        result = resolve_control_loss_test(
            roll=4,
            mph=80,
            handling=0,
            drive_skill=None,
        )

        self.assertEqual(result.total, 10)
        self.assertEqual(result.effect, "roll")
        self.assertTrue(result.control_lost)

    def test_safety_limit_lookup_uses_extracted_ids(self):
        self.assertEqual(safety_limit("passive.smoke"), 60)
        self.assertEqual(safety_limit("roadHazard.debris"), 10)
        self.assertEqual(safety_limit("manoeuvre.uTurn"), 10)

    def test_tgsm_tables_resolve_submunitions_and_hit_locations(self):
        self.assertEqual(tgsm_submunition_count(1), 1)
        self.assertEqual(tgsm_submunition_count(4), 2)
        self.assertEqual(tgsm_submunition_count(6), 3)

        self.assertEqual(tgsm_hit_location(1)["armourFacing"], "front")
        self.assertEqual(tgsm_hit_location(3)["armourFacing"], "side")
        self.assertEqual(tgsm_hit_location(5)["armourFacing"], "rear")
        roof = tgsm_hit_location(6)
        self.assertEqual(roof["armourFacing"], "roof")
        self.assertTrue(roof["bypassesStandardFacingArmour"])

        resolved = resolve_tgsm_hit(5, (1, 4, 6))
        self.assertEqual([item["location"] for item in resolved], ["front", "rear", "roof"])

    def test_three_wheeler_target_matrix_uses_transcribed_arcs(self):
        self.assertEqual(three_wheeler_hit_component("trikeTargetMatrix", "front", 4), "mainBodyRider")
        self.assertEqual(three_wheeler_hit_component("trikeTargetMatrix", "front", 5), "sidecarOrOutriggerWheel")
        self.assertEqual(three_wheeler_hit_component("trikeTargetMatrix", "sidecarSide", 3), "sidecarStructure")
        self.assertEqual(three_wheeler_hit_component("trikeTargetMatrix", "nonSidecarSide", 6), "sidecarStructurePassThrough")
        self.assertEqual(three_wheeler_hit_component("motorcycleCombinationTargetMatrix", "rear", 6), "sidecar")


if __name__ == "__main__":
    unittest.main()

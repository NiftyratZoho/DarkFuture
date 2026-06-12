from pathlib import Path
import unittest

from dark_future.engine import (
    PassiveMarker,
    ai_choose_action,
    apply_action,
    apply_critical_effect,
    apply_rocket_booster_critical,
    curve_safety_limit,
    generate_track_layout,
    load_game,
    legal_actions,
    new_game,
    phase_moves,
    save_game,
    speed_factor,
    vehicle_by_id,
    provisional_track_layout,
)


class EngineTests(unittest.TestCase):
    def test_provisional_track_uses_photo_inventory_window(self):
        layout = provisional_track_layout()
        self.assertEqual(len(layout), 7)
        self.assertIn("curve50to80_left", layout)
        self.assertIn("curve30to60_right", layout)

    def test_generate_track_layout_rolls_connected_track_into_state(self):
        state = new_game()
        state.dice.queue = [5, 6, 1, 1, 1, 1]

        generate_track_layout(state)

        self.assertEqual(state.track_sections, len(state.track_section_types))
        self.assertEqual(state.track_section_types[:5], ["straight", "straight", "straight", "curve30to60_left", "straight"])
        self.assertTrue(any(entry.kind == "track" and "Generated track" in entry.message for entry in state.logs))

    def test_speed_factor_uses_ceil_twenty_mph_bands(self):
        self.assertEqual(speed_factor(0), 0)
        self.assertEqual(speed_factor(1), 1)
        self.assertEqual(speed_factor(20), 1)
        self.assertEqual(speed_factor(21), 2)
        self.assertEqual(speed_factor(60), 3)

    def test_phase_moves_follow_extracted_table(self):
        self.assertEqual(phase_moves(60, 1), 1)
        self.assertEqual(phase_moves(60, 3), 1)
        self.assertEqual(phase_moves(60, 4), 0)

    def test_steady_forward_moves_active_vehicle(self):
        state = new_game()
        self.assertEqual(state.active_vehicle_id, "agency-1")
        vehicle = vehicle_by_id(state, "agency-1")
        self.assertEqual((vehicle.section, vehicle.space, vehicle.lane_pair), (1, 1, 4))
        apply_action(state, "steady")
        self.assertEqual((vehicle.section, vehicle.space, vehicle.lane_pair), (1, 2, 4))

    def test_drift_changes_lane_after_forward_move(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        apply_action(state, "drift_left")
        self.assertEqual((vehicle.section, vehicle.space, vehicle.lane_pair), (1, 2, 3))

    def test_drift_right_caps_at_eight_lane_track_edge(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.lane_pair = 7

        apply_action(state, "drift_right")

        self.assertEqual(vehicle.lane_pair, 7)

    def test_core_curve_drift_inward_is_illegal_until_leaving_curve(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.section = 3
        vehicle.space = 1
        vehicle.lane_pair = 4

        apply_action(state, "drift_left")

        self.assertEqual((vehicle.section, vehicle.space, vehicle.lane_pair), (3, 1, 4))
        self.assertTrue(any(entry.kind == "illegal-action" and "outward" in entry.message for entry in state.logs))

    def test_core_curve_drift_outward_happens_after_forward_move(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.section = 3
        vehicle.space = 1
        vehicle.lane_pair = 4

        apply_action(state, "drift_right")

        self.assertEqual((vehicle.section, vehicle.space, vehicle.lane_pair), (3, 2, 5))

    def test_curve_to_straight_drift_can_go_either_direction(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.section = 3
        vehicle.space = 5
        vehicle.lane_pair = 6

        apply_action(state, "drift_left")

        self.assertEqual((vehicle.section, vehicle.space, vehicle.lane_pair), (4, 1, 5))

    def test_legal_actions_hide_inward_curve_drift(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.section = 3
        vehicle.space = 1
        vehicle.lane_pair = 4

        action_ids = {action.id for action in legal_actions(state)}

        self.assertNotIn("drift_left", action_ids)
        self.assertIn("drift_right", action_ids)

    def test_u_turn_up_to_ten_mph_reverses_facing_without_hazard(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.mph = 10
        original_direction = vehicle.direction

        apply_action(state, "u_turn")

        self.assertEqual(vehicle.direction, -original_direction)
        self.assertFalse(any(entry.kind == "hazard" for entry in state.logs))

    def test_u_turn_from_eleven_to_thirty_mph_triggers_hazard_roll(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.mph = 20
        vehicle.handling = 6
        vehicle.driver_skill = 6
        state.dice.queue = [1]

        apply_action(state, "u_turn")

        self.assertEqual(vehicle.direction, -1)
        self.assertTrue(any(entry.kind == "hazard" and "U-turn" in entry.message for entry in state.logs))

    def test_u_turn_at_thirty_one_or_more_triggers_control_loss_instead(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.mph = 31
        vehicle.handling = 0
        vehicle.driver_skill = 0
        state.dice.queue = [6]

        apply_action(state, "u_turn")

        self.assertEqual(vehicle.direction, 1)
        self.assertEqual(vehicle.control_state, "out_of_control")
        self.assertTrue(any(entry.kind == "control-loss" and "too fast" in entry.message for entry in state.logs))

    def test_curve_edge_u_turn_is_blocked_until_contact_geometry_exists(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.section = 3
        vehicle.space = 1
        vehicle.lane_pair = 1
        vehicle.mph = 10

        apply_action(state, "u_turn")

        self.assertEqual(vehicle.direction, 1)
        self.assertTrue(any(entry.kind == "illegal-action" and "contact-zone geometry" in entry.message for entry in state.logs))

    def test_curve_safety_limit_uses_lower_occupied_lane_limit(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.section = 3
        vehicle.lane_pair = 7
        self.assertEqual(state.track_section_types[3], "curve50to80_left")
        self.assertEqual(curve_safety_limit(state, vehicle), 80)

        vehicle.section = 5
        vehicle.lane_pair = 1
        self.assertEqual(state.track_section_types[5], "curve30to60_right")
        self.assertEqual(curve_safety_limit(state, vehicle), 30)

    def test_action_list_present_for_active_vehicle(self):
        state = new_game()
        labels = [action.label for action in legal_actions(state)]
        self.assertIn("Steady Forward", labels)
        self.assertIn("Accelerate", labels)
        self.assertIn("Shoot", labels)

    def test_idle_tactical_actions_do_not_include_campaign_setup(self):
        state = new_game()
        state.active_vehicle_id = None

        action_ids = [action.id for action in legal_actions(state)]

        self.assertEqual(action_ids, ["next_phase", "save_game", "load_game"])

    def test_rocket_booster_actions_follow_page_22_vehicle_restrictions(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")

        self.assertEqual(agency.rocket_booster_type, "twin")
        self.assertEqual(agency.rocket_booster_shots, 36)
        self.assertEqual(outlaw.rocket_booster_type, "single")
        self.assertEqual(outlaw.rocket_booster_shots, 24)
        self.assertIn("Rocket Pulse", [action.label for action in legal_actions(state, agency)])
        self.assertNotIn("Rocket Cruise", [action.label for action in legal_actions(state, agency)])

    def test_renegade_single_booster_pulse_uses_weight_table(self):
        state = new_game()
        renegade = vehicle_by_id(state, "outlaw-1")
        state.active_vehicle_id = renegade.id
        renegade.acted_this_phase = False
        renegade.section = 1
        renegade.space = 1
        renegade.direction = 1
        renegade.mph = 60

        apply_action(state, "rocket_pulse")

        self.assertEqual(renegade.mph, 105)
        self.assertEqual(renegade.rocket_booster_shots, 22)
        self.assertTrue(any("rocket pulse" in entry.message for entry in state.logs))

    def test_interceptor_twin_booster_pulse_uses_weight_table(self):
        state = new_game()
        interceptor = vehicle_by_id(state, "agency-1")
        interceptor.mph = 60

        apply_action(state, "rocket_pulse")

        self.assertEqual(interceptor.mph, 120)
        self.assertEqual(interceptor.rocket_booster_shots, 34)

    def test_rocket_cruise_maintains_speed_and_blocks_normal_speed_actions(self):
        state = new_game()
        interceptor = vehicle_by_id(state, "agency-1")
        interceptor.mph = 120

        apply_action(state, "rocket_cruise")

        self.assertEqual(interceptor.rocket_booster_mode, "cruise")
        self.assertEqual(interceptor.rocket_booster_cruise_mph, 120)
        self.assertEqual(interceptor.rocket_booster_shots, 35)
        actions = {action.id for action in legal_actions(state, interceptor)}
        self.assertIn("rocket_off", actions)
        self.assertNotIn("accelerate", actions)
        self.assertNotIn("brake", actions)

        interceptor.mph = 80
        apply_action(state, "next_phase")

        self.assertEqual(interceptor.mph, 120)
        self.assertEqual(interceptor.rocket_booster_shots, 34)

    def test_rocket_off_allows_above_max_speed_to_decay_by_phase(self):
        state = new_game()
        interceptor = vehicle_by_id(state, "agency-1")
        interceptor.mph = 150
        interceptor.rocket_booster_mode = "cruise"
        interceptor.rocket_booster_cruise_mph = 150

        apply_action(state, "rocket_off")
        apply_action(state, "next_phase")

        self.assertIsNone(interceptor.rocket_booster_mode)
        self.assertEqual(interceptor.mph, 145)

    def test_rocket_booster_critical_disables_passive_space_system_and_pair(self):
        state = new_game()
        interceptor = vehicle_by_id(state, "agency-1")
        interceptor.mph = 120
        interceptor.rocket_booster_mode = "cruise"
        interceptor.rocket_booster_cruise_mph = 120

        apply_rocket_booster_critical(state, interceptor, explodes=False)

        self.assertTrue(interceptor.rocket_booster_disabled)
        self.assertIsNone(interceptor.rocket_booster_mode)
        self.assertIn("rocket boosters disabled", interceptor.critical_notes)
        self.assertTrue(any("linked twin rocket boosters" in entry.message for entry in state.logs))
        self.assertNotIn("rocket_pulse", {action.id for action in legal_actions(state, interceptor)})

    def test_exploding_rocket_booster_adds_eight_he_hit_and_hazard_roll(self):
        state = new_game()
        renegade = vehicle_by_id(state, "outlaw-1")
        renegade.damage = 18
        renegade.mph = 80
        renegade.handling = 0
        renegade.driver_skill = 0
        state.dice.queue = [1, 6]

        apply_rocket_booster_critical(state, renegade, explodes=True)

        self.assertTrue(renegade.rocket_booster_disabled)
        self.assertEqual(renegade.damage, 12)
        self.assertTrue(any("rocket booster explosion" in entry.message and entry.kind == "damage" for entry in state.logs))
        self.assertTrue(any(entry.kind == "hazard" and "rocket booster explosion" in entry.message for entry in state.logs))

    def test_tyre_destroyed_critical_uses_lower_of_current_max_minus_ten_and_sixty(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.max_mph = 120
        vehicle.mph = 90

        apply_critical_effect(state, vehicle, {"kind": "maxMphBecomesLowerOf", "values": ["currentMaxMinus10", 60]})

        self.assertEqual(vehicle.max_mph, 60)
        self.assertEqual(vehicle.mph, 60)

        apply_critical_effect(state, vehicle, {"kind": "maxMphBecomesLowerOf", "values": ["currentMaxMinus10", 60]})

        self.assertEqual(vehicle.max_mph, 50)

    def test_shooting_can_damage_target(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        outlaw.section = agency.section + 1
        outlaw.space = agency.space
        outlaw.lane_pair = agency.lane_pair
        state.dice.queue = [5, 6]

        apply_action(state, "shoot")

        self.assertLess(outlaw.damage, 18)
        self.assertTrue(any(entry.kind == "damage" for entry in state.logs))

    def test_shooting_can_destroy_target_and_end_game(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        outlaw.section = agency.section + 1
        outlaw.space = agency.space
        outlaw.lane_pair = agency.lane_pair
        outlaw.damage = 2
        state.dice.queue = [5, 6]

        apply_action(state, "shoot")

        self.assertTrue(outlaw.destroyed)
        self.assertTrue(state.game_over)
        self.assertEqual(state.winner, "agency")

    def test_smoke_blocks_line_of_fire(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        agency.section = 1
        agency.space = 1
        agency.lane_pair = 4
        outlaw.section = 3
        outlaw.space = 1
        outlaw.lane_pair = 4
        state.passive_markers.append(PassiveMarker("smoke-test", "smoke", 2, 1, 4, "outlaw"))

        state.dice.queue = [6]
        apply_action(state, "shoot")

        self.assertTrue(any("no target" in entry.message for entry in state.logs))

    def test_head_on_contact_resolves_ram(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        agency.section = 1
        agency.space = 1
        agency.lane_pair = 3
        outlaw.section = 1
        outlaw.space = 2
        outlaw.lane_pair = 3
        outlaw.direction = -1
        state.dice.queue = [4, 4]

        apply_action(state, "steady")

        self.assertEqual(agency.mph, 0)
        self.assertEqual(outlaw.mph, 0)
        self.assertTrue(any(entry.kind == "ram" for entry in state.logs))

    def test_drop_oil_places_passive_marker_behind_vehicle(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")

        apply_action(state, "drop_oil")

        self.assertEqual(len(state.passive_markers), 1)
        marker = state.passive_markers[0]
        self.assertEqual(marker.kind, "oil")
        self.assertEqual(marker.section, agency.section - 1)
        self.assertEqual(marker.space, 3)

    def test_hazard_failure_sets_out_of_control(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.mph = 120
        agency.handling = 0
        agency.driver_skill = 0
        state.dice.queue = [6]

        apply_action(state, "drift_left")

        self.assertEqual(agency.control_state, "out_of_control")
        self.assertTrue(any(entry.kind == "control-loss" for entry in state.logs))

    def test_regain_control_action_restores_control_on_success(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.control_state = "out_of_control"
        agency.driver_skill = 6
        agency.handling = 5
        state.dice.queue = [1]

        apply_action(state, "regain_control")

        self.assertEqual(agency.control_state, "controlled")

    def test_critical_hit_applies_concrete_effect(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        outlaw.section = agency.section + 1
        outlaw.space = agency.space
        outlaw.lane_pair = agency.lane_pair
        state.dice.queue = [5, 6, 6, 6]

        apply_action(state, "shoot")

        self.assertTrue(outlaw.weapon_disabled)
        self.assertIn("weapons: weaponDestroyed", outlaw.critical_notes)

    def test_campaign_settlement_and_new_contract_flow(self):
        state = new_game()
        outlaw = vehicle_by_id(state, "outlaw-1")
        outlaw.destroyed = True

        apply_action(state, "wait")
        self.assertTrue(state.game_over)
        self.assertTrue(state.campaign.settlement_pending)

        apply_action(state, "settle_campaign")
        self.assertFalse(state.campaign.settlement_pending)
        self.assertEqual(state.campaign.contracts_completed, 1)

        apply_action(state, "new_contract")
        self.assertFalse(state.game_over)
        self.assertIsNotNone(state.active_vehicle_id)

    def test_campaign_management_actions_recruit_repair_and_cycle_scenario(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.damage -= 4
        funds_before = state.campaign.funds

        apply_action(state, "recruit_driver")
        apply_action(state, "repair_agency")
        apply_action(state, "cycle_scenario")

        self.assertEqual(len(state.campaign.roster), 3)
        self.assertEqual(agency.damage, 24)
        self.assertLess(state.campaign.funds, funds_before)
        self.assertEqual(state.campaign.current_scenario, "ambush")

    def test_new_game_uses_scenario_setups(self):
        ambush = new_game("ambush")
        pursuit = new_game("pursuit")

        self.assertEqual(ambush.scenario_id, "ambush")
        self.assertEqual(vehicle_by_id(ambush, "outlaw-1").direction, -1)
        self.assertEqual(pursuit.scenario_id, "pursuit")
        self.assertEqual(vehicle_by_id(pursuit, "outlaw-1").direction, 1)

    def test_save_and_load_round_trip(self):
        state = new_game("pursuit")
        state.campaign.funds = 34567

        path = Path(".test-dark-future-save.json")
        try:
            save_game(state, path)
            loaded = load_game(path)
        finally:
            if path.exists():
                path.unlink()

        self.assertEqual(loaded.scenario_id, "pursuit")
        self.assertEqual(loaded.campaign.funds, 34567)
        self.assertEqual(loaded.track_section_types, state.track_section_types)

    def test_ai_brakes_before_entering_curve_over_lane_limit(self):
        state = new_game()
        outlaw = vehicle_by_id(state, "outlaw-1")
        outlaw.section = 2
        outlaw.space = 3
        outlaw.lane_pair = 1
        outlaw.direction = 1
        outlaw.mph = 70

        self.assertEqual(state.track_section_types[3], "curve50to80_left")
        self.assertEqual(ai_choose_action(state, outlaw), "brake")

    def test_ai_does_not_choose_straight_drift_on_curve(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        outlaw.section = 3
        outlaw.space = 1
        outlaw.lane_pair = 6
        outlaw.direction = -1
        outlaw.mph = 50
        agency.section = 2
        agency.space = 1
        agency.lane_pair = 3

        self.assertEqual(state.track_section_types[outlaw.section], "curve50to80_left")
        self.assertEqual(ai_choose_action(state, outlaw), "steady")

    def test_ai_avoids_smoke_in_next_space_with_legal_drift(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        outlaw.section = 1
        outlaw.space = 1
        outlaw.lane_pair = 4
        outlaw.direction = 1
        outlaw.mph = 40
        agency.section = 3
        agency.space = 1
        agency.lane_pair = 4
        state.passive_markers.append(PassiveMarker("smoke-ai", "smoke", 1, 2, 5, "agency"))

        self.assertEqual(ai_choose_action(state, outlaw), "drift_left")

    def test_ai_does_not_shoot_when_smoke_blocks_fire(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        outlaw.section = 1
        outlaw.space = 1
        outlaw.lane_pair = 4
        outlaw.direction = 1
        agency.section = 3
        agency.space = 1
        agency.lane_pair = 4
        state.passive_markers.append(PassiveMarker("smoke-shot-ai", "smoke", 2, 1, 4, "agency"))

        self.assertNotEqual(ai_choose_action(state, outlaw), "shoot")


if __name__ == "__main__":
    unittest.main()

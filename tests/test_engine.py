from pathlib import Path
import unittest

from dark_future.engine import (
    PassiveMarker,
    ai_choose_action,
    apply_action,
    apply_critical_effect,
    apply_hostile_system_effect,
    apply_rocket_booster_critical,
    choose_next_actor,
    curve_safety_limit,
    generate_track_layout,
    initial_track_layout,
    load_game,
    legal_actions,
    make_vehicle,
    new_game,
    phase_moves,
    save_game,
    speed_factor,
    vehicle_acts_in_phase,
    vehicle_by_id,
    provisional_track_layout,
    shoot_targets,
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

    def test_initial_track_layout_uses_rulebook_ten_section_generation(self):
        state = new_game()
        state.dice.queue = [5, 6, 2, 5, 6, 4, 5, 6, 2, 1]

        layout = initial_track_layout(state.dice)

        self.assertEqual(len(layout), 10)
        self.assertEqual(layout[:3], ["straight", "straight", "straight"])
        self.assertIn("curve30to60_right", layout)

    def test_new_game_accepts_generated_track_layout(self):
        layout = ["straight"] * 10

        state = new_game("intercept", track_section_types=layout)

        self.assertEqual(state.track_sections, 10)
        self.assertEqual(state.track_section_types, layout)

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

    def test_stationary_vehicles_act_only_in_phase_one(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.mph = 0

        self.assertTrue(vehicle_acts_in_phase(vehicle, 1))
        self.assertFalse(vehicle_acts_in_phase(vehicle, 2))

    def test_stationary_vehicle_gets_phase_one_activation(self):
        state = new_game()
        for vehicle in state.vehicles:
            vehicle.mph = 0
            vehicle.acted_this_phase = False
        state.phase = 1
        state.active_vehicle_id = None

        choose_next_actor(state)

        self.assertIsNotNone(state.active_vehicle_id)

    def test_stationary_vehicle_has_move_off_and_stationary_actions(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.mph = 0
        state.active_vehicle_id = agency.id

        action_ids = {action.id for action in legal_actions(state)}

        self.assertIn("accelerate", action_ids)
        self.assertIn("reverse", action_ids)
        self.assertIn("shoot", action_ids)
        self.assertIn("drop_smoke", action_ids)
        self.assertNotIn("steady", action_ids)
        self.assertNotIn("brake", action_ids)
        self.assertNotIn("drop_oil", action_ids)

    def test_stationary_move_off_accelerates_and_moves_one_space(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.mph = 0
        state.active_vehicle_id = agency.id

        apply_action(state, "accelerate")

        self.assertEqual((agency.section, agency.space), (1, 2))
        self.assertEqual(agency.mph, 20)

    def test_stationary_reverse_moves_back_one_space_and_ends_at_zero(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.mph = 0
        agency.section = 1
        agency.space = 2
        state.phase = 1
        state.active_vehicle_id = agency.id

        apply_action(state, "reverse")

        self.assertEqual((agency.section, agency.space), (1, 1))
        self.assertEqual(agency.mph, 0)
        self.assertTrue(any("reverses at 10 mph" in entry.message for entry in state.logs))

    def test_reverse_is_only_available_to_stationary_phase_one_cars(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.mph = 0
        state.phase = 2
        state.active_vehicle_id = agency.id

        phase_two_actions = {action.id for action in legal_actions(state)}
        state.phase = 1
        agency.template_id = "bike"
        bike_actions = {action.id for action in legal_actions(state)}

        self.assertNotIn("reverse", phase_two_actions)
        self.assertNotIn("reverse", bike_actions)

    def test_stationary_shoot_does_not_move(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        agency.mph = 0
        agency.section = 1
        agency.space = 1
        agency.lane_pair = 4
        outlaw.section = 1
        outlaw.space = 3
        outlaw.lane_pair = 4
        state.active_vehicle_id = agency.id
        state.dice.queue = [5, 6]

        apply_action(state, "shoot")

        self.assertEqual((agency.section, agency.space), (1, 1))
        self.assertLess(outlaw.damage, 18)

    def test_stationary_ai_uses_legal_move_off_action_when_no_target(self):
        state = new_game()
        outlaw = vehicle_by_id(state, "outlaw-1")
        agency = vehicle_by_id(state, "agency-1")
        outlaw.mph = 0
        outlaw.direction = 1
        outlaw.section = 0
        outlaw.space = 1
        agency.section = 4
        agency.space = 1
        state.phase = 1

        self.assertEqual(ai_choose_action(state, outlaw), "accelerate")

    def test_vehicle_with_no_driver_cannot_shoot(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        agency.driver_skill = 0
        outlaw.section = agency.section
        outlaw.space = agency.space + 2
        outlaw.lane_pair = agency.lane_pair
        state.active_vehicle_id = agency.id

        action_ids = {action.id for action in legal_actions(state)}
        apply_action(state, "shoot")

        self.assertNotIn("shoot", action_ids)
        self.assertEqual(outlaw.damage, 18)
        self.assertTrue(any("no driver" in entry.message for entry in state.logs))

    def test_driver_killed_critical_causes_control_loss(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")

        apply_critical_effect(state, agency, {"kind": "setDriveSkill", "value": 0})

        self.assertEqual(agency.driver_skill, 0)
        self.assertEqual(agency.control_state, "out_of_control")

    def test_steady_forward_moves_active_vehicle(self):
        state = new_game()
        self.assertEqual(state.active_vehicle_id, "agency-1")
        vehicle = vehicle_by_id(state, "agency-1")
        self.assertEqual((vehicle.section, vehicle.space, vehicle.lane_pair), (1, 1, 4))
        apply_action(state, "steady")
        self.assertEqual((vehicle.section, vehicle.space, vehicle.lane_pair), (1, 2, 4))

    def test_hold_still_makes_compulsory_forward_move_for_moving_vehicle(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")

        apply_action(state, "wait")

        self.assertEqual((vehicle.section, vehicle.space, vehicle.lane_pair), (1, 2, 4))
        self.assertTrue(any("compulsory forward move" in entry.message for entry in state.logs))

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

        self.assertEqual((vehicle.section, vehicle.space, vehicle.lane_pair), (3, 3, 5))

    def test_curve_drift_outward_into_occupied_next_space_line_resolves_ram(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        target = vehicle_by_id(state, "outlaw-1")
        vehicle.section = 3
        vehicle.space = 1
        vehicle.lane_pair = 4
        target.section = 3
        target.space = 3
        target.lane_pair = 5
        target.direction = vehicle.direction
        target.mph = 20

        apply_action(state, "drift_right")

        self.assertEqual((vehicle.section, vehicle.space, vehicle.lane_pair), (3, 1, 4))
        self.assertTrue(any(entry.kind == "ram" for entry in state.logs))

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
        vehicle.section = 1
        vehicle.space = 1
        vehicle.lane_pair = 1
        original_direction = vehicle.direction

        apply_action(state, "u_turn")

        self.assertEqual(vehicle.direction, -original_direction)
        self.assertEqual((vehicle.section, vehicle.space, vehicle.lane_pair), (1, 1, 5))
        self.assertFalse(any(entry.kind == "hazard" for entry in state.logs))

    def test_u_turn_from_eleven_to_thirty_mph_triggers_hazard_roll(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.mph = 20
        vehicle.section = 1
        vehicle.space = 1
        vehicle.lane_pair = 1
        vehicle.handling = 6
        vehicle.driver_skill = 6
        state.dice.queue = [1]

        apply_action(state, "u_turn")

        self.assertEqual(vehicle.direction, -1)
        self.assertEqual(vehicle.lane_pair, 5)
        self.assertTrue(any(entry.kind == "hazard" and "U-turn" in entry.message for entry in state.logs))

    def test_u_turn_at_thirty_one_or_more_triggers_control_loss_instead(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.mph = 31
        vehicle.section = 1
        vehicle.space = 1
        vehicle.lane_pair = 1
        vehicle.handling = 0
        vehicle.driver_skill = 0
        state.dice.queue = [6]

        apply_action(state, "u_turn")

        self.assertEqual(vehicle.direction, 1)
        self.assertEqual(vehicle.lane_pair, 1)
        self.assertEqual(vehicle.control_state, "out_of_control")
        self.assertTrue(any(entry.kind == "control-loss" and "too fast" in entry.message for entry in state.logs))

    def test_u_turn_requires_six_lane_width(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.section = 1
        vehicle.space = 1
        vehicle.lane_pair = 4
        vehicle.mph = 10

        apply_action(state, "u_turn")

        self.assertEqual(vehicle.direction, 1)
        self.assertEqual(vehicle.lane_pair, 4)
        self.assertTrue(any(entry.kind == "illegal-action" and "six-lane width" in entry.message for entry in state.logs))

    def test_u_turn_swept_zone_must_be_on_straight(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.section = 2
        vehicle.space = 3
        vehicle.lane_pair = 1
        vehicle.mph = 10

        apply_action(state, "u_turn")

        self.assertEqual(vehicle.direction, 1)
        self.assertEqual(vehicle.lane_pair, 1)
        self.assertTrue(any(entry.kind == "illegal-action" and "must be one space ahead on a straight" in entry.message for entry in state.logs))

    def test_u_turn_contact_zone_blocks_occupied_forward_lanes(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        vehicle.section = 1
        vehicle.space = 1
        vehicle.lane_pair = 1
        vehicle.mph = 10
        outlaw.section = 1
        outlaw.space = 2
        outlaw.lane_pair = 3

        apply_action(state, "u_turn")

        self.assertEqual(vehicle.direction, 1)
        self.assertEqual(vehicle.lane_pair, 1)
        self.assertTrue(any(entry.kind == "illegal-action" and "swept six-lane" in entry.message for entry in state.logs))

    def test_u_turn_from_far_side_lanes_crosses_to_near_side(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.section = 1
        vehicle.space = 1
        vehicle.lane_pair = 7
        vehicle.mph = 10

        apply_action(state, "u_turn")

        self.assertEqual(vehicle.direction, -1)
        self.assertEqual(vehicle.lane_pair, 3)

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

    def test_curve_safety_applies_when_exiting_curve_to_straight(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        vehicle.section = 3
        vehicle.space = 3
        vehicle.lane_pair = 1
        vehicle.mph = 70
        vehicle.handling = 0
        vehicle.driver_skill = 0
        state.dice.queue = [6]

        apply_action(state, "steady")

        self.assertEqual((vehicle.section, vehicle.space), (4, 1))
        self.assertEqual(vehicle.control_state, "out_of_control")
        self.assertTrue(any("exiting curve safety limit" in entry.message for entry in state.logs))

    def test_shooting_range_uses_real_track_section_lengths(self):
        state = new_game()
        shooter = vehicle_by_id(state, "agency-1")
        target = vehicle_by_id(state, "outlaw-1")
        shooter.section = 0
        shooter.space = 3
        shooter.lane_pair = 4
        shooter.direction = 1
        target.section = 3
        target.space = 2
        target.lane_pair = 4
        target.direction = -1

        self.assertIn(target, shoot_targets(state, shooter))

    def test_action_list_present_for_active_vehicle(self):
        state = new_game()
        labels = [action.label for action in legal_actions(state)]
        self.assertIn("Steady Forward", labels)
        self.assertIn("Accelerate", labels)
        self.assertIn("Shoot", labels)

    def test_lightweight_campaign_state_uses_dead_mans_curve_starting_funds(self):
        state = new_game()

        self.assertEqual(state.campaign.funds, 100_000)

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

    def test_hostile_drive_system_applies_extracted_stat_penalties(self):
        state = new_game()
        vehicle = vehicle_by_id(state, "agency-1")
        base = (vehicle.handling, vehicle.acceleration_mph, vehicle.braking_mph)

        apply_hostile_system_effect(state, vehicle, "computerDrive")

        self.assertEqual(vehicle.handling, base[0] - 1)
        self.assertEqual(vehicle.acceleration_mph, base[1] - 5)
        self.assertEqual(vehicle.braking_mph, base[2] - 5)
        self.assertIn("computerDrive", vehicle.hostile_systems)
        self.assertTrue(any(entry.kind == "hack" for entry in state.logs))

    def test_hostile_fire_computer_forces_friendly_only_targets(self):
        state = new_game()
        shooter = vehicle_by_id(state, "agency-1")
        enemy = vehicle_by_id(state, "outlaw-1")
        enemy.section = shooter.section
        enemy.space = shooter.space + 2
        enemy.lane_pair = shooter.lane_pair
        friendly = make_vehicle(
            "agency-2",
            "Wingman",
            "agency",
            "interceptor",
            shooter.section,
            shooter.space + 1,
            shooter.lane_pair,
            1,
            40,
        )

        self.assertIn(enemy, shoot_targets(state, shooter))
        state.vehicles.append(friendly)

        apply_hostile_system_effect(state, shooter, "missileFireComputer")

        self.assertNotIn(enemy, shoot_targets(state, shooter))
        self.assertEqual(shoot_targets(state, shooter), [friendly])
        self.assertIn("shoot", {action.id for action in legal_actions(state, shooter)})

    def test_bulldozer_pushes_stationary_unaligned_target_two_lanes(self):
        state = new_game()
        rammer = vehicle_by_id(state, "agency-1")
        target = vehicle_by_id(state, "outlaw-1")
        rammer.mph = 20
        rammer.section = 1
        rammer.space = 1
        rammer.lane_pair = 4
        target.section = 1
        target.space = 2
        target.lane_pair = 4
        target.mph = 0
        target.aligned_to_grid = False
        state.dice.queue = [6, 6]

        self.assertIn("bulldozer", {action.id for action in legal_actions(state, rammer)})
        apply_action(state, "bulldozer")

        self.assertEqual((rammer.section, rammer.space, rammer.lane_pair), (1, 2, 4))
        self.assertEqual(target.lane_pair, 2)
        self.assertTrue(target.aligned_to_grid)
        self.assertEqual(rammer.damage, 23)
        self.assertEqual(target.damage, 17)
        self.assertTrue(any(entry.kind == "bulldozer" for entry in state.logs))

    def test_bulldozer_not_offered_above_twenty_mph(self):
        state = new_game()
        rammer = vehicle_by_id(state, "agency-1")
        target = vehicle_by_id(state, "outlaw-1")
        rammer.mph = 21
        target.section = rammer.section
        target.space = rammer.space + 1
        target.lane_pair = rammer.lane_pair
        target.mph = 0
        target.aligned_to_grid = False

        self.assertNotIn("bulldozer", {action.id for action in legal_actions(state, rammer)})

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
        outlaw.section = agency.section
        outlaw.space = agency.space + 2
        outlaw.lane_pair = agency.lane_pair
        state.dice.queue = [5, 6]

        apply_action(state, "shoot")

        self.assertEqual((agency.section, agency.space), (1, 2))
        self.assertLess(outlaw.damage, 18)
        self.assertTrue(any(entry.kind == "damage" for entry in state.logs))

    def test_natural_one_always_misses(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        agency.weapon_accuracy = 10
        outlaw.section = agency.section
        outlaw.space = agency.space + 2
        outlaw.lane_pair = agency.lane_pair
        state.dice.queue = [1]

        apply_action(state, "shoot")

        self.assertEqual(outlaw.damage, 18)
        self.assertTrue(any("natural 1" in entry.message for entry in state.logs))

    def test_shooting_uses_counted_range_as_hit_number(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        agency.weapon_accuracy = 0
        outlaw.section = agency.section + 1
        outlaw.space = 2
        outlaw.lane_pair = agency.lane_pair
        state.dice.queue = [3, 6]

        apply_action(state, "shoot")

        self.assertLess(outlaw.damage, 18)
        self.assertTrue(any("vs range 3" in entry.message for entry in state.logs))

    def test_shooting_range_number_is_capped_at_six(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        agency.weapon_accuracy = 0
        agency.section = 0
        agency.space = 1
        outlaw.section = 2
        outlaw.space = 3
        outlaw.lane_pair = agency.lane_pair
        state.dice.queue = [6, 6]

        apply_action(state, "shoot")

        self.assertLess(outlaw.damage, 18)
        self.assertTrue(any("vs range 6" in entry.message for entry in state.logs))

    def test_shooting_is_cancelled_if_movement_hazard_causes_control_loss(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        agency.section = 3
        agency.space = 1
        agency.lane_pair = 1
        agency.mph = 90
        agency.handling = 0
        agency.driver_skill = 0
        outlaw.section = 3
        outlaw.space = 3
        outlaw.lane_pair = 1
        state.dice.queue = [6, 6, 6]

        apply_action(state, "shoot")

        self.assertEqual((agency.section, agency.space), (3, 2))
        self.assertEqual(agency.control_state, "out_of_control")
        self.assertEqual(outlaw.damage, 18)
        self.assertTrue(any("shooting action is cancelled" in entry.message for entry in state.logs))

    def test_shooting_can_destroy_target_and_end_game(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        outlaw.section = agency.section
        outlaw.space = agency.space + 2
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

    def test_passive_marker_dropped_under_tailgater_triggers_when_tailgater_moves_off(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        outlaw.section = agency.section - 1
        outlaw.space = 3
        outlaw.lane_pair = agency.lane_pair
        outlaw.direction = agency.direction
        outlaw.mph = 70
        outlaw.handling = 0
        outlaw.driver_skill = 0

        apply_action(state, "drop_oil")

        marker = state.passive_markers[0]
        self.assertEqual(marker.trigger_on_exit_vehicle_id, outlaw.id)

        state.active_vehicle_id = outlaw.id
        outlaw.acted_this_phase = False
        state.dice.queue = [6]
        apply_action(state, "steady")

        self.assertEqual(state.passive_markers, [])
        self.assertTrue(any(entry.kind == "passive" and "hits oil" in entry.message for entry in state.logs))
        self.assertEqual(outlaw.control_state, "out_of_control")

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
        self.assertEqual((agency.section, agency.space), (1, 2))
        self.assertTrue(any("compulsory straight move" in entry.message for entry in state.logs))

    def test_regain_control_spin_result_applies_spin_template(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.control_state = "out_of_control"
        agency.mph = 40
        agency.handling = 0
        agency.driver_skill = 0
        state.dice.queue = [2, 1]

        apply_action(state, "regain_control")

        self.assertEqual(agency.control_state, "out_of_control")
        self.assertEqual(agency.mph, 20)
        self.assertFalse(agency.aligned_to_grid)
        self.assertTrue(any(entry.kind == "spin" and "anti-clockwise" in entry.message and "-20 mph" in entry.message for entry in state.logs))

    def test_regain_control_spin_result_uses_even_clockwise_spin_test(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.control_state = "out_of_control"
        agency.mph = 40
        agency.handling = 0
        agency.driver_skill = 0
        state.dice.queue = [2, 2]

        apply_action(state, "regain_control")

        self.assertEqual(agency.control_state, "out_of_control")
        self.assertEqual(agency.mph, 20)
        self.assertFalse(agency.aligned_to_grid)
        self.assertTrue(any(entry.kind == "spin" and "clockwise" in entry.message and "-20 mph" in entry.message for entry in state.logs))

    def test_bootlegger_on_straight_success_reverses_facing(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.section = 1
        agency.space = 1
        agency.mph = 40
        agency.handling = 6
        agency.driver_skill = 6
        state.dice.queue = [1]

        apply_action(state, "bootlegger_right")

        self.assertEqual((agency.section, agency.space, agency.lane_pair), (1, 1, 4))
        self.assertEqual(agency.direction, -1)
        self.assertEqual(agency.control_state, "controlled")

    def test_bootlegger_legal_actions_depend_on_four_lane_gap_side(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.mph = 40
        agency.lane_pair = 1

        action_ids = {action.id for action in legal_actions(state)}

        self.assertIn("bootlegger_right", action_ids)
        self.assertNotIn("bootlegger_left", action_ids)

        agency.lane_pair = 7
        action_ids = {action.id for action in legal_actions(state)}

        self.assertIn("bootlegger_left", action_ids)
        self.assertNotIn("bootlegger_right", action_ids)

    def test_bootlegger_failed_control_roll_slides_to_declared_right_side(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.section = 1
        agency.space = 1
        agency.lane_pair = 1
        agency.mph = 120
        agency.handling = 0
        agency.driver_skill = 0
        state.dice.queue = [5, 3]

        apply_action(state, "bootlegger_right")

        self.assertEqual((agency.section, agency.space, agency.lane_pair), (1, 2, 3))
        self.assertEqual(agency.control_state, "out_of_control")
        self.assertTrue(any("position roll 3" in entry.message for entry in state.logs))

    def test_bootlegger_failed_control_roll_slides_to_declared_left_side(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.section = 1
        agency.space = 1
        agency.lane_pair = 7
        agency.mph = 120
        agency.handling = 0
        agency.driver_skill = 0
        state.dice.queue = [5, 3]

        apply_action(state, "bootlegger_left")

        self.assertEqual((agency.section, agency.space, agency.lane_pair), (1, 2, 5))
        self.assertEqual(agency.control_state, "out_of_control")
        self.assertTrue(any("bootlegger left" in entry.message for entry in state.logs))

    def test_bootlegger_rejects_side_without_four_lane_gap(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.section = 1
        agency.space = 1
        agency.lane_pair = 1
        agency.mph = 40

        apply_action(state, "bootlegger_left")

        self.assertEqual((agency.section, agency.space, agency.lane_pair), (1, 1, 1))
        self.assertEqual(agency.direction, 1)
        self.assertTrue(any("four-lane gap" in entry.message for entry in state.logs))

    def test_bootlegger_natural_six_causes_tyre_critical_and_out_of_control_move(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.section = 1
        agency.space = 1
        agency.lane_pair = 1
        agency.mph = 50
        state.dice.queue = [6]

        apply_action(state, "bootlegger_right")

        self.assertEqual((agency.section, agency.space, agency.lane_pair), (1, 2, 1))
        self.assertEqual(agency.control_state, "out_of_control")
        self.assertIn("wheels: tyreDestroyed", agency.critical_notes)
        self.assertTrue(any("natural 6" in entry.message for entry in state.logs))

    def test_bootlegger_on_curve_passes_control_test_but_moves_normally(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.section = 3
        agency.space = 1
        agency.lane_pair = 4
        agency.mph = 40
        agency.handling = 6
        agency.driver_skill = 6
        state.dice.queue = [1]

        apply_action(state, "bootlegger_right")

        self.assertEqual((agency.section, agency.space, agency.lane_pair), (3, 2, 4))
        self.assertEqual(agency.direction, 1)
        self.assertEqual(agency.control_state, "controlled")
        self.assertTrue(any("moves normally" in entry.message for entry in state.logs))

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
        outlaw.space = 2
        outlaw.lane_pair = 6
        outlaw.direction = -1
        outlaw.mph = 50
        agency.section = 2
        agency.space = 1
        agency.lane_pair = 3

        self.assertEqual(state.track_section_types[outlaw.section], "curve50to80_left")
        self.assertEqual(ai_choose_action(state, outlaw), "steady")

    def test_ai_can_choose_legal_outward_curve_drift(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        outlaw = vehicle_by_id(state, "outlaw-1")
        outlaw.section = 3
        outlaw.space = 1
        outlaw.lane_pair = 4
        outlaw.direction = 1
        outlaw.mph = 50
        agency.section = 4
        agency.space = 1
        agency.lane_pair = 5
        state.passive_markers.append(PassiveMarker("smoke-curve-ai", "smoke", 3, 2, 3, "agency"))

        self.assertEqual(state.track_section_types[outlaw.section], "curve50to80_left")
        self.assertEqual(ai_choose_action(state, outlaw), "drift_right")

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

import unittest

from dark_future.engine import apply_action, new_game, vehicle_by_id
from dark_future.ui_model import (
    build_action_panel_model,
    build_campaign_summary_model,
    build_debug_overlay_model,
    build_garage_loadout_model,
    build_log_model,
    build_tactical_board_model,
    build_vehicle_design_model,
    build_vehicle_records_model,
)


class UiModelTests(unittest.TestCase):
    def test_tactical_board_summary_contains_track_tokens_and_active_vehicle(self):
        state = new_game()

        model = build_tactical_board_model(state)

        self.assertEqual(model.turn, 1)
        self.assertEqual(model.phase, 1)
        self.assertEqual(len(model.track_sections), state.track_sections)
        self.assertEqual(model.track_sections[0].label, "1")
        self.assertFalse(model.track_sections[0].is_curve)
        self.assertTrue(all(cell.valid for cell in model.cells if cell.section == 0))
        self.assertEqual(model.active_vehicle_id, "agency-1")
        agency = next(vehicle for vehicle in model.vehicles if vehicle.id == "agency-1")
        self.assertTrue(agency.active)
        self.assertEqual(agency.lane_rows, (4, 5))
        self.assertEqual(agency.occupied_lanes, (4, 5))

    def test_tactical_board_summary_exposes_spun_vehicle_footprint(self):
        state = new_game()
        agency_state = vehicle_by_id(state, "agency-1")
        agency_state.spin_facing_degrees = 135

        model = build_tactical_board_model(state)

        agency = next(vehicle for vehicle in model.vehicles if vehicle.id == "agency-1")
        self.assertEqual(agency.occupied_lanes, (3, 4, 5, 6))

    def test_tactical_board_summary_includes_passive_markers(self):
        state = new_game()
        apply_action(state, "drop_oil")

        model = build_tactical_board_model(state)

        self.assertEqual(len(model.markers), 1)
        self.assertEqual(model.markers[0].kind, "oil")
        self.assertEqual(model.markers[0].owner_side, "agency")

    def test_vehicle_records_include_core_stats_and_damage_status(self):
        state = new_game()
        outlaw = vehicle_by_id(state, "outlaw-1")
        outlaw.destroyed = True
        outlaw.critical_notes.append("weapon disabled")

        model = build_vehicle_records_model(state)

        record = next(item for item in model.records if item.id == "outlaw-1")
        self.assertEqual(record.status, "destroyed")
        self.assertEqual(record.weapon, "6mm MG")
        self.assertEqual(record.position, "section 7, space 3, LP4")
        self.assertEqual(record.critical_notes, ("weapon disabled",))

    def test_campaign_summary_placeholder_exposes_campaign_state(self):
        state = new_game()
        state.campaign.funds = 42000
        state.campaign.settlement_pending = True

        model = build_campaign_summary_model(state)

        self.assertEqual(model.name, "Roadside Sanction")
        self.assertEqual(model.funds, 42000)
        self.assertTrue(model.settlement_pending)
        self.assertEqual(model.scenario, "intercept")
        self.assertIn("Campaign actions", model.placeholder)
        self.assertEqual(model.roster, ("Alex Decker", "Mara Voss"))

    def test_vehicle_design_model_exposes_garage_catalog_and_selected_vehicle(self):
        state = new_game()

        model = build_vehicle_design_model(state, "agency-1")

        self.assertEqual(model.title, "Vehicle Design / Garage")
        self.assertEqual(model.selected_vehicle_id, "agency-1")
        self.assertTrue(any(item.id == "interceptor" for item in model.vehicles))
        self.assertTrue(any(item.id == "interceptorV6" for item in model.chassis))
        chain_gun = next(item for item in model.equipment if item.id == "chainGun")
        self.assertEqual(chain_gun.cost, 22000)
        self.assertEqual(chain_gun.weight, 300)
        self.assertEqual(chain_gun.icon_id, "chainGun")
        self.assertIsNotNone(model.selected_vehicle)
        self.assertEqual(model.selected_vehicle.template_id, "interceptor")
        self.assertEqual(model.selected_vehicle.payload_limit, 850)
        self.assertEqual(model.selected_vehicle.installed_items, ("15mm Autocannon (runtime weapon)",))
        self.assertTrue(any("Payload:" in line for line in model.summary_lines))
        self.assertTrue(any("campaign payload ledger" in message for message in model.validation_messages))

    def test_vehicle_design_model_reports_missing_selected_vehicle(self):
        state = new_game()

        model = build_vehicle_design_model(state, "missing-car")

        self.assertEqual(model.selected_vehicle_id, "missing-car")
        self.assertIsNone(model.selected_vehicle)
        self.assertTrue(any("missing-car" in message for message in model.validation_messages))

    def test_garage_loadout_model_exposes_hardpoints_and_runtime_weapon(self):
        state = new_game()

        model = build_garage_loadout_model(state, "agency-1")

        self.assertEqual(model.vehicle_id, "agency-1")
        self.assertEqual(model.template_id, "interceptor")
        mount_ids = {mount.id for mount in model.mounts}
        self.assertIn("hood", mount_ids)
        self.assertIn("passiveLeft", mount_ids)
        self.assertIn("passiveRight", mount_ids)
        hood = next(mount for mount in model.mounts if mount.id == "hood")
        self.assertEqual(hood.installed_weapon_id, "autocannon15mm")
        self.assertEqual(hood.icon_weapon_id, "autocannon15mm")
        self.assertEqual(model.payload_used, 250)
        self.assertEqual(model.payload_limit, 850)
        self.assertTrue(any("WLF sheet images" in message for message in model.validation_messages))

    def test_action_panel_model_wraps_legal_actions_and_actor_lines(self):
        state = new_game()

        model = build_action_panel_model(state)

        self.assertEqual(model.actor_id, "agency-1")
        self.assertEqual(model.actor_label, "Interceptor")
        self.assertTrue(any("Speed: 60 mph" in line for line in model.actor_lines))
        actions = {action.id: action for action in model.actions}
        self.assertIn("steady", actions)
        self.assertEqual(actions["steady"].hotkey, "1")
        self.assertTrue(actions["shoot"].enabled)

    def test_action_panel_model_handles_no_active_vehicle(self):
        state = new_game()
        state.active_vehicle_id = None

        model = build_action_panel_model(state)

        self.assertIsNone(model.actor_id)
        self.assertEqual(model.actor_label, "None")
        self.assertEqual(
            [action.id for action in model.actions],
            ["next_phase", "save_game", "load_game"],
        )

    def test_log_model_keeps_recent_entries_and_source_payload(self):
        state = new_game()
        apply_action(state, "steady")

        model = build_log_model(state, limit=2)

        self.assertEqual(len(model.entries), 2)
        self.assertEqual(model.total_entries, len(state.logs))
        self.assertTrue(any(entry.kind == "move" for entry in model.entries))
        move_entry = next(entry for entry in model.entries if entry.kind == "move")
        self.assertIsNotNone(move_entry.source)
        self.assertEqual(move_entry.source.book, "Dark Future Rulebook")

    def test_debug_overlay_has_movement_hazard_and_contact_payloads(self):
        state = new_game()
        agency = vehicle_by_id(state, "agency-1")
        agency.section = 3
        agency.lane_pair = 7

        model = build_debug_overlay_model(state)

        movement = next(item for item in model.movement if item.vehicle_id == "agency-1")
        self.assertEqual(movement.speed_factor, 3)
        self.assertEqual(movement.phase_moves, 1)
        self.assertEqual(movement.current, "4.1 LP7")
        self.assertEqual(movement.forward, "4.2 LP7")

        hazard = next(item for item in model.hazards if item.vehicle_id == "agency-1")
        self.assertEqual(hazard.curve_safety_limit_mph, 80)

        contact = next(item for item in model.contacts if item.shooter_id == "agency-1")
        self.assertEqual(contact.target_ids, ())
        self.assertTrue(any("Movement graph" in item for item in model.placeholders))

    def test_board_model_exposes_short_inner_curve_lanes_from_trace_image(self):
        state = new_game()

        model = build_tactical_board_model(state)

        curve = model.track_sections[3]
        self.assertEqual(curve.kind, "curve50to80_left")
        self.assertEqual(curve.spaces, 5)
        inner_space_four = next(
            cell for cell in model.cells if cell.section == 3 and cell.lane == 1 and cell.space == 4
        )
        outer_space_five = next(
            cell for cell in model.cells if cell.section == 3 and cell.lane == 8 and cell.space == 5
        )
        self.assertFalse(inner_space_four.valid)
        self.assertTrue(outer_space_five.valid)
        self.assertEqual(outer_space_five.speed_limit_mph, 80)


if __name__ == "__main__":
    unittest.main()

import os
import math
from pathlib import Path
import shutil
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from dark_future import ui_pygame
from dark_future.engine import LogEntry, save_game
from dark_future.track_layout import curve_lane_boundary_radii


class PygameMissionFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(".test-ui-saves")
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir()
        self.old_save_dir = ui_pygame.SAVE_DIR
        self.old_default_save = ui_pygame.DEFAULT_MISSION_SAVE_PATH
        ui_pygame.SAVE_DIR = self.temp_dir
        ui_pygame.DEFAULT_MISSION_SAVE_PATH = self.temp_dir / "last_mission.json"

    def tearDown(self):
        pygame.quit()
        ui_pygame.SAVE_DIR = self.old_save_dir
        ui_pygame.DEFAULT_MISSION_SAVE_PATH = self.old_default_save
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_mission_tab_opens_menu_then_new_mission_picker(self):
        app = ui_pygame.App()

        app._dispatch_button("open_mission")
        self.assertEqual(app.state.mode, "mission_menu")

        app._dispatch_button("new_mission")
        self.assertEqual(app.state.mode, "mission_new")

        app._dispatch_button("new_mission:pursuit")
        self.assertEqual(app.state.mode, "tactical")
        self.assertEqual(app.state.scenario_id, "pursuit")
        self.assertEqual(app.state.save_path, str(ui_pygame.DEFAULT_MISSION_SAVE_PATH))

    def test_campaign_contract_button_starts_current_campaign_scenario(self):
        app = ui_pygame.App()
        app.state.campaign.current_scenario = "pursuit"

        app._dispatch_button("start_campaign_contract")

        self.assertEqual(app.state.mode, "tactical")
        self.assertEqual(app.state.scenario_id, "pursuit")
        self.assertIn("Started campaign Pursuit contract", app.ui_status)

    def test_campaign_view_exposes_settlement_and_new_contract_actions_when_game_over(self):
        app = ui_pygame.App()
        app._set_screen("campaign")
        app.state.game_over = True
        app.state.winner = "agency"
        app.state.campaign.settlement_pending = True

        app._draw()

        labels = [button.label for button in app.buttons]
        self.assertIn("Settle Campaign", labels)
        self.assertIn("New Contract", labels)

    def test_continue_loads_last_saved_mission(self):
        app = ui_pygame.App()
        app.state.campaign.funds = 12345
        save_game(app.state, ui_pygame.DEFAULT_MISSION_SAVE_PATH)

        app.state.campaign.funds = 999
        app._dispatch_button("continue_mission")

        self.assertEqual(app.state.mode, "tactical")
        self.assertEqual(app.state.campaign.funds, 12345)
        self.assertEqual(app.state.save_path, str(ui_pygame.DEFAULT_MISSION_SAVE_PATH))

    def test_mission_load_summary_shows_contract_turn_and_funds(self):
        app = ui_pygame.App()
        app.state.campaign.funds = 54321
        app.state.turn = 3
        app.state.phase = 4
        save_game(app.state, ui_pygame.DEFAULT_MISSION_SAVE_PATH)

        summary = app._mission_save_summary(ui_pygame.DEFAULT_MISSION_SAVE_PATH)

        self.assertIn("Intercept", summary)
        self.assertIn("T3 P4", summary)
        self.assertIn("$54321", summary)

    def test_garage_fit_preview_uses_design_backend_weight_effects(self):
        app = ui_pygame.App()
        app._dispatch_button("screen:garage")
        current, error = app._design_record(app._current_design_spec())
        self.assertIsNone(error)

        app._dispatch_button("select_mount:roof")
        app._dispatch_button("select_catalog:chainGun")
        preview, error = app._design_record(app._preview_design_spec())

        self.assertIsNone(error)
        self.assertGreater(preview["totalWeight"], current["totalWeight"])
        self.assertLessEqual(preview["maximumSpeedMph"], current["maximumSpeedMph"])
        self.assertLessEqual(preview["accelerationMph"], current["accelerationMph"])

        app._dispatch_button("fit_selected_item")
        saved, error = app._design_record(app._current_design_spec())
        self.assertIsNone(error)
        self.assertEqual(saved["totalWeight"], preview["totalWeight"])

        app._dispatch_button("remove_mount_item")
        restored, error = app._design_record(app._current_design_spec())
        self.assertIsNone(error)
        self.assertLess(restored["totalWeight"], saved["totalWeight"])

    def test_board_zoom_changes_track_scale_and_is_bounded(self):
        app = ui_pygame.App()
        initial_cell_w = app._cell_w()

        app._zoom_board(1)
        self.assertGreater(app._cell_w(), initial_cell_w)

        for _ in range(30):
            app._zoom_board(-1)
        self.assertEqual(app.board_zoom, 0.6)

        for _ in range(30):
            app._zoom_board(1)
        self.assertEqual(app.board_zoom, 1.8)

    def test_curve_speed_labels_are_placed_on_lane_exit_edge(self):
        app = ui_pygame.App()
        app._set_screen("tactical")
        board = ui_pygame.build_tactical_board_model(app.state)
        placements = app._section_placements(board)
        section = board.track_sections[3]
        placement = placements[3]
        cell = next(
            item
            for item in board.cells
            if item.section == 3 and item.lane == 7 and item.space == section.spaces
        )

        x, y = app._curve_speed_label_position(
            placement,
            section,
            cell,
            app._cell_w(),
            app._lane_w(),
            lane_end=8,
        )
        radius = math.hypot(x - placement.center[0], y - placement.center[1])
        angle = math.degrees(math.atan2(y - placement.center[1], x - placement.center[0]))
        expected_angle = placement.heading_degrees - placement.turn_direction * 90
        expected_angle += placement.exit_heading_degrees - placement.heading_degrees
        expected_angle -= (placement.exit_heading_degrees - placement.heading_degrees) / section.spaces * 0.18
        boundaries = curve_lane_boundary_radii(
            section.kind,
            lane_width=app._lane_w(),
            car_length=app._cell_w(),
        )

        self.assertAlmostEqual(radius, (boundaries[6] + boundaries[8]) / 2)
        self.assertAlmostEqual(angle, expected_angle)

    def test_token_screen_heading_uses_pygame_rotation_direction(self):
        app = ui_pygame.App()
        pose = ui_pygame.TokenPose((0, 0), 60, 10, 20)

        self.assertEqual(app._token_render_angle(pose), -60)

    def test_tactical_screen_hides_track_generation_controls(self):
        app = ui_pygame.App()
        app._set_screen("tactical")
        before = tuple(app.state.track_section_types)

        app._handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_g))
        app._draw()

        self.assertEqual(tuple(app.state.track_section_types), before)
        self.assertNotIn("Track", [button.label for button in app.buttons])

    def test_log_panel_scrolls_independently_of_board_zoom(self):
        app = ui_pygame.App()
        app._set_screen("tactical")
        app.state.logs = [LogEntry(f"line {index}", "test") for index in range(12)]
        before_zoom = app.board_zoom

        app._scroll_log(3)

        self.assertEqual(app.board_zoom, before_zoom)
        self.assertEqual(app.log_scroll, 3)
        self.assertEqual([entry.message for entry in app._visible_log_entries(tuple(app.state.logs))][0], "line 2")


if __name__ == "__main__":
    unittest.main()

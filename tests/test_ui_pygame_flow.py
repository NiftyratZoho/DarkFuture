import os
import math
from pathlib import Path
import shutil
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from dark_future import ui_pygame
from dark_future.engine import save_game
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

    def test_continue_loads_last_saved_mission(self):
        app = ui_pygame.App()
        app.state.campaign.funds = 12345
        save_game(app.state, ui_pygame.DEFAULT_MISSION_SAVE_PATH)

        app.state.campaign.funds = 999
        app._dispatch_button("continue_mission")

        self.assertEqual(app.state.mode, "tactical")
        self.assertEqual(app.state.campaign.funds, 12345)
        self.assertEqual(app.state.save_path, str(ui_pygame.DEFAULT_MISSION_SAVE_PATH))

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


if __name__ == "__main__":
    unittest.main()

import unittest

from dark_future.track import (
    LANE_COUNT,
    can_drift,
    drift_lane_pair,
    forward_position,
    is_legal_lane_pair,
    is_valid_lane_space,
    is_valid_position,
    lane_pair_safety_limit,
    lane_pair_section_count,
    lane_section_count,
    lane_speed_limit,
    legal_lane_pairs,
    occupied_lanes,
    piece_angle_degrees,
    piece_family,
    piece_max_spaces,
    render_grid_data,
    straight_spaces,
)


class TrackGeometryTests(unittest.TestCase):
    def test_track_uses_eight_lanes_and_seven_vehicle_lane_pairs(self):
        self.assertEqual(LANE_COUNT, 8)
        self.assertEqual(legal_lane_pairs(), (1, 2, 3, 4, 5, 6, 7))
        self.assertTrue(is_legal_lane_pair(1))
        self.assertTrue(is_legal_lane_pair(7))
        self.assertFalse(is_legal_lane_pair(0))
        self.assertFalse(is_legal_lane_pair(8))
        self.assertEqual(occupied_lanes(4), (4, 5))

    def test_straight_has_three_spaces_and_no_printed_speed_limits(self):
        self.assertEqual(straight_spaces(), 3)
        self.assertEqual(lane_pair_section_count("straight", 1), 3)
        self.assertIsNone(lane_speed_limit("straight", 4))
        self.assertIsNone(lane_pair_safety_limit("straight", 4))
        self.assertTrue(is_valid_position("straight", 7, 3))
        self.assertFalse(is_valid_position("straight", 7, 4))

    def test_curve_30_to_60_speed_limits_and_sections_follow_lane_data(self):
        self.assertEqual(lane_speed_limit("curve30to60", 1), 30)
        self.assertEqual(lane_speed_limit("curve30to60", 8), 60)
        self.assertEqual(lane_section_count("curve30to60", 1), 2)
        self.assertEqual(lane_section_count("curve30to60", 3), 2)
        self.assertEqual(lane_section_count("curve30to60", 4), 3)
        self.assertEqual(lane_section_count("curve30to60", 6), 4)
        self.assertEqual(lane_section_count("curve30to60", 8), 4)
        self.assertEqual(lane_pair_safety_limit("curve30to60", 1), 30)
        self.assertEqual(lane_pair_safety_limit("curve30to60", 7), 60)
        self.assertEqual(lane_pair_section_count("curve30to60", 1), 2)
        self.assertEqual(lane_pair_section_count("curve30to60", 2), 2)
        self.assertEqual(lane_pair_section_count("curve30to60", 3), 3)
        self.assertEqual(lane_pair_section_count("curve30to60", 5), 4)
        self.assertEqual(lane_pair_section_count("curve30to60", 7), 4)
        self.assertEqual(piece_max_spaces("curve30to60"), 4)
        self.assertEqual(piece_family("curve30to60"), "tightCorner")
        self.assertEqual(piece_angle_degrees("curve30to60"), 90)

    def test_curve_50_to_80_speed_limits_and_sections_follow_lane_data(self):
        self.assertEqual(lane_speed_limit("curve50to80", 1), 50)
        self.assertEqual(lane_speed_limit("curve50to80", 8), 80)
        self.assertEqual(lane_section_count("curve50to80", 1), 3)
        self.assertEqual(lane_section_count("curve50to80", 3), 3)
        self.assertEqual(lane_section_count("curve50to80", 4), 4)
        self.assertEqual(lane_section_count("curve50to80", 5), 4)
        self.assertEqual(lane_section_count("curve50to80", 6), 5)
        self.assertEqual(lane_section_count("curve50to80", 8), 5)
        self.assertEqual(lane_pair_safety_limit("curve50to80", 5), 70)
        self.assertEqual(lane_pair_safety_limit("curve50to80", 7), 80)
        self.assertEqual(lane_pair_section_count("curve50to80", 1), 3)
        self.assertEqual(lane_pair_section_count("curve50to80", 3), 4)
        self.assertEqual(lane_pair_section_count("curve50to80", 5), 5)
        self.assertEqual(lane_pair_section_count("curve50to80", 7), 5)
        self.assertEqual(piece_max_spaces("curve50to80"), 5)
        self.assertEqual(piece_family("curve50to80"), "broadBend")
        self.assertEqual(piece_angle_degrees("curve50to80"), 60)

    def test_section_space_validity_is_per_lane_and_per_occupied_pair(self):
        self.assertTrue(is_valid_lane_space("curve50to80", 5, 3))
        self.assertTrue(is_valid_lane_space("curve50to80", 5, 4))
        self.assertFalse(is_valid_lane_space("curve50to80", 5, 5))
        self.assertTrue(is_valid_lane_space("curve50to80", 6, 5))
        self.assertTrue(is_valid_position("curve50to80", 5, 5))
        self.assertFalse(is_valid_position("curve50to80", 4, 5))
        self.assertFalse(is_valid_position("curve50to80", 8, 1))

    def test_forward_movement_respects_variable_curve_lengths(self):
        layout = ("straight", "curve30to60_left", "straight")

        self.assertEqual(forward_position(layout, 1, 2, 1), (2, 1))
        self.assertEqual(forward_position(layout, 1, 2, 7), (1, 3))
        self.assertEqual(forward_position(layout, 1, 4, 7), (2, 1))
        self.assertEqual(forward_position(layout, 2, 1, 4, direction=-1), (1, 3))
        self.assertIsNone(forward_position(layout, 2, 3, 4))

    def test_drift_lane_pair_constraints(self):
        self.assertEqual(drift_lane_pair("straight", 4, "left"), 3)
        self.assertEqual(drift_lane_pair("straight", 4, "right"), 5)
        self.assertIsNone(drift_lane_pair("straight", 1, "left"))
        self.assertIsNone(drift_lane_pair("straight", 7, "right"))

        self.assertEqual(drift_lane_pair("curve30to60", 4, "outward"), 5)
        self.assertFalse(can_drift("curve30to60", 7, "outward"))
        self.assertEqual(
            drift_lane_pair("curve30to60", 4, "inward", allow_inward_curve_drift=True),
            3,
        )
        self.assertFalse(can_drift("curve30to60", 4, "inward"))
        with self.assertRaises(ValueError):
            drift_lane_pair("curve30to60", 4, "left")

    def test_render_grid_data_exposes_lanes_spaces_cells_and_lane_pairs(self):
        grid = render_grid_data("curve30to60_right")
        self.assertEqual(grid["pieceType"], "curve30to60")
        self.assertEqual(grid["kind"], "curve")
        self.assertEqual(grid["family"], "tightCorner")
        self.assertEqual(grid["angleDegrees"], 90)
        self.assertEqual(grid["lanes"], 8)
        self.assertEqual(grid["spaces"], 4)
        self.assertEqual(len(grid["cells"]), 32)
        self.assertEqual(len(grid["lanePairs"]), 7)

        lane_one_space_three = next(
            cell for cell in grid["cells"] if cell["lane"] == 1 and cell["space"] == 3
        )
        lane_eight_space_four = next(
            cell for cell in grid["cells"] if cell["lane"] == 8 and cell["space"] == 4
        )
        self.assertFalse(lane_one_space_three["valid"])
        self.assertTrue(lane_eight_space_four["valid"])
        self.assertEqual(grid["lanePairs"][0]["safetyLimitMph"], 30)
        self.assertEqual(grid["lanePairs"][-1]["spaces"], 4)


if __name__ == "__main__":
    unittest.main()

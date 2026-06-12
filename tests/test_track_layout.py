import unittest
import math

from dark_future.track_layout import (
    curve_lane_boundary_radii,
    curve_lane_center_radii,
    layout_track_sections,
    point_on_curve,
    point_on_straight,
)


def distance(point_a, point_b):
    return math.hypot(point_a[0] - point_b[0], point_a[1] - point_b[1])


class TrackLayoutTests(unittest.TestCase):
    def test_straights_connect_in_current_heading(self):
        placements = layout_track_sections(
            ("straight", "straight"),
            lane_width=10,
            car_length=30,
        )

        self.assertEqual(placements[0].entry, (0.0, 0.0))
        self.assertAlmostEqual(placements[0].exit[0], 90)
        self.assertAlmostEqual(placements[0].exit[1], 0)
        self.assertEqual(placements[1].entry, placements[0].exit)
        self.assertEqual(placements[1].heading_degrees, 0)

    def test_right_tight_corner_rotates_next_section_ninety_degrees(self):
        placements = layout_track_sections(
            ("straight", "curve30to60_right", "straight"),
            lane_width=10,
            car_length=30,
        )

        self.assertAlmostEqual(placements[1].exit_heading_degrees, -90)
        self.assertEqual(placements[2].entry, placements[1].exit)
        self.assertAlmostEqual(placements[2].heading_degrees, -90)
        self.assertLess(placements[2].exit[1], placements[2].entry[1])

    def test_left_broad_bend_rotates_next_section_sixty_degrees(self):
        placements = layout_track_sections(
            ("straight", "curve50to80_left", "straight"),
            lane_width=10,
            car_length=30,
        )

        self.assertAlmostEqual(placements[1].exit_heading_degrees, 60)
        self.assertEqual(placements[2].entry, placements[1].exit)
        self.assertAlmostEqual(placements[2].heading_degrees, 60)

    def test_left_curve_connects_on_boundary_edges(self):
        lane_width = 10
        car_length = 30
        placements = layout_track_sections(
            ("straight", "curve50to80_left", "straight"),
            lane_width=lane_width,
            car_length=car_length,
        )
        curve = placements[1]
        boundaries = curve_lane_boundary_radii(
            curve.piece_type,
            lane_width=lane_width,
            car_length=car_length,
        )

        self.assertIsNotNone(curve.center)
        self.assertIsNotNone(curve.radius)
        self.assertAlmostEqual(distance(curve.center, curve.entry), boundaries[-1])
        self.assertAlmostEqual(distance(curve.center, curve.exit), boundaries[-1])

    def test_right_curve_connects_on_centerline(self):
        placements = layout_track_sections(
            ("straight", "curve30to60_right", "straight"),
            lane_width=10,
            car_length=30,
        )
        curve = placements[1]

        self.assertIsNotNone(curve.center)
        self.assertIsNotNone(curve.radius)
        self.assertAlmostEqual(distance(curve.center, curve.entry), curve.radius)
        self.assertAlmostEqual(distance(curve.center, curve.exit), curve.radius)

    def test_points_follow_section_geometry(self):
        placements = layout_track_sections(
            ("straight", "curve50to80_left"),
            lane_width=10,
            car_length=30,
        )
        straight_point = point_on_straight(
            placements[0],
            space=2,
            lane_pair=4,
            lane_width=10,
            car_length=30,
        )
        curve_point = point_on_curve(
            placements[1],
            space=2,
            lane_pair=4,
            lane_width=10,
            car_length=30,
            spaces=4,
        )

        self.assertGreater(straight_point[0], 30)
        self.assertNotEqual(round(curve_point[0], 3), round(straight_point[0], 3))

    def test_curve_vehicle_center_uses_occupied_lane_centers(self):
        lane_width = 10
        car_length = 30
        placements = layout_track_sections(
            ("straight", "curve50to80_left"),
            lane_width=lane_width,
            car_length=car_length,
        )
        curve = placements[1]
        point = point_on_curve(
            curve,
            space=2,
            lane_pair=4,
            lane_width=lane_width,
            car_length=car_length,
        )
        centers = curve_lane_center_radii(curve.piece_type, car_length=car_length)

        self.assertAlmostEqual(
            distance(curve.center, point),
            (centers[3] + centers[4]) / 2,
        )

    def test_straight_after_clockwise_curve_counts_lanes_from_connected_edge(self):
        placements = layout_track_sections(
            ("straight", "curve50to80_left", "straight"),
            lane_width=10,
            car_length=30,
        )
        following = placements[2]
        lane_pair_1 = point_on_straight(
            following,
            space=1,
            lane_pair=1,
            lane_width=10,
            car_length=30,
        )
        lane_pair_7 = point_on_straight(
            following,
            space=1,
            lane_pair=7,
            lane_width=10,
            car_length=30,
        )

        self.assertEqual(following.lane_direction, -1)
        self.assertGreater(distance(following.entry, lane_pair_1), distance(following.entry, lane_pair_7))


if __name__ == "__main__":
    unittest.main()

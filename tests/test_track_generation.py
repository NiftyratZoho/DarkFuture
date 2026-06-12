import unittest

from dark_future.track_generation import (
    GeneratedSection,
    RollingTrack,
    SequenceDice,
    TrackInventory,
    build_initial_track,
    generate_for_lead,
    generated_curve_direction,
    generated_curve_family,
)
from dark_future.data_loader import track_inventory


class TrackGenerationTests(unittest.TestCase):
    def test_dice_mapping_matches_track_generation_rules(self):
        self.assertFalse(generated_curve_family(1) == "tightCorner")
        self.assertEqual(generated_curve_family(4), "broadBend")
        self.assertEqual(generated_curve_family(5), "tightCorner")
        self.assertEqual(generated_curve_direction(1), "left")
        self.assertEqual(generated_curve_direction(2), "right")

    def test_initial_track_starts_with_three_straights_and_generates_to_ten(self):
        dice = SequenceDice([1, 2, 3, 4, 1, 2, 3])

        track = build_initial_track(dice)

        self.assertEqual(len(track.sections), 10)
        self.assertEqual(track.piece_types, ["straight"] * 10)
        self.assertTrue(all(section.automatic for section in track.sections[:3]))
        self.assertFalse(track.sections[3].automatic)

    def test_initial_curve_is_followed_by_automatic_straight(self):
        dice = SequenceDice([5, 6, 1, 1, 1, 1, 1, 1])

        track = build_initial_track(dice)

        self.assertEqual(track.piece_types[:5], ["straight", "straight", "straight", "curve30to60_left", "straight"])
        self.assertFalse(track.sections[3].automatic)
        self.assertTrue(track.sections[4].automatic)

    def test_unavailable_curve_family_switches_to_other_curve_family(self):
        inventory = TrackInventory(broad_bends=0, tight_corners=2)
        dice = SequenceDice([5, 1, 2])

        track = build_initial_track(dice, inventory=inventory, target_sections=5)

        self.assertEqual(track.piece_types, ["straight", "straight", "straight", "curve30to60_right", "straight"])

    def test_unavailable_straight_ends_generation(self):
        inventory = TrackInventory(straights=3)
        dice = SequenceDice([1])

        track = build_initial_track(dice, inventory=inventory)

        self.assertTrue(track.ended)
        self.assertEqual(track.piece_types, ["straight", "straight", "straight"])

    def test_inventory_adapter_uses_confirmed_counts_and_leaves_unknowns_unlimited(self):
        inventory = TrackInventory.from_rule_inventory(track_inventory())

        self.assertEqual(inventory.straights, 7)
        self.assertIsNone(inventory.broad_bends)
        self.assertIsNone(inventory.tight_corners)

    def test_after_two_same_direction_curves_next_curve_is_forced_opposite(self):
        dice = SequenceDice(
            [
                5, 1, 1,  # broad left
                5, 1, 1,  # broad left
                5, 1, 1,  # rolled left, forced right
            ]
        )
        track = build_initial_track(dice, target_sections=9)

        curves = [section for section in track.sections if section.is_curve]

        self.assertEqual([curve.direction for curve in curves], ["left", "left", "right"])

    def test_continuous_generation_adds_straights_until_three_ahead_are_visible(self):
        track = RollingTrack.starting_straights()
        dice = SequenceDice([1])

        generate_for_lead(track, lead_section_index=0, dice=dice)

        self.assertEqual(track.piece_types, ["straight", "straight", "straight", "straight"])

    def test_continuous_generation_stops_when_curve_blocks_view(self):
        track = RollingTrack.starting_straights()
        dice = SequenceDice([5, 5, 2])

        generate_for_lead(track, lead_section_index=0, dice=dice)

        self.assertEqual(track.piece_types, ["straight", "straight", "straight", "curve30to60_right"])
        self.assertEqual(track.pending_mandatory_straight_after_curve_index, 3)

    def test_mandatory_straight_after_curve_is_placed_when_lead_moves_onto_curve(self):
        track = RollingTrack(
            sections=[
                GeneratedSection("straight", automatic=True),
                GeneratedSection("straight", automatic=True),
                GeneratedSection("straight", automatic=True),
                GeneratedSection("curve50to80", "left"),
            ],
            pending_mandatory_straight_after_curve_index=3,
        )

        generate_for_lead(track, lead_section_index=3, dice=SequenceDice([]))

        self.assertEqual(track.piece_types[-2:], ["curve50to80_left", "straight"])
        self.assertTrue(track.sections[-1].automatic)

    def test_continuous_generation_never_leaves_more_than_seven_sections_in_play(self):
        track = RollingTrack(
            sections=[
                GeneratedSection("straight", automatic=True),
                GeneratedSection("straight", automatic=True),
                GeneratedSection("straight", automatic=True),
                GeneratedSection("straight"),
                GeneratedSection("straight"),
                GeneratedSection("straight"),
                GeneratedSection("straight"),
            ]
        )
        dice = SequenceDice([1])

        generate_for_lead(track, lead_section_index=4, dice=dice)

        self.assertEqual(len(track.sections), 7)
        self.assertEqual(len(track.removed_sections), 1)
        self.assertEqual(track.removed_sections[0].kind, "straight")

    def test_continuous_generation_does_not_generate_past_existing_curve(self):
        track = RollingTrack(
            sections=[
                GeneratedSection("straight", automatic=True),
                GeneratedSection("straight", automatic=True),
                GeneratedSection("curve30to60", "left"),
            ]
        )

        generate_for_lead(track, lead_section_index=0, dice=SequenceDice([]))

        self.assertEqual(track.piece_types, ["straight", "straight", "curve30to60_left"])


if __name__ == "__main__":
    unittest.main()

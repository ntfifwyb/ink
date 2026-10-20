import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ink.stats import (  # noqa: E402
    DeckCounts,
    TreeNode,
    current_streak,
    longest_streak,
    minutes_left,
    rollup,
    secs_in_range,
    share_of_days_studied,
    study_day_average,
    week_start_offset,
)


class RollupTest(unittest.TestCase):
    def test_parent_includes_all_descendants(self):
        tree = [TreeNode(1, [TreeNode(2, [TreeNode(3, [])]), TreeNode(4, [])])]
        own = {
            1: DeckCounts(unseen=1, done=2, secs=10.0),
            2: DeckCounts(unseen=10, done=1),
            3: DeckCounts(mature=5, secs=2.5),
            4: DeckCounts(young=7),
        }
        out = rollup(tree, own)
        self.assertEqual(out[1], DeckCounts(unseen=11, young=7, mature=5, done=3, secs=12.5))
        self.assertEqual(out[2], DeckCounts(unseen=10, mature=5, done=1, secs=2.5))
        self.assertEqual(out[3].mature, 5)

    def test_deck_without_cards_is_zero(self):
        out = rollup([TreeNode(9, [])], {})
        self.assertEqual(out[9], DeckCounts())
        self.assertEqual(out[9].total, 0)

    def test_rollup_does_not_mutate_input(self):
        own = {1: DeckCounts(unseen=1), 2: DeckCounts(unseen=2)}
        rollup([TreeNode(1, [TreeNode(2, [])])], own)
        self.assertEqual(own[1].unseen, 1)


class StreakTest(unittest.TestCase):
    def test_current_streak_includes_today(self):
        self.assertEqual(current_streak({0, -1, -2, -4}), 3)

    def test_current_streak_survives_until_today_is_studied(self):
        self.assertEqual(current_streak({-1, -2}), 2)

    def test_current_streak_broken(self):
        self.assertEqual(current_streak({-2, -3}), 0)
        self.assertEqual(current_streak(set()), 0)

    def test_longest_streak(self):
        self.assertEqual(longest_streak({0, -1, -5, -6, -7, -8, -20}), 4)
        self.assertEqual(longest_streak(set()), 0)
        self.assertEqual(longest_streak({-3}), 1)


class AverageTest(unittest.TestCase):
    def test_study_day_average_ignores_rest_days(self):
        # 16 today and 224 on one other day: 120 per study day, not per calendar day.
        self.assertEqual(study_day_average({0: 16, -10: 224, -5: 0}), 120.0)
        self.assertEqual(study_day_average({}), 0.0)

    def test_share_of_days_studied_spans_first_day_to_today(self):
        self.assertAlmostEqual(share_of_days_studied({0, -1, -9}), 3 / 10)
        self.assertEqual(share_of_days_studied({0}), 1.0)
        self.assertEqual(share_of_days_studied(set()), 0.0)

    def test_week_starts_monday(self):
        self.assertEqual(week_start_offset(0), 0)  # Monday
        self.assertEqual(week_start_offset(6), -6)  # Sunday

    def test_secs_in_range_is_inclusive(self):
        secs = {0: 10.0, -1: 20.0, -6: 30.0, -7: 40.0}
        self.assertEqual(secs_in_range(secs, -6), 60.0)

    def test_minutes_left(self):
        self.assertEqual(minutes_left(30, 8.0), 4.0)
        self.assertEqual(minutes_left(0, 8.0), 0.0)


if __name__ == "__main__":
    unittest.main()

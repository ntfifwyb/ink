import html
import re
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from anki_dashboard import heatmap  # noqa: E402
from anki_dashboard.heatmap import Heatmap  # noqa: E402

TODAY = date(2026, 10, 19)  # a Monday


def cells(out):
    """(class, x, y, tooltip) for each day cell."""
    return [
        (k, int(x), int(y), html.unescape(t or ""))
        for k, x, y, t in re.findall(
            r'<rect class="([^"]+)" x="(\d+)" y="(\d+)"[^>]*?(?: data-tip="([^"]*)")?/>', out
        )
    ]


class ThresholdTest(unittest.TestCase):
    def test_quartiles_of_study_days(self):
        days = {-i: n for i, n in enumerate([0, 10, 20, 30, 40, 50, 0])}
        self.assertEqual(heatmap.thresholds(days), [20, 30, 40])

    def test_levels(self):
        bounds = [20, 30, 40]
        self.assertEqual(
            [heatmap.level(n, bounds) for n in (0, 1, 20, 35, 40, 500)], [0, 1, 2, 3, 4, 4]
        )

    def test_one_study_day_is_brightest(self):
        bounds = heatmap.thresholds({0: 7})
        self.assertEqual(heatmap.level(7, bounds), 4)

    def test_no_history(self):
        self.assertEqual(heatmap.thresholds({}), [1, 1, 1])


class GridTest(unittest.TestCase):
    def test_full_year_monday_first(self):
        out = heatmap.render_grid(Heatmap(2026, TODAY, {}))
        c = cells(out)
        self.assertEqual(len(c), 365)
        # 2026-01-01 is a Thursday: first column, fourth row.
        self.assertEqual(c[0][1:3], (0, heatmap.TOP + 3 * heatmap.STEP))
        # 53 week columns; the viewBox ends at the last cell, so nothing overflows.
        self.assertIn(f'viewBox="0 0 {53 * heatmap.STEP - heatmap.GAP} ', out)
        self.assertEqual(out.count("<text"), 12)

    def test_today_past_and_future(self):
        days = {0: (16, 117.4), -1: (0, 0.0), -2: (120, 900.0)}
        c = cells(heatmap.render_grid(Heatmap(2026, TODAY, days)))
        by_tip = {re.sub("<[^>]+>", "", t.split("\n")[0]): (k, t) for k, _, _, t in c if t}
        self.assertEqual(
            by_tip["Mon, Oct 19, 2026"][1], "<b>Mon, Oct 19, 2026</b>\n16 cards, 2.0 min"
        )
        self.assertEqual(
            by_tip["Sun, Oct 18, 2026"], ("ad-h0", "<b>Sun, Oct 18, 2026</b>\nNo reviews")
        )
        self.assertEqual(by_tip["Sat, Oct 17, 2026"][0], "ad-h4")
        future = [k for k, _, _, t in c if not t]
        self.assertEqual(future, ["ad-f"] * 73)  # Oct 20 through Dec 31

    def test_leap_year(self):
        self.assertEqual(len(cells(heatmap.render_grid(Heatmap(2024, TODAY, {})))), 366)


class RenderTest(unittest.TestCase):
    def test_year_range_and_arrows(self):
        days = {-400: (5, 60.0), 0: (3, 30.0)}  # first review in 2025
        h = Heatmap(2026, TODAY, days)
        self.assertEqual(h.years, (2025, 2026))
        out = heatmap.render(h)
        self.assertIn('pycmd("ad-year:2025")', out)
        self.assertIn('<span class="ad-yr ad-off">&rsaquo;</span>', out)
        h.year = 2025
        out = heatmap.render(h)
        self.assertIn('pycmd("ad-year:2026")', out)
        self.assertIn('<span class="ad-yr ad-off">&lsaquo;</span>', out)

    def test_stats_line(self):
        days = {0: (10, 0.0), -1: (20, 0.0), -3: (30, 0.0), -4: (0, 0.0)}
        out = re.sub(r"<[^>]+>", "", heatmap.render_stats(days))
        self.assertEqual(
            html.unescape(out),
            "20 cards/study day·75% of days studied·longest streak 2·current 2",
        )

    def test_no_history(self):
        h = Heatmap(2026, TODAY, {})
        self.assertEqual(h.years, (2026, 2026))
        out = re.sub(r"<[^>]+>", "", heatmap.render_stats({}))
        self.assertEqual(
            html.unescape(out), "0 cards/study day·0% of days studied·longest streak 0·current 0"
        )


if __name__ == "__main__":
    unittest.main()

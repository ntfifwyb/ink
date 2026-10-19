import html
import re
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from anki_dashboard import stats_page  # noqa: E402
from anki_dashboard.stats_page import StatsPage  # noqa: E402

MONDAY = date(2026, 10, 19)


def page(days, retention=0.82, all_history=False, today=MONDAY):
    return StatsPage(today=today, days=days, retention=retention, all_history=all_history)


def text(fragment):
    """Visible text: tags and data-tip attributes removed, spaces collapsed."""
    fragment = re.sub(r' data-tip="[^"]*"', "", fragment)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def tips(fragment):
    return [html.unescape(html.unescape(t)) for t in re.findall(r'data-tip="([^"]*)"', fragment)]


class PeriodsTest(unittest.TestCase):
    def test_days_end_today(self):
        ps = stats_page.periods(page({0: (4, 60.0), -29: (1, 6.0), -30: (9, 90.0)}), "day")
        self.assertEqual(len(ps), 30)
        self.assertEqual((ps[0].first, ps[0].answers), (date(2026, 9, 20), 1))
        self.assertEqual((ps[-1].first, ps[-1].answers, ps[-1].secs), (MONDAY, 4, 60.0))

    def test_weeks_start_on_monday(self):
        # Sunday the 18th belongs to the week before this Monday
        ps = stats_page.periods(page({0: (2, 20.0), -1: (3, 30.0), -7: (1, 10.0)}), "week")
        self.assertEqual(len(ps), 26)
        self.assertEqual(
            [(p.first, p.answers) for p in ps[-2:]], [(date(2026, 10, 12), 4), (MONDAY, 2)]
        )

    def test_months_are_calendar_months(self):
        # the 19th is today, so offset -19 is Sep 30 and -18 is Oct 1
        ps = stats_page.periods(page({-18: (2, 20.0), -19: (5, 50.0)}), "month")
        self.assertEqual(len(ps), 12)
        self.assertEqual(ps[0].first, date(2025, 11, 1))
        self.assertEqual(
            [(p.first, p.answers) for p in ps[-2:]], [(date(2026, 9, 1), 5), (date(2026, 10, 1), 2)]
        )

    def test_all_history_reaches_the_first_review_month(self):
        days = {-600: (1, 5.0), 0: (1, 5.0)}  # Feb 26, 2025
        ps = stats_page.periods(page(days, all_history=True), "month")
        self.assertEqual((len(ps), ps[0].first, ps[0].answers), (21, date(2025, 2, 1), 1))
        self.assertEqual(len(stats_page.periods(page(days), "month")), 12)

    def test_months_back_crosses_years(self):
        self.assertEqual(stats_page.months_back(date(2026, 2, 1), 3), date(2025, 11, 1))


class SummaryTest(unittest.TestCase):
    def test_four_numbers(self):
        days = {0: (30, 300.0), -1: (10, 120.0), -2: (20, 180.0), -5: (40, 600.0)}
        self.assertEqual(
            text(stats_page.render_summary(page(days))),
            "82% retention 3 day streak 20.0 min study time 25 cards/study day",
        )

    def test_range_limits_totals_but_not_the_streak(self):
        days = {0: (10, 600.0), -400: (30, 3000.0)}
        out = text(stats_page.render_summary(page(days)))
        self.assertIn("10.0 min study time 10 cards/study day", out)
        out = text(stats_page.render_summary(page(days, all_history=True)))
        self.assertIn("1.0 h study time 20 cards/study day", out)

    def test_tooltips(self):
        out = tips(stats_page.render_summary(page({0: (3, 30.0), -1: (1, 5.0), -9: (2, 9.0)})))
        self.assertIn("<b>Current streak</b>\nDays in a row with reviews\nLongest 2", out)
        self.assertIn("<b>Study time, last 12 months</b>\n6 answers on 3 days", out)

    def test_no_reviews(self):
        out = stats_page.render_summary(page({}, retention=None))
        self.assertEqual(text(out), "– retention – day streak – study time – cards/study day")


class StudyTimeTest(unittest.TestCase):
    def test_totals_line(self):
        # Monday: today is this week; -3 (Friday) is this month only; -25 is September
        days = {0: (10, 120.0), -3: (5, 60.0), -25: (5, 180.0)}
        out = stats_page.render_study_time(page(days))
        totals = out[out.index('<div class="ad-st-totals"') :]
        self.assertEqual(
            text(totals),
            "today 2.0 min · this week 2.0 min · this month 3.0 min · 2.0 min /study day",
        )

    def test_three_charts_with_tabs(self):
        out = stats_page.render_study_time(page({0: (1, 6.0)}))
        self.assertEqual(
            re.findall(r'<svg class="ad-st-svg" data-unit="(\w+)"', out), ["day", "week", "month"]
        )
        self.assertEqual(
            re.findall(r'<button type="button" data-unit="(\w+)"', out), ["day", "week", "month"]
        )

    def test_chart_hover_detail_and_axis(self):
        ps = stats_page.periods(page({0: (10, 90.0), -2: (4, 120.0)}), "day")
        svg = stats_page.render_chart(ps, "day")
        self.assertEqual(svg.count('class="ad-st-hover"'), 30)
        self.assertEqual(svg.count("<circle"), 2)  # one per day with answers
        self.assertIn("<b>Mon, Oct 19, 2026</b>\n1.5 min\n10 cards\n9.0 s/card", tips(svg))
        self.assertIn("<b>Sat, Oct 17, 2026</b>\n2.0 min\n4 cards\n30.0 s/card", tips(svg))
        self.assertIn("<b>Fri, Oct 16, 2026</b>\nNo reviews", tips(svg))
        self.assertIn(">2.0 min</text>", svg)  # the tallest bar
        self.assertIn(">30 s/card</text>", svg)  # the slowest day
        self.assertIn(">Sep 20</text>", svg)

    def test_period_labels(self):
        first = date(2026, 10, 12)
        self.assertEqual(stats_page.period_label(first, "week"), "Week of Oct 12, 2026")
        self.assertEqual(stats_page.period_label(first, "month"), "Oct 2026")

    def test_zero_time_answers_do_not_divide_by_zero(self):
        ps = stats_page.periods(page({0: (2, 0.0), -1: (1, 3.0)}), "day")
        self.assertIn("0.0 s/card", "".join(tips(stats_page.render_chart(ps, "day"))))

    def test_empty_range(self):
        out = stats_page.render_study_time(page({-500: (3, 30.0)}))
        self.assertEqual(
            text(out),
            "Study time Time spent answering, and seconds per card. "
            "No reviews in the last 12 months.",
        )
        self.assertNotIn("<svg", out)


class GraphKeysTest(unittest.TestCase):
    def test_titles_from_translations_and_missing_ones_skipped(self):
        class Tr:
            def statistics_today_title(self):
                return "Heute "

            def statistics_hours_title(self):
                return "Stunden"

        self.assertEqual(stats_page.graph_keys(Tr()), {"Heute": "today", "Stunden": "hours"})

    def test_every_config_graph_has_a_title(self):
        from anki_dashboard import config

        self.assertEqual(tuple(stats_page.GRAPH_TITLES), config.GRAPHS)

    def test_titles_exist_in_this_anki(self):
        from anki.collection import Collection

        d = tempfile.mkdtemp()
        col = Collection(str(Path(d) / "t.anki2"))
        try:
            keys = stats_page.graph_keys(col.tr)
            self.assertEqual(sorted(keys.values()), sorted(stats_page.GRAPH_TITLES))
            self.assertEqual(keys["Answer Buttons"], "buttons")
        finally:
            col.close()
            shutil.rmtree(d)


class BuildTest(unittest.TestCase):
    """build() against a real collection, as the bridge handler calls it."""

    def setUp(self):
        from anki.collection import Collection

        self.dir = tempfile.mkdtemp()
        self.col = Collection(str(Path(self.dir) / "test.anki2"))

    def tearDown(self):
        self.col.close()
        shutil.rmtree(self.dir)

    def test_whole_collection_and_bad_search(self):
        from anki_dashboard.queries import DayClock

        cutoff = DayClock.of(self.col).cutoff
        self.col.db.execute(
            "insert into revlog values (?, 1, -1, 3, 1, 0, 2500, 6000, 1)", (cutoff - 3600) * 1000
        )
        out = stats_page.build(self.col, "", False)
        self.assertEqual(
            text(out["summary"]), "100% retention 1 day streak 0.1 min study time 1 cards/study day"
        )
        self.assertIn("ad-st-svg", out["study"])
        self.assertEqual(stats_page.build(self.col, "deck:(", False), {"summary": "", "study": ""})


if __name__ == "__main__":
    unittest.main()

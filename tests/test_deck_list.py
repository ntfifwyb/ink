import html
import json
import re
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from anki_dashboard import config, deck_list  # noqa: E402
from anki_dashboard.deck_list import Row, Today  # noqa: E402
from anki_dashboard.stats import DeckCounts  # noqa: E402


def row(deck_id=1, **kw):
    base = dict(
        deck_id=deck_id,
        name="Artificial Intelligence",
        level=1,
        collapsed=False,
        has_children=False,
        filtered=False,
        current=False,
        group="Default",
        due=0,
        new=0,
        learn=0,
        counts=DeckCounts(young=18, notes=18, done=16, reps=16, secs=117.4),
    )
    base.update(kw)
    return Row(**base)


def today(**kw):
    base = dict(
        reps=16,
        secs=117.4,
        cards_left=0,
        recent_secs_per_card=13.4,
        streak=1,
        total_secs=91489.0,
        week_secs=117.4,
        retention=0.94,
        desired_retention=None,
        per_study_day=120.1,
    )
    base.update(kw)
    return Today(**base)


def text(fragment):
    """Visible text: tags and data-tip attributes removed."""
    fragment = re.sub(r' data-tip="[^"]*"', "", fragment)
    return html.unescape(re.sub(r"<[^>]+>", "", fragment))


class ColumnsTest(unittest.TestCase):
    def test_empty_columns_hide(self):
        cols = deck_list.visible_columns([row()], list(config.DECK_COLUMNS), True)
        self.assertEqual(cols, ["done", "maturity"])

    def test_empty_columns_kept_when_disabled(self):
        cols = deck_list.visible_columns([row()], ["due", "done", "maturity"], False)
        self.assertEqual(cols, ["due", "done", "maturity"])

    def test_column_shown_when_any_deck_has_a_value(self):
        rows = [row(), row(2, due=5, counts=DeckCounts(tomorrow=3))]
        cols = deck_list.visible_columns(rows, list(config.DECK_COLUMNS), True)
        self.assertEqual(cols, ["due", "done", "tmrw", "maturity"])

    def test_unknown_columns_are_ignored(self):
        self.assertEqual(deck_list.visible_columns([row()], ["bogus", "done"], False), ["done"])


class TableTest(unittest.TestCase):
    def test_row_keeps_anki_ids_and_commands(self):
        out = deck_list.render_table([row(42)], ["done", "maturity"])
        self.assertIn('class="deck ad-row" id="42"', out)
        self.assertIn("pycmd('open:42')", out)
        self.assertIn('pycmd("opts:42")', out)
        self.assertIn('pycmd("select:42")', out)
        self.assertIn("top-level-drag-row", out)

    def test_zero_is_a_dash_and_values_show(self):
        r = row(due=0, counts=DeckCounts(done=16, reps=20, secs=120.0))
        out = deck_list.render_table([r], ["due", "done"])
        cells = re.findall(r'<td class="ad-n(?: ad-hi)?"[^>]*>(.*?)</td>', out)
        self.assertEqual([text(c) for c in cells], ["–", "16"])

    def test_tooltips_carry_the_breakdown(self):
        r = row(
            learn=3,
            counts=DeckCounts(learn_now=1, learn_later=2, learn_other=4, done=5, reps=7, secs=90),
        )
        out = html.unescape(deck_list.render_table([r], ["learn", "done"]))
        self.assertIn("<b>Learning 7</b>\nDue now 1\nLater today 2\nOther day 4", out)
        self.assertIn("<b>Reviewed today 5</b>\nAnswers 7\nTime 1.5 min", out)

    def test_maturity_bar_and_percent(self):
        r = row(counts=DeckCounts(unseen=10, young=30, mature=60, notes=50))
        out = deck_list.render_table([r], ["maturity"])
        self.assertIn('class="ad-new" style="width:10.00%"', out)
        self.assertIn('class="ad-mature" style="width:60.00%"', out)
        self.assertIn('<span class="ad-pct">60%</span>', out)
        self.assertIn("100 cards, 50 notes", html.unescape(out))

    def test_empty_deck_maturity_is_a_dash(self):
        out = deck_list.render_table([row(counts=DeckCounts())], ["maturity"])
        self.assertIn('<span class="ad-pct"><span class="ad-zero">', out)

    def test_deck_names_are_escaped(self):
        out = deck_list.render_table([row(name="<b>&")], ["done"])
        self.assertIn("&lt;b&gt;&amp;</a>", out)
        self.assertNotIn("<b>&", out)

    def test_subdeck_indent_and_collapse(self):
        out = deck_list.render_table(
            [row(1, has_children=True, collapsed=True), row(2, level=2)], ["done"]
        )
        self.assertIn('pycmd("collapse:1")', out)
        self.assertIn("padding-left:16px", out)


class TodayTest(unittest.TestCase):
    def test_current_screen_numbers(self):
        out = text(deck_list.render_today(today()))
        self.assertIn("16 cards·2.0 min·7.3 s/card·~0 min left·streak 1", out)
        self.assertIn(
            "all time 25.4 h·this week 2.0 min·retention 94%·120/day avg (study days)",
            out,
        )

    def test_time_left_uses_recent_pace_before_first_review(self):
        out = text(deck_list.render_today(today(reps=0, secs=0, cards_left=30)))
        self.assertIn("0 cards·0.0 min·–·~7 min left", out)

    def test_no_history(self):
        t = today(reps=0, secs=0, cards_left=5, recent_secs_per_card=None, retention=None)
        out = text(deck_list.render_today(t))
        self.assertIn("–·–·streak", out)
        self.assertIn("retention –", out)

    def test_fsrs_desired_retention_in_tooltip(self):
        out = html.unescape(deck_list.render_today(today(desired_retention=0.9)))
        self.assertIn("FSRS desired retention 90%", out)


class ConfigTest(unittest.TestCase):
    def test_menu_bar_uses_config_colors(self):
        qss = config.menu_bar_qss(dict(config.COLORS, bg="#000000", raised="#111111"))
        self.assertIn("QMenuBar { background: #000000;", qss)
        self.assertIn("background: #111111;", qss)

    def test_shipped_config_matches_defaults(self):
        raw = json.loads((SRC / "anki_dashboard" / "config.json").read_text())
        self.assertEqual(raw["colors"], config.COLORS)
        self.assertEqual(config.load(raw), config.Config())

    def test_bad_values_fall_back(self):
        cfg = config.load(
            {
                "colors": {"bg": "red;}</style>", "fg1": "#fff", "nope": "#000"},
                "deck_list": {
                    "columns": ["done", "x", "done"],
                    "today_strip": "yes",
                    "heatmap": False,
                },
                "reviewer": {"progress_bar": False, "session_stats": 0, "edit_more": True},
            }
        )
        self.assertEqual(cfg.colors["bg"], config.COLORS["bg"])
        self.assertEqual(cfg.colors["fg1"], "#fff")
        self.assertNotIn("nope", cfg.colors)
        self.assertEqual(cfg.deck_list.columns, ["done"])
        self.assertTrue(cfg.deck_list.today_strip)
        self.assertFalse(cfg.deck_list.heatmap)
        self.assertEqual(
            cfg.reviewer,
            config.ReviewerConfig(progress_bar=False, session_stats=True, edit_more=True),
        )

    def test_not_a_dict(self):
        self.assertEqual(config.load(None), config.Config())

    def test_css_variables(self):
        self.assertEqual(
            config.css_variables({"bg": "#000", "fg1": "#fff"}),
            ":root{--ad-bg:#000;--ad-fg1:#fff;}",
        )


class BuildTest(unittest.TestCase):
    """build() against a real collection, as the deck browser hook calls it."""

    def test_build_rolls_up_subdecks_into_collapsed_parent(self):
        import shutil
        import tempfile

        from anki.collection import Collection

        tmp = tempfile.mkdtemp()
        col = Collection(str(Path(tmp) / "c.anki2"))
        try:
            parent, child = col.decks.id("AI"), col.decks.id("AI::ML")
            model = col.models.by_name("Basic")
            for did, n in ((parent, 2), (child, 3)):
                for i in range(n):
                    note = col.new_note(model)
                    note["Front"] = f"{did}-{i}"
                    col.add_note(note, did)
            table, stats_html = deck_list.build(col, col.sched.deck_due_tree(), config.Config())
        finally:
            col.close()
            shutil.rmtree(tmp)
        # Anki creates parent decks collapsed, so only the parent row shows.
        self.assertIn(f'id="{parent}"', table)
        self.assertNotIn(f'id="{child}"', table)
        self.assertIn("5 cards, 5 notes", html.unescape(table))
        self.assertIn('class="ad-today"', stats_html)
        self.assertIn('class="ad-heat"', stats_html)


if __name__ == "__main__":
    unittest.main()

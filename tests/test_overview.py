import html
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from anki_dashboard import overview  # noqa: E402
from anki_dashboard.overview import Deck  # noqa: E402
from anki_dashboard.stats import DeckCounts  # noqa: E402


def deck(**kw):
    base = dict(
        due=21,
        new=20,
        learn=3,
        buried_due=0,
        buried_new=0,
        buried_learn=0,
        counts=DeckCounts(
            unseen=90, young=51, mature=19, notes=160, due_all=30, done=25, reps=40, secs=360.0
        ),
        recent_secs_per_card=13.4,
    )
    base.update(kw)
    return Deck(**base)


def text(fragment):
    """Visible text: tags and data-tip attributes removed, spaces collapsed."""
    fragment = re.sub(r' data-tip="[^"]*"', "", fragment)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


class RenderTest(unittest.TestCase):
    def test_counts_button_and_one_line(self):
        out = overview.render(deck(counts=DeckCounts(**{**deck().counts.__dict__, "tomorrow": 23})))
        self.assertEqual(
            text(out),
            "21 due 20 new 3 learn Study "
            "~7 min left · 12% mature · 23 tmrw",  # 44 cards at 9.0 s is 6.6 min
        )
        self.assertIn("pycmd('study')", out)
        self.assertIn("id=study", out)

    def test_tooltips_carry_the_breakdown(self):
        out = html.unescape(html.unescape(overview.render(deck(buried_new=2))))
        self.assertIn("All due, ignoring limits 30", out)
        self.assertIn("Unseen in deck 90\nBuried 2", out)
        self.assertIn("44 cards at 9.0 s/card", out)
        self.assertIn("160 notes", out)
        self.assertIn("Done today 25 cards in 6.0 min, 9.0 s/card", out)

    def test_time_left_uses_recent_pace_before_first_review(self):
        out = overview.render(deck(counts=DeckCounts(unseen=5)))
        self.assertIn("~10 min left", text(out))  # 44 cards at 13.4 s
        self.assertIn("Done today 0 cards", html.unescape(html.unescape(out)))

    def test_no_history_and_empty_deck(self):
        out = text(
            overview.render(
                deck(due=0, new=0, learn=0, counts=DeckCounts(), recent_secs_per_card=None)
            )
        )
        self.assertEqual(
            out,
            "– due – new – learn Study – left · – mature · – tmrw",
        )


class BuildTest(unittest.TestCase):
    """build() against a real collection, as the overview hook calls it."""

    def test_build_counts_the_current_deck_with_subdecks(self):
        from anki.collection import Collection

        tmp = tempfile.mkdtemp()
        col = Collection(str(Path(tmp) / "c.anki2"))
        try:
            parent, child = col.decks.id("AI"), col.decks.id("AI::ML")
            other = col.decks.id("Other")
            model = col.models.by_name("Basic")
            for did, n in ((parent, 2), (child, 3), (other, 4)):
                for i in range(n):
                    note = col.new_note(model)
                    note["Front"] = f"{did}-{i}"
                    col.add_note(note, did)
            col.decks.select(parent)
            out = overview.build(col)
        finally:
            col.close()
            shutil.rmtree(tmp)
        self.assertTrue(text(out).startswith("– due 5 new – learn Study"))
        self.assertIn("0% mature", text(out))


if __name__ == "__main__":
    unittest.main()

import html
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from anki.collection import Collection  # noqa: E402

from anki_dashboard import reviewer  # noqa: E402
from anki_dashboard.reviewer import Review  # noqa: E402


def review(**kw):
    base = dict(
        due=8,
        new=9,
        learn=1,
        done_today=12,
        session_cards=10,
        session_reps=12,
        session_secs=92.0,
        recent_secs_per_card=13.4,
    )
    base.update(kw)
    return Review(**base)


def text(fragment):
    """Visible text: tags and data-tip attributes removed, spaces collapsed."""
    fragment = re.sub(r' data-tip="[^"]*"', "", fragment)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def tips(fragment):
    return html.unescape(html.unescape(fragment))


class FormatTest(unittest.TestCase):
    def test_queue_share(self):
        self.assertEqual(reviewer.queue_share(12, 18), 0.4)
        self.assertEqual(reviewer.queue_share(0, 5), 0.0)
        self.assertEqual(reviewer.queue_share(0, 0), 1.0)

    def test_elapsed(self):
        self.assertEqual(reviewer.elapsed(0), "0:00")
        self.assertEqual(reviewer.elapsed(92.7), "1:32")
        self.assertEqual(reviewer.elapsed(3725), "1:02:05")


class OverlayTest(unittest.TestCase):
    def test_progress_bar_and_session_line(self):
        out = reviewer.overlay(review(), progress_bar=True, session_stats=True)
        self.assertIn('<i style="width:40.00%">', out)  # 12 of 30
        # 18 cards at 92 s / 12 answers = 7.67 s is 2.3 min
        self.assertEqual(text(out), "10 · 1:32 · 7.7s · ~2m")
        out = tips(out)
        self.assertIn("12 of 30 cards done (40%)", out)
        self.assertIn("Left 18: due 8, new 9, learning 1", out)
        self.assertIn("Answers 12", out)
        self.assertIn("18 cards at 7.7 s/card\nthis session's pace", out)

    def test_each_part_can_be_turned_off(self):
        self.assertNotIn("ad-sess", reviewer.overlay(review(), True, False))
        self.assertNotIn("ad-prog", reviewer.overlay(review(), False, True))
        self.assertEqual(reviewer.overlay(review(), False, False), "")

    def test_new_session_uses_recent_pace(self):
        r = review(session_cards=0, session_reps=0, session_secs=0.0)
        out = reviewer.session(r)
        self.assertEqual(text(out), "0 · 0:00 · – · ~4m")  # 18 at 13.4 s
        self.assertIn("the last 30 days' pace", tips(out))

    def test_no_history_at_all(self):
        r = review(session_cards=0, session_reps=0, session_secs=0.0, recent_secs_per_card=None)
        self.assertEqual(text(reviewer.session(r)), "0 · 0:00 · – · –")

    def test_finished_queue_is_a_full_bar(self):
        out = reviewer.overlay(review(due=0, new=0, learn=0), True, False)
        self.assertIn("width:100.00%", out)


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.col = Collection(str(Path(self.dir) / "test.anki2"))

    def tearDown(self):
        self.col.close()
        shutil.rmtree(self.dir)

    def test_counts_and_session_from_the_scheduler(self):
        model = self.col.models.by_name("Basic")
        deck = self.col.decks.id("AI")
        child = self.col.decks.id("AI::ML")
        for did in (deck, child, child):
            note = self.col.new_note(model)
            note["Front"] = "q"
            self.col.add_note(note, did)
        self.col.decks.select(deck)
        card = self.col.sched.getCard()
        card.start_timer()
        self.col.sched.answerCard(card, 4)  # Easy: done for today
        since = self.col.db.scalar("select max(id) from revlog") + 1

        r = reviewer.build(self.col, since)
        self.assertEqual((r.due, r.new, r.learn, r.done_today), (0, 2, 0, 1))
        self.assertEqual((r.session_cards, r.session_reps), (0, 0))

        card = self.col.sched.getCard()
        card.start_timer()
        self.col.sched.answerCard(card, 4)
        r = reviewer.build(self.col, since)
        self.assertEqual((r.new, r.done_today, r.session_cards, r.session_reps), (1, 2, 1, 1))


if __name__ == "__main__":
    unittest.main()

"""Queries against a real collection, built with Anki's own backend (the `anki`
package, which .local-ci installs at the version the add-on is verified against)."""

import ast
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from anki.collection import Collection  # noqa: E402

from ink import queries  # noqa: E402
from ink.queries import DayClock  # noqa: E402

DAY = 86400


class CollectionTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.col = Collection(str(Path(self.dir) / "test.anki2"))
        self.deck = self.col.decks.id("AI")
        self.clock = DayClock.of(self.col)

    def tearDown(self):
        self.col.close()
        shutil.rmtree(self.dir)

    def add_notes(self, n, deck=None):
        model = self.col.models.by_name("Basic")
        ids = []
        for i in range(n):
            note = self.col.new_note(model)
            note["Front"], note["Back"] = f"q{i}", f"a{i}"
            self.col.add_note(note, deck or self.deck)
            ids.append(note.id)
        return ids

    def card_ids(self):
        return self.col.db.list("select id from cards order by id")

    def set_card(self, cid, **values):
        cols = ", ".join(f"{k} = ?" for k in values)
        self.col.db.execute(f"update cards set {cols} where id = ?", *values.values(), cid)

    def add_revlog(self, days_ago, ease=3, ms=8000, type_=1, cid=1):
        # an hour before the end of the Anki day `days_ago` days back
        stamp = (self.clock.cutoff - days_ago * DAY - 3600) * 1000
        while self.col.db.scalar("select 1 from revlog where id = ?", stamp):
            stamp += 1
        self.col.db.execute(
            "insert into revlog values (?, ?, -1, ?, 1, 0, 2500, ?, ?)",
            stamp,
            cid,
            ease,
            ms,
            type_,
        )


class DeckCountsTest(CollectionTest):
    def test_maturity_and_notes(self):
        self.add_notes(4)
        a, b, c, _ = self.card_ids()
        self.set_card(a, type=2, queue=2, ivl=30, due=self.clock.today + 5)
        self.set_card(b, type=2, queue=2, ivl=3, due=self.clock.today + 5)
        self.set_card(c, type=3, queue=1, ivl=40, due=int(time.time()))
        counts = queries.deck_counts(self.col, self.clock)[self.deck]
        self.assertEqual((counts.unseen, counts.young, counts.mature), (1, 1, 2))
        self.assertEqual(counts.notes, 4)
        self.assertEqual(counts.total, 4)

    def test_due_learning_and_tomorrow(self):
        self.add_notes(6)
        a, b, c, d, e, f = self.card_ids()
        self.set_card(a, type=2, queue=2, ivl=5, due=self.clock.today)
        self.set_card(b, type=2, queue=2, ivl=5, due=self.clock.today - 3)  # overdue
        self.set_card(c, type=2, queue=2, ivl=5, due=self.clock.today + 1)
        self.set_card(d, type=1, queue=1, due=int(time.time()) - 60)
        self.set_card(e, type=1, queue=1, due=int(time.time()) + 6 * 3600)
        self.set_card(f, type=1, queue=3, due=self.clock.today + 1)
        counts = queries.deck_counts(self.col, self.clock)[self.deck]
        self.assertEqual(counts.due_all, 2)
        self.assertEqual((counts.learn_now, counts.learn_later, counts.learn_other), (1, 1, 1))
        self.assertEqual(counts.tomorrow, 2)

    def test_suspended_and_buried_reviews_are_not_due(self):
        self.add_notes(2)
        a, b = self.card_ids()
        self.set_card(a, type=2, queue=-1, ivl=5, due=self.clock.today)
        self.set_card(b, type=2, queue=-2, ivl=5, due=self.clock.today)
        counts = queries.deck_counts(self.col, self.clock)[self.deck]
        self.assertEqual(counts.due_all, 0)
        self.assertEqual(counts.young, 2)

    def test_answers_today_through_the_scheduler(self):
        self.add_notes(3)
        self.col.decks.select(self.deck)
        for _ in range(2):
            card = self.col.sched.getCard()
            card.start_timer()
            self.col.sched.answerCard(card, 4)  # Easy: straight to review
        counts = queries.deck_counts(self.col, self.clock)[self.deck]
        self.assertEqual((counts.done, counts.reps), (2, 2))
        self.assertEqual(counts.unseen, 1)
        self.assertEqual(counts.young, 2)

    def test_yesterday_and_manual_entries_are_not_today(self):
        self.add_notes(1)
        (cid,) = self.card_ids()
        self.add_revlog(0, cid=cid, ms=5000)
        self.add_revlog(0, cid=cid, ms=7000)
        self.add_revlog(0, cid=cid, ease=0, ms=0, type_=4)  # manual reschedule
        self.add_revlog(1, cid=cid)
        counts = queries.deck_counts(self.col, self.clock)[self.deck]
        self.assertEqual((counts.done, counts.reps, counts.secs), (1, 2, 12.0))

    def test_cards_are_counted_in_their_own_deck_only(self):
        child = self.col.decks.id("AI::ML")
        self.add_notes(2)
        self.add_notes(3, deck=child)
        counts = queries.deck_counts(self.col, self.clock)
        self.assertEqual(counts[self.deck].unseen, 2)
        self.assertEqual(counts[child].unseen, 3)


class ReviewerQueriesTest(CollectionTest):
    def answer(self, n, ease=4):
        self.col.decks.select(self.deck)
        for _ in range(n):
            card = self.col.sched.getCard()
            card.start_timer()
            self.col.sched.answerCard(card, ease)

    def test_answers_since_counts_only_later_answers(self):
        self.add_notes(4)
        self.answer(1)
        since = self.col.db.scalar("select max(id) from revlog") + 1
        self.answer(2)
        (cid,) = self.col.db.list("select cid from revlog order by id desc limit 1")
        self.add_revlog(0, cid=cid, ease=1)  # the same card again, later today
        self.add_revlog(0, cid=cid, ease=0, type_=4)  # manual reschedule, not an answer
        cards, reps, secs = queries.answers_since(self.col, since)
        self.assertEqual((cards, reps), (2, 3))
        self.assertGreaterEqual(secs, 0)
        self.assertEqual(queries.answers_since(self.col, since + DAY * 1000), (0, 0, 0))

    def test_cards_done_today_by_deck_including_filtered_cards(self):
        child = self.col.decks.id("AI::ML")
        other = self.col.decks.id("Other")
        self.add_notes(1)
        self.add_notes(2, deck=child)
        self.add_notes(1, deck=other)
        for cid in self.col.db.list("select id from cards"):
            self.add_revlog(0, cid=cid)
            self.add_revlog(0, cid=cid)
        self.add_revlog(1, cid=cid)  # yesterday
        ai = [self.deck, child]
        self.assertEqual(queries.cards_done_today(self.col, self.clock, ai), 3)
        # a card moved into a filtered deck still counts for its home deck
        self.set_card(cid, did=self.col.decks.id("Cram"), odid=self.deck)
        self.assertEqual(queries.cards_done_today(self.col, self.clock, ai), 4)
        self.assertEqual(queries.cards_done_today(self.col, self.clock, [other]), 0)
        self.assertEqual(queries.cards_done_today(self.col, self.clock, []), 0)


class DayReviewsTest(CollectionTest):
    def test_answers_grouped_by_day_offset(self):
        for days_ago, n in ((0, 2), (1, 1), (40, 3)):
            for _ in range(n):
                self.add_revlog(days_ago, ms=6000)
        self.add_revlog(2, ease=0, type_=4)
        self.assertEqual(
            queries.day_reviews(self.col, self.clock),
            {0: (2, 12.0), -1: (1, 6.0), -40: (3, 18.0)},
        )

    def test_day_boundaries(self):
        start = self.clock.start_ms // 1000
        for stamp in (start, self.clock.cutoff - 1, start - 1):
            self.col.db.execute(
                "insert into revlog values (?, 1, -1, 3, 1, 0, 2500, 1000, 1)", stamp * 1000
            )
        self.assertEqual(queries.day_reviews(self.col, self.clock), {0: (2, 2.0), -1: (1, 1.0)})


class SearchFilterTest(CollectionTest):
    def test_search_limits_history_to_matching_cards(self):
        other = self.col.decks.id("Other")
        self.add_notes(1)
        self.add_notes(1, deck=other)
        ai, oth = self.card_ids()
        self.add_revlog(0, cid=ai, ms=4000, ease=1)
        self.add_revlog(1, cid=oth, ms=6000)
        cards = queries.search_filter(self.col, "deck:AI")
        self.assertEqual(queries.day_reviews(self.col, self.clock, cards), {0: (1, 4.0)})
        self.assertEqual(queries.retention(self.col, self.clock, cards=cards), 0.0)

    def test_no_search_keeps_deleted_cards(self):
        self.add_revlog(3, cid=12345)  # card no longer in the collection
        self.assertEqual(queries.search_filter(self.col, "  "), "")
        self.assertEqual(queries.day_reviews(self.col, self.clock, ""), {-3: (1, 8.0)})

    def test_search_with_no_matches(self):
        self.add_revlog(0)
        cards = queries.search_filter(self.col, "deck:Nothing")
        self.assertEqual(queries.day_reviews(self.col, self.clock, cards), {})


class SummaryTest(CollectionTest):
    def test_retention_counts_review_answers_only(self):
        for ease in (1, 3, 3, 4):
            self.add_revlog(2, ease=ease)
        self.add_revlog(2, ease=1, type_=0)  # learning answer, not counted
        self.add_revlog(45, ease=1)  # outside the 30-day window
        self.assertEqual(queries.retention(self.col, self.clock), 0.75)

    def test_retention_without_reviews(self):
        self.assertIsNone(queries.retention(self.col, self.clock))

    def test_secs_per_card(self):
        self.add_revlog(0, ms=6000)
        self.add_revlog(3, ms=10000)
        self.assertEqual(queries.secs_per_card(self.col, self.clock), 8.0)
        self.assertIsNone(queries.secs_per_card(self.col, self.clock, days=0))

    def test_fsrs_detection(self):
        self.assertFalse(queries.fsrs_enabled(self.col))
        self.col.set_config("fsrs", True)
        self.assertTrue(queries.fsrs_enabled(self.col))

    def test_options_group_and_desired_retention(self):
        self.assertEqual(queries.options_group(self.col, self.deck), "Default")
        self.assertEqual(queries.desired_retention(self.col, self.deck), 0.9)
        filtered = self.col.decks.new_filtered("Cram")
        self.assertEqual(queries.options_group(self.col, filtered), "filtered")

    def test_clock_date_is_the_anki_day(self):
        c = self.clock
        self.assertEqual(c.rollover, 4)
        self.assertEqual(
            datetime.fromtimestamp(c.start_ms / 1000), datetime(*c.date.timetuple()[:3], 4)
        )
        self.assertEqual(
            datetime.fromtimestamp(c.cutoff),
            datetime(*c.date.timetuple()[:3], 4) + timedelta(days=1),
        )


# Days around Berlin's switch to summer time, 2026-03-29 at 02:00 local: the Anki day
# of the 28th starts at 04:00 CET and ends at 04:00 CEST, 23 hours later. Run in a
# child process, as the time zone has to be set before Anki's backend reads it.
DST_CHECK = """
import sys
from datetime import date, datetime
from anki.collection import Collection
sys.path.insert(0, sys.argv[2])
from ink import queries
col = Collection(sys.argv[1])
cutoff = int(datetime(2026, 3, 30, 4).timestamp())
clock = queries.DayClock(cutoff, 0, date(2026, 3, 29), 4)
def ms(*local):
    return int(datetime(*local).timestamp()) * 1000
for local in ((29, 4, 30), (29, 3, 30), (28, 4, 10), (28, 3, 30)):
    sql = "insert into revlog values (?, 1, -1, 3, 1, 0, 2500, 1000, 1)"
    col.db.execute(sql, ms(2026, 3, *local))
days = sorted(queries.day_reviews(col, clock).items())
print(repr((days, clock.day_start_ms(1) - ms(2026, 3, 28, 4))))
col.close()
"""


class DaylightSavingTest(unittest.TestCase):
    def test_days_follow_local_rollover_across_a_clock_change(self):
        with tempfile.TemporaryDirectory() as d:
            out = subprocess.run(
                [sys.executable, "-c", DST_CHECK, str(Path(d) / "c.anki2"), str(SRC)],
                env=dict(os.environ, TZ="Europe/Berlin"),
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        days, start_error = ast.literal_eval(out)
        # 29th 04:30 is today; 29th 03:30 and 28th 04:10 the 28th; 28th 03:30 the 27th
        self.assertEqual(days, [(-2, (1, 1.0)), (-1, (2, 2.0)), (0, (1, 1.0))])
        self.assertEqual(start_error, 0)


if __name__ == "__main__":
    unittest.main()

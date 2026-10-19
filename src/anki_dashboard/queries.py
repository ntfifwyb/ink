"""Read stats from a collection. Each function runs a few SQL queries against
`col.db` and returns plain data for `stats.py` and the screens.

Card fields used: queue (0 new, 1 intraday learning, 2 review, 3 interday learning,
negative when suspended or buried), type (0 new, 1 learning, 2 review, 3 relearning),
due (days since collection creation for queues 2 and 3, epoch seconds for queue 1)
and ivl (days). Revlog ids are epoch milliseconds; answers have ease > 0, while
manual reschedules have ease 0 and are skipped.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date

from .stats import MATURE_IVL, DeckCounts

DAY = 86400


@dataclass
class DayClock:
    """Today's Anki day: `cutoff` is when it ends (epoch seconds), `today` its
    scheduler day number and `date` its calendar date."""

    cutoff: int
    today: int
    date: date

    @classmethod
    def of(cls, col) -> DayClock:
        cutoff = col.sched.day_cutoff
        return cls(cutoff, col.sched.today, date.fromtimestamp(cutoff - DAY))

    @property
    def start_ms(self) -> int:
        return (self.cutoff - DAY) * 1000

    def days_ago_sql(self) -> str:
        """SQL for how many Anki days before today a revlog entry falls (0 is today)."""
        return f"(({self.cutoff} - id / 1000 - 1) / {DAY})"


def deck_counts(col, clock: DayClock) -> dict[int, DeckCounts]:
    """Counts for each deck's own cards, keyed by deck id (subdecks not included)."""
    learn_ahead = int(time.time()) + int(col.get_config("collapseTime", 1200))
    out: dict[int, DeckCounts] = {}

    for did, unseen, young, mature, notes, due_all, now, later, other, tmrw in col.db.all(
        f"""
        select did,
          sum(type = 0),
          sum(type != 0 and not (type in (2, 3) and ivl >= {MATURE_IVL})),
          sum(type in (2, 3) and ivl >= {MATURE_IVL}),
          count(distinct nid),
          sum(queue = 2 and due <= ?),
          sum(queue = 1 and due <= ?),
          sum(queue = 1 and due > ?),
          sum(queue = 3),
          sum(queue in (2, 3) and due = ?)
        from cards group by did
        """,
        clock.today,
        learn_ahead,
        learn_ahead,
        clock.today + 1,
    ):
        out[did] = DeckCounts(
            unseen=unseen,
            young=young,
            mature=mature,
            notes=notes,
            due_all=due_all,
            learn_now=now,
            learn_later=later,
            learn_other=other,
            tomorrow=tmrw,
        )

    for did, done, reps, ms in col.db.all(
        """
        select c.did, count(distinct r.cid), count(*), sum(r.time)
        from revlog r join cards c on c.id = r.cid
        where r.id >= ? and r.ease > 0
        group by c.did
        """,
        clock.start_ms,
    ):
        counts = out.setdefault(did, DeckCounts())
        counts.done, counts.reps, counts.secs = done, reps, (ms or 0) / 1000
    return out


def search_filter(col, search: str) -> str:
    """An `and cid in (...)` clause for revlog limiting it to the cards a search finds.
    No search keeps the whole history, including cards since deleted."""
    if not search.strip():
        return ""
    ids = ",".join(str(int(c)) for c in col.find_cards(search))
    return f" and cid in ({ids or 0})"


def day_reviews(col, clock: DayClock, cards: str = "") -> dict[int, tuple[int, float]]:
    """Answers and seconds per day over the whole history, keyed by day offset.
    `cards` is a `search_filter` clause."""
    return {
        -days_ago: (reps, (ms or 0) / 1000)
        for days_ago, reps, ms in col.db.all(
            f"""
            select {clock.days_ago_sql()} as d, count(*), sum(time)
            from revlog where ease > 0 and id < ?{cards} group by d
            """,
            clock.cutoff * 1000,
        )
    }


def retention(col, clock: DayClock, days: int = 30, cards: str = "") -> float | None:
    """Share of review-card answers in the last `days` days that were not Again.
    `cards` is a `search_filter` clause."""
    passed, total = col.db.first(
        f"select sum(ease > 1), count(*) from revlog where type = 1 and id >= ?{cards}",
        clock.start_ms - (days - 1) * DAY * 1000,
    )
    return passed / total if total else None


def secs_per_card(col, clock: DayClock, days: int = 30) -> float | None:
    """Average seconds per answer over the last `days` days."""
    reps, ms = col.db.first(
        "select count(*), sum(time) from revlog where ease > 0 and id >= ?",
        clock.start_ms - (days - 1) * DAY * 1000,
    )
    return ms / 1000 / reps if reps else None


def answers_since(col, since_ms: int) -> tuple[int, int, float]:
    """Cards, answers and seconds answered since `since_ms` (epoch milliseconds)."""
    cards, reps, ms = col.db.first(
        "select count(distinct cid), count(*), sum(time) from revlog where ease > 0 and id >= ?",
        since_ms,
    )
    return cards, reps, (ms or 0) / 1000


def cards_done_today(col, clock: DayClock, deck_ids: list[int]) -> int:
    """Cards answered today whose deck, or home deck for cards in a filtered deck,
    is one of `deck_ids`."""
    if not deck_ids:
        return 0
    ids = ",".join(str(int(d)) for d in deck_ids)
    return col.db.scalar(
        f"""
        select count(distinct r.cid) from revlog r join cards c on c.id = r.cid
        where r.id >= ? and r.ease > 0 and (c.did in ({ids}) or c.odid in ({ids}))
        """,
        clock.start_ms,
    )


def fsrs_enabled(col) -> bool:
    return bool(col.get_config("fsrs", False))


def desired_retention(col, deck_id: int) -> float | None:
    """The FSRS desired retention of a deck's options group (None for filtered decks)."""
    conf = col.decks.config_dict_for_deck_id(deck_id)
    value = conf.get("desiredRetention") if conf else None
    return float(value) if value else None


def options_group(col, deck_id: int) -> str:
    """Name of a deck's options group; filtered decks have none."""
    deck = col.decks.get(deck_id)
    if deck is None or deck.get("dyn"):
        return "filtered"
    conf = col.decks.config_dict_for_deck_id(deck_id)
    return conf.get("name", "") if conf else ""

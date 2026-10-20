"""The deck overview: the deck's counts, a plain Study button and one line with time
left, maturity and reviews due tomorrow; the detail is in tooltips.

`build` returns the HTML that replaces the overview's counts table (Anki keeps the
deck name and description above it). Counts include subdecks, as in the deck list.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import deck_list, queries, stats
from .fmt import DASH, SEP, count, duration, percent, tip
from .stats import DeckCounts


@dataclass
class Deck:
    due: int  # today's counts after daily limits, as the reviewer will show them
    new: int
    learn: int
    buried_due: int  # cards held back from today's counts by burying
    buried_new: int
    buried_learn: int
    counts: DeckCounts
    recent_secs_per_card: float | None  # whole collection, last 30 days


def _count(label: str, n: int, buried: int, *lines: str) -> str:
    if buried:
        lines = (*lines, f"Buried {buried}")
    return f'<div class="ad-cnt"{tip(*lines)}><b>{count(n)}</b><span>{label}</span></div>'


def render(d: Deck) -> str:
    c = d.counts
    counts = (
        _count(
            "due",
            d.due,
            d.buried_due,
            f"Due today {d.due}",
            f"All due, ignoring limits {c.due_all}",
        )
        + _count("new", d.new, d.buried_new, f"New today {d.new}", f"Unseen in deck {c.unseen}")
        + _count(
            "learn",
            d.learn,
            d.buried_learn,
            f"Learning {c.learn_now + c.learn_later + c.learn_other}",
            f"Due now {c.learn_now}",
            f"Later today {c.learn_later}",
            f"Other day {c.learn_other}",
        )
    )
    study = '<button id=study class="ad-study" onclick="pycmd(\'study\')" autofocus>Study</button>'

    cards_left = d.due + d.new + d.learn
    spc = c.secs / c.reps if c.reps else d.recent_secs_per_card
    done = f"Done today {c.done} cards"
    if c.reps:
        done += f" in {duration(c.secs)}, {c.secs / c.reps:.1f} s/card"
    if spc is None:
        left = f"<span{tip('Time left today', done)}>{DASH} left</span>"
    else:
        left = (
            f"<span{tip('Time left today', f'{cards_left} cards at {spc:.1f} s/card', done)}>"
            f"~{stats.minutes_left(cards_left, spc):.0f} min left</span>"
        )
    mature = percent(deck_list.mature_share(c)) if c.total else DASH
    line = SEP.join(
        [
            left,
            f"<span{deck_list.maturity_tip(c)}>{mature} mature</span>",
            f"<span{tip('Reviews that become due tomorrow')}>{count(c.tomorrow)} tmrw</span>",
        ]
    )
    return (
        f'<div class="ad-ov"><div class="ad-cnts">{counts}</div>{study}'
        f'<div class="ad-ov-line">{line}</div></div>'
    )


def build(col) -> str:
    """HTML for the overview's counts table, for the current deck."""
    clock = queries.DayClock.of(col)
    node = col.sched.deck_due_tree(col.decks.get_current_id())
    rolled = stats.rollup([deck_list.stats_tree(node)], queries.deck_counts(col, clock))
    new, learn, due = col.sched.counts()
    return render(
        Deck(
            due=due,
            new=new,
            learn=learn,
            buried_due=max(node.review_count - due, 0),
            buried_new=max(node.new_count - new, 0),
            buried_learn=max(node.learn_count - learn, 0),
            counts=rolled.get(node.deck_id, DeckCounts()),
            recent_secs_per_card=queries.secs_per_card(col, clock),
        )
    )

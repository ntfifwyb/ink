"""The deck overview: the deck's counts, Study Now with time left, the maturity bar
and a today line.

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
            "Due",
            d.due,
            d.buried_due,
            f"Due today {d.due}",
            f"All due, ignoring limits {c.due_all}",
        )
        + _count("New", d.new, d.buried_new, f"New today {d.new}", f"Unseen in deck {c.unseen}")
        + _count(
            "Learn",
            d.learn,
            d.buried_learn,
            f"Learning {c.learn_now + c.learn_later + c.learn_other}",
            f"Due now {c.learn_now}",
            f"Later today {c.learn_later}",
            f"Other day {c.learn_other}",
        )
    )

    cards_left = d.due + d.new + d.learn
    spc = c.secs / c.reps if c.reps else d.recent_secs_per_card
    if spc is None:
        left = DASH
    else:
        left = (
            f"<span{tip('Time left today', f'{cards_left} cards at {spc:.1f} s/card')}>"
            f"~{stats.minutes_left(cards_left, spc):.0f} min left</span>"
        )
    go = (
        '<div class="ad-go"><button id=study class="ad-study" onclick="pycmd(\'study\')" '
        f'autofocus>Study Now</button><div class="ad-left">{left}</div></div>'
    )

    legend = SEP.join(
        [
            f"new {count(c.unseen)}",
            f"young {count(c.young)}",
            f"mature {count(c.mature)}",
            f"<b>{percent(deck_list.mature_share(c))}</b> mature" if c.total else DASH,
        ]
    )
    maturity = (
        f'<div class="ad-ov-mat"{deck_list.maturity_tip(c)}>{deck_list.maturity_bar(c)}'
        f'<div class="ad-ov-legend">{legend}</div></div>'
    )

    done = [f"<b>{c.done}</b> cards"]
    if c.reps:
        done += [duration(c.secs), f"{c.secs / c.reps:.1f} s/card"]
    today = SEP.join(
        [
            f"<span{tip('Reviewed today', f'Answers {c.reps}')}>today {done[0]}</span>",
            *done[1:],
            f"<span{tip('Reviews that become due tomorrow')}>{c.tomorrow} due tomorrow</span>",
        ]
    )
    return (
        f'<div class="ad-ov"><div class="ad-cnts">{counts}</div>{go}{maturity}'
        f'<div class="ad-ov-today">{today}</div></div>'
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

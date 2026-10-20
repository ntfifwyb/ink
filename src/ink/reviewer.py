"""The reviewer: a thin progress bar for today's queue and a line of session stats.

Card content keeps the note's own styling; these two elements are laid over it by
reviewer.js. `build` returns what that script needs after each question is shown.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import queries
from .fmt import DASH, SEP, percent, tip


@dataclass
class Review:
    due: int  # left in today's queue after daily limits, the card on screen included
    new: int
    learn: int
    done_today: int  # cards answered today in this deck, with subdecks
    session_cards: int  # since the reviewer opened
    session_reps: int
    session_secs: float
    recent_secs_per_card: float | None  # whole collection, last 30 days

    @property
    def left(self) -> int:
        return self.due + self.new + self.learn


def queue_share(done: int, left: int) -> float:
    """Share of today's queue that is done; an empty queue counts as done."""
    total = done + left
    return done / total if total else 1.0


def elapsed(secs: float) -> str:
    """Elapsed time as m:ss, or h:mm:ss from an hour."""
    s = int(secs)
    h, m = divmod(s // 60, 60)
    return f"{h}:{m:02d}:{s % 60:02d}" if h else f"{m}:{s % 60:02d}"


def progress_tip(r: Review) -> str:
    share = queue_share(r.done_today, r.left)
    return tip(
        "Today's queue",
        f"{r.done_today} of {r.done_today + r.left} cards done ({percent(share)})",
        f"Left {r.left}: due {r.due}, new {r.new}, learning {r.learn}",
    )


def session(r: Review) -> str:
    spc = r.session_secs / r.session_reps if r.session_reps else None
    pace = spc if spc is not None else r.recent_secs_per_card
    if pace is None:
        left = DASH
    else:
        source = "this session's pace" if spc is not None else "the last 30 days' pace"
        left = (
            f"<span{tip('Time left today', f'{r.left} cards at {pace:.1f} s/card', source)}>"
            f"~{round(r.left * pace / 60)}m</span>"
        )
    parts = [
        f"<span{tip('Cards this session', f'Answers {r.session_reps}')}>"
        f"<b>{r.session_cards}</b></span>",
        f"<span{tip('Time this session')}>{elapsed(r.session_secs)}</span>",
        f"<span{tip('Seconds per card')}>{spc:.1f}s</span>" if spc is not None else DASH,
        left,
    ]
    return SEP.join(parts)


def overlay(r: Review, progress_bar: bool, session_stats: bool) -> str:
    """The elements reviewer.js lays over the card."""
    out = ""
    if progress_bar:
        width = queue_share(r.done_today, r.left) * 100
        out += f'<div class="ad-prog"{progress_tip(r)}><i style="width:{width:.2f}%"></i></div>'
    if session_stats:
        out += f'<div class="ad-sess">{session(r)}</div>'
    return out


def build(col, since_ms: int) -> Review:
    """Today's queue for the current deck and the session since `since_ms`."""
    day = queries.DayClock.of(col)
    new, learn, due = col.sched.counts()
    cards, reps, secs = queries.answers_since(col, since_ms)
    deck_ids = list(col.decks.deck_and_child_ids(col.decks.get_current_id()))
    return Review(
        due=due,
        new=new,
        learn=learn,
        done_today=queries.cards_done_today(col, day, deck_ids),
        session_cards=cards,
        session_reps=reps,
        session_secs=secs,
        recent_secs_per_card=queries.secs_per_card(col, day),
    )

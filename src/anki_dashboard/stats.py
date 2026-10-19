"""Pure stats logic: no Anki imports, so every rule here is unit-tested directly.

Days are offsets from today's Anki day: 0 is today, -1 yesterday, and so on.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields

MATURE_IVL = 21  # days; Anki's own young/mature boundary


@dataclass
class DeckCounts:
    """Card and review counts for one deck. From the database each deck holds only
    its own cards; after `rollup` a deck also includes its subdecks."""

    unseen: int = 0  # new cards never studied
    young: int = 0  # studied, interval under MATURE_IVL
    mature: int = 0
    notes: int = 0
    due_all: int = 0  # reviews due today, ignoring daily limits
    learn_now: int = 0  # intraday learning due within the learn-ahead limit
    learn_later: int = 0  # intraday learning due later today
    learn_other: int = 0  # interday learning (steps of a day or more)
    tomorrow: int = 0  # reviews that become due tomorrow
    done: int = 0  # cards reviewed today
    reps: int = 0  # answers today
    secs: float = 0.0  # time spent today

    @property
    def total(self) -> int:
        return self.unseen + self.young + self.mature

    def add(self, other: DeckCounts) -> None:
        for f in fields(self):
            setattr(self, f.name, getattr(self, f.name) + getattr(other, f.name))


@dataclass
class TreeNode:
    deck_id: int
    children: list[TreeNode]


def rollup(roots: Iterable[TreeNode], own: Mapping[int, DeckCounts]) -> dict[int, DeckCounts]:
    """Each deck's counts including all of its subdecks."""
    out: dict[int, DeckCounts] = {}

    def visit(node: TreeNode) -> DeckCounts:
        acc = DeckCounts()
        acc.add(own.get(node.deck_id, DeckCounts()))
        for child in node.children:
            acc.add(visit(child))
        out[node.deck_id] = acc
        return acc

    for root in roots:
        visit(root)
    return out


def current_streak(study_days: set[int]) -> int:
    """Consecutive study days ending today. A streak that reached yesterday still
    counts while today has no reviews yet, so it doesn't read 0 every morning."""
    day = 0 if 0 in study_days else -1
    n = 0
    while day in study_days:
        n += 1
        day -= 1
    return n


def longest_streak(study_days: set[int]) -> int:
    best = 0
    for day in study_days:
        if day + 1 in study_days:
            continue  # count each run once, from its last day
        n = 0
        while day - n in study_days:
            n += 1
        best = max(best, n)
    return best


def study_day_average(day_reps: Mapping[int, int]) -> float:
    """Average answers per day, over days with at least one answer."""
    days = [r for r in day_reps.values() if r > 0]
    return sum(days) / len(days) if days else 0.0


def share_of_days_studied(study_days: set[int]) -> float:
    """Fraction of days studied, from the first study day through today."""
    if not study_days:
        return 0.0
    span = -min(min(study_days), 0) + 1
    return len(study_days) / span


def week_start_offset(weekday: int) -> int:
    """Offset of this week's Monday, given today's weekday (Monday is 0)."""
    return -weekday


def secs_in_range(day_secs: Mapping[int, float], first: int, last: int = 0) -> float:
    return sum(s for d, s in day_secs.items() if first <= d <= last)


def minutes_left(cards_left: int, secs_per_card: float) -> float:
    return cards_left * secs_per_card / 60

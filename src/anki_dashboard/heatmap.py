"""The review heatmap: one calendar year of study days as an SVG grid, a column per
week with Monday on top, and one stats line for the whole history.

The SVG has only a viewBox, so it scales to the width of its container and never
overflows. Days are offsets from today, as in `stats.py`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta

from . import stats
from .fmt import SEP, duration, percent, tip

CELL, GAP = 11, 2
STEP = CELL + GAP
TOP = 14  # room for the month labels
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
WEEKDAYS = "Mon Tue Wed Thu Fri Sat Sun".split()


@dataclass
class Heatmap:
    year: int
    today: date
    days: Mapping[int, tuple[int, float]]  # day offset -> (answers, seconds), whole history

    @property
    def years(self) -> tuple[int, int]:
        """First and last year that can be shown: from the first review to this year."""
        first = min((d for d, (n, _) in self.days.items() if n), default=0)
        return (self.today + timedelta(days=first)).year, self.today.year


def thresholds(day_reps: Mapping[int, int]) -> list[int]:
    """Lower bounds of color levels 2 to 4: the quartiles of answers on study days,
    so the ramp fits each user's own volume."""
    reps = sorted(n for n in day_reps.values() if n > 0)
    if not reps:
        return [1, 1, 1]
    return [reps[(len(reps) - 1) * q // 4] for q in (1, 2, 3)]


def level(reps: int, bounds: list[int]) -> int:
    """0 for no reviews, then 1 (dimmest) to 4 (brightest)."""
    return 1 + sum(reps >= b for b in bounds) if reps > 0 else 0


def day_label(d: date) -> str:
    return f"{WEEKDAYS[d.weekday()]}, {MONTHS[d.month - 1]} {d.day}, {d.year}"


def render_grid(h: Heatmap) -> str:
    start = date(h.year, 1, 1)
    first_col = start.weekday()  # weeks start on Monday
    ndays = (date(h.year + 1, 1, 1) - start).days
    weeks = (ndays + first_col + 6) // 7
    bounds = thresholds({d: n for d, (n, _) in h.days.items()})
    months, cells = [], []
    for i in range(ndays):
        day = start + timedelta(days=i)
        week, row = divmod(i + first_col, 7)
        x, y = week * STEP, TOP + row * STEP
        if day.day == 1:
            months.append(f'<text x="{x}" y="9">{MONTHS[day.month - 1]}</text>')
        offset = (day - h.today).days
        if offset > 0:
            cells.append(f'<rect class="ad-f" x="{x}" y="{y}" width="{CELL}" height="{CELL}"/>')
            continue
        reps, secs = h.days.get(offset, (0, 0.0))
        detail = f"{reps} cards, {duration(secs)}" if reps else "No reviews"
        cells.append(
            f'<rect class="ad-h{level(reps, bounds)}" x="{x}" y="{y}" width="{CELL}" '
            f'height="{CELL}"{tip(day_label(day), detail)}/>'
        )
    return (
        f'<svg class="ad-heat-svg" viewBox="0 0 {weeks * STEP - GAP} {TOP + 7 * STEP - GAP}" '
        f'role="img" aria-label="Reviews in {h.year}">{"".join(months)}{"".join(cells)}</svg>'
    )


def _year_link(year: int, mark: str, label: str, enabled: bool) -> str:
    if not enabled:
        return f'<span class="ad-yr ad-off">{mark}</span>'
    return (
        f'<a class="ad-yr" href=# aria-label="{label}" '
        f"onclick='return pycmd(\"ad-year:{year}\")'>{mark}</a>"
    )


def render_stats(days: Mapping[int, tuple[int, float]]) -> str:
    study_days = {d for d, (n, _) in days.items() if n}
    avg = stats.study_day_average({d: n for d, (n, _) in days.items()})
    return SEP.join(
        [
            f"<span{tip('Daily average', 'Answers on days you studied; rest days not counted')}>"
            f"<b>{avg:.0f}</b> cards/study day</span>",
            f"<span{tip('Days studied', 'From your first review through today')}>"
            f"<b>{percent(stats.share_of_days_studied(study_days))}</b> of days studied</span>",
            f"<span{tip('Longest streak', 'Most days in a row with reviews')}>"
            f"longest streak <b>{stats.longest_streak(study_days)}</b></span>",
            f"<span{tip('Current streak', 'Days in a row with reviews')}>"
            f"current <b>{stats.current_streak(study_days)}</b></span>",
        ]
    )


def render(h: Heatmap) -> str:
    first, last = h.years
    legend = "".join(f'<i class="ad-h{n}"></i>' for n in range(5))
    head = (
        f'<div class="ad-heat-head"><div class="ad-yrs">'
        f"{_year_link(h.year - 1, '&lsaquo;', 'Previous year', h.year > first)}"
        f"<span>{h.year}</span>"
        f"{_year_link(h.year + 1, '&rsaquo;', 'Next year', h.year < last)}</div>"
        f'<span class="ad-legend">less {legend} more</span></div>'
    )
    return (
        f'<div class="ad-heat">{head}{render_grid(h)}'
        f'<div class="ad-heat-stats">{render_stats(h.days)}</div></div>'
    )

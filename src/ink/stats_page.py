"""The stats page: a summary header and a study-time card added to Anki's graphs page,
and a header naming the deck or search that Save PDF prints in place of its controls.

Both count the cards the page shows (its deck, collection or search) and, like the
page, the last 12 months or all history. `stats_page.js` asks for them again whenever
the page's search or range changes. Days are offsets from today, as in `stats.py`.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, timedelta

from . import queries, stats
from .fmt import DASH, SEP, duration, esc, percent, tip
from .heatmap import MONTHS, day_label

RANGE_DAYS = 365  # the page's "last 12 months"
DAYS, WEEKS, MONTHS_SHOWN = 30, 26, 12  # periods in the study-time chart

# Each built-in graph's title, as Anki translates it, by its key in config.GRAPHS
GRAPH_TITLES = {
    "today": "statistics_today_title",
    "future_due": "statistics_future_due_title",
    "calendar": "statistics_calendar_title",
    "reviews": "statistics_reviews_title",
    "card_counts": "statistics_counts_title",
    "intervals": "statistics_intervals_title",
    "ease": "statistics_card_ease_title",
    "difficulty": "statistics_card_difficulty_title",
    "stability": "statistics_card_stability_title",
    "retrievability": "statistics_card_retrievability_title",
    "retention": "statistics_true_retention_title",
    "hours": "statistics_hours_title",
    "buttons": "statistics_answer_buttons_title",
    "added": "statistics_added_title",
}


def graph_keys(tr: object) -> dict[str, str]:
    """Graph key by translated title. Titles this Anki version lacks are skipped."""
    out = {}
    for key, name in GRAPH_TITLES.items():
        title: Callable[[], str] | None = getattr(tr, name, None)
        if title is not None:
            out[title().strip()] = key
    return out


@dataclass
class StatsPage:
    today: date
    days: Mapping[int, tuple[int, float]]  # day offset -> (answers, seconds), whole history
    retention: float | None  # review answers in the last 30 days not marked Again
    all_history: bool  # False: the last 12 months, as the page shows

    @property
    def in_range(self) -> dict[int, tuple[int, float]]:
        if self.all_history:
            return dict(self.days)
        return {d: v for d, v in self.days.items() if d > -RANGE_DAYS}

    @property
    def range_label(self) -> str:
        return "all history" if self.all_history else "last 12 months"


@dataclass
class Period:
    first: date
    answers: int = 0
    secs: float = 0.0


def period_start(day: date, unit: str) -> date:
    """First day of the day, week (from Monday) or month that `day` falls in."""
    if unit == "week":
        return day - timedelta(days=day.weekday())
    if unit == "month":
        return day.replace(day=1)
    return day


def months_back(day: date, n: int) -> date:
    """First day of the month `n` months before `day`'s month."""
    index = day.year * 12 + day.month - 1 - n
    return date(index // 12, index % 12 + 1, 1)


def periods(p: StatsPage, unit: str) -> list[Period]:
    """The chart's periods, oldest first and ending with the current one: 30 days,
    26 weeks, or 12 months (every month since the first review for all history)."""
    now = period_start(p.today, unit)
    if unit == "day":
        firsts = [now - timedelta(days=i) for i in range(DAYS)]
    elif unit == "week":
        firsts = [now - timedelta(weeks=i) for i in range(WEEKS)]
    else:
        count = MONTHS_SHOWN
        studied = [d for d, (n, _) in p.days.items() if n]
        if p.all_history and studied:
            first = p.today + timedelta(days=min(studied))
            count = max(count, (now.year - first.year) * 12 + now.month - first.month + 1)
        firsts = [months_back(now, i) for i in range(count)]
    out = {f: Period(f) for f in reversed(firsts)}
    for offset, (answers, secs) in p.days.items():
        period = out.get(period_start(p.today + timedelta(days=offset), unit))
        if period:
            period.answers += answers
            period.secs += secs
    return list(out.values())


def period_label(first: date, unit: str) -> str:
    if unit == "week":
        return f"Week of {MONTHS[first.month - 1]} {first.day}, {first.year}"
    if unit == "month":
        return f"{MONTHS[first.month - 1]} {first.year}"
    return day_label(first)


def axis_label(first: date, unit: str) -> str:
    if unit == "month":
        return f"{MONTHS[first.month - 1]} {first.year}"
    return f"{MONTHS[first.month - 1]} {first.day}"


def _stat(value: str, label: str, *lines: str) -> str:
    return f'<div class="ad-cnt"{tip(*lines)}><b>{value}</b><span>{label}</span></div>'


def render_summary(p: StatsPage) -> str:
    days = p.in_range
    answers = sum(n for n, _ in days.values())
    secs = sum(s for _, s in days.values())
    study_days = {d for d, (n, _) in p.days.items() if n}
    in_range_days = sum(1 for n, _ in days.values() if n)
    avg = stats.study_day_average({d: n for d, (n, _) in days.items()})
    return (
        '<div class="ad-cnts">'
        + _stat(
            percent(p.retention) if p.retention is not None else DASH,
            "retention",
            "Retention",
            "Review answers in the last 30 days",
            "not marked Again",
        )
        + _stat(
            str(stats.current_streak(study_days)) if study_days else DASH,
            "day streak",
            "Current streak",
            "Days in a row with reviews",
            f"Longest {stats.longest_streak(study_days)}",
        )
        + _stat(
            duration(secs) if secs else DASH,
            "study time",
            f"Study time, {p.range_label}",
            f"{answers} answers on {in_range_days} days",
        )
        + _stat(
            f"{avg:.0f}" if avg else DASH,
            "cards/study day",
            "Daily average",
            "Answers on days you studied; rest days not counted",
        )
        + "</div>"
    )


W, H = 600, 180
LEFT, RIGHT, TOP, BOTTOM = 52, 48, 12, 22  # room for the axis labels


def render_chart(ps: list[Period], unit: str) -> str:
    """Time per period as bars, seconds per card as a line, in an SVG that scales
    to its card's width. Each period has a full-height hover target with the detail."""
    pw, ph = W - LEFT - RIGHT, H - TOP - BOTTOM
    slot = pw / len(ps)
    max_secs = max(p.secs for p in ps)
    paces = [p.secs / p.answers if p.answers else None for p in ps]
    max_pace = max((s for s in paces if s is not None), default=0.0) or 1.0
    base = TOP + ph

    bars, hovers, points = [], [], []
    for i, (p, pace) in enumerate(zip(ps, paces, strict=True)):
        x = LEFT + i * slot
        if p.secs:
            h = max(ph * p.secs / max_secs, 1.0)
            bars.append(
                f'<rect x="{x + slot * 0.15:.1f}" y="{base - h:.1f}" '
                f'width="{slot * 0.7:.1f}" height="{h:.1f}" rx="1"/>'
            )
        if pace is not None:
            points.append((x + slot / 2, base - ph * pace / max_pace))
        detail = (
            [duration(p.secs), f"{p.answers} cards", f"{pace:.1f} s/card"]
            if pace is not None
            else ["No reviews"]
        )
        hovers.append(
            f'<rect class="ad-st-hover" x="{x:.1f}" y="{TOP}" width="{slot:.1f}" '
            f'height="{ph}"{tip(period_label(p.first, unit), *detail)}/>'
        )

    trend = ""
    if points:
        path = " ".join(
            f"{'M' if i == 0 else 'L'}{x:.1f} {y:.1f}" for i, (x, y) in enumerate(points)
        )
        dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2"/>' for x, y in points)
        trend = f'<g class="ad-st-trend"><path d="{path}"/>{dots}</g>'

    now = {"day": "today", "week": "this week", "month": "this month"}[unit]
    labels = (
        f'<text class="ad-st-l" x="{LEFT - 6}" y="{TOP + 4}">{duration(max_secs)}</text>'
        f'<text class="ad-st-l" x="{W}" y="{TOP + 4}">{max_pace:.0f} s/card</text>'
        f'<text x="{LEFT}" y="{H - 6}">{axis_label(ps[0].first, unit)}</text>'
        f'<text class="ad-st-l" x="{W - RIGHT}" y="{H - 6}">{now}</text>'
    )
    return (
        f'<svg class="ad-st-svg" data-unit="{unit}" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="Study time per {unit}">'
        f'<line class="ad-st-grid" x1="{LEFT}" x2="{W - RIGHT}" y1="{TOP}" y2="{TOP}"/>'
        f'<line class="ad-st-base" x1="{LEFT}" x2="{W - RIGHT}" y1="{base}" y2="{base}"/>'
        f'<g class="ad-st-bars">{"".join(bars)}</g>{trend}{labels}'
        f"<g>{''.join(hovers)}</g></svg>"
    )


def render_study_time(p: StatsPage) -> str:
    """The study-time card, laid out like Anki's graph cards so it sits in their grid."""
    head = (
        '<h1>Study time</h1><div class="subtitle">Time spent answering, and seconds per card.</div>'
    )
    days = p.in_range
    if not any(n for n, _ in days.values()):
        return f'{head}<div class="ad-st-empty">No reviews in the {p.range_label}.</div>'
    tabs = "".join(
        f'<button type="button" data-unit="{u}">{u.capitalize()}</button>'
        for u in ("day", "week", "month")
    )
    legend = (
        '<span class="ad-st-key"><i class="ad-st-kbar"></i>time</span>'
        '<span class="ad-st-key"><i class="ad-st-kline"></i>s/card</span>'
    )
    charts = "".join(render_chart(periods(p, u), u) for u in ("day", "week", "month"))
    week = stats.week_start_offset(p.today.weekday())
    secs = {d: s for d, (_, s) in days.items()}
    studied = sum(1 for n, _ in days.values() if n)
    totals = SEP.join(
        [
            f"today <b>{duration(stats.secs_in_range(secs, 0))}</b>",
            f"this week <b>{duration(stats.secs_in_range(secs, week))}</b>",
            f"this month <b>{duration(stats.secs_in_range(secs, 1 - p.today.day))}</b>",
            f"<span{tip('Average time on days you studied', p.range_label)}>"
            f"<b>{duration(sum(secs.values()) / studied)}</b>/study day</span>",
        ]
    )
    return (
        f'{head}<div class="ad-st-bar"><div class="ad-st-tabs">{tabs}</div>{legend}</div>'
        f'{charts}<div class="ad-st-totals">{totals}</div>'
    )


def scope_title(search: str, current_deck: str) -> str:
    """What the page counts: the deck's name for the deck button's search, the whole
    collection for an empty one, otherwise the search as typed."""
    search = search.strip()
    if not search:
        return "Whole collection"
    if search == "deck:current":
        return current_deck
    return search


def render_scope(title: str, p: StatsPage, printed: date) -> str:
    """The printed page's header, in place of the scope and range controls. It's dated
    by the calendar, not by Anki's day, which starts at the rollover hour."""
    when = f"{MONTHS[printed.month - 1]} {printed.day}, {printed.year}"
    return f"<b>{esc(title)}</b><span>{p.range_label}{SEP}{when}</span>"


def render(p: StatsPage, title: str = "", printed: date | None = None) -> dict[str, str]:
    return {
        "scope": render_scope(title, p, printed or date.today()) if title else "",
        "summary": render_summary(p),
        "study": render_study_time(p),
    }


def build(col, search: str, all_history: bool) -> dict[str, str]:
    """Both sections for the page's search and range. A search Anki can't parse gives
    empty sections; the page shows its own error for it."""
    clock = queries.DayClock.of(col)
    try:
        cards = queries.search_filter(col, search)
    except Exception:  # anki.errors.SearchError, kept generic so older versions load
        return {"scope": "", "summary": "", "study": ""}
    return render(
        StatsPage(
            today=clock.date,
            days=queries.day_reviews(col, clock, cards),
            retention=queries.retention(col, clock, cards=cards),
            all_history=all_history,
        ),
        scope_title(search, col.decks.current()["name"]),
    )

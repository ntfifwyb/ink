"""The deck list: a compact deck table, a two-line summary of today's study and the
review heatmap.

`build` reads the collection and returns the HTML that replaces the deck browser's
tree and stats sections. The table keeps Anki's row ids and `deck` class, so drag
and drop, collapsing, options and shift-click selection work as before.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import heatmap, queries, stats
from .config import Config
from .fmt import DASH, SEP, count, duration, esc, percent, tip
from .stats import DeckCounts

GEAR = (
    '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M9.4 1l.3 1.8c.5.2 1 .5 1.4.8'
    "l1.7-.7 1.4 2.4-1.4 1.2a5 5 0 010 1.6l1.4 1.2-1.4 2.4-1.7-.7c-.4.3-.9.6-1.4.8L9.4 "
    "15H6.6l-.3-1.8c-.5-.2-1-.5-1.4-.8l-1.7.7-1.4-2.4 1.4-1.2a5 5 0 010-1.6L1.8 6.7l1.4-"
    '2.4 1.7.7c.4-.3.9-.6 1.4-.8L6.6 1h2.8zM8 5.5a2.5 2.5 0 100 5 2.5 2.5 0 000-5z"/></svg>'
)


@dataclass
class Row:
    deck_id: int
    name: str
    level: int
    collapsed: bool
    has_children: bool
    filtered: bool
    current: bool
    group: str
    due: int  # today's counts after daily limits, as Anki schedules them
    new: int
    learn: int
    counts: DeckCounts  # including subdecks


@dataclass
class Today:
    reps: int
    secs: float
    cards_left: int
    recent_secs_per_card: float | None
    streak: int
    total_secs: float
    week_secs: float
    retention: float | None
    desired_retention: float | None  # set only when FSRS is on
    per_study_day: float


def _due(r: Row) -> str:
    return (
        f'<td class="ad-n{" ad-hi" if r.due else ""}"'
        + tip(f"Due today {r.due}", f"All due, ignoring limits {r.counts.due_all}")
        + f">{count(r.due)}</td>"
    )


def _new(r: Row) -> str:
    return (
        '<td class="ad-n"'
        + tip(f"New today {r.new}", f"Unseen in deck {r.counts.unseen}")
        + f">{count(r.new)}</td>"
    )


def _learn(r: Row) -> str:
    c = r.counts
    return (
        '<td class="ad-n"'
        + tip(
            f"Learning {c.learn_now + c.learn_later + c.learn_other}",
            f"Due now {c.learn_now}",
            f"Later today {c.learn_later}",
            f"Other day {c.learn_other}",
        )
        + f">{count(r.learn)}</td>"
    )


def _done(r: Row) -> str:
    c = r.counts
    return (
        '<td class="ad-n"'
        + tip(f"Reviewed today {c.done}", f"Answers {c.reps}", f"Time {duration(c.secs)}")
        + f">{count(c.done)}</td>"
    )


def _tmrw(r: Row) -> str:
    return (
        '<td class="ad-n"'
        + tip(f"Due tomorrow {r.counts.tomorrow}", "Reviews that become due tomorrow")
        + f">{count(r.counts.tomorrow)}</td>"
    )


def _maturity(r: Row) -> str:
    c = r.counts
    total = c.total

    def width(n: int) -> str:
        return f"{n / total * 100:.2f}%" if total else "0"

    share = c.mature / total if total else 0.0
    bar = (
        f'<div class="ad-bar"><i class="ad-new" style="width:{width(c.unseen)}"></i>'
        f'<i class="ad-young" style="width:{width(c.young)}"></i>'
        f'<i class="ad-mature" style="width:{width(c.mature)}"></i></div>'
    )
    label = percent(share) if total else DASH
    return (
        '<td class="ad-mat"'
        + tip(
            f"{total} cards, {c.notes} notes",
            f"New {c.unseen}",
            f"Young {c.young} (interval under {stats.MATURE_IVL} days)",
            f"Mature {c.mature}",
            f"{percent(share)} mature",
        )
        + f'><div class="ad-mat-in">{bar}<span class="ad-pct">{label}</span></div></td>'
    )


# key: (header, header tooltip, value that decides "empty", cell)
COLUMNS = {
    "due": ("Due", "Reviews due today", lambda r: r.due, _due),
    "new": ("New", "New cards you will see today", lambda r: r.new, _new),
    "learn": ("Learn", "Cards in learning due today", lambda r: r.learn, _learn),
    "done": ("Done", "Cards reviewed today", lambda r: r.counts.done, _done),
    "tmrw": ("Tmrw", "Reviews due tomorrow", lambda r: r.counts.tomorrow, _tmrw),
    "maturity": ("Maturity", "New / young / mature cards", lambda r: 1, _maturity),
}


def visible_columns(rows: list[Row], columns: list[str], hide_empty: bool) -> list[str]:
    return [
        key
        for key in columns
        if key in COLUMNS and (not hide_empty or any(COLUMNS[key][2](r) for r in rows))
    ]


def _name_cell(r: Row) -> str:
    if r.has_children:
        mark = "▸" if r.collapsed else "▾"
        twist = (
            f'<a class="ad-tw" href=# onclick=\'return pycmd("collapse:{r.deck_id}")\'>{mark}</a>'
        )
    else:
        twist = '<span class="ad-tw"></span>'
    klass = "ad-deck ad-filtered" if r.filtered else "ad-deck"
    return (
        f'<td class="ad-name"><div class="ad-name-in" style="padding-left:{(r.level - 1) * 16}px">'
        f'{twist}<a class="{klass}" href=# onclick="return pycmd(\'open:{r.deck_id}\')">'
        f"{esc(r.name)}</a>"
        f'<a class="ad-opt" href=# onclick=\'return pycmd("opts:{r.deck_id}")\'>'
        f"{esc(r.group)}{GEAR}</a></div></td>"
    )


def render_table(rows: list[Row], columns: list[str]) -> str:
    """Rows for Anki's deck table: a colgroup, a header row, then one row per deck."""
    cols = "<col>" + "".join(f'<col class="ad-c-{k}">' for k in columns)
    head = "<th>Deck</th>" + "".join(
        f'<th class="ad-c-{k}"' + tip(COLUMNS[k][1]) + f">{COLUMNS[k][0]}</th>" for k in columns
    )
    out = [
        f"<colgroup>{cols}</colgroup>",
        f'<tr class="ad-head">{head}</tr>',
        f"<tr class='top-level-drag-row'><td colspan='{len(columns) + 1}'></td></tr>",
    ]
    for r in rows:
        klass = "deck ad-row current" if r.current else "deck ad-row"
        cells = "".join(COLUMNS[k][3](r) for k in columns)
        out.append(
            f'<tr class="{klass}" id="{r.deck_id}" '
            f"onclick='if(event.shiftKey) return pycmd(\"select:{r.deck_id}\")'>"
            f"{_name_cell(r)}{cells}</tr>"
        )
    return "".join(out)


def render_today(t: Today) -> str:
    spc = t.secs / t.reps if t.reps else t.recent_secs_per_card
    left = f"~{stats.minutes_left(t.cards_left, spc):.0f} min left" if spc is not None else DASH
    line1 = SEP.join(
        [
            f"<b>{t.reps}</b> cards",
            duration(t.secs),
            f"{t.secs / t.reps:.1f} s/card" if t.reps else DASH,
            f"<span{tip('Time left today', f'{t.cards_left} cards due at {spc or 0:.1f} s/card')}>"
            f"{left}</span>",
            f"<span{tip('Current streak', 'Days in a row with reviews')}>streak {t.streak}</span>",
        ]
    )
    if t.retention is None:
        ret = f"<span{tip('Retention', 'No reviews in the last 30 days')}>retention {DASH}</span>"
    else:
        lines = ["Review answers in the last 30 days that were not Again"]
        if t.desired_retention is not None:
            lines.append(f"FSRS desired retention {percent(t.desired_retention)}")
        ret = (
            f"<span{tip('Retention, last 30 days', *lines)}>retention {percent(t.retention)}</span>"
        )
    line2 = SEP.join(
        [
            f"<span{tip('All study time')}>all time {duration(t.total_secs)}</span>",
            f"<span{tip('Since Monday')}>this week {duration(t.week_secs)}</span>",
            ret,
            f"<span{tip('Average on days you studied', 'Days without reviews are not counted')}>"
            f"{t.per_study_day:.0f}/day avg (study days)</span>",
        ]
    )
    return (
        f'<div class="ad-today"><div class="ad-l1">{line1}</div>'
        f'<div class="ad-l2">{line2}</div></div>'
    )


def rows_from_tree(col, tree, rolled: dict[int, DeckCounts], current_id: int) -> list[Row]:
    rows: list[Row] = []

    def visit(node) -> None:
        rows.append(
            Row(
                deck_id=node.deck_id,
                name=node.name,
                level=node.level,
                collapsed=node.collapsed,
                has_children=bool(node.children),
                filtered=node.filtered,
                current=node.deck_id == current_id,
                group=queries.options_group(col, node.deck_id),
                due=node.review_count,
                new=node.new_count,
                learn=node.learn_count,
                counts=rolled.get(node.deck_id, DeckCounts()),
            )
        )
        if not node.collapsed:
            for child in node.children:
                visit(child)

    for child in tree.children:
        visit(child)
    return rows


def _stats_tree(node) -> stats.TreeNode:
    return stats.TreeNode(node.deck_id, [_stats_tree(c) for c in node.children])


def today_summary(col, tree, clock: queries.DayClock, days: dict[int, tuple[int, float]]) -> Today:
    reps, secs = days.get(0, (0, 0.0))
    study_days = {d for d, (n, _) in days.items() if n}
    day_secs = {d: s for d, (_, s) in days.items()}
    fsrs = queries.fsrs_enabled(col)
    return Today(
        reps=reps,
        secs=secs,
        cards_left=sum(c.new_count + c.learn_count + c.review_count for c in tree.children),
        recent_secs_per_card=queries.secs_per_card(col, clock),
        streak=stats.current_streak(study_days),
        total_secs=sum(day_secs.values()),
        week_secs=stats.secs_in_range(day_secs, stats.week_start_offset(clock.date.weekday())),
        retention=queries.retention(col, clock),
        desired_retention=(
            queries.desired_retention(col, col.decks.get_current_id()) if fsrs else None
        ),
        per_study_day=stats.study_day_average({d: n for d, (n, _) in days.items()}),
    )


def build(col, tree, cfg: Config, year: int | None = None) -> tuple[str, str]:
    """HTML for the deck browser's tree and stats sections. `year` is the heatmap's
    year, this year when None or out of range."""
    clock = queries.DayClock.of(col)
    rolled = stats.rollup([_stats_tree(c) for c in tree.children], queries.deck_counts(col, clock))
    rows = rows_from_tree(col, tree, rolled, col.decks.get_current_id())
    dl = cfg.deck_list
    table = render_table(rows, visible_columns(rows, dl.columns, dl.hide_empty_columns))
    days = queries.day_reviews(col, clock)
    today = render_today(today_summary(col, tree, clock, days)) if dl.today_strip else ""
    heat = ""
    if dl.heatmap:
        h = heatmap.Heatmap(clock.date.year, clock.date, days)
        first, last = h.years
        h.year = min(max(year or last, first), last)
        heat = heatmap.render(h)
    return table, f'<div class="ad-root">{today}{heat}</div>'

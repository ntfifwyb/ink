"""Settings from config.json, merged over the defaults and validated, so a typo in
the add-on config dialog falls back to a default instead of breaking a screen."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

COLORS = {
    "bg": "#0d0d0e",
    "surface": "#151516",
    "raised": "#1c1c1e",
    "line": "#29292b",
    "fg1": "#ececec",
    "fg2": "#a3a3a6",
    "fg3": "#6e6e72",
    "fg4": "#46464a",
    "accent": "#f5f5f5",
    "accent2": "#b0b0b3",
    "accent3": "#727275",
    "accent4": "#3b3b3e",
    "empty": "#1e1e20",
}
DECK_COLUMNS = ("due", "new", "learn", "done", "tmrw", "maturity")
# Anki's built-in graphs, in page order; the stats page hides those listed in hidden_graphs
GRAPHS = (
    "today",
    "future_due",
    "calendar",
    "reviews",
    "card_counts",
    "intervals",
    "ease",
    "difficulty",
    "stability",
    "retrievability",
    "retention",
    "hours",
    "buttons",
    "added",
)

# hex, rgb()/hsl() and named colors; nothing that could close the style block
_COLOR = re.compile(r"^[#a-zA-Z0-9(),.%\s]{1,40}$")


@dataclass
class DeckListConfig:
    columns: list[str] = field(default_factory=lambda: list(DECK_COLUMNS))
    hide_empty_columns: bool = True
    today_strip: bool = True
    heatmap: bool = True


@dataclass
class ReviewerConfig:
    progress_bar: bool = True
    session_stats: bool = True
    edit_more: bool = False


@dataclass
class StatsConfig:
    summary: bool = True
    study_time: bool = True
    hidden_graphs: list[str] = field(default_factory=lambda: ["today", "calendar"])


@dataclass
class Config:
    colors: dict[str, str] = field(default_factory=lambda: dict(COLORS))
    deck_list: DeckListConfig = field(default_factory=DeckListConfig)
    reviewer: ReviewerConfig = field(default_factory=ReviewerConfig)
    stats: StatsConfig = field(default_factory=StatsConfig)


def load(raw: Any) -> Config:
    raw = raw if isinstance(raw, dict) else {}
    cfg = Config()

    colors = raw.get("colors")
    if isinstance(colors, dict):
        for key, value in colors.items():
            if key in COLORS and isinstance(value, str) and _COLOR.match(value):
                cfg.colors[key] = value.strip()

    deck = raw.get("deck_list")
    if isinstance(deck, dict):
        cols = deck.get("columns")
        if isinstance(cols, list):
            cfg.deck_list.columns = [c for c in dict.fromkeys(cols) if c in DECK_COLUMNS]
        for key in ("hide_empty_columns", "today_strip", "heatmap"):
            if isinstance(deck.get(key), bool):
                setattr(cfg.deck_list, key, deck[key])

    rev = raw.get("reviewer")
    if isinstance(rev, dict):
        for key in ("progress_bar", "session_stats", "edit_more"):
            if isinstance(rev.get(key), bool):
                setattr(cfg.reviewer, key, rev[key])

    st = raw.get("stats")
    if isinstance(st, dict):
        hidden = st.get("hidden_graphs")
        if isinstance(hidden, list):
            cfg.stats.hidden_graphs = [g for g in dict.fromkeys(hidden) if g in GRAPHS]
        for key in ("summary", "study_time"):
            if isinstance(st.get(key), bool):
                setattr(cfg.stats, key, st[key])
    return cfg


def css_variables(colors: dict[str, str]) -> str:
    """A :root rule defining each color as --ad-<name>."""
    body = "".join(f"--ad-{k}:{v};" for k, v in colors.items())
    return f":root{{{body}}}"


def menu_bar_qss(colors: dict[str, str]) -> str:
    """Qt stylesheet for the main window's menu bar."""
    c = colors
    return (
        f"QMenuBar {{ background: {c['bg']}; color: {c['fg2']}; border: none; }}"
        f"QMenuBar::item {{ background: transparent; padding: 4px 8px; }}"
        "QMenuBar::item:selected, QMenuBar::item:pressed"
        f" {{ background: {c['raised']}; color: {c['fg1']}; }}"
    )


def stats_dialog_qss(colors: dict[str, str]) -> str:
    """Qt stylesheet for the stats window's frame: its deck chooser and buttons."""
    c = colors
    return (
        f"QDialog {{ background: {c['bg']}; color: {c['fg2']}; }}"
        f"QLabel {{ color: {c['fg3']}; }}"
        f"QPushButton {{ background: {c['bg']}; color: {c['fg2']}; border: 1px solid {c['line']};"
        " border-radius: 4px; padding: 3px 12px; }"
        f"QPushButton:hover {{ background: {c['raised']}; color: {c['fg1']}; }}"
    )

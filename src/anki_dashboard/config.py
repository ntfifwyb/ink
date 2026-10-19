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

# hex, rgb()/hsl() and named colors; nothing that could close the style block
_COLOR = re.compile(r"^[#a-zA-Z0-9(),.%\s]{1,40}$")


@dataclass
class DeckListConfig:
    columns: list[str] = field(default_factory=lambda: list(DECK_COLUMNS))
    hide_empty_columns: bool = True
    today_strip: bool = True
    heatmap: bool = True


@dataclass
class Config:
    colors: dict[str, str] = field(default_factory=lambda: dict(COLORS))
    deck_list: DeckListConfig = field(default_factory=DeckListConfig)


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
    return cfg


def css_variables(colors: dict[str, str]) -> str:
    """A :root rule defining each color as --ad-<name>."""
    body = "".join(f"--ad-{k}:{v};" for k, v in colors.items())
    return f":root{{{body}}}"

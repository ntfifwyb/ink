"""Small HTML and number formatters shared by the screens."""

from __future__ import annotations

import html

DASH = '<span class="ad-zero">&ndash;</span>'
SEP = '<span class="ad-sep">&middot;</span>'


def esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def count(n: int) -> str:
    """A count, or a dim dash for zero."""
    return str(n) if n else DASH


def duration(secs: float) -> str:
    """Minutes with one decimal, or hours once it reaches an hour."""
    minutes = secs / 60
    if minutes >= 60:
        return f"{minutes / 60:.1f} h"
    return f"{minutes:.1f} min"


def percent(share: float) -> str:
    return f"{round(share * 100)}%"


def tip(title: str, *lines: str) -> str:
    """A data-tip attribute: a bold title and plain lines, shown by dashboard.js."""
    body = f"<b>{esc(title)}</b>" + "".join(f"\n{esc(line)}" for line in lines)
    return f' data-tip="{esc(body)}"'

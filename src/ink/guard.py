"""Keeps an error in one of Ink's hooks from breaking Anki.

Anki shows its error dialog when a hook raises, and also removes that hook for the
rest of the session. A guarded hook instead returns its fallback, which leaves
Anki's own content in place, and stays registered. Each error is written to a log
file in the add-on's user_files folder (kept across updates), and the first one in a
session calls `notify`. No Anki imports, so it's tested directly.
"""

from __future__ import annotations

import functools
import sys
import time
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any

MAX_LOG_BYTES = 100_000  # past this the log starts over, so it never grows unbounded


class Guard:
    def __init__(self, log_path: Path, notify: Callable[[], None], version: str = "") -> None:
        self.log_path = log_path
        self.notify = notify
        self.version = version
        self.notified = False

    def report(self, where: str) -> None:
        """Log the exception being handled; notify once per session."""
        text = traceback.format_exc()
        print(text, file=sys.stderr)
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            big = self.log_path.exists() and self.log_path.stat().st_size > MAX_LOG_BYTES
            with open(self.log_path, "w" if big else "a", encoding="utf-8") as f:
                stamp = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{stamp} Ink {self.version} in {where}\n{text}\n")
        except OSError:
            pass
        if not self.notified:
            self.notified = True
            try:
                self.notify()
            except Exception:
                pass

    def __call__(self, fallback: Any = None) -> Callable[[Callable], Callable]:
        """Decorate a hook: on an exception it returns `fallback`, or calls it with the
        hook's arguments when it's a function (None if that raises too)."""

        def wrap(fn: Callable) -> Callable:
            @functools.wraps(fn)
            def run(*args: Any) -> Any:
                try:
                    return fn(*args)
                except Exception:
                    self.report(fn.__name__)
                if not callable(fallback):
                    return fallback
                try:
                    return fallback(*args)
                except Exception:
                    self.report(fallback.__name__)
                    return None

            return run

        return wrap

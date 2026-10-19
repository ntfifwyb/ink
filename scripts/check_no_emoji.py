#!/usr/bin/env python3
"""Fail if any tracked text file contains an emoji (a hard rule of the spec)."""

import re
import subprocess
import sys

EMOJI = re.compile(
    "["
    "\U0001f000-\U0001faff"  # pictographs, emoticons, transport, symbols and arrows
    "\u2600-\u27bf"  # miscellaneous symbols and dingbats
    "\u2b00-\u2bff"  # arrows and stars often rendered as emoji
    "\ufe0f"  # emoji presentation selector
    "]"
)


def main() -> int:
    paths = subprocess.run(
        ["git", "ls-files", "-z"], capture_output=True, check=True, text=True
    ).stdout.split("\0")
    bad = 0
    for path in filter(None, paths):
        try:
            text = open(path, encoding="utf-8").read()
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if m := EMOJI.search(line):
                print(f"{path}:{n}: emoji U+{ord(m.group()):04X}")
                bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Zip src/ink into dist/ink.ankiaddon.

Anki expects the add-on's files at the root of the archive, without the package
folder or bytecode. meta.json and user_files (Ink's error log) are left out: Anki
and Ink write them when the package folder is used as an installed add-on during
development. Entries are sorted and timestamped at a fixed date so the same sources
always produce the same archive.
"""

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "ink"
OUT = ROOT / "dist" / "ink.ankiaddon"
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def files() -> list[Path]:
    return sorted(
        p
        for p in SRC.rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and p.suffix != ".pyc"
        and p.relative_to(SRC).as_posix() != "meta.json"
        and p.relative_to(SRC).parts[0] != "user_files"
    )


def build() -> Path:
    OUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files():
            info = zipfile.ZipInfo(p.relative_to(SRC).as_posix(), FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, p.read_bytes())
    return OUT


if __name__ == "__main__":
    out = build()
    print(f"{out.relative_to(ROOT)} ({out.stat().st_size} bytes)")
    sys.exit(0)

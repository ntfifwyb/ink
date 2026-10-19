# Decisions

Dated log of product choices. Check here before asking a question again.

## 2026-10-19: Add-on 877182321
Identified as "Enhance main window" (Arthur Milchior): the extra deck-list columns and percent bar. Confirmed from its README and from the copy installed in the user's Anki.

## 2026-10-19: Target Anki version
The user runs Anki 26.9.3 (Python 3.13, Qt 6.11). Develop and verify against 26.x; keep `min_point_version` at 23.10 and code to Python 3.9 so older Qt6 builds still load it. FSRS is detected at runtime.

## 2026-10-19: Accent color
Monochrome with white as the only accent, replacing the amber in the spec. Neutral grays (no warm tint). Chosen by the user after reviewing the mockup.

## 2026-10-19: Heatmap weeks start on Monday
Rows run Monday to Sunday. Chosen by the user.

## 2026-10-19: Mockup approved
The deck list and reviewer in `docs/mockup.html` are the reference for spacing, labels and tooltips.

## 2026-10-19: Build and release locally
No GitHub Actions. `scripts/build.py` makes `dist/anki-dashboard.ankiaddon`; `scripts/release.sh` tags `v<version>` and publishes the GitHub Release with `gh`. Checks run with `local-ci` (`.local-ci`).

## 2026-10-19: Replaced add-ons are not declared as conflicts (decided by Claude, pending review)
Declaring them in `manifest.json` would make Anki disable them on install. For now the user turns them off by hand, which keeps them available for side-by-side comparison while screens are being built.

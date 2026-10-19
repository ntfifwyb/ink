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

## 2026-10-19: Stat definitions (decided by Claude, pending review)
- **Study time and heatmap use the whole review history**, including cards since deleted. On the user's collection this gives about 1525 min all time, where Study Time Stats showed 19.7 min (it only counted cards that still exist). Review Heatmap already counted everything, so the two now agree.
- **Current streak** still counts a streak that reached yesterday while today has no reviews yet, so it doesn't read 0 every morning.
- **This week** runs from Monday, matching the Monday-first heatmap.
- **Retention** is the share of review-card answers in the last 30 days that were not Again.
- **Days studied** is a share of the days from the first review through today.
- **Maturity** counts every card in the deck, including suspended and buried ones; mature means an interval of 21 days or more.

## 2026-10-19: Heatmap layout and shading (decided by Claude, pending review)
- **Calendar year with arrows**, as in the approved mockup, rather than a rolling 12 months. The arrows reach back to the year of the first review; Anki re-renders the deck list for the chosen year, so only one year is ever in the page.
- **Shades are the quartiles of your own study days** over the whole history, so the ramp fits any volume and years compare on one scale. A single study day shows white.
- **The stats line covers the whole history**, not just the year shown, matching the streak and average in the today strip.

## 2026-10-19: Recolor Anki's toolbar, menu bar and bottom bars
The page's black stopped at Anki's gray top toolbar and bottom bar. The user asked to bring them to the add-on's background if the add-on can, rather than switching the pages to gray. The add-on redefines Anki's theme variables in those webviews and gives the menu bar a Qt stylesheet; the reviewer's bars are left alone until the reviewer is themed.

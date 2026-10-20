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

## 2026-10-19: Replaced add-ons are not declared as conflicts
Declaring them in `manifest.json` would make Anki disable them on install. For now the user turns them off by hand, which keeps them available for side-by-side comparison while screens are being built. Superseded on 2026-10-20 (below).

## 2026-10-19: Stat definitions
- **Study time and heatmap use the whole review history**, including cards since deleted. On the user's collection this gives about 1525 min all time, where Study Time Stats showed 19.7 min (it only counted cards that still exist). Review Heatmap already counted everything, so the two now agree.
- **Current streak** still counts a streak that reached yesterday while today has no reviews yet, so it doesn't read 0 every morning.
- **This week** runs from Monday, matching the Monday-first heatmap.
- **Retention** is the share of review-card answers in the last 30 days that were not Again.
- **Days studied** is a share of the days from the first review through today.
- **Maturity** counts every card in the deck, including suspended and buried ones; mature means an interval of 21 days or more.

## 2026-10-19: Heatmap layout and shading
- **Calendar year with arrows**, as in the approved mockup, rather than a rolling 12 months. The arrows reach back to the year of the first review; Anki re-renders the deck list for the chosen year, so only one year is ever in the page.
- **Shades are the quartiles of your own study days** over the whole history, so the ramp fits any volume and years compare on one scale. A single study day shows white.
- **The stats line covers the whole history**, not just the year shown, matching the streak and average in the today strip.

## 2026-10-19: Recolor Anki's toolbar, menu bar and bottom bars
The page's black stopped at Anki's gray top toolbar and bottom bar. The user asked to bring them to the add-on's background if the add-on can, rather than switching the pages to gray. The add-on redefines Anki's theme variables in those webviews and gives the menu bar a Qt stylesheet; the reviewer's bars are left alone until the reviewer is themed.

## 2026-10-19: Deck overview layout (superseded on 2026-10-20, below)
- **Counts in the deck list's order and words** (Due, New, Learn) rather than Anki's New, Learning, To Review, so both screens read the same. They include subdecks and are the counts after daily limits that the reviewer will show; buried cards appear in the tooltip.
- **Study Now is a solid white button**, the one filled element on the page, with time left under it. Time left uses today's seconds per card in this deck, or the collection's last 30 days before the first review.
- **The today line is for this deck** (with subdecks): cards, time, seconds per card and reviews due tomorrow. The collection-wide strip and the heatmap stay on the deck list.
- **The congratulations page is recolored too.** Anki shows it in place of the overview when a deck is finished; left alone it was gray inside the black bars.

## 2026-10-19: Reviewer layout
- **Today's queue** is the cards answered today in the deck (subdecks included, and cards it lent to filtered decks) against those plus the cards left after daily limits. A card answered Again counts as done and is still among those left, so the bar only reaches the end when the queue is empty.
- **The session** starts when the reviewer opens and counts every answer since. Time is Anki's per-answer time (capped by the deck's maximum answer seconds), not wall-clock time, matching the deck list and overview. Time left uses this session's pace, or the collection's last 30 days before the first answer.
- **Session stats stay in the top right corner**, as in the approved mockup, inside the 20px top margin Anki gives every card so they don't cover card text.
- **Edit and More are hidden by default** (the mockup's unchecked box); `reviewer.edit_more` shows them. Their shortcuts work either way, and with them hidden so is Anki's answer timer that sits inside More.
- **Night-mode page color only.** The card page and bottom bar take `bg` by redefining Anki's `--canvas`, which the default card background uses; notes that set their own background keep it. In light mode the card stays as Anki draws it, while the bottom bar is still `bg`.
- **Labels inside buttons.** The interval (and Show Answer's remaining counts) move inside their buttons, so the bar keeps one height between question and answer.

## 2026-10-19: Stats page scope and hidden graphs
- **The summary and Study time card follow the page**: its deck, collection or search, and its last 12 months or all history choice, so they always agree with the graphs below. Chosen by the user over always counting the whole collection.
- **Today and Calendar are hidden by default**, since the summary header and the deck-list heatmap already show that data. Chosen by the user; `stats.hidden_graphs` changes the list.

## 2026-10-19: Stats page details
- **Graphs are matched by their translated titles** (Anki's own `tr` strings), as the page gives its graph cards no ids. A title Anki changes in a later version stops that graph from being hidden or recolored, but never breaks the page.
- **Gray mapping**: answer buttons Again to Easy go from dimmest to brightest; card counts use the deck list's maturity grays (new `fg4`, young `accent3`, mature `accent`); review kinds run mature brightest to filtered dimmest. Gradients that only repeat the x axis (future due, intervals, added) become one gray, and the rest are desaturated, keeping their light-to-dark order.
- **Study time card periods**: 30 days, 26 weeks (Monday first) or 12 calendar months; with all history, months reach back to the first review. Day is the default tab and the choice lasts while the window is open.
- **Retention stays the last 30 days** whatever the range, as on the deck list; study time and cards per study day follow the range; the streak uses the whole history of the matched cards.
- **The page is always dark**, in light mode too, like the deck list. The stats window can't be narrower than 700px (Anki's minimum), so it was checked at 1680, 900 and 700px. Superseded by the light theme (2026-10-20, below).

## 2026-10-20: Review of the decisions made for the user
Confirmed by the user: study time and the heatmap use the whole review history; the heatmap shows a calendar year with arrows and shades by the quartiles of the user's own study days; the streak counts through a day with no reviews yet; retention stays the last 30 days; Edit and More stay hidden in the reviewer, its session time is Anki's per-answer time, and only its night-mode page color changes; maturity counts every card, suspended and buried included; the stats page stays dark with gray graphs; the overview keeps the deck list's Due, New, Learn order. The remaining details in those entries were walked through with these and stand as written. The "pending review" marks are removed.

## 2026-10-20: Replaced add-ons declared as conflicts
The user chose to have Anki turn off the four replaced add-ons (1771074083, 1556734708, 1247171202, 877182321) on install, rather than turning them off by hand.

## 2026-10-20: Minimal deck overview
The user found the solid white Study Now button "too AI-slopish" and not minimal, and asked for the page to be overhauled. Chosen from two options each: the counts plus one line (time left, percent mature, reviews due tomorrow), dropping the maturity bar and the today line, rather than counts and button alone; a plain-text Study button, underlined on hover, rather than an outlined one; counts at 24px rather than 32px. Labels are lowercase without letter spacing, and today's cards, time and pace moved into the time-left tooltip.

## 2026-10-20: Light-mode reviewer
The user chose to keep the reviewer's card light in Anki's light mode, as the note and Anki draw it, rather than treating the card page as night mode. The progress bar and the session count turn `fg4` there so they show on white; the answer bar stays `bg`.

## 2026-10-20: Light theme
The user asked for a light theme that follows Anki's theme preference, after checking 0.6.6 on Windows. Chosen from two options each: an inverted monochrome palette (near-white background, near-black accent, the same rules mirrored) rather than Anki's stock light grays; a separate `light_colors` config section with the same keys as `colors` rather than a fixed light palette. This replaces "the stats page is always dark" (2026-10-19) and the light-mode reviewer's `fg4` bar and count (2026-10-20): every screen now takes the theme's palette. Decided by Claude and confirmed by the user after checking 0.7.0: the reviewer's page color becomes `bg` in both themes, not only in night mode, so cards without their own background match the bars; the default note type's white card is unaffected.

## 2026-10-20: Renamed to Ink
The user renamed the add-on Ink, and the repo `montinaops/ink`, chosen from name ideas around its monochrome look. Chosen from two options: rename the package and the add-on folder to `ink` too, rather than keeping the internal `anki_dashboard` package so updates stay in place. The user asked for no code that disables Anki Dashboard or copies its settings, since only one install exists and the old add-on won't be released again: updating means deleting it by hand, as the changelog and README say. The internal `--ad-*` CSS variable prefix stays, as nothing outside the add-on sees it.

## 2026-10-20: Moved to the personal account
The user moved the repo from the `montinaops` organization to their personal account, as `ntfifwyb/ink`, with the local folder at `~/projects/ntfifwyb/ink`. GitHub's transfer kept the releases, issues and PRs, and it redirects the old URLs, so v0.8.0's manifest homepage still resolves. The add-on itself is unchanged, so no release.

# Build: anki-dashboard

Build a single Anki add-on that replaces four add-ons I currently use. Change their info, layout and color scheme into one coherent, minimal but information-dense design. Put it in a new private GitHub repo: **montinaops/anki-dashboard** (org: `montinaops`; the org's repos use descriptive kebab-case names).

## Hard rules
- **No emojis anywhere in the project**: UI, README, comments, commit messages.
- **No horizontal scrolling on any screen.** My current setup shows a horizontal scrollbar at the bottom of the main screen (most likely the wide deck table or the heatmap container is wider than the window). Every layout must fit the window, and you can add `overflow-x: hidden` as a safety net.
- Minimalism plus lots of information: short labels, no redundant columns, detail in hover tooltips rather than on screen.

## Add-ons being replaced (reimplement them; don't vendor their code)
| AnkiWeb code | Add-on | What it currently shows |
|---|---|---|
| 1771074083 | Review Heatmap | GitHub-style yearly heatmap plus "Daily average / Days learned / Longest streak / Current streak" |
| 1556734708 | More Decks Stats and Time Left | "Studied N cards in X minutes today (Ys/card)", "Average: Z cards/minute", "N minutes more", "New / Learn / Reviews / Due / Total" counts row |
| 1247171202 | Study Time Stats | "Total 19.68 min / Past Week 1.96 min" |
| 877182321 | Unknown (could not look it up; ask me or check its AnkiWeb page) | Probably the extra deck-list columns: Learning now (later today (other day)), Due today (all), Total, Total Note, Young, Mature, Progress bar, reviewed/repeated today, Due tomorrow, options-group name ("Default") with a gear icon |

### Problems with the current main screen
- Headers are long ("Learning now (later today (other day))", "reviewed/repeated today", "Total Note").
- Data is repeated: Total, Total Note and Young all showed 18. Empty columns (New, Learning, Due, Mature) still take up width.
- The progress bar has no label.
- "Daily average: 120 cards" sits next to "16 today", which is confusing because the average is over study days only. The label must say what the number means.
- The three stat blocks from different add-ons have mismatched alignment, sizes and colors.

## Environment
- I don't know my Anki version or scheduler. Target recent Anki (23.10+ / 24.x / 25.x, Qt6) and **detect FSRS automatically**. When FSRS is on, show FSRS metrics (average retrievability, desired vs. actual retention). Otherwise fall back to SM-2 equivalents or hide them.
- Use Anki's official hooks (`aqt.gui_hooks`: `deck_browser_will_render_content`, `overview_will_render_content`, `reviewer_did_show_question`, `webview_will_set_content`, and so on) and `mw.col.db` / backend queries for stats. Avoid monkeypatching where a hook exists.

## Visual design
- **Monochrome plus one accent: amber.** Near-black background, 3–4 gray text levels, amber used only for data and highlights (bars, heatmap ramp, progress, key numbers).
- One font stack and one spacing scale across all screens. Define every color as a CSS variable, overridable from `config.json`.
- Zeros shown as a dim dash, not "0".

## Screens

### 1. Deck list (main screen)
Default columns, with short headers and full detail in tooltips:
```
Deck                         Due   New  Learn  Done  Tmrw   Maturity
Artificial Intelligence       -     -     -     16    -    [bar]  0%
```
- **Due / New / Learn**: today's actionable counts. Tooltips break these down (learning now vs. later today vs. other day; due today vs. all).
- **Done**: cards reviewed today. The tooltip shows repetitions and time spent.
- **Tmrw**: due tomorrow.
- **Maturity**: stacked new / young / mature bar plus % mature. The tooltip shows the counts and total cards/notes.
- Hide a column automatically when it's empty for every deck (configurable).
- The options-group name and the gear icon appear only on row hover.
- The column set is configurable in `config.json`; the above is the default.

**Today strip** under the table, two lines:
- Line 1: `16 cards · 2.0 min · 7.3 s/card · ~0 min left · streak 1`
- Line 2, dimmed: `all time 19.7 min · this week 2.0 min · retention X% · N/day avg (study days)`

**Heatmap**: full year, restyled with an amber ramp, fitted to the container width (no overflow), tooltip per day (date, cards, time). One compact stats line underneath: daily average, % days studied, longest streak, current streak. Year navigation is optional.

### 2. Deck overview (after clicking a deck)
The same visual language: the deck's counts, time left today, maturity bar and a small today line. Restyle the Study Now button.

### 3. Reviewer
- A thin (2px) amber progress bar at the top, showing progress through today's queue.
- Small live session stats in a corner: cards done · time · s/card · ETA. Make them toggleable.
- A minimal bottom bar: restyled answer buttons with less clutter (option to hide Edit/More).

### 4. Stats page
- Theme Anki's built-in graphs in monochrome plus amber.
- **Summary header**: retention, streak, total study time, cards/day.
- **Study-time section** (replaces Study Time Stats): time per day/week/month and the s/card trend.
- **Hide noisy graphs**: configurable list of built-in graphs to hide.

## Repo layout and delivery
- Python package: `__init__.py`, modules per screen, `web/` (CSS/JS), `config.json` plus `config.md` (shown in Anki's add-on config dialog), `manifest.json`.
- `README.md`: what it does, screenshots placeholder, install, config reference. Plain and with no emojis.
- **Install method: `.ankiaddon` from GitHub Releases.** A local `build` script zips the package into `anki-dashboard.ankiaddon`; a local release step tags `v*`, creates the GitHub Release and uploads the file with `gh`. No GitHub Actions (checks run locally with `local-ci`).
- Keep a short `docs/design.md` listing the spec decisions above.
- Private repo, MIT license unless I say otherwise.

## How to work
1. Start by confirming the unknown add-on (877182321) and my Anki version if you can. Otherwise proceed with the assumptions above.
2. Optionally first produce a static HTML mockup of the deck list plus reviewer in the amber theme so I can approve spacing and labels before you write Python.
3. Then implement screen by screen: deck list, overview, reviewer, stats. Test that nothing overflows horizontally at narrow and wide window widths.
4. Ask me before adding features beyond this spec. Suggestions are welcome.

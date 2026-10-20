# Design

The rules every screen follows. The full brief is in [spec.md](spec.md); later changes to it are logged in [DECISIONS.md](DECISIONS.md). The approved reference is [mockup.html](mockup.html).

## Rules
- No emojis anywhere in the project. `scripts/check_no_emoji.py` enforces it in local CI.
- No horizontal scrolling on any screen. Layouts fit the window and keep `overflow-x: hidden` as a safety net.
- Minimal but dense: short labels, no redundant columns, detail in hover tooltips.
- Zeros show as a dim dash.

## Color
Monochrome: near-black background, four gray text levels, and white as the only accent, used for data and highlights (key numbers, bars, heatmap ramp, progress). Anki's light theme mirrors it: near-white background and near-black accent. Every color is a CSS variable named `--ad-<key>`, set from the `colors` keys in `config.json` (dark) and `light_colors` (light). Both sets are on every page, the dark one under the `night-mode` class Anki puts on the html element and toggles when the theme changes, so open pages follow a switch; the Qt menu bar and stats frame are restyled on `theme_did_change`.

| Key | Dark | Light | Use |
|---|---|---|---|
| `bg` | `#0d0d0e` | `#fafafa` | page background |
| `surface` | `#151516` | `#f0f0f1` | row hover |
| `raised` | `#1c1c1e` | `#e8e8ea` | buttons, tooltips |
| `line` | `#29292b` | `#dcdcde` | rules and borders |
| `fg1` | `#ececec` | `#151516` | key text |
| `fg2` | `#a3a3a6` | `#505054` | secondary text |
| `fg3` | `#6e6e72` | `#77777c` | labels |
| `fg4` | `#46464a` | `#b0b0b4` | dashes, new cards in the maturity bar |
| `accent`, `accent2`, `accent3`, `accent4` | `#f5f5f5`, `#b0b0b3`, `#727275`, `#3b3b3e` | `#111112`, `#55555a`, `#8e8e93`, `#c6c6c9` | data ramp, strongest first |
| `empty` | `#1e1e20` | `#e8e8ea` | empty heatmap cell, bar track |

## Type and spacing
One font stack (`"Segoe UI", system-ui, ...`) with tabular figures. Spacing scale of 4, 8, 12, 16, 24 and 32 px.

## Screens
- **Window chrome:** the top toolbar, the menu bar and the deck list and overview bottom bars take the page background, so the window reads as one surface. Toolbar links and bottom buttons are `fg2`, `fg1` on hover; buttons have a `line` border. In review the toolbar copies the card page's background, as in Anki.
- **Deck list:** columns Due, New, Learn, Done, Tmrw, Maturity; empty columns hide automatically; options group and gear appear on row hover, over the end of the deck name. Below 640px the columns narrow and the maturity percent hides. A two-line today strip and a full-year heatmap (weeks start Monday) with one stats line.
- **Overview:** one centered 480px column under the deck name and description, with nothing filled or boxed: due, new and learn as 24px white numbers with small lowercase `fg3` labels (deck list order and tooltips, subdecks included); a plain-text Study button in `fg1`, underlined on hover; one `fg3` line with time left, percent mature and reviews due tomorrow, whose tooltips carry today's cards and the maturity breakdown. A finished deck shows Anki's congratulations page, recolored to `bg` and `fg1`.
- **Reviewer:** the card keeps the note's styling; only Anki's page color becomes `bg`, so cards without their own background match the bars (the default note type sets white, which it keeps in light mode). A 2px `accent` bar on an `empty` track along the top shows today's queue (cards done today in the deck against those plus the ones left). Session stats in the top right corner, inside the page's top margin: cards, time, s/card, time left, in `fg3` with the count in `fg2`. The answer bar is `bg` with a `line` rule; answer buttons are `surface` with a `line` border, the interval inside under the label in `fg3`; Good looks like the others (Space still answers Good). Show Answer is wider, with the remaining counts inside in `fg3`. Edit and More are hidden by default and shown as quiet text buttons when enabled.
- **Stats page:** the page and graph cards take `bg` and `surface` with `line` borders, and titles are 15px `fg1`. Graphs are gray: palettes with a meaning map color by color to the ramp (answer buttons Again to Easy from `accent4` to `accent`; card counts in the maturity bar's grays; review kinds mature `accent`, young `accent2`, relearning `accent3`, learning `fg3`, filtered `accent4`), and gradients that only repeat the x axis are desaturated. Above the grid, four large white numbers (retention, streak, study time, cards per study day) with uppercase labels, as in the overview. The Study time card leads the grid: `accent3` bars for time and an `accent` line for seconds per card, Day / Week / Month tabs, and a totals line. Native radios and checkboxes follow the theme. Graphs listed in `stats.hidden_graphs` are hidden (Today and Calendar by default). The window's Qt frame (deck chooser, Save PDF, Close) takes `bg` with `line`-bordered text-only buttons. Save PDF prints the same page with 16px around every card, above one that starts a page too; the range bar's controls give way to a centered header, the deck's name in 18px `fg1` over the range and date in `fg3`.

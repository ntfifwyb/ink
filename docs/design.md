# Design

The rules every screen follows. The full brief is in [spec.md](spec.md); later changes to it are logged in [DECISIONS.md](DECISIONS.md). The approved reference is [mockup.html](mockup.html).

## Rules
- No emojis anywhere in the project. `scripts/check_no_emoji.py` enforces it in local CI.
- No horizontal scrolling on any screen. Layouts fit the window and keep `overflow-x: hidden` as a safety net.
- Minimal but dense: short labels, no redundant columns, detail in hover tooltips.
- Zeros show as a dim dash.

## Color
Monochrome: near-black background, four gray text levels, and white as the only accent, used for data and highlights (key numbers, bars, heatmap ramp, progress). Every color is a CSS variable named `--ad-<key>`, set from the `colors` keys in `config.json`.

| Key | Value | Use |
|---|---|---|
| `bg` | `#0d0d0e` | page background |
| `surface` | `#151516` | row hover |
| `raised` | `#1c1c1e` | buttons, tooltips |
| `line` | `#29292b` | rules and borders |
| `fg1` | `#ececec` | key text |
| `fg2` | `#a3a3a6` | secondary text |
| `fg3` | `#6e6e72` | labels |
| `fg4` | `#46464a` | dashes, new cards in the maturity bar |
| `accent`, `accent2`, `accent3`, `accent4` | `#f5f5f5`, `#b0b0b3`, `#727275`, `#3b3b3e` | data ramp, brightest first |
| `empty` | `#1e1e20` | empty heatmap cell, bar track |

## Type and spacing
One font stack (`"Segoe UI", system-ui, ...`) with tabular figures. Spacing scale of 4, 8, 12, 16, 24 and 32 px.

## Screens
- **Window chrome:** the top toolbar, the menu bar and the deck list and overview bottom bars take the page background, so the window reads as one surface. Toolbar links and bottom buttons are `fg2`, `fg1` on hover; buttons have a `line` border. The reviewer's bars keep Anki's look until the reviewer is themed.
- **Deck list:** columns Due, New, Learn, Done, Tmrw, Maturity; empty columns hide automatically; options group and gear appear on row hover, over the end of the deck name. Below 640px the columns narrow and the maturity percent hides. A two-line today strip and a full-year heatmap (weeks start Monday) with one stats line.
- **Overview:** one centered 480px column under the deck name and description: Due, New and Learn as large white numbers with small uppercase labels (deck list order and tooltips, subdecks included); Study Now as a solid white button (`accent` on `bg`, `accent2` on hover) with time left under it; the full-width maturity bar with a new / young / mature legend; a today line under a rule. A finished deck shows Anki's congratulations page, recolored to `bg` and `fg1`.
- **Reviewer:** 2px progress bar for today's queue, toggleable session stats (cards, time, s/card, time left), minimal answer bar with Edit/More optional.
- **Stats page:** built-in graphs themed monochrome, summary header, study-time section, configurable hidden graphs.

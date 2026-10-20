# Ink

An Anki add-on that replaces four stats add-ons (Review Heatmap, More Decks Stats and Time Left, Study Time Stats, and Enhance main window) with one minimal, information-dense design: monochrome with white as the only accent, across the deck list, deck overview, reviewer and stats page.

Status: all four screens are done: deck list with heatmap, deck overview, reviewer and stats page. The build spec is in [docs/spec.md](docs/spec.md), design rules in [docs/design.md](docs/design.md), and the approved mockup in [docs/mockup.html](docs/mockup.html).

Screenshots: to come.

## What it shows

**Deck list.** One row per deck with short columns. Hover any number for the detail behind it.

| Column | Shows | Tooltip |
|---|---|---|
| Due | reviews due today, after daily limits | all due, ignoring limits |
| New | new cards you will see today | unseen cards in the deck |
| Learn | learning cards due today | due now, later today, other day |
| Done | cards reviewed today | answers and time |
| Tmrw | reviews that become due tomorrow | |
| Maturity | new / young / mature bar and % mature | counts, total cards and notes |

Columns that are empty for every deck hide themselves. Hover a row to see its options group and gear.

Under the decks, two lines sum up today: cards, time, seconds per card, time left and streak; then all-time and this week's study time, 30-day retention and the average per study day.

**Heatmap.** A calendar year of reviews, weeks starting on Monday, shaded from dim to white by your own quartiles. Hover a day for its date, cards and time; the arrows switch years. Underneath: average cards per study day, share of days studied, longest and current streak.

**Deck overview.** The deck's due, new and learn counts (subdecks included, same tooltips as the deck list), a plain Study button, and one line: time left today, percent mature and reviews due tomorrow. Hover the line for the cards done today and the maturity breakdown.

**Reviewer.** A 2px bar along the top for today's queue in the deck, and a session line in the corner: cards, time, seconds per card and time left. The answer bar is flat with the intervals inside the buttons; Edit and More are hidden by default. Your cards keep their own styling.

**Stats page.** Anki's graphs in grays on the same background, with four numbers on top (30-day retention, current streak, study time, cards per study day) and a Study time card: time per day, week or month as bars with seconds per card as a line, and today, this week, this month and the average per study day underneath. Both follow the page's deck / collection / search and its 12 months / all history choice. Today and Calendar are hidden by default, since the summary and the deck-list heatmap cover them.

The top toolbar, menu bar and bottom bar take the same background, and so does Anki's "finished this deck" page.

## Install

Download `ink.ankiaddon` from the [latest release](https://github.com/ntfifwyb/ink/releases) and open it with Anki (or Tools > Add-ons > Install from file). Anki turns off the four add-ons it replaces on install; you can turn them back on in the add-ons list.

Updating from Anki Dashboard (0.7.0 or earlier): Ink is the same add-on under a new name, and Anki installs it as a new add-on. Delete Anki Dashboard in Tools > Add-ons first, or both run at once. Settings don't carry over: copy them from its Config before deleting it if you changed any.

## Configuration

Tools > Add-ons > Ink > Config.

| Key | Default | Meaning |
|---|---|---|
| `colors` | monochrome set | every color in Anki's dark theme, as CSS colors; see the config dialog for each name |
| `light_colors` | monochrome set | the same colors for Anki's light theme |
| `deck_list.columns` | `["due", "new", "learn", "done", "tmrw", "maturity"]` | columns and their order |
| `deck_list.hide_empty_columns` | `true` | hide a column when every deck shows 0 |
| `deck_list.today_strip` | `true` | show the two-line summary under the decks |
| `deck_list.heatmap` | `true` | show the review heatmap and its stats line |
| `reviewer.progress_bar` | `true` | show the 2px bar for today's queue |
| `reviewer.session_stats` | `true` | show the session line in the top right corner |
| `reviewer.edit_more` | `false` | show Anki's Edit and More buttons (E and M work either way) |
| `stats.summary` | `true` | show the four numbers above the graphs |
| `stats.study_time` | `true` | show the Study time card |
| `stats.hidden_graphs` | `["today", "calendar"]` | built-in graphs to hide: `today`, `future_due`, `calendar`, `reviews`, `card_counts`, `intervals`, `ease`, `difficulty`, `stability`, `retrievability`, `retention`, `hours`, `buttons`, `added` |

## Development

The add-on's files are in `src/ink`.

- `./.local-ci` runs the checks: no emojis, ruff format and lint, unit tests, and the build. `local-ci` runs the same file and posts the result to the PR.
- `python3 scripts/build.py` writes `dist/ink.ankiaddon`.
- `scripts/release.sh` publishes the version in `manifest.json` (`human_version`) as a GitHub Release, run from an up-to-date `main`.

## License

MIT

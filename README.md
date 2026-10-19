# anki-dashboard

An Anki add-on that replaces four stats add-ons (Review Heatmap, More Decks Stats and Time Left, Study Time Stats, and Enhance main window) with one minimal, information-dense design: monochrome with white as the only accent, across the deck list, deck overview, reviewer and stats page.

Status: the deck list and heatmap are done; the deck overview, reviewer and stats page come next. The build spec is in [docs/spec.md](docs/spec.md), design rules in [docs/design.md](docs/design.md), and the approved mockup in [docs/mockup.html](docs/mockup.html).

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

## Install

Download `anki-dashboard.ankiaddon` from the [latest release](https://github.com/montinaops/anki-dashboard/releases) and open it with Anki (or Tools > Add-ons > Install from file). Then turn off the four add-ons it replaces.

## Configuration

Tools > Add-ons > Anki Dashboard > Config.

| Key | Default | Meaning |
|---|---|---|
| `colors` | monochrome set | every color, as CSS colors; see the config dialog for each name |
| `deck_list.columns` | `["due", "new", "learn", "done", "tmrw", "maturity"]` | columns and their order |
| `deck_list.hide_empty_columns` | `true` | hide a column when every deck shows 0 |
| `deck_list.today_strip` | `true` | show the two-line summary under the decks |
| `deck_list.heatmap` | `true` | show the review heatmap and its stats line |

## Development

The add-on's files are in `src/anki_dashboard`.

- `./.local-ci` runs the checks: no emojis, ruff format and lint, unit tests, and the build. `local-ci` runs the same file and posts the result to the PR.
- `python3 scripts/build.py` writes `dist/anki-dashboard.ankiaddon`.
- `scripts/release.sh` publishes the version in `manifest.json` (`human_version`) as a GitHub Release, run from an up-to-date `main`.

## License

MIT

# anki-dashboard

An Anki add-on that replaces four stats add-ons (Review Heatmap, More Decks Stats and Time Left, Study Time Stats, and Enhance main window) with one minimal, information-dense design: monochrome with white as the only accent, across the deck list, deck overview, reviewer and stats page.

Status: in development; no release yet. The build spec is in [docs/spec.md](docs/spec.md), design rules in [docs/design.md](docs/design.md), and the approved mockup in [docs/mockup.html](docs/mockup.html).

## Install

Download `anki-dashboard.ankiaddon` from the [latest release](https://github.com/montinaops/anki-dashboard/releases) and open it with Anki (or Tools > Add-ons > Install from file). Then turn off the four add-ons it replaces.

## Development

The add-on's files are in `src/anki_dashboard`.

- `./.local-ci` runs the checks: no emojis, ruff format and lint, unit tests, and the build. `local-ci` runs the same file and posts the result to the PR.
- `python3 scripts/build.py` writes `dist/anki-dashboard.ankiaddon`.
- `scripts/release.sh` publishes the version in `manifest.json` (`human_version`) as a GitHub Release, run from an up-to-date `main`.

## License

MIT

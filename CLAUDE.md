# CLAUDE.md

Ink is an Anki add-on (Anki 26.5+, Qt6) that replaces four stats add-ons with one minimal, monochrome design across the deck list, overview, reviewer and stats page. `README.md` describes what it shows; `docs/spec.md` is the build spec, `docs/design.md` the design rules, `docs/mockup.html` the approved mockup, and `docs/DECISIONS.md` the choices behind them. Read the spec and design rules before changing anything visible.

## Commands

```sh
local-ci push -u origin <branch>; local-ci wait   # PR checks: no emoji, ruff, unit tests on Anki 26.5 and 26.9.3, js tests, build
python3 scripts/build.py     # dist/ink.ankiaddon
scripts/release.sh           # from an up-to-date main after the release PR: tags v<manifest version>, publishes the build
```

## Seeing it live

Unit tests don't show the page. To check behavior in real Anki on Windows without disturbing the owner's profile: run `Anki.exe -b <throwaway dir>` with `QT_QPA_PLATFORM=offscreen`, seed a `_global` prefs row with `firstRun` false so the first-run dialog doesn't block, and install a small harness add-on that does the check, logs it, and quits. Anki shows any stderr write as an add-on error, so the harness logs stderr too. Never open Anki windows on the owner's desktop without asking.

## Rules

- Both themes (dark and light) and both tested Anki versions, for every visible change; update `docs/screenshots/` when the look changes.
- No emoji anywhere (`scripts/check_no_emoji.py` enforces it).
- Every user-visible fix or feature is a release: bump `human_version` in `src/ink/manifest.json`, add the CHANGELOG section, merge, then `scripts/release.sh`. Commit subjects look like `Keep the menu bar visible in full screen; release 1.0.4 (#27)`.

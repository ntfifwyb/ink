# Changelog

All notable changes to this add-on are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.7.0] - 2026-10-20

### Added
- Light theme. Every screen now follows Anki's theme setting (Tools > Preferences > Appearance > Theme, including Follow system): in light mode the deck list, overview, reviewer bars, stats window, menu bar and congratulations page use a near-white monochrome palette with near-black as the accent, the dark look mirrored. Switching themes restyles open screens without a restart.
- `light_colors` config section: the light theme's colors, with the same names as `colors`.

### Changed
- The stats window is no longer dark in light mode; it follows the theme like every other screen.

## [0.6.6] - 2026-10-20

### Fixed
- Stats window on Linux: the Close button no longer shows a faint stray mark before its label. It was Qt's close icon, black on the dark frame; the window's buttons are now text only, as on Windows and macOS.

## [0.6.5] - 2026-10-20

### Fixed
- Saving the add-on's config during a review no longer turns the top toolbar into the dark deck-list bar. It keeps the card's background, as it does in every review.

## [0.6.4] - 2026-10-20

### Fixed
- Light mode: the stats page's unchecked radio buttons are dark like the rest of the page instead of white circles.
- Light mode: the congratulations page's text is light on the dark page instead of black.
- Light mode: in the reviewer, the progress bar and the session card count are dark gray, so they show on a light card.

## [0.6.3] - 2026-10-20

### Fixed
- Save PDF on the stats page: a graph that starts a new page no longer sits against the page's top edge. Every card has the same 16px of space above it and at the sides.

## [0.6.2] - 2026-10-20

### Changed
- Save PDF on the stats page prints a plain header (the deck's name, or the whole collection or the search, then the range and date) in place of the deck/collection and range controls.

### Fixed
- Save PDF on the stats page: the margins on the left and right are now even.

## [0.6.1] - 2026-10-20

### Fixed
- Save PDF on the stats page: the scope and range bar no longer covers the summary numbers, and the graph cards are spaced apart again instead of touching.

## [0.6.0] - 2026-10-20

### Changed
- The deck overview is pared down: smaller counts, a plain-text Study button in place of the white Study Now button, and one line with time left, percent mature and reviews due tomorrow. The maturity bar and the today line are gone; cards done today and the maturity breakdown are in the line's tooltips.
- Installing the add-on turns off the four add-ons it replaces (Review Heatmap, More Decks Stats and Time Left, Study Time Stats, and 877182321), which Anki does for add-ons a manifest declares as conflicts.

## [0.5.0] - 2026-10-19

### Added
- Stats page summary: 30-day retention, current streak (longest in the tooltip), study time and cards per study day, in large numbers above the graphs.
- Study time card (replaces Study Time Stats): time per day (30 days), week (26 weeks) or month (12 months, or every month with all history) as bars, with seconds per card as a line. Hover a bar for its time, cards and pace. Underneath: today, this week, this month and the average per study day.
- Both follow the page's deck, collection or search, and its last 12 months or all history choice.
- `stats.hidden_graphs` hides built-in graphs; Today and Calendar are hidden by default. `stats.summary` and `stats.study_time` turn the new sections off.

### Changed
- The stats window uses the add-on's background and grays. Graphs whose colors mean something (answer buttons, card types, review kinds) map each color to its own gray; the rest are desaturated.

## [0.4.0] - 2026-10-19

### Added
- Reviewer: a 2px bar along the top showing how much of today's queue for the deck is done (hover it for the counts), and a session line in the top right corner with cards, time, seconds per card and time left. Both can be turned off in the config (`reviewer.progress_bar`, `reviewer.session_stats`).
- A quieter answer bar: flat buttons with the interval inside, Good outlined in white, and Show Answer with the remaining counts inside. Edit and More are hidden unless `reviewer.edit_more` is on; E and M still work.

### Changed
- In night mode the reviewer page and its bottom bar use the add-on's background. Card content keeps your note styling, and a note that sets its own background keeps it.

## [0.3.0] - 2026-10-19

### Added
- Deck overview: Due, New and Learn counts with the deck list's tooltips (and buried cards), a restyled Study Now button with the time left today, the maturity bar with new / young / mature counts, and a today line with cards, time, seconds per card and reviews due tomorrow.
- The top toolbar, menu bar and the deck list and overview bottom bars now use the add-on's background, so the black no longer stops at Anki's gray bars. Anki's "finished this deck" page matches too.

## [0.2.0] - 2026-10-19

### Added
- Review heatmap under the today strip: one calendar year with weeks starting on Monday, scaled to the window width so it never scrolls sideways. Hover a day for its date, cards and study time. The arrows switch to earlier years with reviews.
- One stats line under the heatmap: average cards per study day, share of days studied, longest and current streak.
- The heatmap shades scale to your own history (quartiles of your study days), and `deck_list.heatmap` turns it off.

## [0.1.0] - 2026-10-19

### Added
- Deck list: a compact table with Due, New, Learn, Done, Tmrw and Maturity columns. Hover a number for its breakdown (learning now, later today and other day; all due ignoring limits; answers and time; new, young and mature counts with notes). Columns that are empty for every deck hide themselves.
- The options group and gear appear when you hover a deck row. Collapsing, drag and drop, options and shift-click selection work as in Anki.
- Today strip under the decks: cards, time, seconds per card, time left and streak; then all-time and this week's study time, 30-day retention (with the FSRS desired retention in the tooltip when FSRS is on) and the average per study day.
- Monochrome theme with white as the only accent. Every color and the column set can be changed in the add-on config.

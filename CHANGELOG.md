# Changelog

All notable changes to this add-on are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

**colors**: every color the add-on draws with. Values are CSS colors (`#rrggbb`, `rgb(...)` or a name). The defaults are monochrome: near-black `bg`, `surface` for row hover, `raised` for buttons and tooltips, `line` for rules, four text levels `fg1` (brightest) to `fg4` (dim dashes), and the data ramp `accent` (brightest) to `accent4`. `empty` is the track behind bars.

**deck_list**
- `columns`: which columns the deck list shows, in order. Any of `due`, `new`, `learn`, `done`, `tmrw`, `maturity`.
- `hide_empty_columns`: hide a column when every deck shows 0 in it (`maturity` is always shown).
- `today_strip`: show the two-line summary of today's study under the decks.
- `heatmap`: show the review heatmap for a calendar year, with the average, share of days studied and streaks underneath. The arrows switch years.

Hover any number in the deck list for its breakdown.

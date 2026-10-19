"""anki-dashboard: one minimal, monochrome stats layer for the deck list, overview,
reviewer and stats page. Replaces Review Heatmap, More Decks Stats and Time Left,
Study Time Stats and Enhance main window."""

try:
    from aqt import mw
except ImportError:  # imported outside Anki, e.g. by the tests
    mw = None

if mw is not None:
    from . import addon

    addon.init()

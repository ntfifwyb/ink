"""Entry point inside Anki: registers each screen's hooks."""

from __future__ import annotations

from aqt import gui_hooks, mw
from aqt.deckbrowser import DeckBrowser, DeckBrowserContent
from aqt.webview import WebContent

from . import config, deck_list


def _config() -> config.Config:
    return config.load(mw.addonManager.getConfig(__name__))


def _web(path: str) -> str:
    return f"/_addons/{mw.addonManager.addonFromModule(__name__)}/web/{path}"


def on_webview_will_set_content(content: WebContent, context: object | None) -> None:
    if isinstance(context, DeckBrowser):
        content.css += [_web("dashboard.css"), _web("deck_list.css")]
        content.js.append(_web("dashboard.js"))
        content.head += f"<style>{config.css_variables(_config().colors)}</style>"


def on_deck_browser_will_render_content(browser: DeckBrowser, content: DeckBrowserContent) -> None:
    content.tree, content.stats = deck_list.build(mw.col, browser._render_data.tree, _config())


def on_config_updated(_raw: dict) -> None:
    if mw.state == "deckBrowser":
        mw.deckBrowser.refresh()


def init() -> None:
    mw.addonManager.setWebExports(__name__, r"web/.*\.(css|js)")
    mw.addonManager.setConfigUpdatedAction(__name__, on_config_updated)
    gui_hooks.webview_will_set_content.append(on_webview_will_set_content)
    gui_hooks.deck_browser_will_render_content.append(on_deck_browser_will_render_content)

"""Entry point inside Anki: registers each screen's hooks."""

from __future__ import annotations

import json

from aqt import gui_hooks, mw
from aqt.deckbrowser import DeckBrowser, DeckBrowserBottomBar, DeckBrowserContent
from aqt.overview import Overview, OverviewBottomBar, OverviewContent
from aqt.toolbar import TopToolbar
from aqt.webview import AnkiWebView, WebContent

from . import config, deck_list, overview

_heat_year: int | None = None  # heatmap year picked with the arrows; None is this year


def _config() -> config.Config:
    return config.load(mw.addonManager.getConfig(__name__))


def _web(path: str) -> str:
    return f"/_addons/{mw.addonManager.addonFromModule(__name__)}/web/{path}"


def on_webview_will_set_content(content: WebContent, context: object | None) -> None:
    if isinstance(context, (DeckBrowser, Overview)):
        sheet = "deck_list.css" if isinstance(context, DeckBrowser) else "overview.css"
        content.css += [_web("dashboard.css"), _web(sheet)]
        content.js.append(_web("dashboard.js"))
        content.head += f"<style>{config.css_variables(_config().colors)}</style>"
    elif isinstance(context, (TopToolbar, DeckBrowserBottomBar, OverviewBottomBar)):
        content.css.append(_web("chrome.css"))
        content.head += f"<style>{config.css_variables(_config().colors)}</style>"


def style_menu_bar() -> None:
    """The menu bar is a Qt widget, so it takes a Qt stylesheet instead of CSS."""
    mw.form.menubar.setStyleSheet(config.menu_bar_qss(_config().colors))


def on_deck_browser_will_render_content(browser: DeckBrowser, content: DeckBrowserContent) -> None:
    content.tree, content.stats = deck_list.build(
        mw.col, browser._render_data.tree, _config(), _heat_year
    )


def on_style_injected(web: AnkiWebView) -> None:
    """A finished deck shows Anki's congratulations page in place of the overview. It is a
    SvelteKit page that skips webview_will_set_content, so its styles are added here."""
    if web is mw.web and web.page().url().path().endswith("/congrats"):
        tags = (
            f'<link rel="stylesheet" href="{_web("congrats.css")}">'
            f"<style>{config.css_variables(_config().colors)}</style>"
        )
        web.eval(f"document.head.insertAdjacentHTML('beforeend', {json.dumps(tags)})")


def on_overview_will_render_content(_overview: Overview, content: OverviewContent) -> None:
    content.table = overview.build(mw.col)


def on_js_message(handled: tuple[bool, object], message: str, context: object) -> tuple:
    global _heat_year
    if isinstance(context, DeckBrowser) and message.startswith("ad-year:"):
        year = message.split(":", 1)[1]
        _heat_year = int(year) if year.isdigit() else None
        context.refresh()
        return True, None
    return handled


def on_config_updated(_raw: dict) -> None:
    style_menu_bar()
    mw.toolbar.draw()
    if mw.state == "deckBrowser":
        mw.deckBrowser.refresh()
    elif mw.state == "overview":
        mw.overview.refresh()


def init() -> None:
    mw.addonManager.setWebExports(__name__, r"web/.*\.(css|js)")
    mw.addonManager.setConfigUpdatedAction(__name__, on_config_updated)
    gui_hooks.webview_will_set_content.append(on_webview_will_set_content)
    gui_hooks.deck_browser_will_render_content.append(on_deck_browser_will_render_content)
    gui_hooks.overview_will_render_content.append(on_overview_will_render_content)
    gui_hooks.webview_did_receive_js_message.append(on_js_message)
    gui_hooks.webview_did_inject_style_into_page.append(on_style_injected)
    gui_hooks.main_window_did_init.append(style_menu_bar)

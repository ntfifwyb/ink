"""Entry point inside Anki: registers each screen's hooks."""

from __future__ import annotations

import json
import time

from aqt import gui_hooks, mw
from aqt.deckbrowser import DeckBrowser, DeckBrowserBottomBar, DeckBrowserContent
from aqt.overview import Overview, OverviewBottomBar, OverviewContent
from aqt.reviewer import Reviewer, ReviewerBottomBar
from aqt.toolbar import TopToolbar
from aqt.webview import AnkiWebView, WebContent

from . import config, deck_list, overview, reviewer

_heat_year: int | None = None  # heatmap year picked with the arrows; None is this year
_session_since = 0  # epoch ms when the reviewer last opened


def _config() -> config.Config:
    return config.load(mw.addonManager.getConfig(__name__))


def _web(path: str) -> str:
    return f"/_addons/{mw.addonManager.addonFromModule(__name__)}/web/{path}"


def _edit_more_js(show: bool) -> str:
    return f"document.documentElement.classList.toggle('ad-edit-more', {json.dumps(show)});"


def on_webview_will_set_content(content: WebContent, context: object | None) -> None:
    cfg = _config()
    if isinstance(context, (DeckBrowser, Overview)):
        sheet = "deck_list.css" if isinstance(context, DeckBrowser) else "overview.css"
        content.css += [_web("shared.css"), _web("dashboard.css"), _web(sheet)]
        content.js.append(_web("dashboard.js"))
    elif isinstance(context, Reviewer):
        content.css += [_web("shared.css"), _web("reviewer.css")]
        content.js += [_web("dashboard.js"), _web("reviewer.js")]
    elif isinstance(context, (TopToolbar, DeckBrowserBottomBar, OverviewBottomBar)):
        content.css.append(_web("chrome.css"))
    elif isinstance(context, ReviewerBottomBar):
        content.css += [_web("chrome.css"), _web("reviewer_bottom.css")]
        content.head += f"<script>{_edit_more_js(cfg.reviewer.edit_more)}</script>"
    else:
        return
    content.head += f"<style>{config.css_variables(cfg.colors)}</style>"


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


def on_state_will_change(new_state: str, old_state: str) -> None:
    global _session_since
    if new_state == "review" and old_state != "review":
        _session_since = int(time.time() * 1000)


def update_reviewer(*_args: object) -> None:
    """Redraw the progress bar and session stats; runs after each question is shown."""
    cfg = _config().reviewer
    html = reviewer.overlay(
        reviewer.build(mw.col, _session_since), cfg.progress_bar, cfg.session_stats
    )
    mw.reviewer.web.eval(f"adReview({json.dumps(html)});")


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
    elif mw.state == "review" and mw.reviewer.card:
        update_reviewer()
        mw.reviewer.bottom.web.eval(_edit_more_js(_config().reviewer.edit_more))


def init() -> None:
    mw.addonManager.setWebExports(__name__, r"web/.*\.(css|js)")
    mw.addonManager.setConfigUpdatedAction(__name__, on_config_updated)
    gui_hooks.webview_will_set_content.append(on_webview_will_set_content)
    gui_hooks.deck_browser_will_render_content.append(on_deck_browser_will_render_content)
    gui_hooks.overview_will_render_content.append(on_overview_will_render_content)
    gui_hooks.webview_did_receive_js_message.append(on_js_message)
    gui_hooks.webview_did_inject_style_into_page.append(on_style_injected)
    gui_hooks.state_will_change.append(on_state_will_change)
    gui_hooks.reviewer_did_show_question.append(update_reviewer)
    gui_hooks.main_window_did_init.append(style_menu_bar)

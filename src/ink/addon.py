"""Entry point inside Anki: registers each screen's hooks."""

from __future__ import annotations

import json
import time
from pathlib import Path

from aqt import gui_hooks, mw
from aqt.deckbrowser import DeckBrowser, DeckBrowserBottomBar, DeckBrowserContent
from aqt.overview import Overview, OverviewBottomBar, OverviewContent
from aqt.reviewer import Reviewer, ReviewerBottomBar
from aqt.stats import NewDeckStats
from aqt.theme import theme_manager
from aqt.toolbar import TopToolbar
from aqt.utils import tooltip, tr
from aqt.webview import AnkiWebView, WebContent

from . import config, deck_list, overview, reviewer, stats_page
from .guard import Guard

_heat_year: int | None = None  # heatmap year picked with the arrows; None is this year
_session_since = 0  # epoch ms when the reviewer last opened
_HERE = Path(__file__).resolve().parent
_EMPTY_STATS = {"scope": "", "summary": "", "study": ""}


def _notify_error() -> None:
    tooltip(
        "Ink hit an error and left this screen as Anki draws it. Details are in "
        "user_files/errors.log (Tools > Add-ons > Ink > View Files).",
        period=10000,
    )


guarded = Guard(
    _HERE / "user_files" / "errors.log",
    _notify_error,
    json.loads((_HERE / "manifest.json").read_text(encoding="utf-8"))["human_version"],
)


def _config() -> config.Config:
    return config.load(mw.addonManager.getConfig(__name__))


def _palette() -> dict[str, str]:
    return config.palette(_config(), theme_manager.night_mode)


def _web(path: str) -> str:
    return f"/_addons/{mw.addonManager.addonFromModule(__name__)}/web/{path}"


def _edit_more_js(show: bool) -> str:
    return f"document.documentElement.classList.toggle('ad-edit-more', {json.dumps(show)});"


@guarded()
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
    content.head += f"<style>{config.css_variables(cfg)}</style>"


@guarded()
def style_menu_bar() -> None:
    """The menu bar is a Qt widget, so it takes a Qt stylesheet instead of CSS."""
    mw.form.menubar.setStyleSheet(config.menu_bar_qss(_palette()))


@guarded()
def on_deck_browser_will_render_content(browser: DeckBrowser, content: DeckBrowserContent) -> None:
    content.tree, content.stats = deck_list.build(
        mw.col, browser._render_data.tree, _config(), _heat_year
    )


@guarded()
def on_style_injected(web: AnkiWebView) -> None:
    """The congratulations page (shown in place of a finished deck's overview) and the
    stats page are SvelteKit pages that skip webview_will_set_content, so their styles
    and scripts are added here, once Anki has styled them."""
    path = web.page().url().path()
    if web is mw.web and path.endswith("/congrats"):
        sheets, scripts = ["congrats.css"], []
    elif path.endswith("/graphs"):
        sheets, scripts = ["shared.css", "stats.css"], ["dashboard.js", "stats_page.js"]
    else:
        return
    cfg = _config()
    tags = "".join(f'<link rel="stylesheet" href="{_web(s)}">' for s in sheets)
    tags += f"<style>{config.css_variables(cfg)}</style>"
    settings = {
        "titles": stats_page.graph_keys(tr),
        "hidden": cfg.stats.hidden_graphs,
        "summary": cfg.stats.summary,
        "studyTime": cfg.stats.study_time,
    }
    # scripts added as HTML don't run, so they are created as elements, in order
    load = "".join(
        f"s=document.createElement('script');s.src={json.dumps(_web(name))};s.async=false;"
        "document.head.appendChild(s);"
        for name in scripts
    )
    web.eval(
        f"window.adStats={json.dumps(settings)};"
        f"document.head.insertAdjacentHTML('beforeend', {json.dumps(tags)});"
        f"(function(){{var s;{load}}})();"
    )


@guarded()
def on_stats_dialog_will_show(dialog: NewDeckStats) -> None:
    dialog.setStyleSheet(config.stats_dialog_qss(_palette()))


@guarded()
def on_theme_did_change() -> None:
    """Pages switch palettes on their own with Anki's night-mode class; the Qt widgets
    are restyled here."""
    style_menu_bar()
    for widget in mw.app.topLevelWidgets():
        if isinstance(widget, NewDeckStats):
            on_stats_dialog_will_show(widget)


@guarded()
def on_overview_will_render_content(_overview: Overview, content: OverviewContent) -> None:
    content.table = overview.build(mw.col)


@guarded()
def on_state_will_change(new_state: str, old_state: str) -> None:
    global _session_since
    if new_state == "review" and old_state != "review":
        _session_since = int(time.time() * 1000)


def _clear_reviewer(*_args: object) -> None:
    """Without fresh numbers, no bar or session line rather than the last card's."""
    mw.reviewer.web.eval("window.adReview && adReview('');")


@guarded(_clear_reviewer)
def update_reviewer(*_args: object) -> None:
    """Redraw the progress bar and session stats; runs after each question is shown."""
    cfg = _config().reviewer
    html = reviewer.overlay(
        reviewer.build(mw.col, _session_since), cfg.progress_bar, cfg.session_stats
    )
    mw.reviewer.web.eval(f"adReview({json.dumps(html)});")


def _js_message_failed(handled: tuple[bool, object], message: str, _context: object) -> tuple:
    if message.startswith("ad-stats:"):
        return True, _EMPTY_STATS  # the page then shows only Anki's graphs
    if message.startswith("ad-year:"):
        return True, None
    return handled


@guarded(_js_message_failed)
def on_js_message(handled: tuple[bool, object], message: str, context: object) -> tuple:
    global _heat_year
    if isinstance(context, DeckBrowser) and message.startswith("ad-year:"):
        year = message.split(":", 1)[1]
        _heat_year = int(year) if year.isdigit() else None
        context.refresh()
        return True, None
    if isinstance(context, NewDeckStats) and message.startswith("ad-stats:"):
        scope = json.loads(message.split(":", 1)[1])
        return True, stats_page.build(mw.col, str(scope["search"]), bool(scope["all"]))
    return handled


@guarded()
def on_config_updated(_raw: dict) -> None:
    on_theme_did_change()
    mw.toolbar.draw()
    if mw.state == "deckBrowser":
        mw.deckBrowser.refresh()
    elif mw.state == "overview":
        mw.overview.refresh()
    elif mw.state == "review" and mw.reviewer.card:
        # the redrawn toolbar lost the flat look and card background Anki gives it in review
        mw.toolbarWeb.on_body_classes_need_update()
        mw.toolbarWeb.update_background_image()
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
    gui_hooks.stats_dialog_will_show.append(on_stats_dialog_will_show)
    gui_hooks.theme_did_change.append(on_theme_did_change)

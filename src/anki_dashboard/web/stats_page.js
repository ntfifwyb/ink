"use strict";
// Anki's stats page (a SvelteKit app): tags each graph card with its key, found from
// its translated title, hides the configured graphs, and keeps the summary header and
// study-time card in place. Both are rebuilt in Python whenever the page's search or
// range changes, which re-renders the graphs and so wakes the observer below.
// window.adStats = {titles: {title: key}, hidden: [key], summary: bool, studyTime: bool}
(function () {
  const cfg = window.adStats;
  let scope = null; // the search and range the sections were built for
  let waiting = false;
  let sections = { scope: "", summary: "", study: "" };
  let unit = "day";

  function pageScope() {
    const box = document.querySelector(".range-box");
    const search = document.getElementById("statisticsSearchText");
    if (!box || !search) return null;
    // radios in page order: deck, collection, last 12 months, all history
    const radios = box.querySelectorAll("input[type=radio]");
    return JSON.stringify({ search: search.value, all: radios.length === 4 && radios[3].checked });
  }

  function own(id, make) {
    let el = document.getElementById(id);
    if (!el) {
      el = make();
      el.id = id;
    }
    return el;
  }

  function place(grid) {
    const head = own("ad-scope", function () { return document.createElement("div"); });
    if (head.nextElementSibling !== grid && head.nextElementSibling !== document.getElementById("ad-sum")) {
      grid.parentNode.insertBefore(head, grid);
    }
    if (head.innerHTML !== sections.scope) head.innerHTML = sections.scope;
    if (cfg.summary) {
      const sum = own("ad-sum", function () { return document.createElement("div"); });
      if (sum.nextElementSibling !== grid) grid.parentNode.insertBefore(sum, grid);
      if (sum.dataset.html !== sections.summary) {
        sum.innerHTML = sections.summary;
        sum.dataset.html = sections.summary;
      }
    }
    if (cfg.studyTime) {
      const card = own("ad-study", function () {
        const el = document.createElement("div");
        el.dataset.adGraph = "study_time";
        return el;
      });
      if (grid.firstElementChild !== card) grid.insertBefore(card, grid.firstElementChild);
      card.hidden = !sections.study;
      if (card.dataset.html !== sections.study) {
        card.innerHTML = sections.study;
        card.dataset.html = sections.study;
      }
      card.dataset.unit = unit;
    }
  }

  function update() {
    const grid = document.querySelector(".graphs-container");
    if (!grid) return;
    for (const card of grid.children) {
      const h1 = card.querySelector(":scope > div > h1");
      const key = h1 && cfg.titles[h1.textContent.trim()];
      if (!key || card.dataset.adGraph === key) continue;
      card.dataset.adGraph = key;
      if (cfg.hidden.indexOf(key) >= 0) card.dataset.adHidden = "";
    }
    place(grid);
    const now = pageScope();
    if (now === null || now === scope || waiting || !(cfg.summary || cfg.studyTime)) return;
    waiting = true;
    pycmd("ad-stats:" + now, function (result) {
      waiting = false;
      scope = now;
      sections = result;
      update(); // places the new sections, and catches a change made while waiting
    });
  }

  document.addEventListener("click", function (e) {
    const tab = e.target.closest("#ad-study button[data-unit]");
    if (!tab) return;
    unit = tab.dataset.unit;
    document.getElementById("ad-study").dataset.unit = unit;
  });

  let queued = false;
  new MutationObserver(function () {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () {
      queued = false;
      update();
    });
  }).observe(document.body, { childList: true, subtree: true });
  update();
})();

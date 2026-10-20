"use strict";
// stats_page.js on a stand-in for Anki's stats page: the range radios, the search box
// and a graphs grid, with pycmd answering as stats_page.build would.
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");

const SCRIPT = fs.readFileSync(
  path.join(__dirname, "..", "..", "src", "ink", "web", "stats_page.js"),
  "utf8",
);
const SECTIONS = {
  // entities the browser re-serializes differently when innerHTML is read back
  scope: '<b>deck:&quot;a b&quot;</b><span>last 12 months<span class="ad-sep">&middot;</span>Oct 20, 2026</span>',
  summary: '<div class="ad-cnts">summary</div>',
  study: "<h1>Study time</h1>",
};

function page(settings) {
  const dom = new JSDOM(
    `<body><div class="range-box"><input type=radio checked><input type=radio>
    <input type=radio checked><input type=radio></div>
    <input id="statisticsSearchText" value="deck:current">
    <div class="graphs-container"><div><div><h1>Future Due</h1></div></div>
    <div><div><h1>Hours</h1></div></div></div></body>`,
    { runScripts: "outside-only", pretendToBeVisual: true },
  );
  const w = dom.window;
  w.adStats = Object.assign(
    { titles: { "Future Due": "future_due", Hours: "hours" }, hidden: ["hours"] },
    settings,
  );
  const calls = [];
  w.pycmd = (msg, cb) => {
    calls.push(msg);
    setTimeout(() => cb(SECTIONS), 5);
  };
  let mutations = 0;
  new w.MutationObserver((m) => { mutations += m.length; })
    .observe(w.document.body, { childList: true, subtree: true, attributes: true });
  w.eval(SCRIPT);
  return {
    w,
    calls,
    mutations: () => mutations,
    reset: () => { mutations = 0; },
    ids: () => [...w.document.body.children].map((e) => e.id || e.className),
  };
}

const settle = (ms = 300) => new Promise((r) => setTimeout(r, ms));

for (const summary of [true, false]) {
  for (const studyTime of [true, false]) {
    test(`print header placed (summary ${summary}, study time ${studyTime})`, async () => {
      const p = page({ summary, studyTime });
      await settle();
      const order = p.ids().filter((id) => id.startsWith("ad-") || id === "graphs-container");
      assert.deepStrictEqual(
        order,
        summary ? ["ad-scope", "ad-sum", "graphs-container"] : ["ad-scope", "graphs-container"],
      );
      assert.match(p.w.document.getElementById("ad-scope").textContent, /deck:"a b"/);
      assert.strictEqual(!!p.w.document.getElementById("ad-study"), studyTime);
    });
  }
}

test("page settles: nothing is rewritten once the sections are in", async () => {
  const p = page({ summary: true, studyTime: true });
  await settle();
  p.reset();
  await settle(500);
  assert.strictEqual(p.mutations(), 0);
  assert.strictEqual(p.calls.length, 1);
});

test("asks again when the search changes, not otherwise", async () => {
  const p = page({ summary: true, studyTime: true });
  await settle();
  p.w.document.getElementById("statisticsSearchText").value = "tag:x";
  p.w.document.body.appendChild(p.w.document.createElement("span")); // a re-render
  await settle();
  assert.deepStrictEqual(
    p.calls.map((c) => JSON.parse(c.slice("ad-stats:".length)).search),
    ["deck:current", "tag:x"],
  );
});

test("graphs are tagged by title and configured ones hidden", async () => {
  const p = page({ summary: true, studyTime: true });
  await settle();
  const cards = [...p.w.document.querySelector(".graphs-container").children];
  assert.deepStrictEqual(
    cards.map((c) => [c.dataset.adGraph, "adHidden" in c.dataset]),
    [["study_time", false], ["future_due", false], ["hours", true]],
  );
});

"use strict";
// Hover tooltips for any element with data-tip (HTML built and escaped in Python).
// Deck names get one only when they are cut off.
(function () {
  function init() {
    const tip = document.createElement("div");
    tip.id = "ad-tip";
    tip.hidden = true;
    document.body.appendChild(tip);

    document.addEventListener("mouseover", function (e) {
      const deck = e.target.closest(".ad-deck");
      const el = e.target.closest("[data-tip]");
      let html = el ? el.dataset.tip : null;
      if (deck && deck.scrollWidth > deck.clientWidth) {
        html = "<b></b>";
        tip.innerHTML = html;
        tip.firstChild.textContent = deck.textContent;
        return show(deck);
      }
      if (!html) {
        tip.hidden = true;
        return;
      }
      tip.innerHTML = html;
      show(el);
    });
    window.addEventListener("scroll", function () { tip.hidden = true; }, { passive: true });

    function show(target) {
      tip.hidden = false;
      const r = target.getBoundingClientRect();
      const w = tip.offsetWidth, h = tip.offsetHeight;
      const x = Math.min(Math.max(8, r.left + r.width / 2 - w / 2), window.innerWidth - w - 8);
      let y = r.top - h - 8;
      if (y < 8) y = r.bottom + 8;
      tip.style.left = x + "px";
      tip.style.top = y + "px";
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();

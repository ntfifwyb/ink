"use strict";
// The progress bar and session stats over the card (HTML built and escaped in Python).
// Anki only replaces #qa between cards, so the container stays in the page.
function adReview(html) {
  let box = document.getElementById("ad-rev");
  if (!box) {
    box = document.createElement("div");
    box.id = "ad-rev";
    document.body.appendChild(box);
  }
  box.innerHTML = html;
}

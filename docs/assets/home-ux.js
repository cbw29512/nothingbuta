(() => {
  "use strict";

  function init() {
    const input = document.getElementById("oct-tool-search-input");
    const status = document.getElementById("oct-tool-search-status");
    const cards = Array.from(document.querySelectorAll(".tool-card"));
    if (!input || !status || !cards.length) return;

    const update = () => {
      const query = input.value.trim().toLowerCase();
      let visible = 0;
      for (const card of cards) {
        const haystack = card.textContent.toLowerCase();
        const show = !query || haystack.includes(query);
        card.hidden = !show;
        if (show) visible += 1;
      }
      status.textContent = query
        ? `${visible} tool${visible === 1 ? "" : "s"} match “${input.value.trim()}”.`
        : `${cards.length} tools available.`;
    };

    input.addEventListener("input", update);
    update();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();

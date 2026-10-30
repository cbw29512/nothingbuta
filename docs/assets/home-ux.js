(() => {
  "use strict";

  // Data contract: each catalog card has a .badge category and searchable text.
  // State is only the visitor's current query and selected category.
  function init() {
    try {
      const input = document.getElementById("oct-tool-search-input");
      const categorySelect = document.getElementById("oct-tool-category");
      const status = document.getElementById("oct-tool-search-status");
      const cards = Array.from(document.querySelectorAll(".tool-card"));
      if (!input || !categorySelect || !status || !cards.length) return;

      const categoryFor = card =>
        card.querySelector(".badge")?.textContent.trim() || "";
      // Discover categories from the canonical catalog cards, not a separate
      // hard-coded list that can go stale when calculators are added.
      const categories = [...new Set(cards.map(categoryFor).filter(Boolean))]
        .sort((a, b) => a.localeCompare(b));
      for (const category of categories) {
        const option = document.createElement("option");
        option.value = category;
        option.textContent = category;
        categorySelect.appendChild(option);
      }

      const state = { query: "", category: "" };
      function update() {
        try {
          state.query = input.value.trim().toLowerCase();
          state.category = categorySelect.value;
          let visible = 0;
          for (const card of cards) {
            const textMatch = !state.query ||
              card.textContent.toLowerCase().includes(state.query);
            const categoryMatch = !state.category ||
              categoryFor(card) === state.category;
            const show = textMatch && categoryMatch;
            card.hidden = !show;
            if (show) visible += 1;
          }
          if (state.query && state.category) {
            status.textContent = `${visible} tools in ${state.category} match “${input.value.trim()}”.`;
          } else if (state.query) {
            status.textContent = `${visible} tool${visible === 1 ? "" : "s"} match “${input.value.trim()}”.`;
          } else if (state.category) {
            status.textContent = `${visible} tools in ${state.category}.`;
          } else {
            status.textContent = `${cards.length} tools available.`;
          }
        } catch (error) {
          console.error("One Clear Tool catalog filtering failed", error);
          status.textContent = "Unable to filter tools. Reload to try again.";
        }
      }

      input.addEventListener("input", update);
      categorySelect.addEventListener("change", update);
      update();
    } catch (error) {
      console.error("One Clear Tool catalog initialization failed", error);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();

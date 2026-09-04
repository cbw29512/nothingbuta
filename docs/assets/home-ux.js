(() => {
  "use strict";

  const EXPANSION_TOOLS = [
    ["gravel-calculator", "Gravel Calculator", "Estimate gravel volume and order quantity for driveways, paths, and beds."],
    ["mulch-calculator", "Mulch Calculator", "Estimate mulch volume and bag count for beds, borders, and landscaping."],
    ["drywall-calculator", "Drywall Calculator", "Estimate drywall sheet count from wall dimensions, openings, and waste."],
    ["tile-calculator", "Tile Calculator", "Estimate tile area and boxes needed with a configurable waste allowance."],
    ["topsoil-calculator", "Topsoil Calculator", "Estimate topsoil volume for gardens, lawns, raised areas, and leveling."],
    ["grass-seed-calculator", "Grass Seed Calculator", "Estimate grass seed needed from lawn area and application rate."],
    ["overtime-pay-calculator", "Overtime Pay Calculator", "Estimate regular pay, overtime pay, and total gross earnings."],
    ["compound-interest-calculator", "Compound Interest Calculator", "Estimate future savings growth from a starting balance and monthly contributions."],
    ["rice-water-calculator", "Rice Water Calculator", "Scale rice and water amounts for common stovetop cooking ratios."],
    ["meat-per-person-calculator", "Meat Per Person Calculator", "Estimate how many pounds of meat to buy for a group meal."],
  ];

  function addExpansionCards() {
    const grid = document.querySelector(".tool-grid");
    if (!grid) return;

    for (const [slug, title, description] of EXPANSION_TOOLS) {
      if (grid.querySelector(`[href=\"${slug}/\"]`)) continue;
      const card = document.createElement("a");
      card.className = "tool-card";
      card.href = `${slug}/`;
      card.innerHTML = `<span class=\"badge\">Live</span><strong>${title}</strong><span>${description}</span>`;
      grid.appendChild(card);
    }

    const total = grid.querySelectorAll(".tool-card").length;
    const count = document.querySelector(".count");
    if (count) count.textContent = `${total} live tools`;

    const browse = document.querySelector('.hero-button.primary[href="#tools"]');
    if (browse) browse.textContent = `Browse ${total} tools`;
  }

  function init() {
    addExpansionCards();

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
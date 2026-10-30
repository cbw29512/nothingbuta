#!/usr/bin/env node
// Test the real homepage filter with a minimal DOM. No network or npm packages.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

try {
  const root = path.resolve(__dirname, "..");
  const html = fs.readFileSync(path.join(root, "docs/index.html"), "utf8");
  const source = fs.readFileSync(path.join(root, "docs/assets/home-ux.js"), "utf8");
  assert.match(html, /id="oct-tool-category"/, "Category filter is in the homepage");
  const decode = text => text.replace(/&amp;/g, "&");
  const re = /<a class="tool-card" href="[^"]+"><span class="badge">([^<]+)<\/span><strong>([^<]+)<\/strong><span>([^<]+)<\/span><\/a>/g;
  const cards = [...html.matchAll(re)].map(match => {
    const category = decode(match[1]);
    return {
      category,
      textContent: [category, decode(match[2]), decode(match[3])].join(" "),
      hidden: false,
      querySelector: selector =>
        selector === ".badge" ? { textContent: category } : null,
    };
  });
  assert.equal(cards.length, 92, "Test must cover every published calculator");

  // UI state: input text, category choice, live count and card visibility.
  const listeners = {};
  const input = {
    value: "",
    addEventListener: (event, fn) => { listeners["input:" + event] = fn; },
  };
  const select = {
    value: "",
    options: [],
    appendChild(option) { this.options.push(option); },
    addEventListener: (event, fn) => { listeners["select:" + event] = fn; },
  };
  const status = { textContent: "" };
  const document = {
    readyState: "complete",
    getElementById(id) {
      return {
        "oct-tool-search-input": input,
        "oct-tool-category": select,
        "oct-tool-search-status": status,
      }[id] || null;
    },
    querySelectorAll(selector) {
      return selector === ".tool-card" ? cards : [];
    },
    createElement(tag) {
      assert.equal(tag, "option");
      return { value: "", textContent: "" };
    },
  };
  const errors = [];
  vm.runInNewContext(source, {
    document,
    console: { error: (...args) => errors.push(args.join(" ")) },
  }, { filename: "home-ux.js", timeout: 1000 });

  const visible = () => cards.filter(card => !card.hidden);
  assert.equal(visible().length, 92);
  const categories = [...new Set(cards.map(card => card.category))].sort();
  assert.deepEqual(select.options.map(option => option.value).sort(), categories);
  assert.ok(categories.includes("Home") && categories.includes("Money & Work"));

  select.value = "Home";
  listeners["select:change"]();
  assert.equal(visible().length, cards.filter(card => card.category === "Home").length);
  assert.match(status.textContent, /tools in Home/);

  input.value = "mortgage";
  listeners["input:input"]();
  assert.equal(visible().length, 0, "Combined filters must use AND");

  select.value = "";
  listeners["select:change"]();
  assert.ok(visible().some(card => /Mortgage Payment Calculator/.test(card.textContent)));
  assert.match(status.textContent, /match “mortgage”/);

  input.value = "";
  listeners["input:input"]();
  assert.equal(visible().length, 92, "Clearing both controls restores the catalog");
  assert.equal(status.textContent, "92 tools available.");
  assert.deepEqual(errors, []);
  console.log("PASS: 92 tool categories, keyword AND category, zero matches, reset");
} catch (error) {
  console.error("Homepage category-filter regression failed:", error);
  process.exitCode = 1;
}

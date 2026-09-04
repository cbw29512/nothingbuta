'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const DOCS = path.join(ROOT, 'docs');
const CATALOG = JSON.parse(fs.readFileSync(path.join(ROOT, 'scripts', 'tool_catalog.json'), 'utf8'));
const EXCLUDED = new Set(['assets', 'privacy', 'terms']);

function attribute(tag, name) {
  const match = tag.match(new RegExp(`\\b${name}\\s*=\\s*["']([^"']*)["']`, 'i'));
  return match ? match[1] : '';
}

function makeElement(value = '') {
  return {
    value,
    checked: false,
    innerHTML: '',
    textContent: '',
    dataset: {},
    style: {},
    classList: { contains: () => false },
    addEventListener() {},
    dispatchEvent() { return true; },
    querySelector() { return null; },
    querySelectorAll() { return []; },
  };
}

function parseElements(html) {
  const elements = new Map();
  const inputs = [];
  const selects = [];
  const textareas = [];

  for (const match of html.matchAll(/<input\b[^>]*>/gi)) {
    const tag = match[0];
    const id = attribute(tag, 'id');
    if (!id) continue;
    const element = makeElement(attribute(tag, 'value'));
    element.checked = /\bchecked\b/i.test(tag);
    elements.set(id, element);
    inputs.push(element);
  }

  for (const match of html.matchAll(/<select\b([^>]*)>([\s\S]*?)<\/select>/gi)) {
    const tag = `<select${match[1]}>`;
    const id = attribute(tag, 'id');
    if (!id) continue;
    const body = match[2];
    const options = Array.from(body.matchAll(/<option\b([^>]*)>([\s\S]*?)<\/option>/gi));
    const chosen = options.find((option) => /\bselected\b/i.test(option[1])) || options[0];
    const value = chosen ? (attribute(`<option${chosen[1]}>`, 'value') || chosen[2].replace(/<[^>]+>/g, '').trim()) : '';
    const element = makeElement(value);
    elements.set(id, element);
    selects.push(element);
  }

  for (const match of html.matchAll(/<textarea\b([^>]*)>([\s\S]*?)<\/textarea>/gi)) {
    const tag = `<textarea${match[1]}>`;
    const id = attribute(tag, 'id');
    if (!id) continue;
    const value = match[2].replace(/<[^>]+>/g, '');
    const element = makeElement(value);
    elements.set(id, element);
    textareas.push(element);
  }

  for (const id of ['out', 'summary', 'result', 'output']) {
    if (!elements.has(id)) elements.set(id, makeElement(''));
  }

  return { elements, inputs, selects, textareas };
}

function inlineScripts(html) {
  const scripts = [];
  for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
    const attrs = match[1] || '';
    if (/\bsrc\s*=/i.test(attrs)) continue;
    if (/application\/ld\+json/i.test(attrs)) continue;
    if (!match[2].trim()) continue;
    scripts.push(match[2]);
  }
  return scripts;
}

function runPage(file) {
  const html = fs.readFileSync(file, 'utf8');
  const { elements, inputs, selects, textareas } = parseElements(html);
  const errors = [];

  const document = {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, makeElement(''));
      return elements.get(id);
    },
    querySelectorAll(selector) {
      if (selector.includes('textarea')) return textareas;
      if (selector.includes('select')) return selects;
      if (selector.includes('input')) return inputs;
      return [];
    },
    querySelector() { return null; },
    createElement() { return makeElement(''); },
    body: { appendChild() {} },
  };

  const sandbox = {
    console: {
      log() {},
      warn() {},
      error(...args) { errors.push(args.map(String).join(' ')); },
    },
    document,
    Event: class Event { constructor(type) { this.type = type; } },
    Intl,
    Math,
    Date,
    Number,
    String,
    Boolean,
    Array,
    Object,
    JSON,
    RegExp,
    parseInt,
    parseFloat,
    isFinite,
    setTimeout,
    clearTimeout,
  };
  sandbox.window = sandbox;
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);

  const scripts = inlineScripts(html);
  if (!scripts.length) throw new Error('no calculator script found');
  scripts.forEach((script, index) => vm.runInContext(script, sandbox, { filename: `${file}:script-${index + 1}` }));
  if (typeof sandbox.calc === 'function') sandbox.calc();

  const out = elements.get('out');
  if (!out || !String(out.innerHTML).trim()) throw new Error('result output stayed empty');
  if (/needs a stricter formula before it can pass/i.test(out.innerHTML)) throw new Error('renderer fallback was shown');
  if (errors.length) throw new Error(`console error: ${errors.join(' | ')}`);
  return { html, out: String(out.innerHTML), elements };
}

function monthlyPayment(principal, apr, months) {
  const rate = apr / 100 / 12;
  if (!rate) return principal / months;
  return principal * (rate * Math.pow(1 + rate, months)) / (Math.pow(1 + rate, months) - 1);
}

const directories = fs.readdirSync(DOCS, { withFileTypes: true })
  .filter((entry) => entry.isDirectory() && !EXCLUDED.has(entry.name))
  .map((entry) => entry.name)
  .filter((name) => fs.existsSync(path.join(DOCS, name, 'index.html')))
  .sort();

const catalogSlugs = CATALOG.map((item) => item.slug).sort();
const failures = [];

if (new Set(catalogSlugs).size !== catalogSlugs.length) {
  failures.push('tool catalog contains duplicate slugs');
}
if (JSON.stringify(directories) !== JSON.stringify(catalogSlugs)) {
  const disk = new Set(directories);
  const catalog = new Set(catalogSlugs);
  const missingPages = catalogSlugs.filter((slug) => !disk.has(slug));
  const unregistered = directories.filter((slug) => !catalog.has(slug));
  if (missingPages.length) failures.push(`catalog entries missing pages: ${missingPages.join(', ')}`);
  if (unregistered.length) failures.push(`calculator pages missing catalog entries: ${unregistered.join(', ')}`);
}

const results = new Map();
for (const slug of directories) {
  try {
    results.set(slug, runPage(path.join(DOCS, slug, 'index.html')));
  } catch (error) {
    failures.push(`${slug}: ${error.message}`);
  }
}

try {
  const paycheck = results.get('paycheck-estimator')?.out || '';
  if (!paycheck.includes('$1,676.00')) failures.push('paycheck-estimator: default take-home regression');

  const freelance = results.get('freelance-rate-calculator')?.out || '';
  if (!freelance.includes('$90.22')) failures.push('freelance-rate-calculator: default hourly-rate regression');

  const car = results.get('car-payment-calculator')?.out || '';
  const expectedCar = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
    .format(monthlyPayment(27000, 7.5, 60));
  if (!car.includes(expectedCar)) failures.push(`car-payment-calculator: expected default payment ${expectedCar}`);

  const cups = results.get('cups-to-ounces-converter')?.out || '';
  if (!cups.includes('16.00 fl oz')) failures.push('cups-to-ounces-converter: default conversion regression');

  const kg = results.get('kg-to-pounds-converter')?.out || '';
  if (!kg.includes('22.046 lb')) failures.push('kg-to-pounds-converter: default conversion regression');

  const words = results.get('word-counter')?.out || '';
  if (results.has('word-counter') && !words.includes('10')) failures.push('word-counter: default word-count regression');
} catch (error) {
  failures.push(`known-value assertions: ${error.message}`);
}

if (failures.length) {
  console.error('Calculator smoke failures:');
  failures.forEach((failure) => console.error(`- ${failure}`));
  process.exit(1);
}

console.log(`Calculator runtime smoke passed for all ${CATALOG.length} catalog tools.`);

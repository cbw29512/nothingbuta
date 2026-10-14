/* One Clear Tool - Save and Export Pack (client-side only, no server).
   Switch on: set PACK_LIVE = true (and set BUY_URL). Until then it only runs with ?pack=preview. */
(() => {
  "use strict";
  const PACK_LIVE = false;
  const BUY_URL = "https://buymeacoffee.com/divclass016";
  const CODE_SHA256 = "787fa10ee056a92a0818224b054cb546ff105dcd1d32ef60f7fc4eb3bb1d3705";
  const UNLOCK_KEY = "oct-pack-unlocked";
  const SAVE_KEY = "oct-pack-saves";
  const script = document.currentScript;
  const KIND = script?.dataset.kind; // "mortgage" or "debt"
  const preview = new URLSearchParams(location.search).get("pack") === "preview";
  if (!KIND || !(PACK_LIVE || preview)) return;

  const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
  const money = (v) => usd.format(Number.isFinite(v) ? v : 0);
  const val = (id) => Number(document.getElementById(id)?.value) || 0;
  const FIELDS = KIND === "mortgage"
    ? [["price","Home price"],["down","Down payment"],["rate","Interest rate (percent)"],["years","Loan term (years)"],["escrow","Monthly taxes and insurance"]]
    : [["balance","Debt balance"],["apr","Annual interest rate (percent)"],["pay","Monthly payment"],["extra","Extra monthly payment"]];
  const TITLE = KIND === "mortgage" ? "Mortgage payment plan" : "Debt payoff plan";

  // ---------- math ----------
  function schedule() {
    const rows = [];
    let bal, rate, pay, extraMonthly = 0;
    if (KIND === "mortgage") {
      bal = Math.max(val("price") - val("down"), 0);
      rate = val("rate") / 100 / 12;
      const n = Math.round(val("years") * 12);
      if (bal <= 0 || n <= 0) return { rows, error: "Enter a loan amount and term above zero." };
      pay = rate > 0 ? bal * (rate * Math.pow(1 + rate, n)) / (Math.pow(1 + rate, n) - 1) : bal / n;
      extraMonthly = val("escrow");
    } else {
      bal = val("balance"); rate = val("apr") / 100 / 12; pay = val("pay") + val("extra");
      if (bal <= 0 || pay <= 0) return { rows, error: "Enter a balance and payment above zero." };
      if (rate > 0 && pay <= bal * rate) return { rows, error: "Payment is too low to reduce the balance." };
    }
    let m = 0, totalInterest = 0;
    while (bal > 0.005 && m < 1200) {
      m++;
      const interest = bal * rate;
      let principal = pay - interest;
      if (principal > bal) principal = bal;
      bal -= principal; totalInterest += interest;
      rows.push({ month: m, payment: principal + interest, principal, interest, balance: Math.max(bal, 0) });
    }
    const summary = KIND === "mortgage"
      ? [["Loan amount", money(Math.max(val("price") - val("down"), 0))], ["Principal and interest per month", money(pay)], ["Taxes and insurance per month", money(extraMonthly)], ["Total monthly payment", money(pay + extraMonthly)], ["Total interest over the loan", money(totalInterest)], ["Number of payments", String(rows.length)]]
      : [["Monthly payment used", money(pay)], ["Months to pay off", String(rows.length)], ["Total interest", money(totalInterest)], ["Total paid", money(totalInterest + val("balance"))]];
    return { rows, summary };
  }
  const inputsList = () => FIELDS.map(([id, label]) => [label, document.getElementById(id)?.value ?? ""]);

  // ---------- files ----------
  function download(name, type, data) {
    const blob = new Blob([data], { type });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }
  const fileBase = () => `one-clear-tool-${KIND === "mortgage" ? "mortgage" : "debt-payoff"}-${new Date().toISOString().slice(0, 10)}`;
  function csv() {
    const s = schedule(); if (s.error) return alert(s.error);
    const q = (x) => `"${String(x).replace(/"/g, '""')}"`;
    const lines = [[TITLE], [], ["Your numbers"], ...inputsList(), [], ["Summary"], ...s.summary, [], ["Month", "Payment", "Principal", "Interest", "Balance left"],
      ...s.rows.map((r) => [r.month, r.payment.toFixed(2), r.principal.toFixed(2), r.interest.toFixed(2), r.balance.toFixed(2)])];
    download(fileBase() + ".csv", "text/csv;charset=utf-8", "\ufeff" + lines.map((l) => l.map(q).join(",")).join("\r\n"));
  }
  // Minimal text PDF writer (Helvetica, Letter size, multi-page)
  function pdf() {
    const s = schedule(); if (s.error) return alert(s.error);
    const esc = (t) => String(t).replace(/[^\x20-\x7e]/g, "").replace(/([\\()])/g, "\\$1");
    const lines = [{ t: TITLE, size: 18 }, { t: "One Clear Tool - onecleartool.com - " + new Date().toLocaleDateString("en-US"), size: 10 }, { t: "" },
      { t: "Your numbers", size: 13 }, ...inputsList().map(([a, b]) => ({ t: `${a}: ${b}` })), { t: "" },
      { t: "Summary", size: 13 }, ...s.summary.map(([a, b]) => ({ t: `${a}: ${b}` })), { t: "" },
      { t: "Payoff schedule", size: 13 }, { t: "Month      Payment        Principal      Interest       Balance left", mono: true },
      ...s.rows.map((r) => ({ mono: true, t: [String(r.month).padEnd(8), money(r.payment).padStart(13), money(r.principal).padStart(15), money(r.interest).padStart(14), money(r.balance).padStart(16)].join("") })),
      { t: "" }, { t: "Planning estimate only. Not financial advice or a lender quote.", size: 9 }];
    const pages = []; let cur = [], y = 750;
    for (const l of lines) { const sz = l.size || 10, h = sz + 5; if (y - h < 40) { pages.push(cur); cur = []; y = 750; } cur.push({ ...l, sz, y }); y -= h; }
    pages.push(cur);
    const objs = []; const add = (s) => { objs.push(s); return objs.length; };
    const fontR = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>");
    const fontM = add("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>");
    const pagesId = objs.length + 1; objs.push(null);
    const kids = [];
    for (const pg of pages) {
      const stream = pg.map((l) => `BT /${l.mono ? "F2" : "F1"} ${l.mono ? 9 : l.sz} Tf 50 ${l.y} Td (${esc(l.t)}) Tj ET`).join("\n");
      const c = add(`<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`);
      kids.push(add(`<< /Type /Page /Parent ${pagesId} 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 ${fontR} 0 R /F2 ${fontM} 0 R >> >> /Contents ${c} 0 R >>`));
    }
    objs[pagesId - 1] = `<< /Type /Pages /Kids [${kids.map((k) => k + " 0 R").join(" ")}] /Count ${kids.length} >>`;
    const cat = add(`<< /Type /Catalog /Pages ${pagesId} 0 R >>`);
    let out = "%PDF-1.4\n"; const offs = [];
    objs.forEach((o, i) => { offs.push(out.length); out += `${i + 1} 0 obj\n${o}\nendobj\n`; });
    const xref = out.length;
    out += `xref\n0 ${objs.length + 1}\n0000000000 65535 f \n` + offs.map((o) => String(o).padStart(10, "0") + " 00000 n \n").join("");
    out += `trailer\n<< /Size ${objs.length + 1} /Root ${cat} 0 R >>\nstartxref\n${xref}\n%%EOF`;
    download(fileBase() + ".pdf", "application/pdf", out);
  }
  function printSchedule() {
    const s = schedule(); if (s.error) return alert(s.error);
    const w = window.open("", "_blank"); if (!w) return alert("Allow pop-ups to print the schedule.");
    const tr = (cells, tag = "td") => `<tr>${cells.map((c) => `<${tag}>${c}</${tag}>`).join("")}</tr>`;
    w.document.write(`<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${TITLE} | One Clear Tool</title><style>body{font:16px system-ui,sans-serif;color:#111;margin:24px}h1{font-size:26px}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border:1px solid #999;padding:6px;text-align:right}th{background:#eee}td:first-child,th:first-child{text-align:left}.sum td{text-align:left}button{font-size:18px;padding:10px 18px;margin:10px 0}@media print{button{display:none}}</style></head><body><h1>${TITLE}</h1><p>One Clear Tool, ${new Date().toLocaleDateString("en-US")}. Planning estimate only.</p><button onclick="print()">Print this schedule</button><h2>Your numbers</h2><table class="sum">${inputsList().map((r) => tr(r)).join("")}</table><h2>Summary</h2><table class="sum">${s.summary.map((r) => tr(r)).join("")}</table><h2>Payoff schedule</h2><table>${tr(["Month", "Payment", "Principal", "Interest", "Balance left"], "th")}${s.rows.map((r) => tr([r.month, money(r.payment), money(r.principal), money(r.interest), money(r.balance)])).join("")}</table></body></html>`);
    w.document.close();
  }

  // ---------- saving ----------
  const loadSaves = () => { try { return JSON.parse(localStorage.getItem(SAVE_KEY) || "[]"); } catch { return []; } };
  const storeSaves = (list) => localStorage.setItem(SAVE_KEY, JSON.stringify(list));
  function saveNow() {
    const name = prompt("Name this calculation:", `${TITLE} ${new Date().toLocaleDateString("en-US")}`); if (name === null) return;
    const list = loadSaves(); list.unshift({ kind: KIND, name: name || TITLE, at: Date.now(), values: Object.fromEntries(FIELDS.map(([id]) => [id, document.getElementById(id)?.value ?? ""])) });
    storeSaves(list.slice(0, 50)); renderSaves(); status("Saved on this device.");
  }
  function loadOne(i) {
    const item = loadSaves().filter((s) => s.kind === KIND)[i]; if (!item) return;
    for (const [id, v] of Object.entries(item.values)) { const el = document.getElementById(id); if (el) { el.value = v; el.dispatchEvent(new Event("input", { bubbles: true })); } }
    if (typeof window.calc === "function") window.calc();
    status(`Loaded "${item.name}".`);
  }
  function deleteOne(i) {
    const all = loadSaves(); const mine = all.filter((s) => s.kind === KIND); const target = mine[i];
    storeSaves(all.filter((s) => s !== target && !(s.at === target.at && s.name === target.name))); renderSaves();
  }

  // ---------- user interface ----------
  let panel, statusEl, savesEl;
  const status = (t) => { if (statusEl) statusEl.textContent = t; };
  async function sha(t) { const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(t)); return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join(""); }
  const unlocked = () => localStorage.getItem(UNLOCK_KEY) === CODE_SHA256;
  function renderSaves() {
    if (!savesEl) return;
    const mine = loadSaves().filter((s) => s.kind === KIND);
    savesEl.innerHTML = mine.length ? "<h3>Saved on this device</h3>" + mine.map((s, i) => `<div class="oct-pack-save"><span>${s.name.replace(/[<>&]/g, "")}<small>${new Date(s.at).toLocaleString("en-US")}</small></span><button type="button" data-load="${i}">Load</button><button type="button" data-del="${i}">Delete</button></div>`).join("") : "<p>No saved calculations yet.</p>";
  }
  function render() {
    if (unlocked()) {
      panel.innerHTML = `<strong>Save and Export pack</strong><p>Thank you for your support. Everything stays on this device.</p><div class="oct-pack-actions"><button type="button" data-act="save">Save this calculation</button><button type="button" data-act="pdf">Download PDF</button><button type="button" data-act="csv">Download spreadsheet (CSV)</button><button type="button" data-act="print">Printable payoff schedule</button></div><div class="oct-pack-status" aria-live="polite"></div><div class="oct-pack-saves"></div>`;
      savesEl = panel.querySelector(".oct-pack-saves"); renderSaves();
    } else {
      panel.innerHTML = `<strong>Save and Export pack</strong><p>Save your numbers, download a PDF or spreadsheet, and print a month-by-month payoff schedule. The calculator stays free.</p><a class="oct-pack-buy" href="${BUY_URL}" target="_blank" rel="noopener noreferrer">Get the pack on Buy Me a Coffee</a><label for="oct-pack-code">Already have a code?</label><div class="oct-pack-unlock"><input id="oct-pack-code" type="text" autocomplete="off" autocapitalize="characters" placeholder="Enter your unlock code"><button type="button" data-act="unlock">Unlock</button></div><div class="oct-pack-status" aria-live="polite"></div>`;
    }
    statusEl = panel.querySelector(".oct-pack-status");
  }
  async function onClick(e) {
    const b = e.target.closest("button"); if (!b) return;
    const act = b.dataset.act;
    if (act === "unlock") {
      const code = panel.querySelector("#oct-pack-code").value.trim().toUpperCase();
      if (await sha(code) === CODE_SHA256) { localStorage.setItem(UNLOCK_KEY, CODE_SHA256); render(); status("Unlocked. Thank you!"); }
      else status("That code did not match. Check the code in your thank-you message.");
    } else if (act === "save") saveNow();
    else if (act === "pdf") { pdf(); status("PDF downloaded."); }
    else if (act === "csv") { csv(); status("Spreadsheet downloaded."); }
    else if (act === "print") printSchedule();
    else if (b.dataset.load) loadOne(Number(b.dataset.load));
    else if (b.dataset.del) deleteOne(Number(b.dataset.del));
  }
  function init() {
    panel = document.createElement("aside");
    panel.className = "oct-pack"; panel.id = "oct-pack"; panel.setAttribute("aria-label", "Save and Export pack");
    const soon = document.querySelector(".oct-pro-soon");
    if (soon) soon.replaceWith(panel); else document.querySelector(".result")?.insertAdjacentElement("afterend", panel);
    panel.addEventListener("click", onClick);
    render();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true }); else init();
  window.OCTPack = { schedule, csv, pdf, printSchedule };
})();

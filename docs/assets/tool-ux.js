(() => {
  "use strict";

  const SUPPORT_URL = "https://www.buymeacoffee.com/divclass016";

  function textFromResult(result) {
    if (!result) return "";
    const parts = [];
    const summary = result.querySelector("#summary");
    if (summary?.textContent?.trim()) parts.push(summary.textContent.trim());

    const out = result.querySelector("#out");
    if (out) {
      const metrics = Array.from(out.querySelectorAll(".metric"));
      if (metrics.length) {
        for (const metric of metrics) {
          const value = metric.querySelector("strong")?.textContent?.trim() || "";
          const label = metric.querySelector("span")?.textContent?.trim() || "";
          if (value || label) parts.push(label ? `${label}: ${value}` : value);
        }
        const extra = Array.from(out.children)
          .filter((node) => !node.classList.contains("metric"))
          .map((node) => node.textContent?.trim())
          .filter(Boolean);
        parts.push(...extra);
      } else if (out.textContent?.trim()) {
        parts.push(out.textContent.trim());
      }
    }

    if (!parts.length) {
      const clone = result.cloneNode(true);
      clone.querySelector(".oct-result-actions")?.remove();
      parts.push(clone.textContent?.trim() || "");
    }

    return parts.filter(Boolean).join("\n").replace(/\n{3,}/g, "\n\n").trim();
  }

  async function copyText(text) {
    if (!text) throw new Error("No result to copy");
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand("copy");
    area.remove();
    if (!ok) throw new Error("Copy unavailable");
  }

  function announce(node, message) {
    if (!node) return;
    node.textContent = message;
    window.clearTimeout(Number(node.dataset.clearTimer || 0));
    const timer = window.setTimeout(() => { node.textContent = ""; }, 3500);
    node.dataset.clearTimer = String(timer);
  }

  function recalculate(form) {
    const firstInput = form?.querySelector("input, select, textarea");
    if (firstInput) firstInput.dispatchEvent(new Event("input", { bubbles: true }));
    if (typeof window.calc === "function") {
      try { window.calc(); } catch (error) { console.error("Recalculation failed", error); }
    }
  }

  function installResultActions(form, result) {
    if (!form || !result || result.querySelector(".oct-result-actions")) return;

    const actions = document.createElement("div");
    actions.className = "oct-result-actions";

    const copy = document.createElement("button");
    copy.type = "button";
    copy.textContent = "Copy result";

    const reset = document.createElement("button");
    reset.type = "button";
    reset.textContent = "Reset example";

    const share = document.createElement("button");
    share.type = "button";
    share.textContent = "Share";

    const status = document.createElement("div");
    status.className = "oct-action-status";
    status.setAttribute("aria-live", "polite");

    copy.addEventListener("click", async () => {
      try {
        await copyText(textFromResult(result));
        announce(status, "Result copied.");
      } catch (error) {
        console.error("Copy result failed", error);
        announce(status, "Copy is not available in this browser.");
      }
    });

    reset.addEventListener("click", () => {
      form.reset();
      recalculate(form);
      announce(status, "Example values restored.");
    });

    share.addEventListener("click", async () => {
      const resultText = textFromResult(result);
      const shareData = {
        title: document.title,
        text: resultText ? `${document.title}\n${resultText}` : document.title,
        url: window.location.href,
      };
      try {
        if (navigator.share) {
          await navigator.share(shareData);
          announce(status, "Share sheet opened.");
        } else {
          await copyText(`${shareData.text}\n${shareData.url}`);
          announce(status, "Share text copied.");
        }
      } catch (error) {
        if (error?.name !== "AbortError") {
          console.error("Share failed", error);
          announce(status, "Sharing is not available in this browser.");
        }
      }
    });

    actions.append(copy, reset, share, status);
    result.appendChild(actions);
  }

  function installTrustNote(form) {
    if (!form || form.querySelector(".oct-trust-note")) return;
    const note = document.createElement("div");
    note.className = "oct-trust-note";
    note.innerHTML = "<strong>Private by design:</strong><span>Your calculator inputs stay in this browser. No account is required.</span>";
    form.appendChild(note);
  }

  function verifySupportLink() {
    const support = document.querySelector(`a[href=\"${SUPPORT_URL}\"]`);
    if (!support) console.warn("One Clear Tool support link is missing from this calculator page.");
  }

  function init() {
    const form = document.querySelector("form");
    const result = document.querySelector(".result, [aria-live=\"polite\"]");
    installTrustNote(form);
    installResultActions(form, result);
    verifySupportLink();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();

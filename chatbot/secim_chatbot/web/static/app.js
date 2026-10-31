"use strict";
(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const chat = $("#chat"), form = $("#composer"), input = $("#q"), send = $("#send"), modeSel = $("#mode");
  const history = []; // last turns, sent back for follow-up questions
  const fmtInt = new Intl.NumberFormat("tr-TR");
  const fmtDec = new Intl.NumberFormat("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const fmt = (v) => {
    if (v === null || v === undefined) return "—";
    if (typeof v === "number") return Number.isInteger(v) ? (Math.abs(v) >= 10000 ? fmtInt.format(v) : String(v)) : fmtDec.format(v);
    return String(v);
  };
  const isYearish = (col) => /^(yil|yıl|plaka|kod)$/i.test(col);

  // ---------------------------------------------------------------- status + examples
  fetch("/api/health").then(r => r.json()).then(h => {
    const dot = $("#status-dot"), txt = $("#status-text");
    const modes = h.modes || [];
    if (modes.length > 1) {
      [...modeSel.options].forEach(o => { o.hidden = o.disabled = !modes.includes(o.value); });
      let saved = null; try { saved = localStorage.getItem("secim-mode"); } catch (e) { /* storage blocked */ }
      modeSel.value = modes.includes(saved) ? saved : h.mode;
      $("#mode-wrap").hidden = false;
    }
    if (!h.model) { dot.className = "dot ok"; txt.textContent = "şablon"; if (!h.db) { dot.className = "dot err"; txt.textContent = "veritabanı yok"; } return; }
    if (!h.db) { dot.className = "dot err"; txt.textContent = "veritabanı yok"; return; }
    if (h.demo) { dot.className = "dot demo"; txt.textContent = "demo modu"; $("#status").title = "Gerçek model bağlı değil: yalnız örnek sorular yanıtlanır."; }
    else { dot.className = "dot ok"; txt.textContent = h.model.replace("anthropic:", "").replace("ollama:", ""); }
  }).catch(() => { $("#status-dot").className = "dot err"; $("#status-text").textContent = "sunucu yok"; });

  fetch("/api/examples").then(r => r.json()).then(({ examples }) => {
    const box = $("#chips");
    examples.forEach(q => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "chip"; b.textContent = q;
      b.addEventListener("click", () => ask(q));
      box.appendChild(b);
    });
  });

  // ---------------------------------------------------------------- rendering
  const scroller = $("#scroller");
  function scrollDown() { scroller.scrollTo({ top: scroller.scrollHeight, behavior: "smooth" }); }

  function addUser(text) {
    const el = document.createElement("div");
    el.className = "msg user"; el.textContent = text;
    chat.appendChild(el);
  }

  function addThinking() {
    const el = document.createElement("article");
    el.className = "msg bot";
    el.innerHTML = '<div class="thinking"><i></i><i></i><i></i><span>Sorgu yazılıyor ve çalıştırılıyor…</span></div>';
    chat.appendChild(el); scrollDown();
    return el;
  }

  function highlightSql(sql) {
    const esc = sql.replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
    return esc
      .replace(/'(?:[^'\\]|\\.)*'/g, m => `<span class="str">${m}</span>`)
      .replace(/\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|ON|AND|OR|NOT|IN|AS|GROUP BY|ORDER BY|LIMIT|OFFSET|DESC|ASC|SUM|COUNT|ROUND|CASE|WHEN|THEN|ELSE|END|WITH|UNION|DISTINCT|HAVING|LIKE|IS|NULL|AVG|MAX|MIN)\b/g,
        m => `<span class="kw">${m}</span>`)
      .replace(/(?<![\w.'])(\d+(?:\.\d+)?)(?![\w'])/g, m => `<span class="num">${m}</span>`);
  }

  function renderTable(wrap, columns, rows, truncated) {
    if (!columns.length || !rows.length) return;
    const numeric = columns.map((c, i) => rows.every(r => r[i] === null || typeof r[i] === "number") && !isYearish(c));
    // show inline bars when there is a label column and a few numeric columns (top-N / shares)
    // bar on the last numeric column only (usually oran / oy / vekil)
    const lastNum = numeric.lastIndexOf(true);
    const barCols = columns.map((_, i) => i === lastNum && rows.length > 1 && rows.length <= 25 && rows.some(r => r[i] > 0));
    const max = columns.map((_, i) => Math.max(...rows.map(r => (typeof r[i] === "number" ? r[i] : 0))));
    const t = document.createElement("table");
    const head = t.createTHead().insertRow();
    columns.forEach((c, i) => { const th = document.createElement("th"); th.textContent = c.replace(/_/g, " "); if (numeric[i]) th.className = "num"; head.appendChild(th); });
    const body = t.createTBody();
    rows.forEach(r => {
      const tr = body.insertRow();
      r.forEach((v, i) => {
        const td = tr.insertCell();
        if (barCols[i] && max[i] > 0) {
          td.className = "num bar";
          const pct = Math.max(2, (v / max[i]) * 100);
          td.innerHTML = `<div class="cell"><span class="track"><span class="fill${v === max[i] ? " lead" : ""}" style="width:${pct}%"></span></span><span class="v"></span></div>`;
          td.querySelector(".v").textContent = fmt(v);
        } else {
          if (numeric[i]) td.className = "num";
          td.textContent = fmt(v);
        }
      });
    });
    wrap.appendChild(t);
    if (truncated) { const d = document.createElement("div"); d.className = "trunc"; d.textContent = `İlk ${rows.length} satır gösteriliyor.`; wrap.appendChild(d); }
    wrap.hidden = false;
  }

  function renderBot(el, data) {
    const node = $("#tpl-bot").content.firstElementChild.cloneNode(true);
    node.classList.add(data.status);
    $(".answer", node).textContent = data.answer;

    const meta = $(".meta", node), bits = [];
    if (data.status === "ok") bits.push(`${data.rows.length} satır`);
    bits.push(data.elapsed_ms < 1000 ? `${data.elapsed_ms} ms` : `${(data.elapsed_ms / 1000).toLocaleString("tr-TR", { maximumFractionDigits: 1 })} sn`);
    const by = data.answered_by || (data.route === "none" ? "" : data.model);
    if (by) bits.push(by === "fake" ? "demo" : by.replace("anthropic:", "").replace("ollama:", ""));
    bits.forEach((b, i) => {
      const s = document.createElement("span"); s.textContent = b;
      if (b === by || (by === "fake" && b === "demo")) { s.className = data.route === "template" ? "via tpl" : "via"; s.title = data.route === "template" ? `Dil modeli kullanılmadı (şablon: ${data.template})` : "SQL'i dil modeli yazdı"; }
      meta.appendChild(s);
    });
    if (data.status === "ok" && data.attempts.length) {
      const s = document.createElement("span"); s.className = "fix";
      s.textContent = "ilk sorgu hata verdi, model düzeltti"; meta.appendChild(s);
    }

    renderTable($(".table-wrap", node), data.columns || [], data.rows || [], data.truncated);

    if (data.sql) {
      const det = $("details.sql", node);
      $("code", det).innerHTML = highlightSql(data.sql);
      $(".copy", det).addEventListener("click", (e) => {
        navigator.clipboard?.writeText(data.sql); e.target.textContent = "Kopyalandı";
        setTimeout(() => (e.target.textContent = "Kopyala"), 1200);
      });
      if (data.attempts.length) {
        const r = $(".retry", det); r.hidden = false;
        r.innerHTML = "Başarısız deneme: <code></code>";
        $("code", r).textContent = data.attempts[0].error;
      }
      det.hidden = false;
    }
    el.replaceWith(node);
    scrollDown();
  }

  // ---------------------------------------------------------------- ask
  async function ask(question) {
    question = question.trim();
    if (!question || send.disabled) return;
    $("#intro")?.remove();
    addUser(question);
    input.value = ""; autosize();
    send.disabled = true;
    const pending = addThinking();
    try {
      const res = await fetch("/api/ask", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, history: history.slice(-3), ...(modeSel && !$("#mode-wrap").hidden ? { mode: modeSel.value } : {}) }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || res.statusText);
      renderBot(pending, data);
      history.push({ question, sql: data.sql, answer: data.answer });
    } catch (err) {
      renderBot(pending, { status: "failed", answer: `İstek başarısız: ${err.message}`, rows: [], columns: [], attempts: [], elapsed_ms: 0 });
    } finally {
      send.disabled = false; input.focus();
    }
  }

  function autosize() { input.style.height = "auto"; input.style.height = Math.min(input.scrollHeight, 160) + "px"; }
  input.addEventListener("input", autosize);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); ask(input.value); }
  });
  form.addEventListener("submit", (e) => { e.preventDefault(); ask(input.value); });
  modeSel?.addEventListener("change", () => { try { localStorage.setItem("secim-mode", modeSel.value); } catch (e) { /* ignore */ } });
  window.secimAsk = ask; // handy for demos / screenshots
})();

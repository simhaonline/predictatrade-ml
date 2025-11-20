// app.js

function toISODateInput(d) {
  return d.toISOString().slice(0, 10);
}

document.addEventListener("DOMContentLoaded", () => {
  const today = new Date();
  const dateInput = document.getElementById("reportDate");
  dateInput.value = toISODateInput(today);

  document.getElementById("loadBtn").addEventListener("click", loadReport);

  // kick off
  loadReport();
  fetchLivePrice();
  setInterval(fetchLivePrice, 15000);
});

// LIVE PRICE (assumes backend: GET /api/live_price?symbol=XAUUSD)

async function fetchLivePrice() {
  const priceEl = document.getElementById("livePrice");
  const changeEl = document.getElementById("liveChange");
  const providerEl = document.getElementById("liveProvider");
  const utcTsEl = document.getElementById("liveUtcTs");
  const clientTsEl = document.getElementById("liveClientTs");

  if (!priceEl) return; // defensive

  try {
    const res = await fetch("/api/live_price?symbol=XAUUSD");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const last = Number(data.price_last || 0);
    const prevClose = Number(data.price_open || data.prev_close || 0);

    priceEl.textContent = last ? last.toFixed(2) : "–";

    let diff = null;
    let pct = null;
    if (last && prevClose) {
      diff = last - prevClose;
      pct = (diff / prevClose) * 100;
    }

    changeEl.className = "live-change";
    if (diff !== null) {
      const sign = diff >= 0 ? "+" : "−";
      const absDiff = Math.abs(diff);
      const absPct = Math.abs(pct);
      changeEl.textContent = `${sign}${absDiff.toFixed(2)} (${absPct.toFixed(2)}%)`;
      changeEl.classList.add(diff >= 0 ? "up" : "down");
    } else {
      changeEl.textContent = "no ref";
    }

    providerEl.textContent = `source: ${data.provider_primary || "–"}`;

    if (data.timestamp_utc) {
      const iso = new Date(data.timestamp_utc * 1000).toISOString();
      utcTsEl.textContent = iso.replace("T", " ").replace("Z", "Z");
    } else {
      utcTsEl.textContent = "–";
    }
    clientTsEl.textContent = new Date().toLocaleString();
  } catch (err) {
    console.error("live price error:", err);
    changeEl.textContent = "feed error";
    changeEl.className = "live-change down";
  }
}

// REPORT

async function loadReport() {
  const date = document.getElementById("reportDate").value;
  const session = document.getElementById("sessionSelect").value;
  const timeframe = document.getElementById("timeframeSelect").value;
  const clientTz = document.getElementById("clientTzInput").value || "";
  const status = document.getElementById("status");
  const summaryRow = document.getElementById("summaryRow");
  const container = document.getElementById("tableContainer");

  status.textContent = "Loading report…";
  status.classList.remove("ok", "error");
  summaryRow.innerHTML = "";
  container.innerHTML = "";

  try {
    const url =
      `/api/reports/${date}` +
      `?session=${encodeURIComponent(session)}` +
      `&client_tz=${encodeURIComponent(clientTz)}` +
      `&timeframe=${encodeURIComponent(timeframe)}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const table = buildTable(data, timeframe);
    container.appendChild(table);

    const summary = buildSummary(data, timeframe);
    summaryRow.appendChild(summary);

    const totalRows = Object.values(data.sessions || {}).reduce(
      (sum, arr) => sum + arr.length,
      0
    );

    const utcNow = new Date().toISOString();
    const clientNow = new Date().toLocaleString();

    status.textContent =
      `[OK] ${data.date} | TF=${timeframe} | ` +
      `UTC ${utcNow} | Client ${clientNow} | Rows ${totalRows}`;
    status.classList.add("ok");

    // CSV link
    const csvUrl =
      `/api/reports/${date}/csv` +
      `?session=${encodeURIComponent(session)}` +
      `&client_tz=${encodeURIComponent(clientTz)}` +
      `&timeframe=${encodeURIComponent(timeframe)}`;
    document.getElementById("downloadCsv").href = csvUrl;
  } catch (err) {
    console.error("loadReport error:", err);
    status.textContent = `[ERR] ${err.message}`;
    status.classList.add("error");
  }
}

function buildTable(data, timeframe) {
  const wrapper = document.createElement("div");
  wrapper.className = "table-wrapper-inner"; // purely for clarity

  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const tbody = document.createElement("tbody");

  thead.innerHTML = `
    <tr>
      <th>Time (Client)</th>
      <th>Time (UTC)</th>
      <th>Session</th>
      <th>TF</th>
      <th>Hora</th>
      <th>Astro Bias</th>
      <th>Recommendation</th>
      <th>Score</th>
      <th>Position %</th>
    </tr>
  `;

  for (const [sessKey, rows] of Object.entries(data.sessions || {})) {
    for (const row of rows) {
      const tr = document.createElement("tr");

      const biasText = (row.astro_bias || row.astrological_bias || "").toLowerCase();
      const recText = (row.trade_recommendation || "").toUpperCase();
      const score = parseFloat(row.gold_signal_score ?? row.base_score ?? 0);
      const pos = row.position_size_percentage ?? "";

      // bias class
      if (biasText.includes("strong") && biasText.includes("bull")) {
        tr.classList.add("bias-strong-bull");
      } else if (biasText.includes("bull")) {
        tr.classList.add("bias-bull");
      } else if (biasText.includes("strong") && biasText.includes("bear")) {
        tr.classList.add("bias-strong-bear");
      } else if (biasText.includes("bear")) {
        tr.classList.add("bias-bear");
      }

      // rec class
      let recClass = "";
      if (recText.includes("STRONG BUY")) recClass = "rec-strong-buy";
      else if (recText.includes("BUY")) recClass = "rec-buy";
      else if (recText.includes("STRONG SELL")) recClass = "rec-strong-sell";
      else if (recText.includes("SELL")) recClass = "rec-sell";

      const scoreClass = score >= 9 ? "score-strong" : "";
      const posClass = pos === "100%" || pos === 100 ? "pos-100" : "";

      const clientTime = row.time_client || row.time || "";
      const utcTime = row.time_utc || "";

      tr.innerHTML = `
        <td>${clientTime}</td>
        <td>${utcTime}</td>
        <td>${sessKey.toUpperCase()}</td>
        <td>${row.timeframe || timeframe}</td>
        <td>${row.hora_ruler || row.hora_lord || ""}</td>
        <td>${row.astro_bias || row.astrological_bias || ""}</td>
        <td class="${recClass}">${row.trade_recommendation || ""}</td>
        <td class="${scoreClass}">${isFinite(score) ? score.toFixed(2) : ""}</td>
        <td class="${posClass}">${pos}</td>
      `;

      tbody.appendChild(tr);
    }
  }

  table.appendChild(thead);
  table.appendChild(tbody);
  wrapper.appendChild(table);
  return wrapper;
}

// Build a simple session summary: counts per session per direction
function buildSummary(data, timeframe) {
  const container = document.createElement("div");

  const stats = {}; // { session: { buy, strongBuy, sell, strongSell, total } }

  for (const [sessKey, rows] of Object.entries(data.sessions || {})) {
    if (!stats[sessKey]) {
      stats[sessKey] = { buy: 0, strongBuy: 0, sell: 0, strongSell: 0, total: 0 };
    }
    for (const row of rows) {
      const rec = (row.trade_recommendation || "").toUpperCase();
      stats[sessKey].total++;
      if (rec.includes("STRONG BUY")) stats[sessKey].strongBuy++;
      else if (rec.includes("BUY")) stats[sessKey].buy++;
      else if (rec.includes("STRONG SELL")) stats[sessKey].strongSell++;
      else if (rec.includes("SELL")) stats[sessKey].sell++;
    }
  }

  for (const [sess, s] of Object.entries(stats)) {
    const pill = document.createElement("span");
    pill.className = "summary-pill";
    pill.textContent =
      `${sess.toUpperCase()} · TF=${timeframe} · ` +
      `SB:${s.strongBuy} B:${s.buy} S:${s.sell} SS:${s.strongSell} · n=${s.total}`;
    container.appendChild(pill);
  }

  if (!Object.keys(stats).length) {
    const pill = document.createElement("span");
    pill.className = "summary-pill";
    pill.textContent = "No rows for selected filters.";
    container.appendChild(pill);
  }

  return container;
}

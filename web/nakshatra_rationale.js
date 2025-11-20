// --- helpers -------------------------------------------------------

function toISODateInput(d) {
  return d.toISOString().slice(0, 10);
}

// prefer exact keys, then fuzzy match on substrings
function pickField(row, exactKeys = [], fuzzyParts = [], fallback = "") {
  // 1) exact keys
  for (const key of exactKeys) {
    if (row[key] !== undefined && row[key] !== null && row[key] !== "") {
      return row[key];
    }
  }

  // 2) fuzzy key name match (e.g. "micro_rationale_long")
  const lowerParts = fuzzyParts.map((s) => s.toLowerCase());
  for (const [k, v] of Object.entries(row)) {
    if (v === null || v === undefined || v === "") continue;
    const lk = k.toLowerCase();
    if (lowerParts.some((p) => lk.includes(p))) {
      return v;
    }
  }

  return fallback;
}

document.addEventListener("DOMContentLoaded", () => {
  // Default date = today (UTC)
  document.getElementById("dateInput").value = toISODateInput(new Date());

  // Try to auto-fill client TZ if browser knows it
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (tz && !document.getElementById("clientTzInput").value) {
      document.getElementById("clientTzInput").value = tz;
    }
  } catch (_) {
    // ignore
  }

  document.getElementById("loadBtn").addEventListener("click", loadNakshatra);
  loadNakshatra();
});

// --- main loader ---------------------------------------------------

async function loadNakshatra() {
  const date = document.getElementById("dateInput").value;
  const session = document.getElementById("sessionSelect").value;
  const tf = document.getElementById("tfSelect").value;
  const clientTz = document.getElementById("clientTzInput").value || "";

  const status = document.getElementById("status");
  const statusLabel = status.querySelector(".label");
  const statusGlyph = status.querySelector(".glyph");
  const tbody = document.getElementById("nakBody");
  const summaryRow = document.getElementById("summaryRow");

  // Reset UI
  status.classList.remove("ok", "error");
  statusGlyph.textContent = "⌛";
  statusLabel.textContent = "Loading nakshatra rationale…";
  tbody.innerHTML = "";
  summaryRow.innerHTML = "";

  try {
    if (!date) {
      throw new Error("Please select a valid date.");
    }

    const url =
      `/api/reports/${date}` +
      `?session=${encodeURIComponent(session)}` +
      `&client_tz=${encodeURIComponent(clientTz)}` +
      `&timeframe=${encodeURIComponent(tf)}`;

    const res = await fetch(url);
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text.slice(0, 200)}`);
    }

    const data = await res.json();
    if (!data || !data.sessions) {
      throw new Error("No session data returned from API.");
    }

    buildNakshatraRows(data, tf);
    buildSummary(data, tf);

    const totalRows = Object.values(data.sessions).reduce(
      (acc, rows) => acc + (Array.isArray(rows) ? rows.length : 0),
      0
    );

    const utcNow = new Date().toISOString();
    const clientNow = new Date().toLocaleString();

    statusLabel.textContent =
      `[OK] ${data.date} • TF=${tf} • ` +
      `UTC ${utcNow} • CLIENT ${clientNow} • ROWS ${totalRows}`;
    statusGlyph.textContent = "✅";
    status.classList.add("ok");

    const csvUrl =
      `/api/reports/${date}/csv` +
      `?session=${encodeURIComponent(session)}` +
      `&client_tz=${encodeURIComponent(clientTz)}` +
      `&timeframe=${encodeURIComponent(tf)}`;
    document.getElementById("downloadCsv").href = csvUrl;
  } catch (err) {
    console.error("loadNakshatra error:", err);
    statusLabel.textContent = `[ERR] ${err.message}`;
    statusGlyph.textContent = "⚠";
    status.classList.add("error");
  }
}

// --- table rows ----------------------------------------------------

function buildNakshatraRows(data, timeframe) {
  const tbody = document.getElementById("nakBody");
  tbody.innerHTML = "";

  let loggedExample = false;

  for (const [sessKey, rows] of Object.entries(data.sessions || {})) {
    for (const row of rows) {
      if (!loggedExample) {
        console.log("Example nakshatra row from API:", row);
        loggedExample = true;
      }

      const tr = document.createElement("tr");

      const nakName = pickField(
        row,
        ["nakshatra_name", "nakshatra"],
        ["nakshatra", "nak", "star"]
      );

      const pada = pickField(
        row,
        ["nakshatra_pada"],
        ["pada"]
      );

      const ruler = pickField(
        row,
        ["nakshatra_ruler", "ruler"],
        ["ruler", "lord"]
      );

      const quality = pickField(
        row,
        ["nakshatra_quality"],
        ["quality", "guna", "nature"]
      );

      const rationale = pickField(
        row,
        ["nakshatra_rationale"],
        ["micro", "rationale", "comment", "note", "explanation"]
      );

      const biasRaw = pickField(
        row,
        ["nakshatra_bias"],
        ["bias", "direction"]
      );

      const scoreRaw = pickField(
        row,
        ["nakshatra_score", "nakshatra_bullish_score"],
        ["score"],
        0
      );
      const scoreVal = parseFloat(scoreRaw);

      const keyPlanet = pickField(
        row,
        ["key_planet", "key_planetary_trigger"],
        ["planet"]
      );

      const clientTime = pickField(
        row,
        ["time_client"],
        ["client_time", "local_time", "time_client"]
      );

      const utcTime = pickField(
        row,
        ["time_utc"],
        ["utc_time"]
      );

      // --- visual classes -----------------------------------------

      const biasLower = String(biasRaw || "").toLowerCase();
      let biasClass = "";
      if (biasLower.includes("bull")) biasClass = "bias-bull";
      if (biasLower.includes("bear")) biasClass = "bias-bear";
      if (biasLower.includes("strong")) biasClass += " bias-strong";

      const qualityLower = String(quality || "").toLowerCase();
      let qualClass = "";
      if (qualityLower.includes("soft") || qualityLower.includes("mridu")) {
        qualClass = "qual-soft";
      } else if (qualityLower.includes("sharp") || qualityLower.includes("tikshna")) {
        qualClass = "qual-sharp";
      }

      const scoreClass =
        Number.isFinite(scoreVal) && scoreVal >= 8 ? "nak-score-strong" : "";

      // --- row HTML ------------------------------------------------

      tr.innerHTML = `
        <td>${utcTime || "\u2013"}</td>
        <td>${clientTime || "\u2013"}</td>
        <td>${sessKey.toUpperCase()}</td>
        <td>${row.timeframe || timeframe}</td>
        <td>${nakName || "\u2013"}</td>
        <td>${pada || "\u2013"}</td>
        <td>${ruler || "\u2013"}</td>
        <td class="${qualClass}">${quality || "\u2013"}</td>
        <td class="${biasClass}">${biasRaw || "\u2013"}</td>
        <td class="${scoreClass}">
          ${Number.isFinite(scoreVal) ? scoreVal.toFixed(2) : "\u2013"}
        </td>
        <td>${keyPlanet || "\u2013"}</td>
        <td class="rationale-cell">${rationale || "\u2013"}</td>
      `;

      tbody.appendChild(tr);
    }
  }
}

// --- summary row ---------------------------------------------------

function buildSummary(data, timeframe) {
  const summaryRow = document.getElementById("summaryRow");
  summaryRow.innerHTML = "";

  const stats = {};

  for (const [sessKey, rows] of Object.entries(data.sessions || {})) {
    if (!stats[sessKey]) {
      stats[sessKey] = { bull: 0, bear: 0, neutral: 0, strong: 0, total: 0 };
    }
    for (const row of rows) {
      const biasRaw = pickField(
        row,
        ["nakshatra_bias"],
        ["bias", "direction"]
      );
      const bias = String(biasRaw || "").toLowerCase();
      stats[sessKey].total++;

      if (!bias) {
        stats[sessKey].neutral++;
      } else if (bias.includes("bull")) {
        stats[sessKey].bull++;
      } else if (bias.includes("bear")) {
        stats[sessKey].bear++;
      } else {
        stats[sessKey].neutral++;
      }

      if (bias.includes("strong")) {
        stats[sessKey].strong++;
      }
    }
  }

  const sessions = Object.keys(stats);
  if (!sessions.length) {
    const pill = document.createElement("span");
    pill.className = "summary-pill";
    pill.textContent = "No rows for selected filters.";
    summaryRow.appendChild(pill);
    return;
  }

  for (const [sess, s] of Object.entries(stats)) {
    const pill = document.createElement("span");
    pill.className = "summary-pill";
    pill.textContent =
      `${sess.toUpperCase()} · TF=${timeframe} · ` +
      `Bull:${s.bull} · Bear:${s.bear} · Neutral:${s.neutral} · ` +
      `Strong tags:${s.strong} · n=${s.total}`;
    summaryRow.appendChild(pill);
  }
}

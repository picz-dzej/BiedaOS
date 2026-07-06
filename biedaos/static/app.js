const $ = (sel) => document.querySelector(sel);
const state = { month: new Date().toISOString().slice(0, 7), categories: [], charts: {} };
const PALETTE = ["#A64B2A", "#8A6B4F", "#4A6B4A", "#5B4A6B", "#B08A3E",
                 "#6B4A4A", "#3E6B8A", "#7A7A52", "#9C5B70", "#4F6B5E", "#807566"];

async function api(path, opts = {}) {
  const res = await fetch("/api" + path, { headers: { "Content-Type": "application/json" }, ...opts });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Błąd " + res.status);
  }
  return res.json();
}

const zl = (g) => (g / 100).toLocaleString("pl-PL", { style: "currency", currency: "PLN" });

function monthLabel(month) {
  const [y, m] = month.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString("pl-PL", { month: "long", year: "numeric" });
}

function shiftMonth(month, delta) {
  const [y, m] = month.split("-").map(Number);
  const d = new Date(y, m - 1 + delta, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

async function load() {
  const [data, cats, trend] = await Promise.all([
    api("/months/" + state.month), api("/categories"), api("/trend"),
  ]);
  state.categories = cats;
  $("#month-label").textContent = monthLabel(state.month);
  renderSummary(data);
  renderRecs(data.recommendations);
  renderTransactions(data.transactions);
  renderDonut(data);
  renderTrend(trend);
}

function renderSummary(d) {
  $("#sum-income").textContent = zl(d.income);
  $("#sum-expenses").textContent = zl(d.expenses);
  const bal = $("#sum-balance");
  bal.textContent = zl(d.balance);
  bal.className = d.balance < 0 ? "negative" : "positive";
}

function renderRecs(recs) {
  $("#recs").innerHTML = "";
  for (const r of recs) {
    const li = document.createElement("li");
    li.textContent = r;
    $("#recs").appendChild(li);
  }
  if (!recs.length) $("#recs").innerHTML = "<li>Brak danych w tym miesiącu.</li>";
}

function renderTransactions(txs) {
  const tbody = $("#tx-table tbody");
  tbody.innerHTML = "";
  for (const t of txs) {
    const tr = document.createElement("tr");
    tr.className = t.type;
    const cat = document.createElement("td");
    if (t.type === "expense") {
      const sel = document.createElement("select");
      for (const c of state.categories) {
        const o = document.createElement("option");
        o.value = c.id; o.textContent = c.name;
        if (c.id === t.category_id) o.selected = true;
        sel.appendChild(o);
      }
      sel.onchange = async () => {
        await api(`/transactions/${t.id}`, { method: "PATCH", body: JSON.stringify({ category_id: Number(sel.value) }) });
        load();
      };
      cat.appendChild(sel);
    } else {
      cat.textContent = "przychód";
    }
    const del = document.createElement("button");
    del.className = "del"; del.textContent = "✕";
    del.onclick = async () => {
      if (!confirm("Usunąć wpis „" + t.description + ""?")) return;
      await api(`/transactions/${t.id}`, { method: "DELETE" });
      load();
    };
    const cells = [t.date, t.description || "—"];
    for (const c of cells) {
      const td = document.createElement("td");
      td.textContent = c;
      tr.appendChild(td);
    }
    tr.appendChild(cat);
    const amount = document.createElement("td");
    amount.className = "num";
    amount.textContent = (t.type === "income" ? "+" : "−") + zl(t.amount_grosze);
    tr.appendChild(amount);
    const delTd = document.createElement("td");
    delTd.appendChild(del);
    tr.appendChild(delTd);
    tbody.appendChild(tr);
  }
}

function upsertChart(key, canvasId, config) {
  if (state.charts[key]) state.charts[key].destroy();
  state.charts[key] = new Chart($(canvasId), config);
}

function renderDonut(d) {
  const labels = Object.keys(d.by_category);
  const values = Object.values(d.by_category);
  const base = d.income > 0 ? d.income : d.expenses;
  const colors = labels.map((_, i) => PALETTE[i % PALETTE.length]);
  if (d.income > 0 && d.balance > 0) {
    labels.push("zostaje"); values.push(d.balance); colors.push("#D9CDB8");
  }
  upsertChart("donut", "#donut", {
    type: "doughnut",
    data: { labels, datasets: [{ data: values, backgroundColor: colors, borderColor: "#F4EDE0" }] },
    options: {
      plugins: {
        legend: { position: "right" },
        tooltip: { callbacks: { label: (ctx) =>
          ` ${ctx.label}: ${zl(ctx.parsed)} (${base ? (ctx.parsed / base * 100).toFixed(1) : 0}% przychodu)` } },
      },
    },
  });
}

function renderTrend(trend) {
  upsertChart("trend", "#trend", {
    type: "bar",
    data: {
      labels: trend.map((t) => t.month),
      datasets: [
        { label: "przychody", data: trend.map((t) => t.income / 100), backgroundColor: "#4A6B4A" },
        { label: "wydatki", data: trend.map((t) => t.expenses / 100), backgroundColor: "#A64B2A" },
      ],
    },
    options: { scales: { y: { beginAtZero: true } } },
  });
}

async function refreshOllamaBadge() {
  try {
    const s = await api("/ollama/status");
    const badge = $("#ollama-badge");
    badge.textContent = s.available ? `AI: aktywne (${s.model})` : "AI: offline — kategorie ze słownika";
    badge.classList.toggle("on", s.available);
    $("#ollama-model").value = s.model;
  } catch { /* serwer jeszcze wstaje */ }
}

$("#entry-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = $("#entry-text").value.trim();
  if (!text) return;
  const payload = {
    text,
    type: $("#entry-type").checked ? "income" : "expense",
    date: $("#entry-date").value || undefined,
  };
  try {
    await api("/transactions", { method: "POST", body: JSON.stringify(payload) });
    $("#entry-text").value = "";
    $("#entry-error").textContent = "";
    const entryMonth = (payload.date || new Date().toISOString()).slice(0, 7);
    state.month = entryMonth;
    load();
  } catch (err) {
    $("#entry-error").textContent = err.message;
  }
});

$("#prev-month").onclick = () => { state.month = shiftMonth(state.month, -1); load(); };
$("#next-month").onclick = () => { state.month = shiftMonth(state.month, 1); load(); };

$("#add-category").onclick = async () => {
  const name = $("#new-category").value.trim();
  if (!name) return;
  try {
    await api("/categories", { method: "POST", body: JSON.stringify({ name }) });
    $("#new-category").value = "";
    load();
  } catch (err) { alert(err.message); }
};

$("#save-model").onclick = async () => {
  await api("/settings", { method: "PUT", body: JSON.stringify({ ollama_model: $("#ollama-model").value.trim() }) });
  refreshOllamaBadge();
};

$("#entry-date").value = new Date().toISOString().slice(0, 10);
load();
refreshOllamaBadge();

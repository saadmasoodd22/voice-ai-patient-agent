const api = "";
const charts = {};
const phoneLabel = document.getElementById("phone-label");
phoneLabel.textContent = "Call +1 (860) 410-8127";

function qs(id) {
  return document.getElementById(id);
}

async function fetchEnvelope(path, options) {
  const res = await fetch(`${api}${path}`, {
    headers: { "Content-Type": "application/json", ...(options && options.headers) },
    ...options,
  });
  const body = await res.json();
  if (!res.ok || body.error) {
    throw new Error((body.error && body.error.message) || `Request failed (${res.status})`);
  }
  return body.data;
}

function setView(name) {
  document.querySelectorAll(".view").forEach((el) => el.classList.add("hidden"));
  qs(`view-${name}`).classList.remove("hidden");
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === name);
  });
  const titles = {
    overview: ["Registration overview", "Live counts and charts from MySQL."],
    patients: ["Patient registry", "Search uses the same filters as GET /patients."],
    calls: ["Call activity", "Transcripts stored after each Vapi call."],
  };
  qs("page-title").textContent = titles[name][0];
  qs("page-subtitle").textContent = titles[name][1];
}

function palette(n) {
  const colors = ["#3ee0c1", "#7aa7ff", "#f4c15d", "#ff7b8a", "#c084fc", "#67e8f9", "#86efac", "#fda4af"];
  return Array.from({ length: n }, (_, i) => colors[i % colors.length]);
}

function drawChart(id, type, labels, values, extra = {}) {
  const ctx = qs(id);
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart(ctx, {
    type,
    data: {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: type === "line" ? "rgba(62, 224, 193, 0.18)" : palette(values.length),
          borderColor: type === "line" ? "#3ee0c1" : palette(values.length),
          fill: type === "line",
          tension: 0.35,
          borderWidth: type === "line" ? 2 : 0,
          borderRadius: 8,
        },
      ],
    },
    options: {
      plugins: { legend: { display: type === "doughnut" } },
      scales: type === "doughnut" ? {} : { x: { ticks: { color: "#93b3c1" } }, y: { ticks: { color: "#93b3c1" }, beginAtZero: true } },
      ...extra,
    },
  });
}

async function loadOverview() {
  const stats = await fetchEnvelope("/stats");
  const k = stats.kpis;
  qs("kpis").innerHTML = [
    ["Total patients", k.total_patients],
    ["New this week", k.new_this_week],
    ["With insurance", k.with_insurance],
    ["Emergency contact", k.with_emergency_contact],
  ]
    .map(([label, value]) => `<div class="kpi"><span>${label}</span><b>${value}</b></div>`)
    .join("");

  drawChart(
    "chart-trend",
    "line",
    stats.registrations.map((r) => r.label.slice(5)),
    stats.registrations.map((r) => r.value)
  );
  drawChart(
    "chart-state",
    "bar",
    stats.by_state.map((r) => r.label),
    stats.by_state.map((r) => r.value)
  );
  drawChart(
    "chart-sex",
    "doughnut",
    stats.by_sex.map((r) => r.label),
    stats.by_sex.map((r) => r.value)
  );
  drawChart(
    "chart-insurance",
    "bar",
    stats.by_insurance.map((r) => r.label),
    stats.by_insurance.map((r) => r.value)
  );
  drawChart(
    "chart-language",
    "doughnut",
    stats.by_language.map((r) => r.label),
    stats.by_language.map((r) => r.value)
  );
  renderCalls(stats.recent_calls || []);
}

function renderCalls(rows) {
  if (!rows.length) return;
  qs("call-rows").innerHTML = rows
    .map(
      (row) =>
        `<div class="call-item"><strong>${row.caller_number || "Unknown caller"}</strong><div>${row.outcome} · ${row.created_at || ""}</div></div>`
    )
    .join("");
}

async function loadPatients() {
  const params = new URLSearchParams();
  const last = qs("q-last").value.trim();
  const dob = qs("q-dob").value.trim();
  const phone = qs("q-phone").value.trim();
  if (last) params.set("last_name", last);
  if (dob) params.set("date_of_birth", dob);
  if (phone) params.set("phone_number", phone);
  const qsPath = params.toString() ? `/patients?${params}` : "/patients";
  const rows = await fetchEnvelope(qsPath);
  const body = qs("patient-rows");
  if (!rows.length) {
    body.innerHTML = `<tr><td colspan="7">No patients match those filters.</td></tr>`;
    return;
  }
  body.innerHTML = rows
    .map(
      (p) => `<tr>
        <td>${p.first_name} ${p.last_name}</td>
        <td>${p.date_of_birth_display}</td>
        <td>${p.sex}</td>
        <td>${p.phone_display}</td>
        <td>${p.city}, ${p.state}</td>
        <td>${p.insurance_provider || "—"}</td>
        <td><button class="linkish" data-id="${p.patient_id}">View</button></td>
      </tr>`
    )
    .join("");
  body.querySelectorAll("button[data-id]").forEach((btn) => {
    btn.addEventListener("click", () => openPatient(btn.dataset.id));
  });
}

async function openPatient(id) {
  const p = await fetchEnvelope(`/patients/${id}`);
  qs("drawer").classList.remove("hidden");
  qs("drawer-body").innerHTML = `
    <h2>${p.first_name} ${p.last_name}</h2>
    <p>${p.patient_id}</p>
    <div class="kv">
      <span>DOB</span><div>${p.date_of_birth_display}</div>
      <span>Sex</span><div>${p.sex}</div>
      <span>Phone</span><div>${p.phone_display}</div>
      <span>Email</span><div>${p.email || "—"}</div>
      <span>Address</span><div>${p.address_line_1}${p.address_line_2 ? ", " + p.address_line_2 : ""}</div>
      <span>City / State</span><div>${p.city}, ${p.state} ${p.zip_code}</div>
      <span>Insurance</span><div>${p.insurance_provider || "—"} ${p.insurance_member_id || ""}</div>
      <span>Language</span><div>${p.preferred_language}</div>
      <span>Emergency</span><div>${p.emergency_contact_name || "—"} ${p.emergency_contact_phone_display || ""}</div>
    </div>
    <div class="modal-actions">
      <button class="ghost" id="soft-delete">Soft delete</button>
    </div>`;
  qs("soft-delete").onclick = async () => {
    if (!confirm("Soft-delete this patient? The row is kept with deleted_at set.")) return;
    await fetchEnvelope(`/patients/${id}`, { method: "DELETE" });
    qs("drawer").classList.add("hidden");
    await loadPatients();
    await loadOverview();
  };
}

function emptyToNull(value) {
  const trimmed = (value || "").trim();
  return trimmed === "" ? null : trimmed;
}

qs("patient-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const payload = Object.fromEntries(form.entries());
  ["email", "address_line_2", "insurance_provider", "insurance_member_id", "emergency_contact_name", "emergency_contact_phone"].forEach(
    (key) => {
      payload[key] = emptyToNull(payload[key]);
    }
  );
  qs("form-error").textContent = "";
  try {
    await fetchEnvelope("/patients", { method: "POST", body: JSON.stringify(payload) });
    qs("modal").classList.add("hidden");
    event.target.reset();
    await loadPatients();
    await loadOverview();
    setView("patients");
  } catch (err) {
    qs("form-error").textContent = err.message;
  }
});

document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => setView(btn.dataset.view));
});
qs("add-btn").onclick = () => qs("modal").classList.remove("hidden");
qs("cancel-add").onclick = () => qs("modal").classList.add("hidden");
qs("close-drawer").onclick = () => qs("drawer").classList.add("hidden");
qs("search-btn").onclick = () => loadPatients();
qs("reset-btn").onclick = () => {
  qs("q-last").value = "";
  qs("q-dob").value = "";
  qs("q-phone").value = "";
  loadPatients();
};

function formatUsPhone(value) {
  const digits = (value || "").replace(/\D/g, "");
  const ten = digits.length === 11 && digits.startsWith("1") ? digits.slice(1) : digits;
  if (ten.length === 10) return `Call +1 (${ten.slice(0, 3)}) ${ten.slice(3, 6)}-${ten.slice(6)}`;
  return value ? `Call ${value}` : "US line pending";
}

async function boot() {
  try {
    await fetchEnvelope("/health");
    qs("api-status").textContent = "API connected";
    try {
      const info = await fetchEnvelope("/meta");
      phoneLabel.textContent = formatUsPhone(info.phone_number);
    } catch (_err) {
      phoneLabel.textContent = "Call +1 (860) 410-8127";
    }
    await loadOverview();
    await loadPatients();
  } catch (err) {
    qs("api-status").textContent = "API offline";
    qs("api-status").classList.add("bad");
  }
}

boot();

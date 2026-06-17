// Module 4 — frontend logic. Fetches from the API and renders the result.
// Deliberately holds NO growing logic: every decision is made server-side
// (Modules 1–3) and only displayed here. All text is written with textContent,
// so values from the API can never inject HTML. The I18N object below holds the
// static UI strings for both languages; the advice content itself is translated
// server-side and arrives already localized via the ?lang= query parameter.

const I18N = {
  en: {
    tagline: "Organic tomato growing advice for your backyard — pick your region and sowing date.",
    regionLabel: "Your region",
    sowingLabel: "Sowing date",
    todayLabel: "Pretend today is",
    todayHint: "(optional — for trying different stages)",
    submit: "Get advice",
    choose: "Choose your region…",
    whenToStart: "When to start",
    sowBetween: (e, l) => `Sow indoors between ${e} and ${l}.`,
    transplantAround: (d) => `Transplant outdoors around ${d}, after your last frost.`,
    rightNow: (label) => `Right now: ${label}`,
    daySince: (n) => `Day ${n} since sowing`,
    watering: "💧 Watering",
    wateringLine: (n, note) => `About ${n}× per week. ${note}`,
    care: "🌱 Care tasks now",
    timeline: "Your season timeline",
    notStartedHead: "Not sown yet",
    notStartedBody: "Your sowing date hasn't arrived. Follow the plan below when it does.",
    frostLine: (last, first) => `Average frost — last: ${last} · first: ${first}`,
    errGeneric: "Something went wrong.",
    errNetwork: "Could not reach the server. Is it still running?",
    errRegions: "Could not load the region list.",
  },
  bg: {
    tagline: "Съвети за биологично отглеждане на домати у дома — изберете регион и дата на сеитба.",
    regionLabel: "Вашият регион",
    sowingLabel: "Дата на сеитба",
    todayLabel: "Приемете, че днес е",
    todayHint: "(по избор — за различни етапи)",
    submit: "Вземи съвет",
    choose: "Изберете регион…",
    whenToStart: "Кога да започнете",
    sowBetween: (e, l) => `Сейте на закрито между ${e} и ${l}.`,
    transplantAround: (d) => `Разсадете навън около ${d}, след последния слан.`,
    rightNow: (label) => `В момента: ${label}`,
    daySince: (n) => `Ден ${n} от сеитбата`,
    watering: "💧 Поливане",
    wateringLine: (n, note) => `Около ${n}× седмично. ${note}`,
    care: "🌱 Задачи за грижа сега",
    timeline: "Вашият сезонен график",
    notStartedHead: "Още не е засято",
    notStartedBody: "Датата на сеитба още не е настъпила. Следвайте плана по-долу, когато настъпи.",
    frostLine: (last, first) => `Среден слан — последен: ${last} · първи: ${first}`,
    errGeneric: "Нещо се обърка.",
    errNetwork: "Сървърът е недостъпен. Работи ли още?",
    errRegions: "Списъкът с региони не можа да се зареди.",
  },
};

let lang = localStorage.getItem("lang") === "bg" ? "bg" : "en";
const t = () => I18N[lang];

const form = document.getElementById("advice-form");
const regionSelect = document.getElementById("region");
const errorEl = document.getElementById("error");
const results = document.getElementById("results");

// --- tiny DOM helper (rendering only) ---
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
  results.hidden = true;
}

function clearError() {
  errorEl.hidden = true;
  errorEl.textContent = "";
}

// Apply the static UI strings for the current language.
function applyChrome() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const value = t()[node.getAttribute("data-i18n")];
    if (typeof value === "string") node.textContent = value;
  });
  document.querySelectorAll(".lang-btn").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.lang === lang);
  });
}

// Populate the region dropdown from the API (option value = stable key).
async function loadRegions() {
  try {
    const resp = await fetch(`/api/regions?lang=${lang}`);
    if (!resp.ok) throw new Error();
    const regions = await resp.json();
    const previous = regionSelect.value;
    regionSelect.replaceChildren();
    const placeholder = new Option(t().choose, "", !previous, !previous);
    placeholder.disabled = true;
    regionSelect.add(placeholder);
    for (const r of regions) regionSelect.add(new Option(r.name, r.key));
    if (previous) regionSelect.value = previous;
  } catch {
    showError(t().errRegions);
  }
}

function renderRegionNote(region) {
  document.getElementById("region-note").replaceChildren(
    el("h2", null, region.name),
    el("p", null, region.note),
    el("p", "muted", t().frostLine(region.last_frost, region.first_frost))
  );
}

function renderRecommended(rec) {
  document.getElementById("recommended").replaceChildren(
    el("h2", null, t().whenToStart),
    el("p", null, t().sowBetween(rec.sowing_window.earliest, rec.sowing_window.latest)),
    el("p", null, t().transplantAround(rec.transplant_date))
  );
}

function renderCurrent(data) {
  const box = document.getElementById("current");
  box.replaceChildren();

  if (data.not_started) {
    box.append(
      el("h2", null, t().notStartedHead),
      el("p", null, t().notStartedBody)
    );
    return;
  }

  const c = data.current;
  box.append(
    el("h2", null, t().rightNow(c.stage_label)),
    el("p", "muted", t().daySince(c.days_since_sowing)),
    el("p", null, c.stage_description)
  );

  const w = c.watering;
  box.append(
    el("h3", null, t().watering),
    el("p", null, t().wateringLine(w.times_per_week, w.stage_note)),
    el("p", "muted", w.region_note)
  );

  box.append(el("h3", null, t().care));
  const ul = el("ul");
  for (const tip of c.tips) ul.append(el("li", null, tip));
  box.append(ul);
}

function renderTimeline(data) {
  const box = document.getElementById("timeline");
  box.replaceChildren(el("h2", null, t().timeline));
  const currentKey = data.current ? data.current.stage_key : null;

  const list = el("ol", "timeline-list");
  for (const item of data.timeline) {
    const li = el("li", item.stage_key === currentKey ? "is-current" : null);
    li.append(
      el("span", "stage-date", item.start),
      el("span", "stage-name", item.stage_label)
    );
    list.append(li);
  }
  box.append(list);
}

function render(data) {
  renderRegionNote(data.region);
  renderRecommended(data.recommended);
  renderCurrent(data);
  renderTimeline(data);
}

async function requestAdvice() {
  clearError();
  const region = regionSelect.value;
  const planting = document.getElementById("planting-date").value;
  if (!region || !planting) return;

  const params = new URLSearchParams({ region, planting_date: planting, lang });
  const today = document.getElementById("today").value;
  if (today) params.set("today", today);

  try {
    const resp = await fetch(`/api/advice?${params.toString()}`);
    const data = await resp.json();
    if (!resp.ok) {
      showError(data.error || t().errGeneric);
      return;
    }
    render(data);
    results.hidden = false;
  } catch {
    showError(t().errNetwork);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  requestAdvice();
});

document.getElementById("lang-switch").addEventListener("click", (event) => {
  const btn = event.target.closest(".lang-btn");
  if (!btn || btn.dataset.lang === lang) return;
  lang = btn.dataset.lang;
  localStorage.setItem("lang", lang);
  applyChrome();
  const hadResults = !results.hidden;
  loadRegions().then(() => {
    if (hadResults) requestAdvice();
  });
});

applyChrome();
loadRegions();

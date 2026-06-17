# 🍅 Tomato Coach

An **offline web assistant for growing organic tomatoes in a small backyard garden**.
You pick your region and your planting date; the app tells you when to sow and transplant,
what growth stage your plants are in today, when to water, and which organic care task is
due now (including hilling/earthing-up and pruning) — all from a built-in knowledge base,
with no internet connection required.

Built as a small, tested university project for the course *AI-Assisted Development*.

## Stack
- **Python 3.10+**
- **Flask + Jinja2** (backend + single page)
- Vanilla JavaScript front-end (calls a JSON endpoint)
- **pytest** for tests

## Modules
1. **`data`** — knowledge base: regions & frost dates, growth stages, watering rules, organic care tips.
2. **`advisor`** — core logic: pure, deterministic functions that turn region + dates into advice.
3. **`app`** — Flask backend: serves the page and a JSON advice API.
4. **`frontend`** — single-page GUI (`templates/` + `static/`) that calls the API and renders results.

## Status
🚧 Scaffold only — modules are built and tested one at a time. See `evidence-log.md` for the build journal.

## Repository
<!-- GitHub link goes here once published -->
`<add your GitHub repo link here>`

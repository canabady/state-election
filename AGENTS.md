# AGENTS.md

## 1) Purpose
This repository is a **multi-state election data dashboard framework**.

The app must stay generic and data-driven so new states can be added by configuration + data files, without UI rewrites.

Current core behavior:
- State-aware routing (`/:state/...`) with lowercase state codes
- District and AC elector dashboards from CSV
- State switcher menu controlled by `show_in_menu`
- Strict NotFound behavior for invalid state or district paths

---

## 2) Tech Stack
- Vite + React + TypeScript
- TanStack Router
- TanStack Query (router context)
- Tailwind CSS
- PapaParse (CSV parsing)
- Python scripts for data scraping

---

## 3) Project Layout
- `src/routes/` route files (`/$state/data`, `/$state/data/$district`, `/$state/map`)
- `src/services/` state registry/config and CSV loading
- `src/components/common/` shared UI (`NotFound`, `Loader`, `DisclaimerModal`)
- `public/data/states.json` state registry
- `public/data/states/<code>/config.json` per-state config
- `public/data/states/<code>/electors.csv` per-state elector data
- `scripts/` scraping + parser tests per state

---

## 4) Routing Contract
### Required Routes
- `/` -> redirects to first menu-enabled state (`/$state/data`)
- `/:state/data` -> district summary table
- `/:state/data/:district` -> AC table for district
- `/:state/map` -> map placeholder route

### Route Rules
- `:state` uses **lowercase code** from `states.json`
- Non-existent/unconfigured states must throw `notFound()`
- Missing district in `/:state/data/:district` must throw `notFound()`

---

## 5) State Registry Contract (`public/data/states.json`)
Each entry:
```json
{
  "id": 33,
  "code": "TN",
  "name": "Tamil Nadu",
  "show_in_menu": true
}
```

Rules:
- `code` is canonical state route key (normalized to lowercase in app)
- `show_in_menu` controls visibility in header dropdown
- A state can be present but hidden (`show_in_menu: false`)

---

## 6) Per-State Config Contract (`public/data/states/<code>/config.json`)
Example:
```json
{
  "state_id": "tn",
  "state_name": "Tamil Nadu",
  "election_title": "Tamil Nadu State Election Dashboard",
  "election_subtitle": "Assembly Election Analysis",
  "elector_csv_path": "/data/states/tn/electors.csv",
  "district_label": "District",
  "ac_label": "Assembly Constituency",
  "ac_short_label": "AC"
}
```

Validation expectations:
- `state_id` must match folder/code (`tn`, `as`, `wb`, etc.)
- `elector_csv_path` must point to a readable CSV

Without valid config, `stateExists()` returns false and route goes NotFound.

---

## 7) Elector CSV Contract
### App-required columns (minimum)
- `district_name`
- `ac_no`
- `ac_name`
- `male`
- `female`
- `third_gender`
- `total`

### Recommended standard columns
- `district_no` (recommended for stable row keys and ordering)
- `polling_stations` (optional but encouraged if source provides)

Current state files are not fully uniform yet; app tolerates this, but new scrapers should target a stable schema.

---

## 8) Data Flow
1. `fetchStatesRegistry()` loads `states.json`
2. Route param `:state` is normalized by `normalizeStateId()`
3. `stateExists()` checks registry + `config.json`
4. `fetchStateConfig()` resolves labels/title/csv path
5. `fetchElectorCsvRows()` parses CSV with PapaParse
6. Route loaders aggregate/transform for views

Do not fetch raw files directly from components except through service helpers.

---

## 9) UI Behavior Requirements
### Header
- App title + logo
- State selector between title and Data/Map tabs
- Search supports district name, AC name, AC number
- Search navigation opens `/:state/data/:district`

### `/ :state /data`
- District table with sortable headers
- Row checkbox selection in-table
- Select-all checkbox in header
- Summary cards recompute based on selected districts
- If no selection: summary uses all districts

### `/ :state /data/:district`
- AC-wise table
- Sortable headers
- Back link to `/:state/data`

---

## 10) Scraper Standards (`scripts/`)
Each state scraper should include:
- `scripts/scrape_<state>_ac_electors.py`
- `scripts/test_scrape_<state>_ac_electors.py`

### Expectations
- Handle messy source formatting (broken HTML, PDF wraps, split lines)
- Fail loudly with actionable errors when structure changes
- Write CSV into `public/data/states/<code>/electors.csv`
- Keep parsing deterministic and idempotent

### Existing scrapers
- Tamil Nadu HTML scraper
- Puducherry HTML scraper
- Kerala PDF scraper
- Assam PDF scraper (includes polling stations)
- West Bengal PDF scraper (includes polling stations)

---

## 11) Adding a New State (Checklist)
1. Add entry in `public/data/states.json`
2. Set `show_in_menu` as needed
3. Create `public/data/states/<code>/config.json`
4. Add `public/data/states/<code>/electors.csv`
5. Prefer adding scraper + parser test under `scripts/`
6. Verify routes:
   - `/<code>/data`
   - `/<code>/data/<district>`
7. Run checks:
   - `npm run lint`
   - `npm run build`

---

## 12) Developer Commands
- Install: `npm install`
- Dev server: `npm run dev`
- Lint: `npm run lint`
- Build: `npm run build`
- Preview: `npm run preview`

Scraper examples:
- `python3 scripts/scrape_tn_ac_electors.py`
- `python3 scripts/scrape_as_ac_electors.py`
- `python3 scripts/scrape_wb_ac_electors.py`

---

## 13) Guardrails
- Do not hardcode one-state assumptions in routes/components
- Do not bypass `stateExists()` checks
- Keep state route codes lowercase in URLs
- Preserve NotFound behavior for invalid state and district
- Avoid introducing state-specific UI branches

---

## 14) Known Gaps / Next Improvements
- Normalize all existing CSVs to a single canonical schema
- Add map data pipeline (`geojson/topojson`) for `/:state/map`
- Add automated schema validation for state CSV/config files
- Add app-level tests for route guards and search navigation


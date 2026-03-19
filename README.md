# State Election in India

A multi-state, data-driven election dashboard built with React + TanStack Router.

This app is designed to serve election elector summaries for multiple Indian states using state-scoped routes and CSV datasets.

## Features
- State-aware routing (`/:state/...`) using lowercase state codes
- District-wise dashboard with sortable columns
- District drilldown (`/:state/data/:district`) with AC-wise details
- Header search by district name, AC name, and AC number
- State switcher menu controlled by `show_in_menu`
- Strict NotFound handling for invalid states/districts
- Python scrapers for generating state CSV datasets

## Tech Stack
- Vite + React + TypeScript
- TanStack Router + TanStack Query
- Tailwind CSS
- PapaParse for CSV parsing
- Python scripts for data ingestion

## Repository Structure
```text
src/
  routes/
    __root.tsx
    index.tsx
    $state/data/index.tsx
    $state/data/$district.tsx
    $state/map.tsx
  services/
    appConfig.ts
    electors.ts
  components/common/

public/data/
  states.json
  states/<state_code>/
    config.json
    electors.csv

scripts/
  scrape_<state>_ac_electors.py
  test_scrape_<state>_ac_electors.py
```

## State Data Model

### 1) State Registry
`public/data/states.json`

Controls:
- available state codes
- state display names
- `show_in_menu` visibility in header dropdown

### 2) State Config
`public/data/states/<code>/config.json`

Controls:
- `state_id`
- UI labels (`district_label`, `ac_label`, etc.)
- `election_title`, `election_subtitle`
- CSV path (`elector_csv_path`)

### 3) Electors CSV
`public/data/states/<code>/electors.csv`

Common fields used by UI:
- `district_name`
- `ac_no`
- `ac_name`
- `male`
- `female`
- `third_gender`
- `total`

Optional fields supported:
- `district_no`
- `polling_stations`

## Currently Added States
- `tn` (Tamil Nadu)
- `py` (Puducherry)
- `kl` (Kerala)
- `as` (Assam)
- `wb` (West Bengal)

Menu visibility is controlled by `show_in_menu` in `public/data/states.json`.

## How to Run the Repo

## Prerequisites
- Node.js 20+
- npm 10+
- Python 3.10+
- `pdftotext` (required for PDF-based scrapers)
- `curl` (used by some scrapers)

## Install Dependencies
```bash
npm install
```

## Start Development Server
```bash
npm run dev
```

Open the app at the local URL printed by Vite (usually `http://localhost:5173`).

## Build for Production
```bash
npm run build
```

## Preview Production Build
```bash
npm run preview
```

## Lint
```bash
npm run lint
```

## Route Examples
- `/tn/data`
- `/kl/data`
- `/as/data`
- `/wb/data`
- `/wb/data/COOCHBEHAR` (district drilldown example)

## Add a New State
1. Add entry in `public/data/states.json`
2. Set `show_in_menu` as needed
3. Create `public/data/states/<code>/config.json`
4. Generate/add `public/data/states/<code>/electors.csv`
5. Verify:
   - `/<code>/data`
   - `/<code>/data/<district>`
6. Run:
   - `npm run lint`
   - `npm run build`

## Troubleshooting
- State opens NotFound:
  - Check state `code` in `states.json`
  - Ensure `public/data/states/<code>/config.json` exists and `state_id` matches code
  - Ensure `elector_csv_path` points to existing CSV

- District route opens NotFound:
  - District name in URL must exist in that state CSV

- Scraper fails on PDF:
  - Ensure `pdftotext` is installed and available in PATH

## License
MIT License

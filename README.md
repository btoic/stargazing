# 🔭 Stargazing — Astronomical Observation Planning & Field Guides

An automated astronomical observation planning system and field guide compiler designed for amateur astronomers, visual observers, and Dobsonian telescope users.

The toolkit computes exact solar/lunar ephemerides, curates high-impact observing programs based on observer skill and local horizon limits, and builds toner-saver negative finder charts and screen-optimized e-reader field books (**EPUB**) for red-light night viewing on E-Ink devices (like PocketBook Era, Kobo, Boox, and Kindle).

---

## 🌟 Key Features

- 🌓 **Precise Celestial Ephemerides**: Calculates sunset, civil, nautical, and astronomical twilight windows, lunar phases, moonrise/moonset, and target transit altitudes using `astropy` and `skyfield`.
- 📱 **PocketBook Era & E-Reader Optimized EPUB**:
  - Calibrated for 7.0" E-Ink Carta 1200 screens at **12px font zoom**.
  - **Natural 4-Page Target Pagination** (zero blank pages, no artificial sub-chapters):
    1. **Page 1**: Side-by-side Eyepiece Simulation (pre-inverted 180° for Newtonian reflectors) & Target Technical Dossier.
    2. **Page 2**: Constellation Context Orientation Chart (~50°–65° naked-eye field, stars to mag 6.5, with next-page finder viewport bounding box).
    3. **Page 3**: Wide-Field Star-Hopping Chart (stars to visual mag 8.5, concentric Telrad reticles, step badges, magnitude key).
    4. **Page 4**: Reflowable text-based star-hopping guide with direct bottom navigation to the next target.
  - Automatic Calibre & EPUB 3 series indexing (`Stargazing Observations #N`).
- ⚡ **Shared Asset Caching (`shared/`)**:
  - Reusable chart assets are cached across sessions in `shared/<object_slug>/`.
  - Date- and site-specific ephemeris is decoupled from graphics into text guides, making context and eyepiece graphics 100% reusable.
  - Subsequent session builds hit the cache in **~8 seconds**.
- 📄 **On-Demand Printable A4 PDFs**:
  - **Master Plan Guide (`STARGAZING_PLAN.pdf`)**: Formatted strictly as a 2-page document for 1 single double-sided A4 sheet.
  - **All-Sky Planisphere (`full_sky_map.pdf`)**: Strict 1:1 circular aspect ratio with clean `N`, `S`, `E`, `W` orientation.
  - **A4 Landscape Finder Charts (`charts/chart_<N>_*.pdf`)**: High-resolution negative toner-saver charts.
- 🎯 **Target Budgeting & Clustering**:
  - Interview-calibrated target lists matched to find-time skill levels.
  - Spatial neighbor clustering (e.g. M56 near M57, M71 near M27, M103 near Double Cluster).
  - Reproducible plain-text target manifests (`targets.md`).

---

## 🚀 Quickstart Guide

### 1. Installation

Python 3.10+ is recommended. Install required astronomical and rendering libraries:

```bash
pip install -r requirements.txt
```

Key libraries used:
- `astropy` & `skyfield`: High-precision celestial ephemerides and coordinate transformations.
- `matplotlib`: Chart rendering, Telrad reticle drawing, and toner-saver inverted projections.
- `reportlab` & `pypdfium2`: Standard A4 PDF compilation and verification.

### 2. Running the Complete Planning Pipeline

Run the end-to-end observation planner for an observing site and date:

```bash
python3 scripts/run_observation_planner.py \
  --location dvigrad \
  --equipment skywatcher-skyliner-200p \
  --date 2026-09-12
```

By default, this generates:
1. `observations/<session>/targets.md` (Target manifest)
2. `observations/<session>/STARGAZING_PLAN.md` (Master markdown plan)
3. `observations/<session>/full_sky_map.png` (Planisphere)
4. `observations/<session>/charts/*.png` (Master finder charts, leveraging `shared/` cache)
5. `observations/<session>/<session>.epub` (Standalone PocketBook Era field book)

### 3. Compiling On-Demand Printable PDFs

To include print-ready A4 PDFs (`STARGAZING_PLAN.pdf`, `full_sky_map.pdf`, and `charts/*.pdf`), add the `--pdf` flag:

```bash
python3 scripts/run_observation_planner.py \
  --location dvigrad \
  --equipment skywatcher-skyliner-200p \
  --date 2026-09-12 \
  --pdf
```

### 4. Running Pipeline Components Individually

You can also run or re-run individual stages:

- **Generate charts only**:
  ```bash
  python3 scripts/generate_charts.py --output-dir observations/dvigrad-2026-09-12
  ```
- **Force re-render cached shared assets**:
  ```bash
  python3 scripts/generate_charts.py --output-dir observations/dvigrad-2026-09-12 --force
  ```
- **Compile E-Reader EPUB only**:
  ```bash
  python3 scripts/build_session_epub.py --session-dir observations/dvigrad-2026-09-12
  ```
- **Compile Master Plan 2-page PDF only**:
  ```bash
  python3 scripts/build_plan_pdf.py --output-dir observations/dvigrad-2026-09-12
  ```

---

## 🤖 Using with LLM Coding Agents

This repository is optimized for autonomous or pair-programming with LLM coding agents (such as **Antigravity CLI**, **Claude Code**, or **Cursor**).

### Agent Skills & Instruction Architecture

- **`AGENTS.md`**: Contains workspace invariants, directory conventions, and execution rules that agents follow across sessions.
- **`.agents/skills/stargazing-planner/`**: A self-contained agent skill providing step-by-step instructions for ephemeris calculations, target curation, difficulty rating calibration, and asset packaging.

### Example Prompts for Agents

#### 1. Plan a New Observation Session
> *"Plan a stargazing session for September 15, 2026 at Dvigrad using my Sky-Watcher 200P Dobsonian. I am an intermediate observer and usually take around 15 minutes to find an object. Generate the markdown plan and e-reader EPUB."*

The agent will:
1. Load `locations/dvigrad.md` and `equipment/skywatcher-skyliner-200p.md`.
2. Calibrate target volume based on your find-time (6–8 primary anchors + 3–6 bonus neighbors).
3. Compute the darkness window and transit times.
4. Save `targets.md`.
5. Check `shared/` for cached charts (reusing existing assets instantly).
6. Render the planisphere and missing targets.
7. Compile `<session>.epub` and `STARGAZING_PLAN.md`.

#### 2. Add a New Observing Site
> *"I am planning a trip to Tićan Observatory (Višnjan). Can you research its coordinates, Bortle class, and horizon profile, create a location profile in locations/tican.md, and plan a stargazing session for tomorrow night?"*

The agent will:
1. Research the geographic coordinates (45.29° N, 13.75° E, ~250m elevation, Bortle 4).
2. Create `locations/tican.md`.
3. Calculate local solar/lunar twilights and transit altitudes.
4. Generate the full session package in `observations/tican-<date>/`.

#### 3. Register New Optical Equipment
> *"I bought a Celestron Omni XLT 150 (150/750mm f/5 reflector) with 25mm and 9mm eyepieces. Create an equipment profile in equipment/celestron-omni-150.md with magnifications, exit pupils, and field of views."*

#### 4. Regenerate Deliverables from Manifest
> *"Update the target manifest in observations/dvigrad-2026-09-12/targets.md to replace M11 with M22, then rebuild the charts and EPUB."*

---

## 📖 Field Craft & Tutorial Library

- 🔧 **[Dobsonian Mirror Collimation Guide](tutorials/dobsonian-mirror-collimation.md)**: Illustrated 3-step collimation protocol for Newtonian reflectors, safety practices, and star test diffraction analysis.
- ⏱️ **[Session Target Budgeting & Star-Hopping](tutorials/session-target-budgeting-and-hopping.md)**: Dwell-time math, eyepiece progression, and spatial neighbor hopping strategies.
- 🧭 **[Star-Hopping Fundamentals](tutorials/star-hopping-fundamentals.md)**: Finder scope vs. naked-eye orientation, Telrad reticle geometry, and field alignment.
- 🌌 **[Astronomical Darkness & Ephemeris Guide](tutorials/astronomical-darkness-and-ephemeris.md)**: Civil, nautical, and astronomical twilight definitions, lunar phase interference, and airmass limits.
- 🛡️ **[Dobsonian Field Craft & Night Logistics](tutorials/dobsonian-field-craft.md)**: Thermal acclimation, dew management, red-light etiquette, and dark adaptation.

---

## 📂 Repository Layout

```text
├── README.md                   # Repository overview, quickstart & LLM guide
├── AGENTS.md                   # Core invariants & operational rules for AI coding agents
├── requirements.txt            # Python dependencies
├── locations/
│   └── dvigrad.md              # Observing site profiles (coordinates, Bortle, obstruction)
├── equipment/
│   ├── skywatcher-skyliner-200p.md # Telescope optical profiles (aperture, FL, eyepieces)
│   └── pocketbook-era.md       # E-reader display hardware specifications
├── catalogs/
│   ├── messier_catalog.json    # Complete 110 Messier objects catalog with coordinates, optics & Swanson ratings
│   └── messier_difficulty_ratings.md # Swanson Messier difficulty reference catalog
├── shared/                     # Universal cross-session reusable charts cache (All 110 Messier objects!)
│   └── m<N>/                   # m1 through m110 pre-rendered assets
│       ├── context.png         # Naked-eye constellation orientation chart (mag <= 6.5)
│       ├── widefield_<equip>.png # Wide-field star hop chart (mag <= 8.5)
│       ├── eyepiece_dossier_<equip>.png # Eyepiece simulation & dossier graphic
│       └── chart_<equip>.png   # Full A4 master finder chart (and .pdf)
├── observations/
│   └── <location>-<YYYY-MM-DD>/# Observation session packages (e.g. dvigrad-2026-09-12)
│       ├── targets.md          # Plain text target manifest for fast regeneration
│       ├── STARGAZING_PLAN.md  # Complete observation guide (Primary deliverable)
│       ├── <location>-<date>.epub # Standalone E-Reader Field Book (Primary deliverable)
│       ├── full_sky_map.png    # High-resolution planisphere image
│       ├── charts/             # Session master finder charts (PNG + optional PDF)
│       │   ├── chart_1_lyra_m57.png
│       │   └── ...
│       ├── STARGAZING_PLAN.pdf # Print-optimized 2-page Master Plan (On-demand via --pdf)
│       └── full_sky_map.pdf    # All-sky planisphere vector PDF (On-demand via --pdf)
├── tutorials/                  # Standalone astronomy guides, field craft & optical tutorials
│   ├── dobsonian-mirror-collimation.md
│   ├── session-target-budgeting-and-hopping.md
│   ├── star-hopping-fundamentals.md
│   ├── dobsonian-field-craft.md
│   └── astronomical-darkness-and-ephemeris.md
├── .agents/skills/
│   └── stargazing-planner/     # Automated planning skill for AI coding agents
└── scripts/
    ├── build_messier_catalog.py # Compiles unified 110 Messier astronomical dataset
    ├── generate_all_messier_shared.py # Parallel batch pre-renderer for all 110 Messier shared assets
    ├── calculate_ephemeris.py  # Solar/lunar twilight and target visibility calculator
    ├── generate_charts.py      # Planisphere & finder chart generator with shared caching
    ├── build_plan_pdf.py       # Two-page master guide PDF builder
    ├── build_session_epub.py   # Standalone EPUB e-reader book builder
    └── run_observation_planner.py # End-to-end observation planner pipeline
```


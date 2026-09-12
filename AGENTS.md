# Stargazing Workspace & Observation Guide

This repository contains astronomical observation plans, sky charts, target catalogs, location profiles, equipment specifications, and educational tutorials for stargazing sessions.

---

## 1. Repository Structure

All stargazing assets and sessions are organized into structured directories:

```text
├── locations/
│   └── <location-slug>.md      # Reusable observing site profiles (coordinates, Bortle, obstruction)
├── equipment/
│   └── <equipment-slug>.md     # Reusable optical equipment profiles (aperture, FL, eyepieces)
├── observations/
│   └── <location>-<YYYY-MM-DD>/# Observation session packages
│       ├── STARGAZING_PLAN.md  # Complete observation guide markdown
│       ├── STARGAZING_PLAN.pdf # Print-optimized 2-page Master Plan (1 double-sided A4 sheet)
│       ├── STARGAZING_FIELD_GUIDE.epub # Standalone, indexed e-book for e-readers
│       ├── full_sky_map.pdf    # All-sky planisphere (PDF vector)
│       ├── full_sky_map.png    # High-resolution planisphere image
│       └── charts/             # Dedicated finder charts (PDF + PNG)
│           ├── chart_1_*.pdf
│           └── ...
├── tutorials/
│   └── <topic>.md              # General astronomy tutorials, optical rules & field craft
├── .agents/skills/
│   └── stargazing-planner/     # Automated planning skill for agents
├── scripts/
│   ├── calculate_ephemeris.py  # Solar/lunar twilight and target visibility calculator
│   ├── generate_charts.py      # Vector planisphere & toner-saver negative finder chart generator
│   ├── build_plan_pdf.py       # Two-page master guide PDF builder
│   ├── build_session_epub.py   # Standalone EPUB e-reader book builder
│   └── run_observation_planner.py # End-to-end observation planner pipeline
└── requirements.txt            # Python dependencies (astropy, matplotlib, reportlab, etc.)
```

---

## 2. Core Agent Invariants & Workflow Rules

### Rule 2.1: Location Resolution & Caching
- When the user requests an observation plan, check `locations/` for an existing profile whose name or coordinates match the input.
- **Cache Hit**: Reuse the existing `locations/<location-slug>.md` data directly.
- **Cache Miss**: Thoroughly research the new location's geographic coordinates, elevation, Bortle class, SQM sky brightness, and local horizon obstructions (trees/topography). Save the new profile into `locations/<location-slug>.md` for future sessions.

### Rule 2.2: Equipment Resolution & Caching
- Check `equipment/` for an existing profile matching the specified telescope and eyepieces.
- **Cache Hit**: Reuse the existing `equipment/<equipment-slug>.md` data directly.
- **Cache Miss**: Research the instrument's optical specifications (aperture, focal length, focal ratio, Dawes resolving limit, limiting magnitude, eyepiece magnifications, exit pupils, true fields of view, and optical inversion behavior). Save the profile into `equipment/<equipment-slug>.md` for future sessions.

### Rule 2.3: Stargazing Plan Generation (`stargazing-planner` skill)
- Always activate the `stargazing-planner` skill to calculate ephemerides and curate an optimal, customized observation portfolio.
- **Visibility Criteria**:
  - Filter targets to ensure they remain at **altitude $\ge 15^\circ$** (preferably $\ge 20^\circ$) to clear local horizon obstructions and atmospheric extinction.
  - Schedule objects within $\pm 1.5$ hours of their meridian transit.
  - Avoid scheduling manual Alt-Az tracking directly overhead (>80° Alt, *"Dobson's Hole"*).
- **Target Diversity**: Curate a balanced portfolio across twilight double stars, low-altitude early targets, rich globulars, planetary nebulae, open clusters/star clouds, external galaxies, and bright planets.

### Rule 2.4: Observation Session Packaging
- Store all outputs in `observations/<location-slug>-<YYYY-MM-DD>/`.
- **Primary Deliverables (Default)**:
  - **Master Markdown Plan (`STARGAZING_PLAN.md`)**: Complete observation guide with Mermaid timelines and interactive links.
  - **Standalone E-Reader Field Book (`<session-folder>.epub` / `STARGAZING_FIELD_GUIDE.epub`)**: Compiles the entire session (site profile, twilight schedule, full-sky planisphere, target catalog, and all screen-optimized finder charts) into a single, fully indexed EPUB.
  - **Finder Charts (High-Resolution PNGs)**: Both A4 landscape master charts and PocketBook Era screen-optimized multi-page assets.
- **On-Demand Deliverables (PDF Mode, via `--pdf` flag or user request)**:
  - **Master Guide Plan (`STARGAZING_PLAN.pdf`)**: Format strictly as a **2-page document** in **Standard A4 Portrait** (`210 × 297 mm` / `595.28 × 841.89 pt`, printable on **1 single double-sided A4 sheet**). Page 1: Header, site profile box, optical config box, moon status banner, timeline Gantt chart, twilight schedule table. Page 2: Curated target catalog table, practical field protocols box, sky charts directory table. Zero hopping text duplication.
  - **All-Sky Planisphere (`full_sky_map.pdf`)**: Format strictly as **Standard A4 Portrait** (`210 × 297 mm` / `595.28 × 841.89 pt`).
  - **Finder Charts (`charts/chart_<N>_*.pdf`)**: Format strictly as **Standard A4 Landscape** (`297 × 210 mm` / `841.89 × 595.28 pt`, `bbox_inches='tight'` prohibited).
- **Finder Chart Rendering Standards (Toner-Saver Negative B/W Edition)**:
  - **Viewport A**: Wide-Field Star-Hopping Chart (Upright naked-eye / finder: N ↑, E ←). Star density rendered down to **visual magnitude 8.5** (cutting out noise and clutter) with a dedicated star dot size to magnitude legend printed in the bottom corner.
  - **Viewport B**: Telescope Eyepiece Simulation in **Toner-Saver Negative** (pure white background `#ffffff`, black stars, grey DSO contours, pre-inverted 180°: N ↓, E →).
  - **Viewport C**: Target Dossier & Star-Hopping Instructions.
  - Full B/W printer compatibility with solid, dashed, and dash-dot Telrad reticles.
- **Standalone E-Reader Field Book (`<session-folder>.epub` / `STARGAZING_FIELD_GUIDE.epub`)**:
  - Compiles the entire session into a single, fully indexed EPUB.
  - **PocketBook Era Hardware & 12px Zoom Optimization**: Calibrated for 7.0" Carta 1200 (`1264 × 1680`, 300 ppi, 3:4 aspect ratio) at **12px font zoom**.
  - **Natural 4-Page Target Pagination (Zero Blank Pages)**: Each target lives in a single document (`chart_<N>_<slug>.xhtml`) with strict CSS page-break controls (`.chart-page`, `.instructions-page` using `break-before: page`), eliminating artificial sub-chapter breaks and empty page flips:
    - **Page 1 (Eyepiece & Dossier)**: Side-by-side Viewport B (eyepiece simulation, inverted 180°) and Viewport C (target dossier with eyepiece quick reference integrated directly inside graphic, omitting trailing HTML callouts).
    - **Page 2 (Constellation Context Orientation Chart)**: Moderately wide field of view (~50°–65°) displaying naked-eye stars (`mag <= 6.2`), surrounding constellation stick lines and labels, and a prominent dashed bounding box marking the field of view covered by the next-page finder chart (`"[NEXT PAGE FINDER VIEWPORT]"`).
    - **Page 3 (Wide-Field Finder Chart)**: Screen-fitted Viewport A wide-field chart with stars to **mag 8.5**, Telrad rings, hop badges, and magnitude key. Redundant intermediate headers and tips are dropped so the chart fills the entire screen.
    - **Page 4 (Step-by-Step Hop Narrative)**: Reflowable text-based star-hopping guide with direct bottom navigation to the next target.
  - **Dynamic Naming & Series Metadata**:
    - Named after the observation directory (e.g. `dvigrad-2026-09-12.epub`), with backward-compatible symlink to `STARGAZING_FIELD_GUIDE.epub`.
    - Auto-discovers past sessions in `observations/` to calculate and increment the series index (`calibre:series`, `calibre:series_index`, EPUB 3 `belongs-to-collection`, `pocketbook:font-size="12px"`).

### Rule 2.5: Educational Tutorials & Field Craft
- Store general tutorials, operational rules, and explanatory guides in `tutorials/`.
- General educational tutorials (such as mirror collimation or star testing) are published and maintained as dedicated standalone guides/epubs outside of observation sessions. They are not bundled into nightly observation session EPUBs.
- Whenever a user asks questions regarding astronomical concepts, optical handling, or observational techniques, refer to or create new markdown guides in `tutorials/<topic>.md`.

### Rule 2.6: GitHub Mermaid Compatibility for Markdown Charts
- Whenever creating charts, timelines, schedules, workflows, or decision trees inside markdown (`.md`) files (such as `STARGAZING_PLAN.md`, tutorials, or guides), **always use Mermaid code blocks** (` ```mermaid `) to ensure compatibility with GitHub web and mobile previews.
- **Syntax Standards**:
  - Prefer `flowchart TD` / `flowchart LR` or `gantt` charts.
  - Always quote node labels containing special characters like parentheses, colons, or brackets (e.g. `step["M57 Ring Nebula (96×)"]`).
  - For `gantt` charts, ensure time formats and milestone syntax strictly adhere to Mermaid specs so GitHub renders them smoothly without parser warnings.
  - Never use plain ASCII diagrams or external proprietary chart embeds when a Mermaid diagram can represent the structure.

---

## 3. Python Environment & Script Execution

Dependencies are specified in `requirements.txt`:
```bash
pip install -r requirements.txt
```

To run the complete observation planning pipeline (defaults to EPUB and Markdown deliverables):
```bash
python3 scripts/run_observation_planner.py \
  --location dvigrad \
  --equipment skywatcher-skyliner-200p \
  --date YYYY-MM-DD
```
To additionally generate printable A4 master and chart PDFs, add the `--pdf` flag:
```bash
python3 scripts/run_observation_planner.py \
  --location dvigrad \
  --equipment skywatcher-skyliner-200p \
  --date YYYY-MM-DD \
  --pdf
```
- Matplotlib cache should be directed to a writable location if running in sandboxed or read-only home directory environments (`MPLCONFIGDIR=/tmp/matplotlib`).
- If a local vendor directory `.pylibs/` is present, it is automatically resolved by the scripts.


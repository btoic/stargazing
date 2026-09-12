---
name: stargazing-planner
description: >-
  Plan astronomical observation parties and stargazing sessions, calculate celestial
  ephemerides, curate optimal deep-sky and planetary target lists, and compile screen-optimized
  EPUB e-books and markdown observation plans (with on-demand printable A4 PDFs).
---

# Stargazing Planner Skill

This skill provides the end-to-end procedure for planning a stargazing observation session, evaluating location and equipment profiles, computing astronomical ephemerides, curating a high-impact observing program, and generating screen-optimized e-reader and markdown deliverables (with on-demand printable A4 PDFs).

---

## 1. Directory Structure & Invariants

All session assets follow a standardized repository layout:

```text
├── catalogs/
│   ├── messier_catalog.json    # Complete 110 Messier objects catalog with coordinates, optics & Swanson ratings
│   └── messier_difficulty_ratings.md # Swanson Messier difficulty reference catalog
├── messier_catalog.md          # Global 110-target Messier catalog observer's guide in repository root
├── locations/
│   └── <location-slug>.md      # Reusable site profiles (coordinates, Bortle, obstruction)
├── equipment/
│   ├── <equipment-slug>.md     # Reusable optics profiles (aperture, FL, eyepieces, inversion)
│   ├── pocketbook-era.md       # PocketBook Era hardware & display specifications
│   └── amazon-kindle-paperwhite.md # Amazon Kindle Paperwhite display & KF8 rendering profile
├── shared/
│   └── <object-slug>/          # Shared, cross-session reusable charts cache (m1 through m110)
│       ├── context.png         # Universal constellation orientation chart (mag <= 6.5)
│       ├── widefield_<equip>.png # Wide-field star hopping chart (mag <= 8.5)
│       ├── eyepiece_dossier_<equip>.png # Eyepiece simulation & dossier graphic
│       └── chart_<equip>.png   # Full A4 master finder chart (and .pdf)
├── observations/
│   └── <location>-<YYYY-MM-DD>/# Observation session packages
│       ├── targets.md          # Plain text target manifest for fast regeneration
│       ├── STARGAZING_PLAN.md  # Complete observation guide (Primary deliverable)
│       ├── <location>-<date>.epub # Standalone, indexed e-book for e-readers (Primary deliverable)
│       ├── full_sky_map.png    # High-res planisphere image
│       ├── charts/             # Screen-optimized & master finder chart PNGs (Primary deliverable)
│       ├── STARGAZING_PLAN.pdf # Print-optimized 2-page Master Plan (On-demand via --pdf)
│       ├── full_sky_map.pdf    # All-sky planisphere vector PDF (On-demand via --pdf)
│       └── charts/*.pdf        # Toner-saver negative finder chart PDFs (On-demand via --pdf)
├── tutorials/
│   └── <topic>.md              # Standalone astronomy guides, field craft & optical tutorials
├── scripts/
│   ├── build_messier_catalog.py # Compiles unified 110 Messier astronomical dataset
│   ├── generate_all_messier_shared.py # Parallel batch pre-renderer for all 110 Messier shared assets
│   ├── build_messier_catalog_markdown.py # Compiles global messier_catalog.md observer guide
│   ├── calculate_ephemeris.py  # Solar/lunar twilight and target visibility calculator
│   ├── generate_charts.py      # Vector planisphere & toner-saver negative finder chart generator
│   ├── build_plan_pdf.py       # Two-page master guide PDF builder
│   ├── build_session_epub.py   # Standalone EPUB e-reader book builder
│   └── run_observation_planner.py # End-to-end observation planner pipeline
└── requirements.txt            # Python package dependencies
```

---

## 2. Location & Equipment Resolution Rules

### Step 2.1: Resolve Location (`locations/<location-slug>.md`)
1. Check `locations/` for an existing file matching the user's location name or coordinates.
2. **If found**: Load coordinates, elevation, Bortle class, SQM sky brightness, and local horizon obstruction angle.
3. **If NOT found**:
   - Research the coordinates, light pollution metrics (via [lightpollutionmap.info](https://www.lightpollutionmap.info)), elevation, and local terrain/tree obstructions.
   - Save the new profile as `locations/<location-slug>.md` for future reuse.

### Step 2.2: Resolve Equipment (`equipment/<equipment-slug>.md`)
1. Check `equipment/` for an existing file matching the user's telescope model.
2. **If found**: Load aperture, focal length, focal ratio ($f/\#$), resolving limit (Dawes), limiting magnitude, eyepieces, true field of view (TFOV), and optical inversion behavior.
3. **If NOT found**:
   - Extract optical specs, calculate magnifications, exit pupils, and field of view for each eyepiece.
   - Save the new profile as `equipment/<equipment-slug>.md` for future reuse.

---

## 3. Ephemeris Calculation & Target Curation

### Step 3.1: Celestial Phases
Calculate for the observing date and location:
- **Sunset & Civil Twilight** ($\text{Alt}_\odot \le -6^\circ$): Mirror acclimation and finder scope alignment.
- **Nautical Twilight** ($\text{Alt}_\odot \le -12^\circ$): Double star contrast (e.g. Albireo) and urgent low-altitude sweeps.
- **Astronomical Darkness** ($\text{Alt}_\odot \le -18^\circ$): Zero atmospheric solar scattering; prime deep-sky window.
- **Moon Ephemeris**: Phase illumination percentage, moonrise, and moonset times. True dark-sky observing requires $\text{Alt}_\text{Moon} \le 0^\circ$.

### Step 3.2: Target Curation & Session Budgeting Rules

#### Dwell-Time Budget: Observer Skill × Object Difficulty
Flat target dwell times are inaccurate because acquisition time scales dramatically with both **Observer Skill** and **Object Difficulty** (calibrated from Michael Swanson's *NexStar User's Guide II*).
Total dwell time is:
$$T_\text{dwell} = T_\text{acquire} + T_\text{observe}$$

- **Very Easy / Easy Showpieces (e.g. M13, M31, M42, M45, M57, Albireo)**:
  - **Advanced Observer**: Acquisition takes only **1 to 2 minutes**; eyepiece inspection takes 4–6 min $\rightarrow$ Total dwell: **5 to 8 minutes** (avg ~6.5 min).
  - **Intermediate Observer**: Acquisition takes 2–4 min; inspection takes 5–8 min $\rightarrow$ Total dwell: **7 to 12 minutes** (avg ~9.5 min).
  - **Beginner / Starter**: Acquisition takes 5–10 min; inspection takes 5–8 min $\rightarrow$ Total dwell: **10 to 18 minutes** (avg ~14 min).
- **Medium Targets (e.g. M1, M27, M11, M56, M81/M82)**:
  - Advanced: $T_\text{dwell} = \mathbf{7\text{--}12\text{ min}}$ (avg ~9.5 min, 2–4m acq).
  - Intermediate: $T_\text{dwell} = \mathbf{10\text{--}16\text{ min}}$ (avg ~13 min, 4–7m acq).
  - Beginner: $T_\text{dwell} = \mathbf{18\text{--}25\text{ min}}$ (avg ~21.5 min, 10–15m acq).
- **Hard Targets (e.g. M33, M74, M76, M87, M71)**:
  - Advanced: $T_\text{dwell} = \mathbf{12\text{--}20\text{ min}}$ (avg ~16 min, 4–8m acq).
  - Intermediate: $T_\text{dwell} = \mathbf{16\text{--}22\text{ min}}$ (avg ~19 min, 8–12m acq).
  - Beginner: $T_\text{dwell} = \mathbf{26\text{--}35\text{ min}}$ (avg ~30 min, 18–25m acq).

#### Mathematical Session Budget Formula
Deduct **30 minutes of overhead** (equipment setup, mirror acclimation, finder alignment, dark-adaptation breaks):
$$T_\text{net} = T_\text{darkness} - 30\text{ min}$$

For a standard 2.5-hour darkness session ($T_\text{net} = 120\text{ min}$):
- **Beginner / Starter**:
  - **Min (Relaxed)**: **4 primary targets** (~30 min/target, deep averted vision inspection)
  - **Avg (Balanced)**: **6 primary targets** (~20 min/target, 4 Easy + 2 Medium) — *(Recommended)*
  - **Max (Active Sweeps)**: **8 primary targets** (~15 min/target, strictly bright Easy showpieces)
- **Intermediate Observer**:
  - **Min (Relaxed)**: **6 primary targets** (~20 min/target, in-depth visual study)
  - **Avg (Balanced)**: **8 to 9 primary targets** (~13–15 min/target, 5 Easy + 3 Medium + 1 Hard) — *(Recommended)*
  - **Max (Active Sweeps)**: **12 primary targets** (~10 min/target, active hopping + 2–3 neighbor hops)
- **Advanced / Seasoned Observer**:
  - **Min (Relaxed)**: **8 primary targets** (~15 min/target, averted vision sketches / difficult targets)
  - **Avg (Balanced)**: **12 to 14 primary targets** (~8–10 min/target, rapid 1–2m hops + high-power detail) — *(Recommended)*
  - **Max (Active Sweeps)**: **16 to 18 primary targets** (~6–7 min/target, rapid Messier marathon pace)

#### Interactive Observer Consultation Protocol (`ask_question`)
Never unilaterally dictate a target count. During initial planning:
1. Assess or inquire about observer skill level (Beginner, Intermediate, Advanced).
2. Calculate $T_\text{net}$ and compute Min, Avg (Recommended), and Max target counts.
3. Call `ask_question` with 3 concrete options plus the UI's built-in custom write-in field:
   - `(Recommended) Balanced Program: <Avg> primary targets (+ <Y> bonus neighbor hops)`
   - `Relaxed Pace: <Min> primary targets (more time per object, deep inspection/sketching)`
   - `Active Sweeps: <Max> primary targets (fast acquisition, high-volume tour)`
4. Respect the observer's selection or write-in custom wishlist before generating targets.


Target Curation Criteria:
1. **Target Manifest (`targets.md`)**: Save the curated targets into `observations/<session>/targets.md` (plain text markdown list with object slug, common name, constellation, difficulty rating, recommended magnification, and hops). This file serves as the reproducible source of truth for chart rendering and EPUB/PDF rebuilds.
2. **Anchor + Neighbor Clustering**: Group targets into spatial clusters so observers can easily hop to nearby bonus objects from the same constellation field (e.g. M56 near M57, M71 near M27, M103 near the Double Cluster / Ruchbah). (See [tutorials/session-target-budgeting-and-hopping.md](../../../tutorials/session-target-budgeting-and-hopping.md)).
3. **Target Catalog & Difficulty Calibration**: Use repository astronomical dataset [catalogs/messier_catalog.json](../../../catalogs/messier_catalog.json) for authoritative target coordinates, dimensions, magnitudes, and optical configs. Calibrate difficulty ratings (`Very Easy`, `Easy`, `Medium`, `Hard`) using [catalogs/messier_difficulty_ratings.md](../../../catalogs/messier_difficulty_ratings.md) (from Michael Swanson's *NexStar User Guide II*).
4. **Horizon Obstruction Hard Floor**: All targets must be at **Altitude $\ge 15^\circ$** (preferably $\ge 20^\circ$) to clear local valley/tree obstructions and atmospheric extinction.
5. **Meridian Timing**: Schedule targets within $\pm 1.5$ hours of their highest nightly transit.
6. **Zenith Blindspot ("Dobson Hole") Avoidance**: Avoid scheduling manual Alt-Az tracking for targets directly overhead (>80° Alt); catch them at 65°–75° Alt.
7. **Balanced Program Portfolio**:
   - **Showpiece Double Stars**: Twilight warm-up (e.g., Albireo).
   - **Early Setting Targets**: Low-altitude objects before they set into trees (e.g., M22 in Sagittarius).
   - **Globular Clusters**: Core resolution showpieces (e.g., M13, M92).
   - **Planetary Nebulae**: Distinctive structures (e.g., M57 Ring, M27 Dumbbell).
   - **Open Clusters / Milky Way Clouds**: Wide-field jewel boxes (e.g., M11 Wild Duck, Perseus Double Cluster).
   - **External Galaxies**: Large disks and dust lanes (e.g., M31 Andromeda, M32, M110).
   - **Planetary Finale**: Naked-eye planets once cleared above tree lines (e.g., Saturn).

---

### Step 3.3: Deliverables & Output Formats

#### Primary Deliverables (Default)
1. **Master Plan Markdown Guide (`STARGAZING_PLAN.md`)**:
   - Complete observation guide and digital companion for desktop and mobile reading.
   - **GitHub Mermaid Compatibility**: All timelines, schedules, workflows, and decision trees must be implemented using **Mermaid code blocks** (` ```mermaid `) for native, high-resolution rendering in GitHub web and mobile previews.
   - Format observation schedules as Mermaid `gantt` charts or `flowchart LR` process pipelines. Quote labels containing parentheses or brackets.
2. **Standalone E-Reader Field Book (`<session-slug>.epub`)**:
   - Compiles the entire session into a single, fully indexed, cross-linked EPUB e-book named dynamically after the session folder (e.g. `dvigrad-2026-09-12.epub`). Do not generate redundant duplicate EPUB files.
   - **Modular E-Reader Display Profiles (`--device`)**:
     - **`pocketbook-era` (Default)**: Calibrated for 7.0" E-Ink Carta 1200 (`1264 × 1680`, 300 ppi, 3:4 portrait aspect ratio) at **12px font zoom** (`pocketbook:font-size="12px"`, 84vh/98vh chart viewports).
     - **`amazon-kindle` / `kindle-paperwhite`**: Tailored for Kindle Paperwhite (6.8"), Oasis (7.0"), and Scribe (10.2") running the Amazon KF8/KFX engine. Features zero `@page` margins, scalable `1.0rem` typography, and safe 78vh/88vh viewport caps to prevent phantom blank page flips.
     - **`generic`**: Standard reflowable layout for Kobo, Boox, and other E-Ink readers.
   - **Calibre & EPUB 3 Series Metadata**: Automatically discovers past observation sessions in `observations/`, registers series title `"Stargazing Observations"`, and assigns incrementing sequence numbers via `calibre:series`, `calibre:series_index`, EPUB 3 `belongs-to-collection`, and device-specific rendering metadata.
   - **E-Ink High Contrast**: Pure white background (`#ffffff`), dark typography, crisp toner-saver negative charts, and responsive styling.
   - **Natural 4-Page Target Pagination (Zero Blank Pages)**: Each target is stored in a single unified document (`chart_<N>_<slug>.xhtml`) with strict CSS page-break controls (`break-before: page`), eliminating artificial sub-chapter breaks and empty page flips:
     1. **Page 1 (Eyepiece & Dossier)**: Viewport B (Eyepiece simulation, inverted 180°) and Viewport C (Target Dossier) rendered side-by-side in landscape 4:3 ratio (`_eyepiece_dossier.png`). Eyepiece quick reference notes are integrated directly inside the dossier graphic, eliminating trailing HTML callouts.
     2. **Page 2 (Constellation Context Orientation Chart)**: Moderately wide field of view (~50°–65°) displaying naked-eye stars (`mag <= 6.5`), surrounding constellation stick lines and labels, and a prominent dashed bounding box marking the field of view covered by the next-page finder chart (`"[NEXT PAGE FINDER VIEWPORT]"`).
     3. **Page 3 (Wide-Field Finder Chart)**: Viewport A rendered full-screen in portrait 3:4 ratio (`_widefield.png`) matching the e-reader display. Star density is rendered down to visual **magnitude 8.5** (cutting out noise and clutter), complete with Telrad rings, hop badges, and a dot size vs. magnitude legend. Redundant intermediate headers and tips are omitted so the chart fills the entire screen.
     4. **Page 4 (Step-by-Step Hop Narrative)**: Reflowable text-based star-hopping guide with direct bottom navigation to the next target or catalog.
   - **E-Reader Catalog Ergonomics**: In the curated target catalog table, place the `Finder Chart` link column inward (before `Recommended Eyepiece`) rather than on the right edge, preventing accidental page-turn touch gestures on e-readers. Replace coordinate columns with difficulty ratings.
   - **Dual Compatibility**: Implements both EPUB 3 (`nav.xhtml`) and EPUB 2 (`toc.ncx`) navigation for compatibility across all e-readers (PocketBook, Kindle, Kobo, Boox, Tolino).
3. **High-Resolution Finder Chart PNGs & Shared Asset Caching (`shared/<object-slug>/`)**:
   - Master A4 landscape PNGs and dedicated PocketBook Era screen-optimized multi-page PNG assets saved in `charts/`.
   - **Shared Cross-Session Cache (`shared/`)**:
     - `shared/<object>/context.png`: Universal constellation context chart (mag $\le 6.5$), location-agnostic.
     - `shared/<object>/widefield_<equipment>.png`: Wide-field star hopping chart (mag $\le 8.5$) cached per telescope model.
     - `shared/<object>/eyepiece_dossier_<equipment>.png`: Eyepiece simulation & technical dossier graphic. Ephemeris details (session-specific transit time/altitude) are decoupled and placed in markdown/text instructions, allowing the graphic to be 100% reusable across dates and locations.
     - `shared/<object>/chart_<equipment>.png` (and `.pdf`): Master A4 chart.
     - On subsequent runs or future sessions, existing charts are copied instantly (`[CACHE HIT]`), drastically reducing generation time.
4. **All-Sky Planisphere (`full_sky_map.png` / `full_sky_map.pdf`)**:
   - Strictly maintains a 1:1 circular aspect ratio with clean, shortened cardinal direction labels (`N`, `S`, `E`, `W`).
5. **Global Messier Catalog Guide (`messier_catalog.md`)**:
   - Repository-level observer's guide in root compiling all 110 Messier objects.
   - Replicates the exact 4-part EPUB layout: (1) Eyepiece simulation & dossier graphic, (2) Constellation context orientation chart, (3) Wide-field star hop chart & master A4 link, (4) Observing strategy & hop text.
   - Interactive master index with Michael Swanson difficulty ratings and `#m{N}` anchor jump links.
   - 100% GitHub markdown preview compatible (explicit `<a id="m{N}"></a>` anchors, repository-relative paths).
   - Generated via `python3 scripts/build_messier_catalog_markdown.py`.

#### On-Demand Deliverables (PDF Mode, via `--pdf` flag or user request)
1. **Master Plan PDF (`STARGAZING_PLAN.pdf`)**:
   - Must fit onto **exactly 2 pages** in **Standard A4 Portrait** (`210 × 297 mm` / `595.28 × 841.89 pt`, for 1 single double-sided A4 sheet):
     - **Page 1**: Title, location profile box, telescope configuration box, moon verdict banner, observation timeline Gantt chart, twilight schedule table.
     - **Page 2**: Curated Target Catalog table (referencing charts), Practical Field Protocols box, and Sky Charts Directory table.
     - **Zero Step-by-Step Hop Duplication**: Omit detailed hop text from the master plan—star-hopping instructions live on the dedicated charts.
2. **All-Sky Planisphere PDF (`full_sky_map.pdf`)**:
   - Format strictly as **Standard A4 Portrait** (`210 × 297 mm` / `595.28 × 841.89 pt`).
3. **Printable Finder Charts (`charts/chart_<N>_<name>.pdf`)**:
   - Formatted strictly as **Standard A4 Landscape** (`297 × 210 mm` / `841.89 × 595.28 pt`).
   - **Zero Auto-Cropping (`bbox_inches='tight'` prohibited)**: Never pass `bbox_inches='tight'` to `plt.savefig()` when exporting printable PDF charts. Matplotlib's tight bounding box calculation alters the MediaBox dimensions and ruins 100% scale A4 printing. Use explicit subplots within safe margins (`x: 0.035..0.965`, `y: 0.045..0.880`).
   - Three viewports side-by-side:
     - **`VIEWPORT A: WIDE-FIELD STAR-HOPPING CHART`**: Upright naked-eye / finder orientation (N ↑, E ←), black stars down to mag 8.5, constellation guide lines, Telrad concentric rings (0.5°, 2.0°, 4.0°, 5.0°), and numbered step badges.
     - **`VIEWPORT B: TELESCOPE EYEPIECE SIMULATION`**: Toner-Saver Negative (pure white background `#ffffff`, black stars, grey DSO contours, pre-inverted 180° for Newtonian reflectors: N ↓, E →).
     - **`VIEWPORT C: TARGET DOSSIER & STAR-HOPPING INSTRUCTIONS`**: Monospaced technical dossier with ephemeris, recommended eyepieces, and complete step-by-step hopping text.

---

## 4. Tutorials & Field Craft Separation
- General educational tutorials and maintenance guides (e.g. mirror collimation, star testing, dew mitigation, dark adaptation) are maintained in `tutorials/` as standalone guides and independent EPUBs/PDFs.
- They are **decoupled from observation session packages** and not bundled into nightly observation EPUBs.
- When the user asks general astronomical questions or seeks procedural advice, consult or update `tutorials/<topic>.md`.

---

## 5. Python Environment & Execution

Dependencies are specified in `requirements.txt`:
```bash
pip install -r requirements.txt
```

To run the complete observation planning pipeline (defaults to PocketBook Era EPUB and Markdown deliverables):
```bash
python3 scripts/run_observation_planner.py \
  --location <location-slug> \
  --equipment <equipment-slug> \
  --device pocketbook-era \
  --date <YYYY-MM-DD>
```
To compile with an Amazon Kindle profile (`amazon-kindle` / `kindle-paperwhite`):
```bash
python3 scripts/run_observation_planner.py \
  --location <location-slug> \
  --equipment <equipment-slug> \
  --device amazon-kindle \
  --date <YYYY-MM-DD>
```
To additionally generate printable A4 master and chart PDFs, pass `--pdf`:
```bash
python3 scripts/run_observation_planner.py \
  --location <location-slug> \
  --equipment <equipment-slug> \
  --device pocketbook-era \
  --date <YYYY-MM-DD> \
  --pdf
```

To compile or regenerate the global Messier catalog markdown guide:
```bash
python3 scripts/build_messier_catalog_markdown.py
```

To pre-render or update shared assets for all 110 Messier objects in parallel:
```bash
python3 scripts/generate_all_messier_shared.py --workers 4
```

- Required libraries: `astropy`, `skyfield`, `numpy`, `matplotlib`, `reportlab`, `pypdfium2`.
- Matplotlib cache should be directed to a writable location in sandboxed environments via `MPLCONFIGDIR=/tmp/matplotlib`.


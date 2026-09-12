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
├── locations/
│   └── <location-slug>.md      # Reusable site profiles (coordinates, Bortle, obstruction)
├── equipment/
│   └── <equipment-slug>.md     # Reusable optics profiles (aperture, FL, eyepieces, inversion)
├── observations/
│   └── <location>-<YYYY-MM-DD>/# Observation session packages
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
Select 6 to 8 primary anchor showpiece objects and 3 to 6 adjacent bonus neighbor targets meeting these criteria:
1. **Dwell-Time Budgeting**: Budget 15–20 minutes of dwell time per primary anchor target (accounting for acquisition, eyepiece steps, dark adaptation, and visual integration). A 2.5-hour darkness session realistically supports **6 to 8 primary targets**. (See [tutorials/session-target-budgeting-and-hopping.md](file:///home/branko/Documents/repos/github.com/btoic/stargazing/tutorials/session-target-budgeting-and-hopping.md)).
2. **Anchor + Neighbor Clustering**: Group targets into spatial clusters so observers can easily hop to nearby bonus objects from the same constellation field (e.g. M56 near M57, M71 near M27, M103 near the Double Cluster / Ruchbah).
3. **Difficulty Rating Calibration**: Assign difficulty ratings (`Very Easy`, `Easy`, `Medium`, `Hard`) using repository catalog [catalogs/messier_difficulty_ratings.md](file:///home/branko/Documents/repos/github.com/btoic/stargazing/catalogs/messier_difficulty_ratings.md) (from Michael Swanson's *NexStar User Guide II*).
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
   - Compiles the entire session into a single, fully indexed, cross-linked EPUB e-book named dynamically after the session folder (e.g. `dvigrad-2026-09-12.epub`, with backward-compatible copy to `STARGAZING_FIELD_GUIDE.epub`).
   - **PocketBook Era Hardware & 12px Zoom Optimization**: Optimized for 7.0" E-Ink Carta 1200 (`1264 × 1680`, 300 ppi, 3:4 portrait aspect ratio) at **12px font zoom**.
   - **Calibre & EPUB 3 Series Metadata**: Automatically discovers past observation sessions in `observations/`, registers series title `"Stargazing Observations"`, and assigns incrementing sequence numbers via `calibre:series`, `calibre:series_index`, EPUB 3 `belongs-to-collection`, and `pocketbook:font-size="12px"`.
   - **E-Ink High Contrast**: Pure white background (`#ffffff`), dark typography, crisp toner-saver negative charts, and responsive styling.
   - **Natural 4-Page Target Pagination (Zero Blank Pages)**: Each target is stored in a single unified document (`chart_<N>_<slug>.xhtml`) with strict CSS page-break controls (`break-before: page`), eliminating artificial sub-chapter breaks and empty page flips:
     1. **Page 1 (Eyepiece & Dossier)**: Viewport B (Eyepiece simulation, inverted 180°) and Viewport C (Target Dossier) rendered side-by-side in landscape 4:3 ratio (`_eyepiece_dossier.png`). Eyepiece quick reference notes are integrated directly inside the dossier graphic, eliminating trailing HTML callouts.
     2. **Page 2 (Constellation Context Orientation Chart)**: Moderately wide field of view (~50°–65°) displaying naked-eye stars (`mag <= 6.2`), surrounding constellation stick lines and labels, and a prominent dashed bounding box marking the field of view covered by the next-page finder chart (`"[NEXT PAGE FINDER VIEWPORT]"`).
     3. **Page 3 (Wide-Field Finder Chart)**: Viewport A rendered full-screen in portrait 3:4 ratio (`_widefield.png`) matching the PocketBook Era display. Star density is rendered down to visual **magnitude 8.5** (cutting out noise and clutter), complete with Telrad rings, hop badges, and a dot size vs. magnitude legend. Redundant intermediate headers and tips are omitted so the chart fills the entire screen.
     4. **Page 4 (Step-by-Step Hop Narrative)**: Reflowable text-based star-hopping guide with direct bottom navigation to the next target or catalog.
   - **Dual Compatibility**: Implements both EPUB 3 (`nav.xhtml`) and EPUB 2 (`toc.ncx`) navigation for compatibility across all e-readers (PocketBook, Kindle, Kobo, Boox, Tolino).
3. **High-Resolution Finder Chart PNGs**:
   - Master A4 landscape PNGs and dedicated PocketBook Era screen-optimized multi-page PNG assets saved in `charts/`.

#### On-Demand Deliverables (PDF Mode, via `--pdf` flag or user request)
1. **Master Plan PDF (`STARGAZING_PLAN.pdf`)**:
   - Must fit onto **exactly 2 pages** in **Standard A4 Portrait** (`210 × 297 mm` / `595.28 × 841.89 pt`, for 1 single double-sided A4 sheet):
     - **Page 1**: Title, location profile box, telescope configuration box, moon verdict banner, observation timeline Gantt chart, twilight schedule table.
     - **Page 2**: Curated Target Catalog table (referencing charts), Practical Field Protocols box, and Sky Charts Directory table.
     - **Zero Step-by-Step Hop Duplication**: Omit detailed hop text from the master plan—star-hopping instructions live on the dedicated charts.
2. **All-Sky Planisphere (`full_sky_map.pdf`)**:
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

To run the complete observation planning pipeline (defaults to EPUB and Markdown deliverables):
```bash
python3 scripts/run_observation_planner.py \
  --location <location-slug> \
  --equipment <equipment-slug> \
  --date <YYYY-MM-DD>
```
To additionally generate printable A4 master and chart PDFs, pass `--pdf`:
```bash
python3 scripts/run_observation_planner.py \
  --location <location-slug> \
  --equipment <equipment-slug> \
  --date <YYYY-MM-DD> \
  --pdf
```
- Required libraries: `astropy`, `skyfield`, `numpy`, `matplotlib`, `reportlab`, `pypdfium2`.
- Matplotlib cache should be directed to a writable location in sandboxed environments via `MPLCONFIGDIR=/tmp/matplotlib`.


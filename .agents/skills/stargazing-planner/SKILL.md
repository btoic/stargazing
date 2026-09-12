---
name: stargazing-planner
description: >-
  Plan astronomical observation parties and stargazing sessions, calculate celestial
  ephemerides, curate optimal deep-sky and planetary target lists, and generate printable
  2-page master guide PDFs and toner-saver negative star-hopping finder charts.
---

# Stargazing Planner Skill

This skill provides the end-to-end procedure for planning a stargazing observation session, evaluating location and equipment profiles, computing astronomical ephemerides, curating a high-impact observing program, and generating print-ready deliverables.

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
│       ├── STARGAZING_PLAN.md  # Complete observation guide
│       ├── STARGAZING_PLAN.pdf # Print-optimized 2-page Master Plan (1 double-sided sheet)
│       ├── full_sky_map.pdf    # All-sky planisphere with 15° obstruction ring
│       ├── full_sky_map.png    # High-res planisphere image
│       └── charts/             # Toner-saver negative finder charts (PDF + PNG)
│           ├── chart_1_*.pdf
│           └── ...
├── tutorials/
│   └── <topic>.md              # General astronomy guides, field craft & optical tutorials
├── scripts/
│   ├── calculate_ephemeris.py  # Solar/lunar twilight and target visibility calculator
│   ├── generate_charts.py      # Vector planisphere & toner-saver negative finder chart generator
│   ├── build_plan_pdf.py       # Two-page master guide PDF builder
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

### Step 3.2: Target Curation Rules
Select 8 to 12 showpiece objects meeting these criteria:
1. **Horizon Obstruction Hard Floor**: All targets must be at **Altitude $\ge 15^\circ$** (preferably $\ge 20^\circ$) to clear local valley/tree obstructions and atmospheric extinction.
2. **Meridian Timing**: Schedule targets within $\pm 1.5$ hours of their highest nightly transit.
3. **Zenith Blindspot ("Dobson Hole") Avoidance**: Avoid scheduling manual Alt-Az tracking for targets directly overhead (>80° Alt); catch them at 65°–75° Alt.
4. **Balanced Program Portfolio**:
   - **Showpiece Double Stars**: Twilight warm-up (e.g., Albireo).
   - **Early Setting Targets**: Low-altitude objects before they set into trees (e.g., M22 in Sagittarius).
   - **Globular Clusters**: Core resolution showpieces (e.g., M13, M92).
   - **Planetary Nebulae**: Distinctive structures (e.g., M57 Ring, M27 Dumbbell).
   - **Open Clusters / Milky Way Clouds**: Wide-field jewel boxes (e.g., M11 Wild Duck, Perseus Double Cluster).
   - **External Galaxies**: Large disks and dust lanes (e.g., M31 Andromeda, M32, M110).
   - **Planetary Finale**: Naked-eye planets once cleared above tree lines (e.g., Saturn).

---

## 4. Output Generation Standards

### Master Plan PDF (`STARGAZING_PLAN.pdf`)
- Must fit onto **exactly 2 pages** (for 1 single double-sided A4 sheet):
  - **Page 1**: Title, location profile box, telescope configuration box, moon verdict banner, observation timeline Gantt chart, twilight schedule table.
  - **Page 2**: Curated Target Catalog table (referencing charts), Practical Field Protocols box, and Sky Charts Directory table.
  - **Zero Step-by-Step Hop Duplication**: Omit detailed hop text from the master plan—star-hopping instructions live on the dedicated charts.

### Finder Charts (Toner-Saver Negative B/W Edition)
Every finder chart (`charts/chart_<N>_<name>.pdf` and `.png`) must have three distinct, labeled viewports:
1. **`VIEWPORT A: WIDE-FIELD STAR-HOPPING CHART`**:
   - Upright naked-eye / finder orientation (N ↑, E ←).
   - High-contrast black stars, constellation guide lines, Telrad concentric rings (solid 0.5°, dashed 2.0°, dash-dot 4.0°, dotted 5.0° finder circle), and numbered step badges (`[STEP 1]`, `[STEP 2]`).
2. **`VIEWPORT B: TELESCOPE EYEPIECE SIMULATION`**:
   - **Toner-Saver Negative**: Pure white background (`#ffffff`), crisp black circular rim, black stars, and delicate light-grey shaded DSO contours.
   - **Optical Inversion**: Pre-rotated 180° for Newtonian reflectors (N ↓, E →).
   - Labeled for the specific eyepiece focal length, magnification, and true FOV.
3. **`VIEWPORT C: TARGET DOSSIER & STAR-HOPPING INSTRUCTIONS`**:
   - Monospaced boxed technical dossier with tonight's ephemeris at the site, recommended eyepieces, visual descriptions, and clear step-by-step hopping narrative.

---

## 5. Tutorials & Continuous Refinement
When the user asks general astronomical questions or seeks procedural advice (e.g., collimation, mirror cooldown, averted vision, dew shields):
- Consult existing tutorials in `tutorials/`.
- If a new concept or technique is explained, write or update a tutorial in `tutorials/<topic>.md` for persistent reuse.

---

## 6. Python Environment & Execution

Dependencies are specified in `requirements.txt`:
```bash
pip install -r requirements.txt
```

To run the complete observation planning pipeline:
```bash
python3 scripts/run_observation_planner.py \
  --location <location-slug> \
  --equipment <equipment-slug> \
  --date <YYYY-MM-DD>
```
- Required libraries: `astropy`, `skyfield`, `numpy`, `matplotlib`, `reportlab`, `pypdfium2`.
- Matplotlib cache should be directed to a writable location in sandboxed environments via `MPLCONFIGDIR=/tmp/matplotlib`.


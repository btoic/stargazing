# Equipment: PocketBook Era E-Reader (PB700)

## 1. Hardware & Display Specifications
- **Model**: PocketBook Era (PB700)
- **Device Class**: 7.0-inch E-Ink Handheld E-Reader / Field Companion
- **Screen Technology**: E-Ink Carta™ 1200 with protective glass layer
- **Display Dimensions**: 7.0 inches (17.78 cm diagonal)
- **Active Resolution**: `1264 × 1680 pixels`
- **Pixel Density**: `300 ppi` (High-definition print-quality line sharpness)
- **Aspect Ratio**: `3:4` (`~0.752` in portrait; `~1.329` in landscape)
- **Color Depth / Grayscale**: 16 levels of greyscale (high micro-contrast for nebular boundaries and faint field stars)
- **Refresh Technology**: Fast partial screen updates with minimal ghosting; high response speed
- **Touch Interface**: Capacitive multi-touch screen supporting dual-finger pinch-to-zoom for detailed sky chart inspection
- **Physical Controls**: Side-mounted mechanical page-turn buttons (easy tactile operation with gloved hands at night)
- **Auto-Rotation**: Built-in G-sensor (accelerometer) enabling seamless 360° rotation between portrait and landscape modes
- **Environmental Rating**: `IPX8` waterproof (immersion up to 2 meters for 60 min); immune to heavy nocturnal valley dew, ground fog, and condensation

---

## 2. Field Craft & Dark Adaptation Protocols
- **SMARTlight Frontlight Calibration**:
  - The PocketBook Era features bi-color frontlight LEDs with independent brightness and color temperature control.
  - **Astronomical Field Mode**: Shift SMARTlight color temperature completely towards **100% warm amber/orange** (minimum blue-light emission) and reduce overall illumination to lowest comfortable legibility (5%–15%).
  - Avoid using standard white frontlight to preserve dark-adapted rod cells (rhodopsin).
- **Physical Operation Under Red Light**:
  - Mechanical edge buttons allow advancing pages without touching or smudging the screen with dew-moist fingers.
  - Matte anti-glare screen surface prevents red headlamp beam reflections during field use.

---

## 3. Digital Book & Sky Chart Rendering Standards
When generating EPUB session packages tailored for the PocketBook Era:
1. **Screen Aspect Ratio & 12px Zoom Optimization**:
   - Calibrated for standard PocketBook Era **12px font zoom**.
   - Base typography set to 12px sans-serif with 1.35 line height and compact margins (8–10px) to prevent accidental overflow.
   - Master chart viewport images target the **3:4 aspect ratio** (e.g. `1264 × 1680` or `1200 × 1600`) to fill the screen without letterboxing or squishing.
2. **Natural 3-Page Target Pagination (Zero Blank Pages)**:
   - Each target is compiled as a single unified document (`chart_<N>_<slug>.xhtml`) with strict CSS page-break rules (`.chart-page`, `.instructions-page` using `break-before: page`), eliminating artificial sub-chapter breaks and empty page flips.
   - **Page 1 (Target Dossier & Eyepiece Simulation)**: Side-by-side Viewport B (negative inverted 180° simulation) and Viewport C (object ephemeris & specs, with eyepiece quick reference integrated directly inside the dossier graphic, removing trailing HTML callouts).
   - **Page 2 (Wide-Field Star Hopping Chart)**: Full-screen Viewport A with deep star magnitude (telescope limit - 3, mag 10.3), Telrad circles, hop badges, and magnitude key. Redundant HTML headers and pinch-to-zoom tips are omitted so the chart occupies the full page.
   - **Page 3 (Step-by-Step Star-Hopping Narrative)**: Clean typography with readable hop steps and direct bottom navigation to the next target or catalog.
3. **High-Contrast Pure Monochrome**:
   - High-contrast pure white (`#ffffff`) background with solid black (`#000000`) stars, lines, and borders.
4. **Metadata & Library Organization**:
   - Name e-book file after the observation session (`<location-slug>-<YYYY-MM-DD>.epub`).
   - Populate standard Calibre series metadata (`calibre:series` and `calibre:series_index`), EPUB 3 collection tags, and PocketBook optimization metadata (`pocketbook:font-size="12px"`, `pocketbook:optimized-zoom="12px"`) so PocketBook OS automatically groups stargazing field guides into an indexed collection.

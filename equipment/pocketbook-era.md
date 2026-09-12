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
1. **Screen Aspect Ratio Optimization**:
   - Master chart viewport images should target the **3:4 aspect ratio** (e.g. `1264 × 1680` or `1200 × 1600`) to fill the screen without letterboxing or squishing.
2. **Multi-Page Target Flow**:
   - Rather than cramming three viewports onto one screen, split target guides into 3 dedicated, full-screen pages:
     - **Page 1 (Target Dossier & Eyepiece Simulation)**: Side-by-side Viewport B (negative inverted 180° simulation) and Viewport C (object ephemeris & specs, with hopping text dropped).
     - **Page 2 (Wide-Field Star Hopping Chart)**: Full-screen Viewport A with deep star magnitude (telescope limit - 3, mag ~10.0), Telrad circles, hop badges, and magnitude key.
     - **Page 3 (Step-by-Step Star-Hopping Narrative)**: Clean typography with large text for field reading.
3. **High-Contrast Pure Monochrome**:
   - High-contrast pure white (`#ffffff`) background with solid black (`#000000`) stars, lines, and borders.
4. **Metadata & Library Organization**:
   - Name e-book file after the observation session (`<location-slug>-<YYYY-MM-DD>.epub`).
   - Populate standard Calibre series metadata (`calibre:series` and `calibre:series_index`) and EPUB 3 collection tags so PocketBook OS automatically groups stargazing field guides into an indexed collection.

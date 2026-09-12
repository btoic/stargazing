# Equipment: Amazon Kindle Paperwhite (11th Gen)

## 1. Hardware & Display Specifications
- **Model**: Amazon Kindle Paperwhite (11th Generation / Signature Edition, Model M2L3EK / M2L4EK)
- **Device Class**: 6.8-inch E-Ink Handheld E-Reader / Field Companion
- **Screen Technology**: E-Ink Carta™ 1200 flush-front anti-glare display
- **Display Dimensions**: 6.8 inches (17.27 cm diagonal)
- **Active Resolution**: `1236 × 1648 pixels`
- **Pixel Density**: `300 ppi` (High-definition print-quality line sharpness)
- **Aspect Ratio**: `~3:4` (`0.750` portrait; `1.333` landscape)
- **Color Depth / Grayscale**: 16 levels of greyscale (smooth gradations for nebular contours and faint star magnitude discs)
- **Refresh Technology**: Fast partial screen refresh with minimal ghosting
- **Touch Interface**: Capacitive multi-touch supporting pinch-to-zoom for detailed chart inspection
- **Physical Controls**: Power button at bottom edge; page-turning via screen tap / swipe gestures
- **Environmental Rating**: `IPX8` waterproof (immersion up to 2 meters in freshwater for 60 min); resistant to nocturnal grass condensation, valley ground fog, and heavy dew

---

## 2. Field Craft & Dark Adaptation Protocols
- **Adjustable Warm Frontlight**:
  - The Kindle Paperwhite 11th Gen features 17 white and amber LEDs with independent brightness and color warmth controls (24 levels).
  - **Astronomical Field Mode**: Set warmth slider to **Level 24 (Maximum Amber/Orange)** to eliminate blue-spectrum photons and preserve rhodopsin in dark-adapted eyes.
  - Set overall brightness to lowest legible level (3–8 in dark-sky locations).
- **Physical Operation Under Red Light**:
  - Flush-front glass with etched matte finish minimizes reflection from red headlamps.
  - Capacitive tap zones allow easy page turns; avoid wet hands to prevent accidental touch input.

---

## 3. Digital Book & Sky Chart Rendering Standards
When compiling EPUB session packages tailored for Amazon Kindle:
1. **Amazon KF8 Rendering Engine Compatibility**:
   - Kindle reads EPUB files converted via **Send-to-Kindle** (Amazon Whispernet KFX pipeline) or side-loaded via Calibre.
   - EPUB 3 navigation (`nav.xhtml`) with fallback NCX (`toc.ncx`) ensures seamless table of contents access in the Kindle reading menu.
2. **Viewport Bounding (Preventing Trailing Phantom Blank Pages)**:
   - Amazon's KF8 renderer reserves top/bottom screen margins for the reading header and reading progress bar (time left in chapter / location).
   - Wide-field full-screen charts must cap height at `max-height: 88vh` (rather than 98vh) and side-by-side dossier charts at `max-height: 78vh` to prevent Kindle from inserting an artificial empty page flip after every chart image.
   - `@page` margins set to `0` with explicit `margin: 0 auto; display: block;` on chart containers.
3. **Typography & Font Scaling**:
   - Base font specified in scalable units (`1.0rem` / `16px` equivalent) to coordinate smoothly with Kindle's system font size slider (Aa menu).
   - Compact table cell padding (3–4px) to ensure multi-column target specs fit within 6.8" screen width without line clipping.
4. **Natural 4-Page Target Pagination (Zero Blank Pages)**:
   - **Page 1**: Eyepiece Simulation (inverted 180°) & Target Technical Dossier (`_eyepiece_dossier.png`).
   - **Page 2**: Constellation Context Orientation Chart (`_context.png`).
   - **Page 3**: Screen-fitted Wide-Field Star-Hopping Chart (`_widefield.png`) with stars down to mag 8.5.
   - **Page 4**: Step-by-Step Star-Hopping Narrative with direct jump links to previous/next targets.
5. **EPUB 3 Rendition Metadata**:
   - Declares standard EPUB 3 rendition properties:
     ```xml
     <meta property="rendition:layout">reflowable</meta>
     <meta property="rendition:orientation">portrait</meta>
     ```

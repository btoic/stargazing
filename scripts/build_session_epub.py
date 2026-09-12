#!/usr/bin/env python3
"""
scripts/build_session_epub.py - Compiles an observation session package into a single,
fully indexed, high-contrast EPUB e-book optimized for e-ink e-readers (specifically PocketBook Era,
Kindle, Kobo, Boox) and red-light nighttime viewing.

Key PocketBook Era Features:
- Multi-page target navigation (Natural 4-Page Zero-Blank-Page Flow):
  1. Eyepiece Simulation & Target Dossier side-by-side (Viewport B + C)
  2. Constellation Context & Orientation Chart (surrounding constellations, naked-eye stars to mag 6.2, next-page finder viewport boundary)
  3. Full-screen Wide-Field Star Hopping Chart (Viewport A, stars to mag 8.5, Telrad rings, magnitude key)
  4. Text-based Step-by-Step Star-Hopping Narrative
- Dynamic series metadata (Calibre series and EPUB 3 collection tags) incremented per observation
- Dynamic naming matching the observation session directory (<location>-<date>.epub)
"""

import os
import sys
import zipfile
import argparse
import uuid
import html
import shutil
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

def get_series_info(session_dir):
    """Calculates series metadata by discovering all observation directories."""
    observations_dir = os.path.join(REPO_ROOT, "observations")
    session_folder = os.path.basename(os.path.abspath(session_dir))
    series_name = "Stargazing Observations"

    if os.path.isdir(observations_dir):
        all_sessions = sorted([
            d for d in os.listdir(observations_dir)
            if os.path.isdir(os.path.join(observations_dir, d)) and not d.startswith('.')
        ])
    else:
        all_sessions = [session_folder]

    try:
        series_index = all_sessions.index(session_folder) + 1
    except ValueError:
        series_index = len(all_sessions) + 1

    return series_name, series_index

def build_epub(session_dir=None, output_path=None):
    if session_dir is None:
        session_dir = os.path.join(REPO_ROOT, "observations", "dvigrad-2026-09-12")
    session_dir = os.path.abspath(session_dir)

    if not os.path.isdir(session_dir):
        print(f"Error: Session directory '{session_dir}' does not exist.")
        sys.exit(1)

    session_folder = os.path.basename(os.path.abspath(session_dir))
    series_name, series_index = get_series_info(session_dir)

    # Output path default: <session-folder>.epub inside session_dir
    if output_path is None:
        output_path = os.path.join(session_dir, f"{session_folder}.epub")
    output_path = os.path.abspath(output_path)
    legacy_symlink_path = os.path.join(session_dir, "STARGAZING_FIELD_GUIDE.epub")

    print(f"Session:      {session_dir}")
    print(f"Folder Name:  {session_folder}")
    print(f"Series:       {series_name} (Issue #{series_index})")
    print(f"Output:       {output_path}")
    print(f"Legacy:       {legacy_symlink_path}")
    print(f"=======================================================\n")

    # Image source paths
    img_sources = {
        "full_sky_map.png": os.path.join(session_dir, "full_sky_map.png"),
        "timeline_gantt.png": os.path.join(session_dir, "timeline_gantt.png"),
        # Screen-optimized PocketBook Era assets
        "chart_1_lyra_m57_eyepiece_dossier.png": os.path.join(session_dir, "charts", "chart_1_lyra_m57_eyepiece_dossier.png"),
        "chart_1_lyra_m57_context.png": os.path.join(session_dir, "charts", "chart_1_lyra_m57_context.png"),
        "chart_1_lyra_m57_widefield.png": os.path.join(session_dir, "charts", "chart_1_lyra_m57_widefield.png"),
        "chart_2_vulpecula_m27_albireo_eyepiece_dossier.png": os.path.join(session_dir, "charts", "chart_2_vulpecula_m27_albireo_eyepiece_dossier.png"),
        "chart_2_vulpecula_m27_albireo_context.png": os.path.join(session_dir, "charts", "chart_2_vulpecula_m27_albireo_context.png"),
        "chart_2_vulpecula_m27_albireo_widefield.png": os.path.join(session_dir, "charts", "chart_2_vulpecula_m27_albireo_widefield.png"),
        "chart_3_hercules_m13_m92_eyepiece_dossier.png": os.path.join(session_dir, "charts", "chart_3_hercules_m13_m92_eyepiece_dossier.png"),
        "chart_3_hercules_m13_m92_context.png": os.path.join(session_dir, "charts", "chart_3_hercules_m13_m92_context.png"),
        "chart_3_hercules_m13_m92_widefield.png": os.path.join(session_dir, "charts", "chart_3_hercules_m13_m92_widefield.png"),
        "chart_4_andromeda_m31_eyepiece_dossier.png": os.path.join(session_dir, "charts", "chart_4_andromeda_m31_eyepiece_dossier.png"),
        "chart_4_andromeda_m31_context.png": os.path.join(session_dir, "charts", "chart_4_andromeda_m31_context.png"),
        "chart_4_andromeda_m31_widefield.png": os.path.join(session_dir, "charts", "chart_4_andromeda_m31_widefield.png"),
        "chart_5_perseus_double_cluster_eyepiece_dossier.png": os.path.join(session_dir, "charts", "chart_5_perseus_double_cluster_eyepiece_dossier.png"),
        "chart_5_perseus_double_cluster_context.png": os.path.join(session_dir, "charts", "chart_5_perseus_double_cluster_context.png"),
        "chart_5_perseus_double_cluster_widefield.png": os.path.join(session_dir, "charts", "chart_5_perseus_double_cluster_widefield.png"),
        "chart_6_scutum_m11_and_saturn_eyepiece_dossier.png": os.path.join(session_dir, "charts", "chart_6_scutum_m11_and_saturn_eyepiece_dossier.png"),
        "chart_6_scutum_m11_and_saturn_context.png": os.path.join(session_dir, "charts", "chart_6_scutum_m11_and_saturn_context.png"),
        "chart_6_scutum_m11_and_saturn_widefield.png": os.path.join(session_dir, "charts", "chart_6_scutum_m11_and_saturn_widefield.png"),
    }

    # Verify required images exist
    for name, path in img_sources.items():
        if not os.path.exists(path):
            print(f"Warning: Image {name} not found at {path}")

    # CSS Content (Optimized for PocketBook Era 12px Zoom)
    css_content = """/* Stargazing E-Reader Optimized Stylesheet (PocketBook Era 12px Zoom) */
@page {
    margin: 8px 10px;
}
html, body {
    font-family: sans-serif;
    font-size: 12px;
    line-height: 1.35;
    color: #000000;
    background-color: #ffffff;
    margin: 0;
    padding: 0;
}
h1, h2, h3, h4 {
    font-family: sans-serif;
    font-weight: bold;
    color: #000000;
    page-break-after: avoid;
    break-after: avoid;
}
h1 {
    font-size: 16px;
    border-bottom: 1.5px solid #000000;
    padding-bottom: 2px;
    margin-top: 0.25em;
    margin-bottom: 0.15em;
    line-height: 1.2;
}
h2 {
    font-size: 14px;
    border-bottom: 1px solid #666666;
    padding-bottom: 2px;
    margin-top: 0.35em;
    margin-bottom: 0.2em;
}
h3 {
    font-size: 12px;
    margin-top: 0.3em;
    margin-bottom: 0.1em;
}
p {
    margin: 0.3em 0;
}
.subtitle {
    font-family: sans-serif;
    font-size: 11px;
    color: #333333;
    margin-bottom: 0.35em;
    line-height: 1.25;
}
.nav-bar {
    font-family: sans-serif;
    font-size: 11px;
    margin: 0.2em 0 0.35em 0;
    padding: 0.2em 0;
    border-bottom: 1px dashed #666666;
}
.nav-bar a {
    text-decoration: none;
    font-weight: bold;
    color: #000000;
    background-color: #f0f0f0;
    padding: 2px 6px;
    border: 1px solid #333333;
    border-radius: 3px;
    margin-right: 4px;
    display: inline-block;
}
.nav-bar a:hover {
    background-color: #000000;
    color: #ffffff;
}
.bottom-nav {
    margin-top: 0.8em;
    border-top: 1px dashed #666666;
    border-bottom: none;
    padding-top: 0.4em;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.5em 0;
    font-size: 11px;
}
th, td {
    border: 1px solid #000000;
    padding: 4px 5px;
    text-align: left;
    vertical-align: top;
}
th {
    background-color: #e5e5e5;
    font-family: sans-serif;
    font-weight: bold;
}
tr:nth-child(even) td {
    background-color: #f9f9f9;
}
.center {
    text-align: center;
}
.callout {
    border: 1.5px solid #000000;
    background-color: #f8f8f8;
    padding: 6px 10px;
    margin: 0.5em 0;
    font-size: 11px;
}
.chart-img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0.4em auto;
    border: 1px solid #000000;
}
.chart-page {
    page-break-before: always;
    break-before: page;
    text-align: center;
    margin: 0;
    padding: 0;
}
.chart-img-side {
    max-width: 100%;
    max-height: 84vh;
    height: auto;
    display: block;
    margin: 0.2em auto;
    border: 1px solid #000000;
}
.chart-img-wide {
    max-width: 100%;
    max-height: 98vh;
    height: auto;
    display: block;
    margin: 0 auto;
    border: 1px solid #000000;
}
.instructions-page {
    page-break-before: always;
    break-before: page;
    margin-top: 0.4em;
    padding-top: 0;
}
.cover-box {
    text-align: center;
    padding: 2.0em 1em;
    border: 2px solid #000000;
    margin: 1.0em auto;
}
.cover-title {
    font-family: sans-serif;
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 0.2em;
}
.cover-sub {
    font-family: sans-serif;
    font-size: 13px;
    margin-bottom: 0.8em;
    color: #333333;
}
ol.hop-list {
    margin: 0.3em 0 0.8em 0;
    padding-left: 1.2em;
    font-size: 12px;
}
ol.hop-list li {
    margin-bottom: 0.45em;
    line-height: 1.35;
}
.series-tag {
    font-family: sans-serif;
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #555555;
    margin-bottom: 0.4em;
}
"""

    chapters = []

    # 1. Cover
    cover_html = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>{html.escape(session_folder)}</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="cover-box">
        <div class="series-tag">{html.escape(series_name)} — Issue #{series_index}</div>
        <div class="cover-title">{html.escape(session_folder.upper())}</div>
        <div class="cover-sub">Stargazing Field Manual &amp; High-Contrast Finder Charts</div>
        <hr style="border: 1px solid #000000; margin: 1.0em 0;"/>
        <p><b>Observation Target:</b> Dvigrad Medieval Ruins, Istria (Bortle 4)</p>
        <p><b>Date:</b> Saturday, September 12, 2026 (20:00 – 22:30 CEST)</p>
        <p><b>Coordinates:</b> 45.12637° N, 13.81296° E | Elevation: 143 m</p>
        <p><b>Telescope:</b> Sky-Watcher Skyliner 200P Dobsonian (8" f/6 Newtonian)</p>
        <p><b>Display Profile:</b> PocketBook Era E-Reader (Carta 1200, 300 ppi)</p>
        <p><b>Display Optimization:</b> 12px Font Zoom / Screen-Fitted 4-Page Flow</p>
        <hr style="border: 1px dashed #666666; margin: 1.0em 0;"/>
        <p style="font-size: 11px; color: #444444;">PocketBook Era Screen-Fitted Flow (Optimized for 12px Font Zoom)<br/>Toner-Saver Negative B/W Star Charts (Stars to Mag 8.5)</p>
        <p style="margin-top: 1.2em;"><a href="toc.xhtml" style="font-family: sans-serif; font-weight: bold; text-decoration: none; border: 2px solid #000; padding: 5px 12px; background: #eee; color: #000;">OPEN TABLE OF CONTENTS →</a></p>
    </div>
</body>
</html>"""
    chapters.append(("cover.xhtml", "Cover", cover_html))

    # 2. Table of Contents
    toc_html = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Table of Contents</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <h1>Table of Contents</h1>
    <div class="subtitle">{html.escape(session_folder)} — {html.escape(series_name)} #{series_index} (Optimized for 12px Zoom)</div>

    <h2>Part I: Field Protocols &amp; Sky Overview</h2>
    <ul>
        <li><a href="01_site_profile.xhtml">1. Location &amp; Dark Sky Profile (Dvigrad Bortle 4)</a></li>
        <li><a href="02_ephemeris.xhtml">2. Twilight Phases &amp; Astronomical Timeline</a></li>
        <li><a href="03_optics_and_fieldcraft.xhtml">3. Sky-Watcher 200P &amp; PocketBook Era Field Craft</a></li>
        <li><a href="04_target_catalog.xhtml">4. Curated Target Catalog (Interactive Index)</a></li>
        <li><a href="05_full_sky_map.xhtml">5. All-Sky Planisphere (Full Night Sky Map)</a></li>
    </ul>

    <h2>Part II: Target Navigation &amp; Star-Hops</h2>
    <ul>
        <li><a href="chart_1_m57.xhtml"><b>Target 1: M57 Ring Nebula in Lyra</b> (Planetary Nebula)</a></li>
        <li><a href="chart_2_m27.xhtml"><b>Target 2: M27 Dumbbell Nebula &amp; Albireo</b> (Nebula &amp; Double Star)</a></li>
        <li><a href="chart_3_hercules.xhtml"><b>Target 3: Hercules Globulars M13 &amp; M92</b> (Globular Clusters)</a></li>
        <li><a href="chart_4_andromeda.xhtml"><b>Target 4: M31 Andromeda Galaxy &amp; Satellites</b> (Spiral Galaxy)</a></li>
        <li><a href="chart_5_perseus.xhtml"><b>Target 5: Perseus Double Cluster</b> (Twin Open Clusters)</a></li>
        <li><a href="chart_6_scutum_saturn.xhtml"><b>Target 6: M11 Wild Duck Cluster &amp; Saturn</b> (Cluster &amp; Planet)</a></li>
    </ul>
</body>
</html>"""
    chapters.append(("toc.xhtml", "Table of Contents", toc_html))

    # 3. Location & Site Profile
    site_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>1. Site Profile</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="nav-bar">
        <a href="toc.xhtml">← Table of Contents</a>
        <a href="02_ephemeris.xhtml">Twilight &amp; Timeline →</a>
    </div>

    <h1>1. Location &amp; Dark Sky Profile</h1>
    <div class="subtitle">Dvigrad Medieval Ruins — Kanfanar Municipality, Istria, Croatia</div>

    <h2>Geographic Position</h2>
    <table>
        <tr><th>Parameter</th><th>Value</th><th>Field Significance</th></tr>
        <tr><td><b>Coordinates</b></td><td><b>45.12637° N, 13.81296° E</b></td><td>Central Istrian karst plateau; Lim Valley floor.</td></tr>
        <tr><td><b>Elevation</b></td><td><b>143 m</b></td><td>Depression topography: prone to nocturnal cold air pooling &amp; dew.</td></tr>
        <tr><td><b>Accessibility</b></td><td>Direct asphalt / macadam</td><td>Unload telescope 10 m from observing clearing outside ruins.</td></tr>
    </table>

    <h2>Sky Brightness &amp; Transparency</h2>
    <table>
        <tr><th>Metric</th><th>Observed Value</th><th>Visual Characteristics</th></tr>
        <tr><td><b>Bortle Class</b></td><td><b>Class 4 (Rural/Suburban)</b></td><td>Zodiacal light visible in autumn; subtle light domes on horizons.</td></tr>
        <tr><td><b>SQM</b></td><td><b>~21.05 mag/arcsec²</b></td><td>High-contrast deep sky observing; M31 and M13 visible naked-eye.</td></tr>
        <tr><td><b>NELM</b></td><td><b>6.0 – 6.2 mag</b></td><td>Faint naked-eye stars visible at zenith.</td></tr>
        <tr><td><b>Milky Way</b></td><td><b>Clearly Structured</b></td><td>Great Rift through Cygnus/Aquila visible with dark clouds.</td></tr>
    </table>

    <h2>Horizon Obstruction Profile</h2>
    <p>Surrounding oak/pine forests and terrain ridges create a <b>10° to 15° obstruction</b>:</p>
    <ul>
        <li><b>South &amp; South-West (Lim Valley):</b> Ridge rises 12°–15°. Southern targets sink into foliage early.</li>
        <li><b>East &amp; North-East:</b> Rising terrain slope of 10°–14°. Rising targets (Saturn, Perseus) clear thermal turbulence above ~15°.</li>
        <li><b>Zenith (&gt;30° Altitude):</b> Completely unobstructed, crystalline transparency.</li>
    </ul>
</body>
</html>"""
    chapters.append(("01_site_profile.xhtml", "1. Location & Site Profile", site_html))

    # 4. Ephemeris & Timeline
    eph_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>2. Twilight &amp; Timeline</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="nav-bar">
        <a href="toc.xhtml">← Table of Contents</a>
        <a href="01_site_profile.xhtml">← Site Profile</a>
        <a href="03_optics_and_fieldcraft.xhtml">Optics &amp; Field Craft →</a>
    </div>

    <h1>2. Twilight Phases &amp; Observation Timeline</h1>
    <div class="subtitle">Saturday, September 12, 2026 — Ephemeris for Dvigrad</div>

    <div class="callout">
        <b>MOON STATUS: ZERO LUNAR LIGHT POLLUTION!</b><br/>
        On September 12, 2026, the Moon is a razor-thin <b>3.1% waxing crescent</b> and <b>sets at 19:38 CEST</b>. Throughout the session (20:00–22:30 CEST), the Moon is <b>below the horizon (-4° to -30° Alt)</b>, providing 100% dark sky contrast!
    </div>

    <h2>Twilight Schedule Table</h2>
    <table>
        <tr><th>Phase</th><th>Window (CEST)</th><th>Sun Alt</th><th>Program Guidance</th></tr>
        <tr><td><b>Setup &amp; Cooldown</b></td><td>19:30 – 20:00</td><td>-2° to -8°</td><td>Primary mirror cooldown. 9x50 finder alignment on Vega / Arcturus.</td></tr>
        <tr><td><b>Nautical Twilight</b></td><td>20:00 – 20:26</td><td>-8° to -12°</td><td>Sky deepens to slate blue. High-contrast double star Albireo sweep.</td></tr>
        <tr><td><b>Astro Twilight</b></td><td>20:26 – 21:05</td><td>-12° to -18°</td><td>Milky Way emerges. Globular clusters pop into view (M13, M92, M11).</td></tr>
        <tr><td><b>True Astro Darkness</b></td><td><b>21:05 – 22:30+</b></td><td><b>&lt; -18.0°</b></td><td><b>Maximum darkness.</b> Diffuse nebulae (M57, M27) and external galaxies (M31, M32, M110).</td></tr>
    </table>

    <h2>Observation Timeline Chart</h2>
    <img src="images/timeline_gantt.png" class="chart-img" alt="Timeline Gantt Chart"/>
</body>
</html>"""
    chapters.append(("02_ephemeris.xhtml", "2. Twilight & Timeline", eph_html))

    # 5. Optics & Field Craft
    optics_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>3. Optics &amp; Field Craft</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="nav-bar">
        <a href="toc.xhtml">← Table of Contents</a>
        <a href="02_ephemeris.xhtml">← Twilight &amp; Timeline</a>
        <a href="04_target_catalog.xhtml">Target Catalog →</a>
    </div>

    <h1>3. Telescope Optics &amp; Field Craft</h1>
    <div class="subtitle">Sky-Watcher 200P Dobsonian &amp; PocketBook Era Field Configuration</div>

    <h2>Telescope Optical Specifications</h2>
    <table>
        <tr><th>Specification</th><th>Value</th><th>Field Significance</th></tr>
        <tr><td><b>Aperture</b></td><td>200 mm (7.87")</td><td>Collects 820× more light than human eye.</td></tr>
        <tr><td><b>Focal Length</b></td><td>1200 mm</td><td>f/6 focal ratio with minimal off-axis coma.</td></tr>
        <tr><td><b>Dawes Resolving Limit</b></td><td>0.58 arcsec</td><td>Resolves tight double stars &amp; ring features.</td></tr>
        <tr><td><b>Limiting Magnitude</b></td><td>13.3 – 14.0 mag</td><td>Telescope chart threshold: mag 8.5.</td></tr>
    </table>

    <h2>Eyepiece Reference</h2>
    <table>
        <tr><th>Eyepiece</th><th>Power</th><th>Exit Pupil</th><th>True Field (TFOV)</th><th>Primary Use</th></tr>
        <tr><td><b>20 mm</b></td><td><b>60×</b></td><td>3.33 mm</td><td><b>~50' (0.83°)</b></td><td>Wide fields: M31 Andromeda, M27 Dumbbell, Double Cluster.</td></tr>
        <tr><td><b>12.5 mm</b></td><td><b>96×</b></td><td>2.08 mm</td><td><b>~31' (0.52°)</b></td><td>Resolution: M13 &amp; M92 core stars, M57 Ring hole, Saturn rings.</td></tr>
    </table>

    <h2>PocketBook Era Field Protocols</h2>
    <div class="callout">
        <b>1. SMARTLIGHT NIGHT-VISION CALIBRATION</b><br/>
        Set SMARTlight frontlight to <b>100% warm amber</b> (zero blue light emission) and set overall brightness to minimum legibility (5%–15%) to prevent pupil constriction and preserve scotopic vision.
    </div>

    <div class="callout">
        <b>2. SCREEN-FITTED PINCH-TO-ZOOM</b><br/>
        All wide-field star charts in Part II are formatted for the PocketBook Era's 3:4 screen ratio. Use a two-finger pinch gesture on the touchscreen to zoom directly into dense field star clusters.
    </div>

    <div class="callout">
        <b>3. DEW RESISTANCE (IPX8)</b><br/>
        The PocketBook Era is IPX8 waterproof. Heavy Lim Valley condensation will not harm the device. Use the physical edge buttons to turn pages if moist fingers cause capacitive touch resistance.
    </div>
</body>
</html>"""
    chapters.append(("03_optics_and_fieldcraft.xhtml", "3. Optics & Field Craft", optics_html))

    # 6. Curated Target Catalog
    catalog_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>4. Curated Target Catalog</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="nav-bar">
        <a href="toc.xhtml">← Table of Contents</a>
        <a href="03_optics_and_fieldcraft.xhtml">← Optics &amp; Field Craft</a>
        <a href="05_full_sky_map.xhtml">All-Sky Map →</a>
    </div>

    <h1>4. Curated Target Catalog</h1>
    <div class="subtitle">Mid-Session Ephemeris @ 21:15 CEST — Tap any chart link to open</div>

    <table>
        <tr>
            <th>#</th>
            <th>Target Name</th>
            <th>Const</th>
            <th>Type</th>
            <th>Mag</th>
            <th>Alt / Az @ 21:15</th>
            <th>Eyepiece</th>
            <th>Finder Chart Link</th>
        </tr>
        <tr>
            <td>1</td>
            <td><b>Albireo (β Cyg)</b></td>
            <td>Cyg</td>
            <td>Double Star</td>
            <td>3.1/5.1</td>
            <td>73° / 170° (S)</td>
            <td>20mm &amp; 12.5mm</td>
            <td><a href="chart_2_m27.xhtml"><b>Chart 2 →</b></a></td>
        </tr>
        <tr>
            <td>2</td>
            <td><b>M57 Ring Nebula</b></td>
            <td>Lyr</td>
            <td>Planetary Neb.</td>
            <td>8.8</td>
            <td>75.4° / 218° (SW)</td>
            <td>12.5mm (96×)</td>
            <td><a href="chart_1_m57.xhtml"><b>Chart 1 →</b></a></td>
        </tr>
        <tr>
            <td>3</td>
            <td><b>M13 Great Globular</b></td>
            <td>Her</td>
            <td>Globular Cl.</td>
            <td>5.8</td>
            <td>56.2° / 271° (W)</td>
            <td>12.5mm (96×)</td>
            <td><a href="chart_3_hercules.xhtml"><b>Chart 3 →</b></a></td>
        </tr>
        <tr>
            <td>4</td>
            <td><b>M92 Globular</b></td>
            <td>Her</td>
            <td>Globular Cl.</td>
            <td>6.3</td>
            <td>65.4° / 295° (WNW)</td>
            <td>12.5mm (96×)</td>
            <td><a href="chart_3_hercules.xhtml"><b>Chart 3 →</b></a></td>
        </tr>
        <tr>
            <td>5</td>
            <td><b>M11 Wild Duck</b></td>
            <td>Sct</td>
            <td>Open Cluster</td>
            <td>5.8</td>
            <td>37.7° / 196° (SSW)</td>
            <td>12.5mm (96×)</td>
            <td><a href="chart_6_scutum_saturn.xhtml"><b>Chart 6 →</b></a></td>
        </tr>
        <tr>
            <td>6</td>
            <td><b>Coathanger (Cr 399)</b></td>
            <td>Vul</td>
            <td>Asterism</td>
            <td>3.6</td>
            <td>65.0° / 195° (SSW)</td>
            <td>20mm (60×)</td>
            <td><a href="chart_2_m27.xhtml"><b>Chart 2 →</b></a></td>
        </tr>
        <tr>
            <td>7</td>
            <td><b>M27 Dumbbell Neb.</b></td>
            <td>Vul</td>
            <td>Planetary Neb.</td>
            <td>7.4</td>
            <td>67.2° / 166° (SSE)</td>
            <td>20mm (60×)</td>
            <td><a href="chart_2_m27.xhtml"><b>Chart 2 →</b></a></td>
        </tr>
        <tr>
            <td>8</td>
            <td><b>Double Cluster</b></td>
            <td>Per</td>
            <td>Dual Open Cl.</td>
            <td>3.7/3.8</td>
            <td>31.6° / 039° (NE)</td>
            <td>20mm (60×)</td>
            <td><a href="chart_5_perseus.xhtml"><b>Chart 5 →</b></a></td>
        </tr>
        <tr>
            <td>9</td>
            <td><b>M31 Andromeda</b></td>
            <td>And</td>
            <td>Spiral Galaxy</td>
            <td>3.4</td>
            <td>36.2° / 065° (ENE)</td>
            <td>20mm (60×)</td>
            <td><a href="chart_4_andromeda.xhtml"><b>Chart 4 →</b></a></td>
        </tr>
        <tr>
            <td>10</td>
            <td><b>Saturn &amp; Titan</b></td>
            <td>Aqr</td>
            <td>Planet &amp; Rings</td>
            <td>+0.6</td>
            <td>18°–23° / 115° (ESE)</td>
            <td>12.5mm (96×)</td>
            <td><a href="chart_6_scutum_saturn.xhtml"><b>Chart 6 →</b></a></td>
        </tr>
    </table>
</body>
</html>"""
    chapters.append(("04_target_catalog.xhtml", "4. Curated Target Catalog", catalog_html))

    # 7. All-Sky Planisphere
    skymap_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>5. All-Sky Planisphere</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="nav-bar">
        <a href="toc.xhtml">← Table of Contents</a>
        <a href="04_target_catalog.xhtml">← Target Catalog</a>
        <a href="chart_1_m57.xhtml">Chart 1: M57 →</a>
    </div>

    <h1>5. All-Sky Planisphere</h1>
    <div class="subtitle">Full Night Sky Map @ 21:15 CEST — Dvigrad, Istria (Bortle 4)</div>

    <div class="callout">
        <b>HOW TO READ THE PLANISPHERE:</b><br/>
        • <b>Center of Map:</b> Zenith (straight up overhead).<br/>
        • <b>Outer Perimeter:</b> Horizon. Red inner dashed ring marks Dvigrad's <b>15° terrain &amp; forest obstruction limit</b>.<br/>
        • <b>Holding the Chart:</b> When facing South, hold the chart with "SOUTH" at the bottom. When facing North, turn the chart so "NORTH" is at the bottom.
    </div>

    <img src="images/full_sky_map.png" class="chart-img" alt="All-Sky Planisphere"/>
</body>
</html>"""
    chapters.append(("05_full_sky_map.xhtml", "5. All-Sky Planisphere", skymap_html))


    # ==============================================================================
    # TARGET 1: M57 RING NEBULA (Unified 4-Page Flow)
    # ==============================================================================
    c1_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Target 1: M57 Ring Nebula</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <!-- SCREEN 1: Eyepiece Simulation & Target Dossier -->
    <div class="nav-bar">
        <a href="toc.xhtml">← Contents</a>
        <a href="04_target_catalog.xhtml">Catalog</a>
        <a href="chart_2_m27.xhtml">Target 2 (M27) →</a>
    </div>

    <h1>Target 1: M57 Ring Nebula</h1>
    <div class="subtitle">Lyra • Planetary Nebula • Mag 8.8 • Size 1.4' × 1.0'</div>

    <img src="images/chart_1_lyra_m57_eyepiece_dossier.png" class="chart-img-side" alt="M57 Eyepiece Simulation and Target Dossier"/>

    <!-- SCREEN 2: Constellation Context Orientation Chart -->
    <div class="chart-page">
        <img src="images/chart_1_lyra_m57_context.png" class="chart-img-wide" alt="M57 Constellation Context Orientation Chart"/>
    </div>

    <!-- SCREEN 3: Fullscreen Wide-Field Star-Hopping Chart -->
    <div class="chart-page">
        <img src="images/chart_1_lyra_m57_widefield.png" class="chart-img-wide" alt="M57 Wide-Field Star-Hopping Chart"/>
    </div>

    <!-- SCREEN 4: Step-by-Step Star-Hopping Guide -->
    <div class="instructions-page">
        <h2>Target 1: Step-by-Step Star-Hopping Guide</h2>
        <div class="subtitle">Field Navigation &amp; Eyepiece Acquisition Strategy</div>

        <ol class="hop-list">
            <li><b>[STEP 1] Start at Vega (α Lyrae, Mag 0.03):</b> Look almost straight overhead for the brilliant sapphire-white anchor of the Summer Triangle. Center Vega in your finder scope.</li>
            <li><b>[STEP 2] Trace the Lyra Parallelogram:</b> Nudge 6° south of Vega to locate the prominent four-star parallelogram formed by ζ, δ, γ, and β Lyrae (Sulafat &amp; Sheliak).</li>
            <li><b>[STEP 3] Bridge between β and γ Lyrae:</b> Locate β Lyrae (Sheliak, mag 3.5) and γ Lyrae (Sulafat, mag 3.2), separated by 3.2° at the southern base of the parallelogram. Center your Telrad / finder reticle exactly halfway between them.</li>
            <li><b>[STEP 4] Acquire in 20 mm Eyepiece:</b> Look through the 20 mm eyepiece. M57 appears as a small, intense, grey smoke ring or hollow "smoke cheerio" floating between two faint 12th-mag field stars.</li>
            <li><b>[STEP 5] Resolve at 12.5 mm (96×):</b> Switch to the 12.5 mm eyepiece. The dark central hole and oval torus ring structure become unmistakable. Use averted vision to enhance contrast along the outer ring boundary!</li>
        </ol>

        <div class="nav-bar bottom-nav">
            <a href="04_target_catalog.xhtml">← Back to Catalog</a>
            <a href="chart_2_m27.xhtml">Next: Target 2 (M27 &amp; Albireo) →</a>
        </div>
    </div>
</body>
</html>"""
    chapters.append(("chart_1_m57.xhtml", "Target 1: M57 Ring Nebula", c1_html))


    # ==============================================================================
    # TARGET 2: M27 DUMBBELL NEBULA & ALBIREO (Unified 4-Page Flow)
    # ==============================================================================
    c2_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Target 2: M27 Dumbbell &amp; Albireo</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <!-- SCREEN 1: Eyepiece Simulation & Target Dossier -->
    <div class="nav-bar">
        <a href="toc.xhtml">← Contents</a>
        <a href="04_target_catalog.xhtml">Catalog</a>
        <a href="chart_1_m57.xhtml">← Target 1 (M57)</a>
        <a href="chart_3_hercules.xhtml">Target 3 (Hercules) →</a>
    </div>

    <h1>Target 2: M27 Dumbbell &amp; Albireo</h1>
    <div class="subtitle">Vulpecula / Cygnus • Planetary Nebula &amp; Showcase Binary Star</div>

    <img src="images/chart_2_vulpecula_m27_albireo_eyepiece_dossier.png" class="chart-img-side" alt="M27 Eyepiece Simulation and Target Dossier"/>

    <!-- SCREEN 2: Constellation Context Orientation Chart -->
    <div class="chart-page">
        <img src="images/chart_2_vulpecula_m27_albireo_context.png" class="chart-img-wide" alt="M27 and Albireo Constellation Context Orientation Chart"/>
    </div>

    <!-- SCREEN 3: Fullscreen Wide-Field Star-Hopping Chart -->
    <div class="chart-page">
        <img src="images/chart_2_vulpecula_m27_albireo_widefield.png" class="chart-img-wide" alt="M27 Wide-Field Star-Hopping Chart"/>
    </div>

    <!-- SCREEN 4: Step-by-Step Star-Hopping Guide -->
    <div class="instructions-page">
        <h2>Target 2: Step-by-Step Star-Hopping Guide</h2>
        <div class="subtitle">Field Navigation &amp; Eyepiece Acquisition Strategy</div>

        <ol class="hop-list">
            <li><b>Showcase Double Star: Albireo (β Cygni):</b> Look at the base of the Northern Cross in Cygnus. Center the naked-eye 3rd-mag star in your finder. In the 20 mm eyepiece, marvel at the striking color contrast between the golden-topaz primary and vivid sky-blue companion star!</li>
            <li><b>[STEP 1] Locate Sagitta (The Arrow):</b> From Albireo, look ~8° south-east for the compact, distinctive asterism of Sagitta (α, β, δ, γ Sge).</li>
            <li><b>[STEP 2] Find γ Sagittae:</b> Identify γ Sge (+3.5 mag), the sharp forward tip of the arrow pointing eastward.</li>
            <li><b>[STEP 3] Hop 3.2° North into Vulpecula:</b> Place the outer ring of your Telrad (or edge of 9x50 finder) on γ Sge and nudge directly North by 3.2°.</li>
            <li><b>[STEP 4] Acquire M27 in 20 mm Eyepiece:</b> Look near 14 Vulpeculae (+5.8 mag). M27 appears as a huge, bright, glowing ghostly hourglass or "apple-core" nebula against the rich star field of the Milky Way!</li>
        </ol>

        <div class="nav-bar bottom-nav">
            <a href="04_target_catalog.xhtml">← Back to Catalog</a>
            <a href="chart_3_hercules.xhtml">Next: Target 3 (Hercules Globulars) →</a>
        </div>
    </div>
</body>
</html>"""
    chapters.append(("chart_2_m27.xhtml", "Target 2: M27 & Albireo", c2_html))


    # ==============================================================================
    # TARGET 3: HERCULES GLOBULARS M13 & M92 (Unified 4-Page Flow)
    # ==============================================================================
    c3_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Target 3: Hercules Globulars M13 &amp; M92</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <!-- SCREEN 1: Eyepiece Simulation & Target Dossier -->
    <div class="nav-bar">
        <a href="toc.xhtml">← Contents</a>
        <a href="04_target_catalog.xhtml">Catalog</a>
        <a href="chart_2_m27.xhtml">← Target 2 (M27)</a>
        <a href="chart_4_andromeda.xhtml">Target 4 (Andromeda) →</a>
    </div>

    <h1>Target 3: Hercules Globulars M13 &amp; M92</h1>
    <div class="subtitle">Hercules • Showcase Globular Star Clusters</div>

    <img src="images/chart_3_hercules_m13_m92_eyepiece_dossier.png" class="chart-img-side" alt="Hercules M13 Eyepiece Simulation and Target Dossier"/>

    <!-- SCREEN 2: Constellation Context Orientation Chart -->
    <div class="chart-page">
        <img src="images/chart_3_hercules_m13_m92_context.png" class="chart-img-wide" alt="Hercules Globulars Constellation Context Orientation Chart"/>
    </div>

    <!-- SCREEN 3: Fullscreen Wide-Field Star-Hopping Chart -->
    <div class="chart-page">
        <img src="images/chart_3_hercules_m13_m92_widefield.png" class="chart-img-wide" alt="Hercules Wide-Field Star-Hopping Chart"/>
    </div>

    <!-- SCREEN 4: Step-by-Step Star-Hopping Guide -->
    <div class="instructions-page">
        <h2>Target 3: Step-by-Step Star-Hopping Guide</h2>
        <div class="subtitle">Field Navigation &amp; Eyepiece Acquisition Strategy</div>

        <ol class="hop-list">
            <li><b>[STEP 1] Locate the Keystone of Hercules:</b> High in the western sky, locate the distinctive four-star trapezoid ("Keystone") formed by η, ζ, ε, and π Herculis.</li>
            <li><b>[STEP 2] Trace the Western Edge:</b> Identify η Herculis (NW corner, mag 3.5) and ζ Herculis (SW corner, mag 2.8).</li>
            <li><b>[STEP 3] Hop along the η–ζ Line:</b> Move roughly 1/3 of the way down from η toward ζ Herculis.</li>
            <li><b>[STEP 4] Acquire M13:</b> In your finder or 20 mm eyepiece, M13 appears as an unmistakable bright fuzzy snowball. In Bortle 4 skies at Dvigrad, it is even visible to the naked eye with averted vision!</li>
            <li><b>[STEP 5] Core Resolution at 12.5 mm:</b> Switch to 12.5 mm (96×). Hundreds of sparkling diamond stars resolve across the core. Search for the famous dark three-bladed "propeller" dust lane in the cluster's southeastern quadrant.</li>
            <li><b>[STEP 6] Bonus Target M92:</b> Return to the Keystone. From π Herculis (NE corner, mag 3.2), hop 6.2° due North to find M92, a brilliant, compact globular cluster with a dense, glittering nucleus.</li>
        </ol>

        <div class="nav-bar bottom-nav">
            <a href="04_target_catalog.xhtml">← Back to Catalog</a>
            <a href="chart_4_andromeda.xhtml">Next: Target 4 (Andromeda Galaxy) →</a>
        </div>
    </div>
</body>
</html>"""
    chapters.append(("chart_3_hercules.xhtml", "Target 3: Hercules Globulars", c3_html))


    # ==============================================================================
    # TARGET 4: M31 ANDROMEDA GALAXY (Unified 4-Page Flow)
    # ==============================================================================
    c4_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Target 4: M31 Andromeda Galaxy &amp; Satellites</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <!-- SCREEN 1: Eyepiece Simulation & Target Dossier -->
    <div class="nav-bar">
        <a href="toc.xhtml">← Contents</a>
        <a href="04_target_catalog.xhtml">Catalog</a>
        <a href="chart_3_hercules.xhtml">← Target 3 (Hercules)</a>
        <a href="chart_5_perseus.xhtml">Target 5 (Perseus) →</a>
    </div>

    <h1>Target 4: M31 Andromeda Galaxy &amp; Satellites</h1>
    <div class="subtitle">Andromeda • Giant Spiral Galaxy + Satellite Dwarfs M32 &amp; M110</div>

    <img src="images/chart_4_andromeda_m31_eyepiece_dossier.png" class="chart-img-side" alt="M31 Eyepiece Simulation and Target Dossier"/>

    <!-- SCREEN 2: Constellation Context Orientation Chart -->
    <div class="chart-page">
        <img src="images/chart_4_andromeda_m31_context.png" class="chart-img-wide" alt="Andromeda Galaxy Constellation Context Orientation Chart"/>
    </div>

    <!-- SCREEN 3: Fullscreen Wide-Field Star-Hopping Chart -->
    <div class="chart-page">
        <img src="images/chart_4_andromeda_m31_widefield.png" class="chart-img-wide" alt="Andromeda Wide-Field Star-Hopping Chart"/>
    </div>

    <!-- SCREEN 4: Step-by-Step Star-Hopping Guide -->
    <div class="instructions-page">
        <h2>Target 4: Step-by-Step Star-Hopping Guide</h2>
        <div class="subtitle">Field Navigation &amp; Eyepiece Acquisition Strategy</div>

        <ol class="hop-list">
            <li><b>[STEP 1] Start at the Great Square of Pegasus:</b> Locate the large celestial diamond rising in the East. Identify Alpheratz (α Andromedae / δ Pegasi, mag 2.1), the northeastern corner star.</li>
            <li><b>[STEP 2] Trace the Andromeda Star Chain to Mirach:</b> Move northeast along Andromeda’s main backbone through δ Andromedae (mag 3.3) to prominent reddish Mirach (β Andromedae, mag 2.1), roughly 14° from Alpheratz.</li>
            <li><b>[STEP 3] Turn 90° North-West to μ Andromedae:</b> From Mirach, make a sharp 90° turn toward the northwest and hop 3.5° to μ Andromedae (mag 3.9).</li>
            <li><b>[STEP 4] Continue North-West to ν Andromedae:</b> Hop another 3.5° in the exact same direction to ν Andromedae (mag 4.5).</li>
            <li><b>[STEP 5] Slew 1.5° NW into M31:</b> Nudge 1.5° northwest past ν Andromedae. The dazzling nuclear bulge of the Andromeda Galaxy floods the field of view!</li>
            <li><b>[STEP 6] Scan for Satellite Galaxies:</b> In the 20 mm eyepiece, look 24' south of the core for bright, compact elliptical dwarf <b>M32</b>, and 35' northwest across the dust lane for faint, elongated dwarf spheroidal <b>M110</b>.</li>
        </ol>

        <div class="nav-bar bottom-nav">
            <a href="04_target_catalog.xhtml">← Back to Catalog</a>
            <a href="chart_5_perseus.xhtml">Next: Target 5 (Double Cluster) →</a>
        </div>
    </div>
</body>
</html>"""
    chapters.append(("chart_4_andromeda.xhtml", "Target 4: M31 Andromeda Galaxy", c4_html))


    # ==============================================================================
    # TARGET 5: PERSEUS DOUBLE CLUSTER (Unified 4-Page Flow)
    # ==============================================================================
    c5_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Target 5: Perseus Double Cluster</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <!-- SCREEN 1: Eyepiece Simulation & Target Dossier -->
    <div class="nav-bar">
        <a href="toc.xhtml">← Contents</a>
        <a href="04_target_catalog.xhtml">Catalog</a>
        <a href="chart_4_andromeda.xhtml">← Target 4 (Andromeda)</a>
        <a href="chart_6_scutum_saturn.xhtml">Target 6 (M11 &amp; Saturn) →</a>
    </div>

    <h1>Target 5: Perseus Double Cluster</h1>
    <div class="subtitle">Perseus • Twin Open Star Clusters NGC 869 &amp; NGC 884 (Caldwell 14)</div>

    <img src="images/chart_5_perseus_double_cluster_eyepiece_dossier.png" class="chart-img-side" alt="Double Cluster Eyepiece Simulation and Target Dossier"/>

    <!-- SCREEN 2: Constellation Context Orientation Chart -->
    <div class="chart-page">
        <img src="images/chart_5_perseus_double_cluster_context.png" class="chart-img-wide" alt="Double Cluster Constellation Context Orientation Chart"/>
    </div>

    <!-- SCREEN 3: Fullscreen Wide-Field Star-Hopping Chart -->
    <div class="chart-page">
        <img src="images/chart_5_perseus_double_cluster_widefield.png" class="chart-img-wide" alt="Double Cluster Wide-Field Star-Hopping Chart"/>
    </div>

    <!-- SCREEN 4: Step-by-Step Star-Hopping Guide -->
    <div class="instructions-page">
        <h2>Target 5: Step-by-Step Star-Hopping Guide</h2>
        <div class="subtitle">Field Navigation &amp; Eyepiece Acquisition Strategy</div>

        <ol class="hop-list">
            <li><b>[STEP 1] Locate Cassiopeia's "W":</b> High in the northeastern sky, identify the prominent zigzag of Cassiopeia.</li>
            <li><b>[STEP 2] Identify γ and δ Cassiopeiae:</b> Find central star Navi (γ Cas) and bottom-left vertex Ruchbah (δ Cas, mag 2.7).</li>
            <li><b>[STEP 3] Extend the Line toward Perseus:</b> Draw a line from γ Cas through δ Cas and project it southeast into Perseus by roughly the same distance (~6°).</li>
            <li><b>[STEP 4] Naked-Eye Confirmation:</b> In Bortle 4 skies at Dvigrad, an unmistakable glowing double patch of mist is clearly visible without optical aid.</li>
            <li><b>[STEP 5] Center in Finder / Telrad:</b> Point your finder reticle directly at the twin mist patches.</li>
            <li><b>[STEP 6] Marvel in 20 mm Eyepiece:</b> Looking through the 20 mm eyepiece reveals hundreds of glittering diamond stars across NGC 869 and NGC 884. Note the bright orange carbon supergiant stars in the heart of NGC 884!</li>
        </ol>

        <div class="nav-bar bottom-nav">
            <a href="04_target_catalog.xhtml">← Back to Catalog</a>
            <a href="chart_6_scutum_saturn.xhtml">Next: Target 6 (M11 &amp; Saturn) →</a>
        </div>
    </div>
</body>
</html>"""
    chapters.append(("chart_5_perseus.xhtml", "Target 5: Perseus Double Cluster", c5_html))


    # ==============================================================================
    # TARGET 6: M11 WILD DUCK CLUSTER & SATURN (Unified 4-Page Flow)
    # ==============================================================================
    c6_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Target 6: M11 Wild Duck &amp; Saturn</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <!-- SCREEN 1: Eyepiece Simulation & Target Dossier -->
    <div class="nav-bar">
        <a href="toc.xhtml">← Contents</a>
        <a href="04_target_catalog.xhtml">Catalog</a>
        <a href="chart_5_perseus.xhtml">← Target 5 (Perseus)</a>
        <a href="toc.xhtml">Contents →</a>
    </div>

    <h1>Target 6: M11 Wild Duck &amp; Saturn</h1>
    <div class="subtitle">Scutum / Aquarius • Dense Open Cluster &amp; Ringed Planet Finale</div>

    <img src="images/chart_6_scutum_m11_and_saturn_eyepiece_dossier.png" class="chart-img-side" alt="M11 and Saturn Eyepiece Simulations and Target Dossier"/>

    <!-- SCREEN 2: Constellation Context Orientation Chart -->
    <div class="chart-page">
        <img src="images/chart_6_scutum_m11_and_saturn_context.png" class="chart-img-wide" alt="M11 and Saturn Constellation Context Orientation Chart"/>
    </div>

    <!-- SCREEN 3: Fullscreen Wide-Field Star-Hopping Chart -->
    <div class="chart-page">
        <img src="images/chart_6_scutum_m11_and_saturn_widefield.png" class="chart-img-wide" alt="M11 and Saturn Wide-Field Star-Hopping Chart"/>
    </div>

    <!-- SCREEN 4: Step-by-Step Star-Hopping Guide -->
    <div class="instructions-page">
        <h2>Target 6: Step-by-Step Star-Hopping Guide</h2>
        <div class="subtitle">Field Navigation &amp; Eyepiece Acquisition Strategy</div>

        <ol class="hop-list">
            <li><b>[STEP 1] Find M11 via Aquila's Backbone:</b> Start at brilliant Altair (α Aql). Trace the eagle's body southwest across 14° of sky to λ Aquilae (+3.4 mag).</li>
            <li><b>[STEP 2] Hop 4.5° WSW into the Scutum Star Cloud:</b> From λ Aql, nudge 4.5° west-southwest into the rich star clouds of Scutum.</li>
            <li><b>[STEP 3] View M11:</b> In the 20 mm eyepiece, M11 resembles a compact, glittering V-shaped wedge (like a flight of wild ducks) containing over 400 stars with an 8th-mag yellow giant star near its apex. At 12.5 mm (96×), the star field explodes into dense pinpricks.</li>
            <li><b>[STEP 4] Saturn Planetary Finale (Observe after 21:40 CEST):</b> Look low in the East-South-East horizon below Pegasus. Saturn is the brightest golden, steady non-twinkling object in Aquarius.</li>
            <li><b>[STEP 5] Inspect Saturn at 96× (12.5 mm):</b> As Saturn rises past 20° altitude above ground air turbulence:
                <br/>• <b>Rings:</b> View the stunning ring plane tilted nearly edge-on. Look for the Cassini Division during moments of steady seeing.
                <br/>• <b>Titan:</b> Saturn's largest moon (mag 8.4) shines clearly 4 ring-diameters away!
            </li>
        </ol>

        <div class="nav-bar bottom-nav">
            <a href="04_target_catalog.xhtml">← Back to Catalog</a>
            <a href="toc.xhtml">Return to Table of Contents →</a>
        </div>
    </div>
</body>
</html>"""
    chapters.append(("chart_6_scutum_saturn.xhtml", "Target 6: M11 & Saturn", c6_html))


    # Package files into EPUB ZIP archive
    print("Packaging EPUB files...")

    book_uuid = f"urn:uuid:stargazing-{session_folder}"
    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    with zipfile.ZipFile(output_path, "w") as zf:
        # 1. mimetype (MUST be first and uncompressed)
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

        # 2. META-INF/container.xml
        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
        zf.writestr("META-INF/container.xml", container_xml, compress_type=zipfile.ZIP_DEFLATED)

        # 3. OEBPS/style.css
        zf.writestr("OEBPS/style.css", css_content, compress_type=zipfile.ZIP_DEFLATED)

        # 4. Images
        for img_name, img_path in img_sources.items():
            if os.path.exists(img_path):
                zf.write(img_path, f"OEBPS/images/{img_name}", compress_type=zipfile.ZIP_DEFLATED)

        # 5. XHTML Chapters
        for filename, title, content in chapters:
            zf.writestr(f"OEBPS/{filename}", content, compress_type=zipfile.ZIP_DEFLATED)

        # 6. OEBPS/nav.xhtml (EPUB 3 Navigation)
        nav_items_html = "\n".join([f'        <li><a href="{fn}">{html.escape(t)}</a></li>' for fn, t, _ in chapters if fn != "cover.xhtml"])
        nav_html = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en">
<head>
    <title>Table of Contents</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <nav epub:type="toc" id="toc">
        <h1>Table of Contents</h1>
        <ol>
{nav_items_html}
        </ol>
    </nav>
</body>
</html>"""
        zf.writestr("OEBPS/nav.xhtml", nav_html, compress_type=zipfile.ZIP_DEFLATED)

        # 7. OEBPS/toc.ncx (EPUB 2 Navigation for legacy readers)
        ncx_points = []
        for i, (fn, t, _) in enumerate(chapters, 1):
            ncx_points.append(f"""    <navPoint id="np-{i}" playOrder="{i}">
      <navLabel><text>{html.escape(t)}</text></navLabel>
      <content src="{fn}"/>
    </navPoint>""")
        ncx_map_content = "\n".join(ncx_points)
        ncx_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{book_uuid}"/>
    <meta name="dtb:depth" content="2"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{html.escape(session_folder)}</text></docTitle>
  <docAuthor><text>Branko Toic</text></docAuthor>
  <navMap>
{ncx_map_content}
  </navMap>
</ncx>"""
        zf.writestr("OEBPS/toc.ncx", ncx_xml, compress_type=zipfile.ZIP_DEFLATED)

        # 8. OEBPS/content.opf
        manifest_items = [
            '<item id="css" href="style.css" media-type="text/css"/>',
            '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
            '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
        ]
        for fn, _, _ in chapters:
            manifest_items.append(f'<item id="{fn.replace(".", "_")}" href="{fn}" media-type="application/xhtml+xml"/>')

        for img_name in img_sources.keys():
            img_id = img_name.replace(".", "_")
            manifest_items.append(f'<item id="{img_id}" href="images/{img_name}" media-type="image/png"/>')

        spine_items = []
        for fn, _, _ in chapters:
            spine_items.append(f'<itemref idref="{fn.replace(".", "_")}"/>')

        manifest_content = "\n    ".join(manifest_items)
        spine_content = "\n    ".join(spine_items)

        opf_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="pub-id" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">{book_uuid}</dc:identifier>
    <dc:title>{html.escape(session_folder)}</dc:title>
    <dc:creator>Branko Toic</dc:creator>
    <dc:language>en</dc:language>
    <dc:date>2026-09-12</dc:date>
    <meta property="dcterms:modified">{now_iso}</meta>
    <!-- Calibre series metadata for PocketBook & e-readers -->
    <meta name="calibre:series" content="{html.escape(series_name)}"/>
    <meta name="calibre:series_index" content="{series_index}"/>
    <!-- EPUB 3 Series Collection Metadata -->
    <meta property="belongs-to-collection" id="series-01">{html.escape(series_name)}</meta>
    <meta refines="#series-01" property="collection-type">series</meta>
    <meta refines="#series-01" property="group-position">{series_index}</meta>
    <!-- PocketBook Era Display Optimization Metadata -->
    <meta name="pocketbook:font-size" content="12px"/>
    <meta name="pocketbook:optimized-zoom" content="12px"/>
    <meta property="schema:accessibilityFeature">readingOrder</meta>
    <meta property="schema:accessibilitySummary">Optimized for PocketBook Era at 12px font zoom with screen-fitted finder charts and natural 4-page target pagination.</meta>
    <dc:description>Stargazing observation guide and toner-saver finder charts for {html.escape(session_folder)}. Optimized for PocketBook Era at 12px font zoom with natural 4-page target flow.</dc:description>
  </metadata>
  <manifest>
    {manifest_content}
  </manifest>
  <spine toc="ncx">
    {spine_content}
  </spine>
  <guide>
    <reference type="toc" title="Table of Contents" href="toc.xhtml"/>
    <reference type="text" title="Beginning" href="01_site_profile.xhtml"/>
  </guide>
</package>"""
        zf.writestr("OEBPS/content.opf", opf_xml, compress_type=zipfile.ZIP_DEFLATED)

    # Maintain backward-compatible copy or symlink
    if os.path.exists(legacy_symlink_path) or os.path.islink(legacy_symlink_path):
        try:
            os.remove(legacy_symlink_path)
        except OSError:
            pass
    try:
        shutil.copyfile(output_path, legacy_symlink_path)
    except Exception as e:
        print(f"Notice: could not copy to legacy path: {e}")

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n=======================================================")
    print(f"EPUB BOOK SUCCESSFULLY GENERATED!")
    print(f"Path:     {output_path}")
    print(f"Legacy:   {legacy_symlink_path}")
    print(f"Size:     {file_size_mb:.2f} MB")
    print(f"Series:   {series_name} #{series_index}")
    print(f"Chapters: {len(chapters)}")
    print(f"Images:   {len(img_sources)}")
    print(f"=======================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile Stargazing Session into an E-Reader EPUB")
    parser.add_argument("--session-dir", type=str, default=None, help="Path to observations/<session-folder>")
    parser.add_argument("--output", type=str, default=None, help="Output .epub file path")
    args = parser.parse_args()
    build_epub(args.session_dir, args.output)

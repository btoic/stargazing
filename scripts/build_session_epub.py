#!/usr/bin/env python3
"""
scripts/build_session_epub.py - Compiles an observation session package into a single,
fully indexed, high-contrast EPUB e-book optimized for e-ink e-readers (Kindle, Kobo, Boox)
and red-light nighttime viewing.
"""

import os
import sys
import zipfile
import argparse
import uuid
import html
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

def build_epub(session_dir=None, output_path=None):
    if session_dir is None:
        session_dir = os.path.join(REPO_ROOT, "observations", "dvigrad-2026-09-12")
    session_dir = os.path.abspath(session_dir)

    if output_path is None:
        output_path = os.path.join(session_dir, "STARGAZING_FIELD_GUIDE.epub")
    output_path = os.path.abspath(output_path)

    print(f"\n=======================================================")
    print(f"BUILDING EPUB FIELD GUIDE")
    print(f"Session: {session_dir}")
    print(f"Output:  {output_path}")
    print(f"=======================================================\n")

    # Image source paths
    img_sources = {
        "full_sky_map.png": os.path.join(session_dir, "full_sky_map.png"),
        "timeline_gantt.png": os.path.join(session_dir, "timeline_gantt.png"),
        "chart_1_lyra_m57.png": os.path.join(session_dir, "charts", "chart_1_lyra_m57.png"),
        "chart_2_vulpecula_m27_albireo.png": os.path.join(session_dir, "charts", "chart_2_vulpecula_m27_albireo.png"),
        "chart_3_hercules_m13_m92.png": os.path.join(session_dir, "charts", "chart_3_hercules_m13_m92.png"),
        "chart_4_andromeda_m31.png": os.path.join(session_dir, "charts", "chart_4_andromeda_m31.png"),
        "chart_5_perseus_double_cluster.png": os.path.join(session_dir, "charts", "chart_5_perseus_double_cluster.png"),
        "chart_6_scutum_m11_and_saturn.png": os.path.join(session_dir, "charts", "chart_6_scutum_m11_and_saturn.png"),
        # Collimation tutorial figures
        "collimation_hardware_controls.png": os.path.join(REPO_ROOT, "tutorials", "images", "collimation_hardware_controls.png"),
        "collimation_steps_view.png": os.path.join(REPO_ROOT, "tutorials", "images", "collimation_steps_view.png"),
        "star_test_patterns.png": os.path.join(REPO_ROOT, "tutorials", "images", "star_test_patterns.png"),
    }

    # Verify required images exist
    for name, path in img_sources.items():
        if not os.path.exists(path):
            print(f"Warning: Image {name} not found at {path}")

    # CSS Content
    css_content = """/* Stargazing E-Reader Optimized Stylesheet */
@page {
    margin: 4% 4%;
}
body {
    font-family: serif;
    font-size: 1.0em;
    line-height: 1.45;
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
    font-size: 1.6em;
    border-bottom: 2px solid #000000;
    padding-bottom: 0.2em;
    margin-top: 0.8em;
    margin-bottom: 0.4em;
}
h2 {
    font-size: 1.25em;
    border-bottom: 1px solid #666666;
    padding-bottom: 0.15em;
    margin-top: 1.0em;
    margin-bottom: 0.3em;
}
h3 {
    font-size: 1.05em;
    margin-top: 0.8em;
    margin-bottom: 0.2em;
}
p {
    margin: 0.5em 0;
}
.subtitle {
    font-family: sans-serif;
    font-size: 0.9em;
    color: #333333;
    margin-bottom: 1.2em;
    line-height: 1.35;
}
.nav-bar {
    font-family: sans-serif;
    font-size: 0.82em;
    margin: 0.6em 0 1.2em 0;
    padding: 0.4em 0;
    border-bottom: 1px dashed #666666;
}
.nav-bar a {
    text-decoration: none;
    font-weight: bold;
    color: #000000;
    background-color: #f0f0f0;
    padding: 3px 8px;
    border: 1px solid #333333;
    border-radius: 3px;
    margin-right: 6px;
    display: inline-block;
}
.nav-bar a:hover {
    background-color: #000000;
    color: #ffffff;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.8em 0;
    font-size: 0.82em;
}
th, td {
    border: 1px solid #000000;
    padding: 5px 6px;
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
.badge {
    display: inline-block;
    font-family: monospace;
    font-size: 0.82em;
    background-color: #f0f0f0;
    border: 1px solid #000000;
    padding: 2px 6px;
    margin: 2px;
}
.callout {
    border: 2px solid #000000;
    background-color: #f8f8f8;
    padding: 8px 12px;
    margin: 1.0em 0;
}
.chart-img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0.8em auto;
    border: 1px solid #000000;
}
.cover-box {
    text-align: center;
    padding: 3em 1em;
    border: 3px solid #000000;
    margin: 2em auto;
}
.cover-title {
    font-family: sans-serif;
    font-size: 2.0em;
    font-weight: bold;
    margin-bottom: 0.3em;
}
.cover-sub {
    font-family: sans-serif;
    font-size: 1.1em;
    margin-bottom: 1.5em;
    color: #333333;
}
.hop-step {
    margin: 0.5em 0 0.5em 1.2em;
    text-indent: -1.2em;
}
ol.hop-list {
    margin: 0.5em 0;
    padding-left: 1.5em;
}
ol.hop-list li {
    margin-bottom: 0.5em;
}
"""

    # Chapters dictionary
    chapters = []

    # 1. Cover
    cover_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Dvigrad Stargazing Party</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="cover-box">
        <div class="cover-title">DVIGRAD STARGAZING PARTY</div>
        <div class="cover-sub">Master Observation Guide &amp; High-Contrast Finder Charts</div>
        <hr style="border: 1px solid #000000; margin: 1.5em 0;"/>
        <p><b>Date:</b> Saturday, September 12, 2026</p>
        <p><b>Observing Window:</b> 20:00 – 22:30 CEST (UTC+2)</p>
        <p><b>Location:</b> Dvigrad Medieval Ruins, Kanfanar, Istria (Bortle 4)</p>
        <p><b>Coordinates:</b> 45.12637° N, 13.81296° E | Elev: 143 m</p>
        <p><b>Instrument:</b> Sky-Watcher Skyliner 200P Dobsonian (200 mm f/6)</p>
        <hr style="border: 1px dashed #666666; margin: 1.5em 0;"/>
        <p style="font-size: 0.85em; color: #444444;">E-Reader &amp; Night-Vision Print Edition<br/>Toner-Saver Negative B/W Star Charts</p>
        <p style="margin-top: 1.5em;"><a href="toc.xhtml" style="font-family: sans-serif; font-weight: bold; text-decoration: none; border: 2px solid #000; padding: 6px 14px; background: #eee; color: #000;">OPEN TABLE OF CONTENTS →</a></p>
    </div>
</body>
</html>"""
    chapters.append(("cover.xhtml", "Cover", cover_html))

    # 2. Table of Contents
    toc_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Table of Contents</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <h1>Table of Contents</h1>
    <div class="subtitle">Dvigrad Stargazing Field Manual — September 12, 2026</div>

    <h2>Part I: Field Guide &amp; Ephemeris</h2>
    <ul>
        <li><a href="01_site_profile.xhtml">1. Location &amp; Dark Sky Profile (Dvigrad Bortle 4)</a></li>
        <li><a href="02_ephemeris.xhtml">2. Twilight Phases &amp; Astronomical Timeline</a></li>
        <li><a href="03_optics_and_fieldcraft.xhtml">3. Sky-Watcher 200P Optics &amp; Field Craft</a></li>
        <li><a href="04_target_catalog.xhtml">4. Curated Target Catalog (Interactive Index)</a></li>
        <li><a href="05_full_sky_map.xhtml">5. All-Sky Planisphere (Full Night Sky Map)</a></li>
    </ul>

    <h2>Part II: High-Contrast Finder Charts &amp; Star-Hops</h2>
    <ul>
        <li><a href="chart_1_m57.xhtml"><b>Chart 1:</b> M57 Ring Nebula in Lyra (12.5mm / 96×)</a></li>
        <li><a href="chart_2_m27_albireo.xhtml"><b>Chart 2:</b> M27 Dumbbell Nebula &amp; Albireo Double (20mm / 60×)</a></li>
        <li><a href="chart_3_hercules.xhtml"><b>Chart 3:</b> Hercules Globulars M13 &amp; M92 (12.5mm / 96×)</a></li>
        <li><a href="chart_4_andromeda.xhtml"><b>Chart 4:</b> M31 Andromeda Galaxy, M32 &amp; M110 (20mm / 60×)</a></li>
        <li><a href="chart_5_perseus.xhtml"><b>Chart 5:</b> Perseus Double Cluster NGC 869/884 (20mm / 60×)</a></li>
        <li><a href="chart_6_scutum_saturn.xhtml"><b>Chart 6:</b> M11 Wild Duck Cluster &amp; Saturn (20mm &amp; 12.5mm)</a></li>
    </ul>

    <h2>Part III: Field Reference</h2>
    <ul>
        <li><a href="appendix_collimation.xhtml">Appendix: Dobsonian Mirror Collimation Field Guide</a></li>
    </ul>
</body>
</html>"""
    chapters.append(("toc.xhtml", "Table of Contents", toc_html))

    # 3. Site Profile
    site_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>1. Location &amp; Dark Sky Profile</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="nav-bar">
        <a href="toc.xhtml">← Table of Contents</a>
        <a href="04_target_catalog.xhtml">Target Catalog →</a>
    </div>

    <h1>1. Location &amp; Dark Sky Profile</h1>
    <div class="subtitle">Dvigrad Medieval Fortress Ruins (Kanfanar, Istria, Croatia)</div>

    <div class="callout">
        <b>GEOGRAPHIC COORDINATES &amp; TOPOGRAPHY</b><br/>
        • <b>Coordinates:</b> 45.12637° N, 13.81296° E (Google Plus Code: <code>4RG7+G5 Kanfanar</code>)<br/>
        • <b>Elevation:</b> 143 m ASL<br/>
        • <b>Terrain:</b> Protected limestone depression in the Lim Valley (Draga)
    </div>

    <h2>Dark Sky Metrics</h2>
    <table>
        <tr><th>Metric</th><th>Observed Value</th><th>Field Interpretation</th></tr>
        <tr><td><b>Bortle Class</b></td><td><b>Class 4</b></td><td>Rural/Suburban transition. High contrast, dark sky.</td></tr>
        <tr><td><b>Sky Brightness</b></td><td><b>20.86 – 21.15 mag/arcsec²</b></td><td>Pristine background contrast for diffuse nebulae.</td></tr>
        <tr><td><b>NELM</b></td><td><b>6.0 – 6.2 mag</b></td><td>Faint naked-eye stars visible at zenith.</td></tr>
        <tr><td><b>Milky Way</b></td><td><b>Clearly Structured</b></td><td>Great Rift through Cygnus/Aquila visible with dark clouds.</td></tr>
    </table>

    <h2>Horizon Obstruction Profile</h2>
    <p>Because the ruins lie on the floor and flanks of the Lim Valley, surrounding oak/pine forests and terrain ridges create a <b>10° to 15° obstruction</b> across the horizon:</p>
    <ul>
        <li><b>South &amp; South-West (Lim Valley floor):</b> Ridge rises 12°–15°. Deep southern targets (Sagittarius core) sink into foliage early.</li>
        <li><b>East &amp; North-East:</b> Rising terrain slope of 10°–14°. Rising targets (Saturn, Perseus) must reach ~15° before clearing boundary-layer thermal turbulence.</li>
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
        On September 12, 2026, the Moon is a razor-thin <b>3.1% waxing crescent</b> (1.1 days after New Moon) and <b>sets at 19:38 CEST</b> (prior to observation start). Throughout the session (20:00–22:30 CEST), the Moon is <b>below the horizon (-4° to -30° Alt)</b>, providing 100% dark sky contrast!
    </div>

    <h2>Twilight Schedule Table</h2>
    <table>
        <tr><th>Phase</th><th>Window (CEST)</th><th>Sun Alt</th><th>Program Guidance</th></tr>
        <tr><td><b>Setup &amp; Cooldown</b></td><td>19:30 – 20:00</td><td>-2° to -8°</td><td>Primary mirror cooldown (30-45 min). 9x50 finder alignment on Vega / Arcturus.</td></tr>
        <tr><td><b>Nautical Twilight</b></td><td>20:00 – 20:26</td><td>-8° to -12°</td><td>Sky deepens to slate blue. High-contrast double star Albireo &amp; urgent low M22 sweep.</td></tr>
        <tr><td><b>Astro Twilight</b></td><td>20:26 – 21:05</td><td>-12° to -18°</td><td>Milky Way dust lanes emerge. Rich globular clusters pop into view (M13, M92, M11).</td></tr>
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
    <div class="subtitle">Sky-Watcher Skyliner Classic 200P Dobsonian (f/6 Newtonian)</div>

    <h2>Optical Specifications</h2>
    <table>
        <tr><th>Specification</th><th>Value</th><th>Field Significance</th></tr>
        <tr><td><b>Aperture</b></td><td>200 mm (7.87")</td><td>Collects 820× more light than human eye.</td></tr>
        <tr><td><b>Focal Length</b></td><td>1200 mm</td><td>f/6 focal ratio with minimal off-axis coma.</td></tr>
        <tr><td><b>Dawes Resolving Limit</b></td><td>0.58 arcsec</td><td>Easily resolves tight binary stars &amp; ring gaps.</td></tr>
        <tr><td><b>Limiting Magnitude</b></td><td>13.3 – 14.0 mag</td><td>Reveals faint star cluster cores &amp; nebular envelopes.</td></tr>
    </table>

    <h2>Eyepiece Reference</h2>
    <table>
        <tr><th>Eyepiece</th><th>Power</th><th>Exit Pupil</th><th>True Field (TFOV)</th><th>Primary Use</th></tr>
        <tr><td><b>20 mm</b></td><td><b>60×</b></td><td>3.33 mm</td><td><b>~50' (0.83°)</b></td><td>Wide fields: M31 Andromeda, M27 Dumbbell, Double Cluster.</td></tr>
        <tr><td><b>12.5 mm</b></td><td><b>96×</b></td><td>2.08 mm</td><td><b>~31' (0.52°)</b></td><td>Resolution: M13 &amp; M92 core stars, M57 Ring hole, Saturn rings.</td></tr>
    </table>

    <h2>Field Protocols for Dvigrad Ruins</h2>
    <div class="callout">
        <b>1. VALLEY DEW MANAGEMENT</b><br/>
        Dvigrad sits in the Lim Valley depression where nocturnal cold air drains and humidity reaches saturation.<br/>
        • Keep unmounted eyepieces in warm jacket pockets or closed foam cases.<br/>
        • Keep the front dust cover on the telescope during breaks to protect the secondary mirror.<br/>
        • Use a front dew shield extending 1.5× tube diameter.
    </div>

    <div class="callout">
        <b>2. THE ZENITH TRAP ("DOBSON'S HOLE")</b><br/>
        At altitudes &gt;80° straight overhead (e.g. Vega, M57), horizontal nudging requires swinging the entire heavy rocker box rapidly, making manual tracking jerky.<br/>
        • <b>Pro Tip:</b> Observe M57 and Albireo between 21:00 and 21:45 when they have rolled slightly past the meridian (70°–75°), making manual tracking smooth.
    </div>

    <div class="callout">
        <b>3. OPTICAL INVERSION REMINDER</b><br/>
        The view in a Newtonian reflector is <b>inverted 180°</b> (rotated: Up becomes Down, Left becomes Right). The eyepiece simulation viewports on all finder charts in this book are pre-inverted 180° to match your actual view!
    </div>
</body>
</html>"""
    chapters.append(("03_optics_and_fieldcraft.xhtml", "3. Optics & Field Craft", optics_html))

    # 6. Curated Target Catalog (Interactive Table)
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
            <td><a href="chart_2_m27_albireo.xhtml"><b>Chart 2 →</b></a></td>
        </tr>
        <tr>
            <td>2</td>
            <td><b>M22 (NGC 6656)</b></td>
            <td>Sgr</td>
            <td>Globular Cl.</td>
            <td>5.1</td>
            <td>17.5° / 195° (SSW)</td>
            <td>20mm → 12.5mm</td>
            <td><a href="05_full_sky_map.xhtml"><b>Sky Map →</b></a> <i>(Early!)</i></td>
        </tr>
        <tr>
            <td>3</td>
            <td><b>M13 Great Globular</b></td>
            <td>Her</td>
            <td>Globular Cl.</td>
            <td>5.8</td>
            <td>63.4° / 268° (W)</td>
            <td>12.5mm (96×)</td>
            <td><a href="chart_3_hercules.xhtml"><b>Chart 3 →</b></a></td>
        </tr>
        <tr>
            <td>4</td>
            <td><b>M92 (NGC 6341)</b></td>
            <td>Her</td>
            <td>Globular Cl.</td>
            <td>6.3</td>
            <td>71.2° / 295° (WNW)</td>
            <td>12.5mm (96×)</td>
            <td><a href="chart_3_hercules.xhtml"><b>Chart 3 →</b></a></td>
        </tr>
        <tr>
            <td>5</td>
            <td><b>M11 Wild Duck</b></td>
            <td>Sct</td>
            <td>Open Cluster</td>
            <td>5.8</td>
            <td>35.2° / 205° (SSW)</td>
            <td>20mm &amp; 12.5mm</td>
            <td><a href="chart_6_scutum_saturn.xhtml"><b>Chart 6 →</b></a></td>
        </tr>
        <tr>
            <td>6</td>
            <td><b>M57 Ring Nebula</b></td>
            <td>Lyr</td>
            <td>Planetary Neb.</td>
            <td>8.8</td>
            <td>76.1° / 222° (SW)</td>
            <td>12.5mm (96×)</td>
            <td><a href="chart_1_m57.xhtml"><b>Chart 1 →</b></a></td>
        </tr>
        <tr>
            <td>7</td>
            <td><b>M27 Dumbbell Neb.</b></td>
            <td>Vul</td>
            <td>Planetary Neb.</td>
            <td>7.4</td>
            <td>68.2° / 164° (SSE)</td>
            <td>20mm (60×)</td>
            <td><a href="chart_2_m27_albireo.xhtml"><b>Chart 2 →</b></a></td>
        </tr>
        <tr>
            <td>8</td>
            <td><b>Double Cluster</b></td>
            <td>Per</td>
            <td>Dual Open Cl.</td>
            <td>3.7/3.8</td>
            <td>34.1° / 038° (NE)</td>
            <td>20mm (60×)</td>
            <td><a href="chart_5_perseus.xhtml"><b>Chart 5 →</b></a></td>
        </tr>
        <tr>
            <td>9</td>
            <td><b>M31 Andromeda</b></td>
            <td>And</td>
            <td>Spiral Galaxy</td>
            <td>3.4</td>
            <td>43.5° / 068° (ENE)</td>
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

    # 7. Full Sky Map
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

    <h2>Key Constellations to Locate</h2>
    <ul>
        <li><b>The Summer Triangle:</b> Vega (Lyra), Deneb (Cygnus), and Altair (Aquila) dominate the high southern sky.</li>
        <li><b>The Keystone of Hercules:</b> High in the West; home to globular clusters M13 and M92.</li>
        <li><b>The Great Square of Pegasus &amp; Andromeda:</b> Rising high in the East/North-East; guiding arrow to M31.</li>
        <li><b>Cassiopeia ("W"):</b> Circling high in the North-East; anchor for the Double Cluster.</li>
    </ul>
</body>
</html>"""
    chapters.append(("05_full_sky_map.xhtml", "5. All-Sky Planisphere", skymap_html))

    # 8. Chart 1: M57
    chart1_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Chart 1: M57 Ring Nebula</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="nav-bar">
        <a href="toc.xhtml">← Table of Contents</a>
        <a href="04_target_catalog.xhtml">← Target Catalog</a>
        <a href="chart_2_m27_albireo.xhtml">Next: Chart 2 (M27) →</a>
    </div>

    <h1>Chart 1: M57 Ring Nebula in Lyra</h1>
    <div class="subtitle">Planetary Nebula • Mag 8.8 • Size 1.4' × 1.0' • RA 18h 53.6m | Dec +33° 02'</div>

    <div class="callout">
        <b>TONIGHT'S EPHEMERIS @ 21:15 CEST:</b><br/>
        • <b>Altitude / Azimuth:</b> 76.1° / 222° (SW)<br/>
        • <b>Meridian Status:</b> Transited at 20:38 CEST (Rolling west off zenith; optimal Dobsonian tracking!)<br/>
        • <b>Eyepieces:</b> 20 mm (60×) for acquisition → <b>12.5 mm (96×, 31' FOV)</b> for resolution
    </div>

    <img src="images/chart_1_lyra_m57.png" class="chart-img" alt="Finder Chart 1: M57 Ring Nebula"/>

    <h2>Step-by-Step Star-Hopping Guide</h2>
    <ol class="hop-list">
        <li><b>[STEP 1] Start at Vega (α Lyrae, Mag 0.03):</b> Look almost straight overhead for the brilliant sapphire-white anchor of the Summer Triangle. Center Vega in your finder scope.</li>
        <li><b>[STEP 2] Trace the Lyra Parallelogram:</b> Nudge 6° south of Vega to locate the prominent four-star parallelogram formed by ζ, δ, γ, and β Lyrae (Sulafat &amp; Sheliak).</li>
        <li><b>[STEP 3] Bridge between β and γ Lyrae:</b> Locate β Lyrae (Sheliak, mag 3.5) and γ Lyrae (Sulafat, mag 3.2), separated by 3.2° at the southern base of the parallelogram. Center your Telrad / finder reticle exactly halfway between them.</li>
        <li><b>[STEP 4] Acquire in 20 mm Eyepiece:</b> Look through the 20 mm eyepiece. M57 appears as a small, intense, grey smoke ring or hollow "smoke cheerio" floating between two faint 12th-mag field stars.</li>
        <li><b>[STEP 5] Resolve at 12.5 mm (96×):</b> Switch to the 12.5 mm eyepiece. The dark central hole and oval torus ring structure become unmistakable. Use averted vision to enhance contrast along the outer ring boundary!</li>
    </ol>
</body>
</html>"""
    chapters.append(("chart_1_m57.xhtml", "Chart 1: M57 Ring Nebula", chart1_html))

    # 9. Chart 2: M27 & Albireo
    chart2_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Chart 2: M27 &amp; Albireo</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="nav-bar">
        <a href="toc.xhtml">← Table of Contents</a>
        <a href="04_target_catalog.xhtml">← Target Catalog</a>
        <a href="chart_3_hercules.xhtml">Next: Chart 3 (Hercules) →</a>
    </div>

    <h1>Chart 2: M27 Dumbbell Nebula &amp; Albireo</h1>
    <div class="subtitle">Vulpecula / Cygnus • Planetary Nebula &amp; Showcase Binary Star</div>

    <div class="callout">
        <b>TARGET PARAMETERS &amp; MID-SESSION EPHEMERIS @ 21:15 CEST:</b><br/>
        • <b>Albireo (β Cygni):</b> Mag 3.1 / 5.1 (34.3" sep) • Alt 73.0° / Az 170° (S). Golden-amber primary &amp; sapphire companion.<br/>
        • <b>M27 Dumbbell (NGC 6853):</b> Mag 7.4 • Size 8.0' × 5.6' • Alt 68.2° / Az 164° (SSE). Transits 21:44 CEST.<br/>
        • <b>Recommended Eyepiece:</b> <b>20 mm (60×, 50' FOV)</b>
    </div>

    <img src="images/chart_2_vulpecula_m27_albireo.png" class="chart-img" alt="Finder Chart 2: M27 &amp; Albireo"/>

    <h2>Step-by-Step Star-Hopping Guide</h2>
    <ol class="hop-list">
        <li><b>Target 1: Albireo (Showcase Double Star):</b> Look at the base of the Northern Cross in Cygnus. Center the naked-eye 3rd-mag star in your finder. In the 20 mm eyepiece, marvel at the striking color contrast between the golden-topaz primary and vivid sky-blue companion star!</li>
        <li><b>[STEP 1] Locate Sagitta (The Arrow):</b> From Albireo, look ~8° south-east for the compact, distinctive asterism of Sagitta (α, β, δ, γ Sge).</li>
        <li><b>[STEP 2] Find γ Sagittae:</b> Identify γ Sge (+3.5 mag), the sharp forward tip of the arrow pointing eastward.</li>
        <li><b>[STEP 3] Hop 3.2° North into Vulpecula:</b> Place the outer ring of your Telrad (or edge of 9x50 finder) on γ Sge and nudge directly North by 3.2°.</li>
        <li><b>[STEP 4] Acquire M27 in 20 mm Eyepiece:</b> Look near 14 Vulpeculae (+5.8 mag). M27 appears as a huge, bright, glowing ghostly hourglass or "apple-core" nebula against the rich star field of the Milky Way!</li>
    </ol>
</body>
</html>"""
    chapters.append(("chart_2_m27_albireo.xhtml", "Chart 2: M27 & Albireo", chart2_html))

    # 10. Chart 3: Hercules Globulars
    chart3_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Chart 3: Hercules M13 &amp; M92</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="nav-bar">
        <a href="toc.xhtml">← Table of Contents</a>
        <a href="04_target_catalog.xhtml">← Target Catalog</a>
        <a href="chart_4_andromeda.xhtml">Next: Chart 4 (Andromeda) →</a>
    </div>

    <h1>Chart 3: Hercules Globulars M13 &amp; M92</h1>
    <div class="subtitle">Globular Clusters • Showcase Stellar Swarms of the Northern Sky</div>

    <div class="callout">
        <b>TARGET PARAMETERS &amp; MID-SESSION EPHEMERIS @ 21:15 CEST:</b><br/>
        • <b>M13 (Great Globular Cluster):</b> Mag 5.8 • Size 20.0' • Alt 63.4° / Az 268° (W). ~300,000 ancient stars.<br/>
        • <b>M92 (NGC 6341):</b> Mag 6.3 • Size 14.0' • Alt 71.2° / Az 295° (WNW). Extremely dense, luminous core.<br/>
        • <b>Recommended Eyepiece:</b> <b>12.5 mm (96×, 31' FOV)</b>
    </div>

    <img src="images/chart_3_hercules_m13_m92.png" class="chart-img" alt="Finder Chart 3: Hercules Globulars"/>

    <h2>Step-by-Step Star-Hopping Guide</h2>
    <ol class="hop-list">
        <li><b>[STEP 1] Locate the Keystone of Hercules:</b> Look high in the western sky for the four-star Keystone asterism (η, ζ, ε, π Herculis).</li>
        <li><b>[STEP 2] Hop to M13 (The Great Cluster):</b> Look along the western side of the Keystone between η Her (+3.5 mag) and ζ Her (+2.8 mag). M13 lies exactly one-third of the way from η toward ζ Her (2.5° south of η).</li>
        <li><b>[STEP 3] Resolve M13 in 12.5 mm (96×):</b> In the 200P aperture, M13 resolves into thousands of brilliant pinprick diamond stars across its 20' diameter. Look for prominent outward-curving stellar chains resembling spider legs!</li>
        <li><b>[STEP 4] Hop to M92:</b> Return to η Her. Sight 6.3° north-east towards ι Her (+3.8 mag), forming a triangle with π Her. Center the finder on the empty patch: M92 will glow brightly with an intensely concentrated, fiery core!</li>
    </ol>
</body>
</html>"""
    chapters.append(("chart_3_hercules.xhtml", "Chart 3: Hercules M13 & M92", chart3_html))

    # 11. Chart 4: Andromeda M31
    chart4_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Chart 4: M31 Andromeda Galaxy</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="nav-bar">
        <a href="toc.xhtml">← Table of Contents</a>
        <a href="04_target_catalog.xhtml">← Target Catalog</a>
        <a href="chart_5_perseus.xhtml">Next: Chart 5 (Double Cluster) →</a>
    </div>

    <h1>Chart 4: M31 Andromeda Galaxy, M32 &amp; M110</h1>
    <div class="subtitle">Spiral Galaxy System • 2.5 Million Light-Years • Mag 3.4 • Size 190' × 60'</div>

    <div class="callout">
        <b>TONIGHT'S EPHEMERIS @ 21:15 CEST:</b><br/>
        • <b>Altitude / Azimuth:</b> 43.5° / 068° (ENE)<br/>
        • <b>Climbing:</b> Transits after midnight at 78° Alt. Excellent dark-sky contrast above 40° altitude.<br/>
        • <b>Recommended Eyepiece:</b> <b>20 mm (60×, 50' FOV)</b> for wide framing
    </div>

    <img src="images/chart_4_andromeda_m31.png" class="chart-img" alt="Finder Chart 4: M31 Andromeda Galaxy"/>

    <h2>Step-by-Step Star-Hopping Guide</h2>
    <ol class="hop-list">
        <li><b>[STEP 1] Start at the Great Square of Pegasus:</b> Identify Alpheratz (α Andromedae, mag 2.1), the top-left star marking the boundary between Pegasus and Andromeda.</li>
        <li><b>[STEP 2] Follow Andromeda's Main Spine:</b> Hop 7° north-east along the northern curve to δ And (+3.3 mag), then another 8° in the same line to bright reddish Mirach (β And, +2.1 mag).</li>
        <li><b>[STEP 3] Make a 90° North-West Turn:</b> From Mirach, turn 90° toward Cassiopeia. Hop 3.5° north-west to μ And (+3.9 mag), then another 3.5° in the exact same direction to ν And (+4.5 mag).</li>
        <li><b>[STEP 4] Acquire M31:</b> Place your Telrad / finder 1.3° west of ν And. In the 20 mm eyepiece, M31's brilliant galactic nucleus fills the center of the field with sprawling elliptical haze.</li>
        <li><b>[STEP 5] Locate Satellite Galaxies:</b>
            <br/>• <b>M32:</b> Look 24' south of the core for a bright, round, high-surface-brightness fuzzy ball resembling an unresolved globular cluster.
            <br/>• <b>M110:</b> Look 35' north-west across the primary dust lane for a large, faint, elongated ghostly companion galaxy.
        </li>
    </ol>
</body>
</html>"""
    chapters.append(("chart_4_andromeda.xhtml", "Chart 4: M31 Andromeda Galaxy", chart4_html))

    # 12. Chart 5: Perseus Double Cluster
    chart5_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Chart 5: Double Cluster</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="nav-bar">
        <a href="toc.xhtml">← Table of Contents</a>
        <a href="04_target_catalog.xhtml">← Target Catalog</a>
        <a href="chart_6_scutum_saturn.xhtml">Next: Chart 6 (M11 &amp; Saturn) →</a>
    </div>

    <h1>Chart 5: Perseus Double Cluster (NGC 869 / 884)</h1>
    <div class="subtitle">Twin Open Clusters • 7,500 Light-Years • Mag 3.7 / 3.8 • Size 60' across</div>

    <div class="callout">
        <b>TONIGHT'S EPHEMERIS @ 21:15 CEST:</b><br/>
        • <b>Altitude / Azimuth:</b> 34.1° / 038° (NE)<br/>
        • <b>Observing Window:</b> High above the 15° Dvigrad eastern tree line; rising toward zenith throughout the night.<br/>
        • <b>Recommended Eyepiece:</b> <b>20 mm (60×, 50' FOV)</b> — fits both clusters into a single view!
    </div>

    <img src="images/chart_5_perseus_double_cluster.png" class="chart-img" alt="Finder Chart 5: Perseus Double Cluster"/>

    <h2>Step-by-Step Star-Hopping Guide</h2>
    <ol class="hop-list">
        <li><b>[STEP 1] Locate the "W" of Cassiopeia:</b> Find the bright zigzag shape of Cassiopeia in the north-east sky. Identify γ Cas (center of the W) and δ Cas (Ruchbah, +2.7 mag).</li>
        <li><b>[STEP 2] Project the Pointer Line:</b> Draw an imaginary line from γ Cas through δ Cas, and extend it straight south-east for approximately twice that distance (~7°–8°).</li>
        <li><b>[STEP 3] Spot the Naked-Eye Shimmer:</b> Under Dvigrad's dark Bortle 4 sky, the Double Cluster is easily visible to the naked eye as an elongated, glittering patch of light between Cassiopeia and Perseus.</li>
        <li><b>[STEP 4] Center in Finder &amp; Eyepiece:</b> Place your 9x50 finder crosshairs on the patch. In the 20 mm eyepiece (60×), both NGC 869 (western cluster) and NGC 884 (eastern cluster) fill the 50' field of view simultaneously!</li>
        <li><b>[STEP 5] Visual Highlights:</b> Count over 300 glittering blue-white stars in each cluster. Look closely in the center of NGC 884 for several unmistakable ruby-red supergiant stars contrasting against the icy-blue diamonds!</li>
    </ol>
</body>
</html>"""
    chapters.append(("chart_5_perseus.xhtml", "Chart 5: Double Cluster", chart5_html))

    # 13. Chart 6: Scutum M11 & Saturn
    chart6_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Chart 6: M11 &amp; Saturn</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="nav-bar">
        <a href="toc.xhtml">← Table of Contents</a>
        <a href="04_target_catalog.xhtml">← Target Catalog</a>
        <a href="appendix_collimation.xhtml">Appendix: Collimation →</a>
    </div>

    <h1>Chart 6: M11 Wild Duck Cluster &amp; Saturn</h1>
    <div class="subtitle">Scutum / Aquarius • Rich Open Cluster &amp; Ringed Planetary Finale</div>

    <div class="callout">
        <b>TARGET PARAMETERS &amp; MID-SESSION EPHEMERIS @ 21:15 CEST:</b><br/>
        • <b>M11 Wild Duck Cluster (NGC 6705):</b> Mag 5.8 • Size 14.0' • Alt 35.2° / Az 205° (SSW). Observe by 21:30 before setting.<br/>
        • <b>Saturn &amp; Titan:</b> Mag +0.6 • Disk 19.2" • Alt 18°–23° / Az 115° (ESE). Clears 15° Dvigrad trees after 21:40 CEST!<br/>
        • <b>Eyepieces:</b> 20 mm (60×) for M11 framing → <b>12.5 mm (96×)</b> for M11 core &amp; Saturn's rings
    </div>

    <img src="images/chart_6_scutum_m11_and_saturn.png" class="chart-img" alt="Finder Chart 6: M11 &amp; Saturn"/>

    <h2>Step-by-Step Star-Hopping Guide</h2>
    <ol class="hop-list">
        <li><b>[STEP 1] Find M11 via Aquila's Tail:</b> Start at brilliant Altair (α Aql). Trace the eagle's body southwest to λ Aquilae (+3.4 mag).</li>
        <li><b>[STEP 2] Hop 4.5° South-West into Scutum:</b> From λ Aql, nudge 4.5° SW toward 12 Aquilae and into the dense star clouds of Scutum.</li>
        <li><b>[STEP 3] View M11:</b> In the 20 mm eyepiece, M11 resembles a compact, glittering V-shaped wedge (like a flight of wild ducks) containing over 400 stars with an 8th-mag yellow giant star near its apex. At 12.5 mm (96×), the star field explodes into dense pinpricks.</li>
        <li><b>[STEP 4] Saturn Planetary Finale (Observe after 21:40 CEST):</b> Look low in the East-South-East horizon below Pegasus. Saturn is the brightest golden, steady non-twinkling object in Aquarius.</li>
        <li><b>[STEP 5] Inspect Saturn at 96× (12.5 mm):</b> As Saturn rises past 20° altitude above ground air turbulence:
            <br/>• <b>Rings:</b> View the stunning ring plane tilted nearly edge-on. Look for the Cassini Division during moments of steady seeing.
            <br/>• <b>Titan:</b> Saturn's largest moon (mag 8.4) shines clearly 4 ring-diameters away!
        </li>
    </ol>
</body>
</html>"""
    chapters.append(("chart_6_scutum_saturn.xhtml", "Chart 6: M11 & Saturn", chart6_html))

    # 14. Appendix: Collimation
    appendix_html = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <title>Appendix: Collimation Guide</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <div class="nav-bar">
        <a href="toc.xhtml">← Table of Contents</a>
        <a href="04_target_catalog.xhtml">← Target Catalog</a>
    </div>

    <h1>Appendix: Dobsonian Mirror Collimation</h1>
    <div class="subtitle">Sky-Watcher Skyliner Classic 200P — Quick Field Reference</div>

    <div class="callout" style="border-color: #b91c1c; background-color: #fef2f2;">
        <b>CRITICAL SAFETY: TILT TUBE HORIZONTALLY BEFORE COLLIMATING!</b><br/>
        Never collimate with the telescope pointing straight up. If an Allen key or thumbscrew slips from your fingers, it will fall directly onto the 200 mm primary mirror and chip the optical coatings. Tilt the tube 20°–30° above horizontal so any dropped tool harmlessly hits the steel tube wall!
    </div>

    <h2>Hardware Controls</h2>
    <img src="images/collimation_hardware_controls.png" class="chart-img" alt="Collimation Hardware Controls"/>
    <ul>
        <li><b>Secondary Spider Hub:</b> 1 center Phillips bolt (axial depth/rotation) + 3 Allen tilt screws (2.0/2.5 mm).</li>
        <li><b>Primary Rear Cell:</b> 3 large white thumbscrews (spring collimation) + 3 small black thumbscrews (locking). Back off locking screws 1/2 turn before collimating!</li>
    </ul>

    <h2>The 3-Step Alignment Procedure</h2>
    <img src="images/collimation_steps_view.png" class="chart-img" alt="Collimation Sight Tube Progression"/>
    <ol>
        <li><b>Step 1: Center Secondary under Focuser:</b> Secondary appears circular and centered in drawtube.</li>
        <li><b>Step 2: Adjust Secondary Tilt:</b> Sight tube crosshairs point dead-center inside the primary center donut.</li>
        <li><b>Step 3: Adjust Primary Tilt:</b> Turn 3 rear white thumbscrews until black pupil spot sits centered in the donut. Snug black lock screws.</li>
    </ol>

    <h2>The High-Power Star Test</h2>
    <img src="images/star_test_patterns.png" class="chart-img" alt="Star Test Patterns"/>
    <p>Center Polaris in your 12.5 mm eyepiece (96×). Defocus slightly 1/4 turn inside and outside of focus:</p>
    <ul>
        <li><b>✓ Perfect Collimation:</b> Concentric bullseye rings with centered secondary shadow.</li>
        <li><b>✗ Miscollimated (Coma):</b> Rings bunched on one side; secondary shadow shifted off-center. Adjust primary thumbscrews toward the flare.</li>
        <li><b>✗ Pinched Optics:</b> Triangular 3-lobed rings. Loosen primary mirror clips!</li>
    </ul>

    <h2>Recommended Video Tutorials</h2>
    <ul>
        <li><b>AstroBiscuits (Live Star Test):</b> <code>https://www.youtube.com/watch?v=mviFGu37AcI</code></li>
        <li><b>Small Optics (Dobsonian Collimation):</b> <code>https://www.youtube.com/watch?v=ht0WAEpya1o</code></li>
        <li><b>Orion Telescopes (Theory &amp; Tools):</b> <code>https://www.youtube.com/watch?v=YAVGcGEBmCE</code></li>
    </ul>
</body>
</html>"""
    chapters.append(("appendix_collimation.xhtml", "Appendix: Collimation Guide", appendix_html))

    # Package files into EPUB ZIP archive
    print("Packaging EPUB files...")

    # Unique book identifier
    book_uuid = f"urn:uuid:stargazing-dvigrad-2026-09-12"
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
  <docTitle><text>Dvigrad Stargazing Party — Field Guide &amp; Finder Charts</text></docTitle>
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
    <dc:title>Dvigrad Stargazing Party — Master Field Guide &amp; Finder Charts</dc:title>
    <dc:creator>Branko Toic</dc:creator>
    <dc:language>en</dc:language>
    <dc:date>2026-09-12</dc:date>
    <meta property="dcterms:modified">{now_iso}</meta>
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

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n=======================================================")
    print(f"EPUB BOOK SUCCESSFULLY GENERATED!")
    print(f"Path: {output_path}")
    print(f"Size: {file_size_mb:.2f} MB")
    print(f"Chapters: {len(chapters)}")
    print(f"Images:   {len(img_sources)}")
    print(f"=======================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile Stargazing Session into an E-Reader EPUB")
    parser.add_argument("--session-dir", type=str, default=None, help="Path to observations/<session-folder>")
    parser.add_argument("--output", type=str, default=None, help="Output .epub file path")
    args = parser.parse_args()
    build_epub(args.session_dir, args.output)

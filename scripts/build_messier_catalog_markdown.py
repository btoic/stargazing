#!/usr/bin/env python3
"""Builds a comprehensive, GitHub-optimized messier_catalog.md in the repository root
compiling all 110 Messier catalog objects with interactive index, relative image embeds,
optical configurations, and step-by-step observing guides.
"""

import os
import sys
import json
import math

script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
pylibs_dir = os.path.join(repo_root, '.pylibs')
if os.path.isdir(pylibs_dir) and pylibs_dir not in sys.path:
    sys.path.insert(0, pylibs_dir)

from astropy.coordinates import SkyCoord
import astropy.units as u

CATALOG_FILE = os.path.join(repo_root, 'catalogs', 'messier_catalog.json')
OUTPUT_FILE = os.path.join(repo_root, 'messier_catalog.md')

# Bespoke rich descriptions for the showpiece objects
BESPOKE_DESCRIPTIONS = {
    "M1": {
        "acq": "Ghostly oval smudge floating ~1.1° northwest of Tianguan (ζ Tauri); distinctive diffuse envelope stands out from faint field stars.",
        "detail": "Careful examination at 96× reveals subtle brightness variations across the 6' × 4' elliptical cloud and irregular, ragged outer boundaries.",
        "hop": "From Aldebaran, trace Taurus's horns northeast to Tianguan (ζ Tau, mag 3.0). Slew 1.1° northwest into the finder field; M1 floats right beside a 6th-magnitude field star."
    },
    "M11": {
        "acq": "Incredible, compact star swarm resembling a flight of wild ducks in V-formation, anchored by an 8th-magnitude star near the apex.",
        "detail": "12.5mm (96×) resolves hundreds of diamond-dust stellar points within the rich Scutum Star Cloud; one of the richest open clusters known (~2,900 member stars).",
        "hop": "Locate Altair in Aquila. Follow Aquila's backbone 14° South to λ Aquilae (mag 3.4), then slew 4.5° WSW into the glowing Scutum star cloud."
    },
    "M13": {
        "acq": "Majestic globular cluster visible even in the optical finder as a hazy, luminous circular patch on the western edge of the Hercules Keystone.",
        "detail": "96× resolution is breathtaking: core resolves into hundreds of diamond points with spider-leg star chains sprawling across 20 arcminutes. Search the SE quadrant for the subtle three-bladed 'Propeller' dust lane.",
        "hop": "Identify the Keystone of Hercules between Vega and Corona Borealis. Trace the western edge between η and ζ Herculis; M13 lies exactly 1/3 of the way from η toward ζ."
    },
    "M27": {
        "acq": "Ethereal apple-core / hourglass nebula glow floating prominently against the rich starry Milky Way background in Vulpecula.",
        "detail": "12.5mm (96×) brings out the bright central waist, flanking outer 'ear' lobes, and subtle green-grey ionization tints under dark skies.",
        "hop": "Locate Sagitta (The Arrow) just south of Albireo. From γ Sagittae (the arrow tip), slew 3.2° due North; M27 appears unmistakably in the center of the field."
    },
    "M31": {
        "acq": "Magnificent Andromeda Galaxy; naked-eye visible under Bortle 4 skies. Sweeps the entire 50' field of view in the 20mm Super eyepiece.",
        "detail": "20mm (60×) captures the brilliant concentrated galactic nucleus, sprawling spiral disk, satellite dwarf galaxy M32 to the south, companion M110 to the northwest, and the prominent dark dust absorption lane along the northwest flank.",
        "hop": "From the Great Square of Pegasus, identify Alpheratz (α And). Follow the Andromeda chain 7° to δ And, then 7° to reddish Mirach (β And). Turn 90° NW: hop 3.5° to μ And, then 3.5° to ν And. Slew 1.5° further NW into M31."
    },
    "M42": {
        "acq": "The Great Orion Nebula; sweeping luminous green-grey gas curtains surrounding the radiant Trapezium multiple star cluster in Orion's Sword.",
        "detail": "60× frames the immense wings of nebulosity, the dark 'Fish's Mouth' absorption bay, and the neighboring reflection nebula M43.",
        "hop": "Locate Orion's Belt (Alnitak, Alnilam, Mintaka). Drop 4° South to Orion's Sword; M42 is the middle fuzzy 'star' easily visible to the naked eye."
    },
    "M45": {
        "acq": "The Pleiades (Seven Sisters); spectacular open cluster spanning nearly 2° of sky; fills the finder and low-power eyepiece with radiant blue-white B-type giants.",
        "detail": "Best observed with the lowest magnification available (20mm / 60× or binoculars) to take in the cluster geometry, Alcyone, Maia, Electra, and surrounding star chains.",
        "hop": "Look 14° northwest of Aldebaran in Taurus; unmistakable naked-eye cluster visible from almost any location."
    },
    "M51": {
        "acq": "The Whirlpool Galaxy; famous face-on spiral interacting with dwarf companion NGC 5195 near Alkaid in Ursa Major.",
        "detail": "96× reveals the dual galactic cores and distinctive annular spiral structure with averted vision under steady, dark skies.",
        "hop": "Locate Alkaid (η UMa) at the tip of the Big Dipper's handle. Slew 3.5° southwest toward Cor Caroli; center the pair of interacting cores."
    },
    "M57": {
        "acq": "The Ring Nebula; unmistakable smoky cheerio disc floating midway between Sheliak (β) and Sulafat (γ) in Lyra.",
        "detail": "12.5mm (96×) magnifies the ring to 1.4' × 1.0', clearly displaying the hollow dark core, bright outer oval rim, and delicate grey-green gas contrast.",
        "hop": "Locate Vega in Lyra. Drop 6° south to the bottom parallelogram stars Sheliak (β) and Sulafat (γ). Center the Telrad reticle exactly halfway between β and γ Lyrae."
    },
    "M81": {
        "acq": "Bode's Galaxy; brilliant spiral galaxy with bright oval disk and highly concentrated starlike nucleus in Ursa Major.",
        "detail": "Pairs beautifully with nearby cigar galaxy M82 in a single wide field; 96× reveals subtle disk elongation and high surface brightness.",
        "hop": "Draw a diagonal line from Phad (γ UMa) through Dubhe (α UMa) at the lip of the Big Dipper and extend it an equal distance northwest."
    },
    "M82": {
        "acq": "The Cigar Galaxy; famous edge-on starburst galaxy located only 38 arcminutes north of M81.",
        "detail": "12.5mm (96×) reveals a dramatic splinter of light bisected by dark dust clouds and irregular mottled starburst knots across the nuclear region.",
        "hop": "From M81, slew 0.6° due North; M82's bright edge-on needle appears in the same wide-field eyepiece."
    },
    "M104": {
        "acq": "The Sombrero Galaxy; striking edge-on spiral galaxy in Virgo boasting an immense central bulge and prominent dust lane.",
        "detail": "96× reveals the classic sombrero hat profile: brilliant glowing core sharply bisected along its southern edge by a crisp dark dust lane.",
        "hop": "Locate the Spica-Algorab line. From Algorab (δ Corvi), slew 5.5° northeast into southern Virgo."
    }
}

def format_coords(ra_deg, dec_deg):
    sc = SkyCoord(ra=ra_deg*u.deg, dec=dec_deg*u.deg)
    hms = sc.ra.to_string(unit=u.hour, sep=('h ', 'm ', 's'), precision=1)
    dms = sc.dec.to_string(unit=u.deg, sep=('° ', "' ", '"'), precision=1, alwayssign=True)
    return hms, dms

def get_observing_notes(obj):
    m_id = obj['m_id']
    if m_id in BESPOKE_DESCRIPTIONS:
        b = BESPOKE_DESCRIPTIONS[m_id]
        return b['acq'], b['detail'], b['hop']

    cat = obj.get('type_category', 'Other')
    fl_mm = obj['eyepiece_fl_mm']
    mag = obj['magnification']
    c_ra = obj['ra_deg']
    c_dec = obj['dec_deg']
    constel = obj['constellation']

    if cat == 'GC':
        acq = f"Noticeable circular misty ball with bright concentrated core floating against a dark starry backdrop in {constel}."
        detail = f"{fl_mm:g}mm ({mag}×) resolves the outer edges into sharp, glittering diamond star points; averted vision reveals rich granularity across the core."
        hop = f"Locate anchor constellation {constel} on the Context Chart. Slew Telrad reticle to RA {c_ra:.2f}°, Dec {c_dec:.2f}° and center the fuzzy ball in the 20mm finder eyepiece."
    elif cat == 'OC':
        acq = f"Gorgeous scattered star cluster filling the field with diverse stellar magnitudes and pleasing geometric groupings."
        detail = f"{fl_mm:g}mm ({mag}×) deepens sky contrast and splits intimate stellar pairs and chains within the rich central grouping."
        hop = f"Locate {constel} via Context Chart. Align Telrad reticle to target coordinates (RA {c_ra:.2f}°, Dec {c_dec:.2f}°); cluster stars emerge immediately in the finder."
    elif cat == 'PN':
        acq = f"Distinct smoky disc or oval with crisp boundaries, standing out conspicuously from surrounding point-like field stars."
        detail = f"{fl_mm:g}mm ({mag}×) brightens the outer nebular shell; subtle brightness variations and central hollow emerge clearly under steady seeing."
        hop = f"Locate {constel} anchor stars. Slew Telrad reticle to target coordinates (RA {c_ra:.2f}°, Dec {c_dec:.2f}°); identify the tiny non-twinkling smoky disk."
    elif cat == 'Galaxy':
        acq = f"Ethereal oval glow with condensed galactic nucleus; framing the galaxy within the wide 50' field maximizes contrast against the sky."
        detail = f"{fl_mm:g}mm ({mag}×) darkens the background sky, aiding detection of subtle core elongation, dust lanes, and halo extent with averted vision."
        hop = f"Locate constellation {constel}. Follow the guide stars on the Wide-Field Chart to RA {c_ra:.2f}°, Dec {c_dec:.2f}°; look for a soft hazy smudge."
    elif cat in ['Nebula', 'SNR']:
        acq = f"Soft, sprawling contrast signature floating among field stars; best detected by sweeping slowly across the field at 60×."
        detail = f"{fl_mm:g}mm ({mag}×) highlights subtle ionization knots, filamentary edges, and embedded star groupings within the glowing cloud."
        hop = f"Locate {constel} guide stars. Align Telrad reticle to RA {c_ra:.2f}°, Dec {c_dec:.2f}°; sweep gently until nebulous glow fills the field."
    else:
        acq = f"Sweep field at 20mm (60×) until distinct contrast signature appears centered in the 50' view."
        detail = f"{fl_mm:g}mm ({mag}×) deepens sky contrast and brings out fine structural detail under dark, transparent skies."
        hop = f"Align finder to {constel} target coordinates at RA {c_ra:.2f}°, Dec {c_dec:.2f}°."

    return acq, detail, hop

def main():
    print(f"Loading {CATALOG_FILE}...")
    with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
        catalog_data = json.load(f)
    objects = catalog_data['objects']
    print(f"Loaded {len(objects)} Messier objects.")

    md = []

    # Title & Introduction
    md.append("# 🌌 Complete Messier Catalog Observer's Guide (M1 – M110)\n")
    md.append("**Visual Observing Program & Deep-Sky Field Guide for Amateur Astronomers**\n")
    md.append("> **Optics Profile**: Sky-Watcher Skyliner Classic 200P (203/1200mm $f/6$ Dobsonian Newtonian Reflector)  \n"
              "> **Eyepieces**: 20mm Super (60×, 50' TFOV, 3.4mm exit pupil) & 12.5mm Plössl (96×, 31' TFOV, 2.1mm exit pupil)  \n"
              "> **Chart Format**: Toner-Saver Negative B/W Edition (Pure `#ffffff` background, black stars, pre-inverted 180° for Newtonians)  \n"
              "> **Difficulty Ratings**: Calibrated from Michael Swanson's *NexStar User's Guide II* (`Easy`, `Medium`, `Hard`)\n")
    md.append("---\n")

    # Interactive Master Catalog Index
    md.append("<a id=\"messier-catalog-index\"></a>\n")
    md.append("## 📋 Messier Catalog Master Index\n")
    md.append("Click any object's **Finder Guide Link** to jump directly to its complete 4-part visual observation suite.\n\n")

    md.append("| # | Object Name / Designation | Constellation | Type | Mag ($V$) | Size | Difficulty | Finder Guide |\n")
    md.append("| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: |\n")

    for obj in objects:
        m_id = obj['m_id']
        m_num = obj['number']
        cname = obj.get('common_name', '')
        ngc = obj.get('ngc', '')
        if cname and ngc:
            name_str = f"**{cname}** ({ngc})"
        elif cname:
            name_str = f"**{cname}**"
        elif ngc:
            name_str = f"{ngc}"
        else:
            name_str = m_id

        constel = obj['constellation']
        otype = obj['type']
        vmag = f"{obj['v_mag']:.1f}" if obj.get('v_mag') is not None else "—"
        size_str = f"{obj['major_arcmin']}' × {obj['minor_arcmin']}'"
        diff = obj['difficulty']

        md.append(f"| **{m_id}** | {name_str} | {constel} | {otype} | {vmag} | {size_str} | {diff} | [View Guide](#m{m_num}) |\n")

    md.append("\n---\n\n")

    # Detailed Per-Object Sections (M1 to M110)
    for i, obj in enumerate(objects):
        m_id = obj['m_id']
        m_num = obj['number']
        m_slug = m_id.lower()
        cname = obj.get('common_name', '')
        ngc = obj.get('ngc', '')
        constel = obj['constellation']
        otype = obj['type']
        vmag = f"{obj['v_mag']:.1f}" if obj.get('v_mag') is not None else "—"
        size_str = f"{obj['major_arcmin']}' × {obj['minor_arcmin']}'"
        diff = obj['difficulty']
        dist_str = obj.get('dist_str', 'Varies')
        rec_eye = obj.get('recommended_eyepiece', '12.5mm Plössl (96×)')
        fl_mm = obj.get('eyepiece_fl_mm', 12.5)
        mag_val = obj.get('magnification', 96)
        fov_val = int(obj.get('fov_deg', 0.52) * 60)
        exit_pupil = round(203.0 / mag_val, 1)

        ra_hms, dec_dms = format_coords(obj['ra_deg'], obj['dec_deg'])
        acq_note, detail_note, hop_guide = get_observing_notes(obj)

        prev_num = 110 if m_num == 1 else m_num - 1
        next_num = 1 if m_num == 110 else m_num + 1

        title_parts = [m_id]
        if cname:
            title_parts.append(cname)
        if ngc:
            title_parts.append(f"({ngc})")
        title_heading = " ".join(title_parts) + f" — {constel}"

        md.append(f"<a id=\"m{m_num}\"></a>\n")
        md.append(f"## {title_heading}\n\n")
        md.append(f"[↑ Back to Catalog Index](#messier-catalog-index) • [← Previous: M{prev_num}](#m{prev_num}) • [Next: M{next_num} →](#m{next_num})\n\n")

        # Technical Parameters Table
        md.append("| Technical Parameter | Specification |\n")
        md.append("| :--- | :--- |\n")
        md.append(f"| **Designation** | {m_id} {f'({ngc})' if ngc else ''} |\n")
        if cname:
            md.append(f"| **Common Name** | **{cname}** |\n")
        md.append(f"| **Constellation** | {constel} |\n")
        md.append(f"| **Classification** | {otype} ({obj.get('type_category', 'DSO')}) |\n")
        md.append(f"| **Visual Magnitude ($V$)** | {vmag} mag |\n")
        md.append(f"| **Apparent Dimensions** | {size_str} |\n")
        md.append(f"| **Estimated Distance** | {dist_str} |\n")
        md.append(f"| **Swanson Difficulty** | **{diff}** (*NexStar User's Guide II*) |\n")
        md.append(f"| **Coordinates (J2000)** | RA **{ra_hms}** • Dec **{dec_dms}** |\n")
        md.append(f"| **Recommended Eyepiece** | {fl_mm:g}mm ({mag_val}× magnification, {fov_val}' TFOV, {exit_pupil}mm exit pupil) |\n\n")

        # 1. Eyepiece Simulation & Technical Dossier
        md.append("### 1. Telescope Eyepiece Simulation & Technical Dossier\n")
        md.append("> [!NOTE]\n"
                  f"> **Viewport B** depicts the pre-inverted 180° field view through the Newtonian reflector ({fl_mm:g}mm eyepiece / {mag_val}× magnification, {fov_val}' true field of view: South at top, West at left, N ↓, E →). **Viewport C** integrates target ephemeris and optical notes.\n\n")
        md.append(f"![{m_id} Eyepiece Simulation and Technical Dossier](shared/{m_slug}/eyepiece_dossier_skywatcher-skyliner-200p.png)\n\n")

        # 2. Constellation Context Orientation Chart
        md.append("### 2. Constellation Context & Regional Orientation Chart\n")
        md.append("> [!TIP]\n"
                  "> **Viewport Context** presents a wide ~50°–65° naked-eye orientation field (stars down to visual magnitude 6.5) with official IAU constellation guide lines. The dashed bounding box marks the exact area covered by the wide-field star-hopping chart below.\n\n")
        md.append(f"![{m_id} Constellation Context Orientation Chart](shared/{m_slug}/context.png)\n\n")

        # 3. Wide-Field Star-Hopping Chart
        md.append("### 3. Wide-Field Star-Hopping Finder Chart\n")
        md.append("> [!IMPORTANT]\n"
                  "> **Viewport A** provides an upright naked-eye / optical finder orientation (N ↑, E ←) with stars down to visual magnitude 8.5. Standard concentric Telrad rings (0.5°, 2.0°, 4.0°) and 5.0° finder circle are centered directly on the target.\n\n")
        md.append(f"![{m_id} Wide-Field Star-Hopping Finder Chart](shared/{m_slug}/widefield_skywatcher-skyliner-200p.png)\n\n")
        md.append(f"*([📄 Open Full High-Resolution Master A4 Finder Chart](shared/{m_slug}/chart_skywatcher-skyliner-200p.png))*\n\n")

        # 4. Observing Strategy & Hop Instructions
        md.append("### 4. Observing Strategy & Step-by-Step Hop Instructions\n\n")
        md.append(f"- **Acquisition & Framing (20mm Super / 60×, 50' FOV)**:\n  {acq_note}\n")
        md.append(f"- **High-Power Inspection & Detail ({fl_mm:g}mm / {mag_val}×, {fov_val}' FOV)**:\n  {detail_note}\n\n")
        md.append(f"**Step-by-Step Star Hop Narrative**:\n{hop_guide}\n\n")

        md.append("---\n\n")

    # Write output file
    content = "".join(md)
    print(f"Writing {len(content)} characters ({len(content.splitlines())} lines) to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Successfully generated {OUTPUT_FILE}!")

if __name__ == '__main__':
    main()

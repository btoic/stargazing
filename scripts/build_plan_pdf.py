#!/usr/bin/env python3
"""
scripts/build_plan_pdf.py - Generates a publication-quality, printable 2-Page PDF Master Guide
for observation sessions (formatted for a single double-sided A4 sheet).
"""

import os
import sys
import argparse
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
PYLIBS_DIR = os.path.join(REPO_ROOT, '.pylibs')
if PYLIBS_DIR not in sys.path:
    sys.path.insert(0, PYLIBS_DIR)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, HRFlowable
)
from reportlab.pdfgen import canvas

def generate_timeline_chart(output_path):
    fig, ax = plt.subplots(figsize=(9.5, 3.2), dpi=300)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#f8fafc')

    t_start = datetime(2026, 9, 12, 19, 15)
    t_end = datetime(2026, 9, 12, 22, 45)

    twilight_bands = [
        (datetime(2026, 9, 12, 19, 19), datetime(2026, 9, 12, 19, 50), '#cbd5e1', 'Civil Twilight'),
        (datetime(2026, 9, 12, 19, 50), datetime(2026, 9, 12, 20, 26), '#94a3b8', 'Nautical Twilight'),
        (datetime(2026, 9, 12, 20, 26), datetime(2026, 9, 12, 21, 5), '#475569', 'Astronomical Twilight'),
        (datetime(2026, 9, 12, 21, 5), datetime(2026, 9, 12, 22, 45), '#0f172a', 'True Astro Darkness (Moonless)')
    ]

    for start, end, col, lbl in twilight_bands:
        ax.axvspan(start, end, color=col, alpha=0.35, zorder=1)

    tasks = [
        ("Mirror Cooldown", datetime(2026, 9, 12, 19, 30), datetime(2026, 9, 12, 20, 0), '#64748b'),
        ("Albireo & M22", datetime(2026, 9, 12, 20, 0), datetime(2026, 9, 12, 20, 30), '#0284c7'),
        ("Globulars: M13, M92, M11", datetime(2026, 9, 12, 20, 30), datetime(2026, 9, 12, 21, 15), '#2563eb'),
        ("Peak Dark: M57, M27, M31, Double Cl.", datetime(2026, 9, 12, 21, 15), datetime(2026, 9, 12, 22, 0), '#7c3aed'),
        ("Saturn & Moons", datetime(2026, 9, 12, 22, 0), datetime(2026, 9, 12, 22, 30), '#d97706'),
    ]

    y_pos = range(len(tasks)-1, -1, -1)
    for y, (name, start, end, bar_col) in zip(y_pos, tasks):
        dur = (end - start).total_seconds() / 86400.0
        ax.barh(y, dur, left=start, height=0.55, color=bar_col, edgecolor='#1e293b', linewidth=1.0, zorder=3)
        mid_time = start + (end - start) / 2
        ax.text(mid_time, y, name, ha='center', va='center', color='white', fontweight='bold', fontsize=7.8, zorder=4)

    ax.axvline(datetime(2026, 9, 12, 19, 19), color='#ea580c', linestyle='--', linewidth=1.2, zorder=5)
    ax.text(datetime(2026, 9, 12, 19, 19), 4.75, "Sunset 19:19", color='#ea580c', fontsize=7.5, fontweight='bold', ha='center')

    ax.axvline(datetime(2026, 9, 12, 19, 38), color='#b45309', linestyle=':', linewidth=1.2, zorder=5)
    ax.text(datetime(2026, 9, 12, 19, 38), 4.25, "Moonset 19:38", color='#b45309', fontsize=7.5, fontweight='bold', ha='center')

    ax.axvline(datetime(2026, 9, 12, 21, 5), color='#38bdf8', linestyle='--', linewidth=1.2, zorder=5)
    ax.text(datetime(2026, 9, 12, 21, 5), 4.75, "Astro Dark 21:05", color='#0369a1', fontsize=7.5, fontweight='bold', ha='center')

    ax.axvline(datetime(2026, 9, 12, 21, 40), color='#16a34a', linestyle=':', linewidth=1.2, zorder=5)
    ax.text(datetime(2026, 9, 12, 21, 40), 4.75, "Saturn >15°", color='#15803d', fontsize=7.5, fontweight='bold', ha='center')

    ax.set_yticks([])
    ax.set_xlim(t_start, t_end)
    ax.set_ylim(-0.6, 5.2)

    ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=[15, 30, 45, 0]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.tick_params(axis='x', labelsize=8.5, colors='#334155')
    ax.grid(True, axis='x', color='#cbd5e1', linestyle=':', linewidth=0.8, alpha=0.7)

    for spine in ax.spines.values():
        spine.set_color('#94a3b8')

    plt.title("DVIGRAD OBSERVATION SCHEDULE & CELESTIAL PHASES (2026-09-12)", fontsize=10, fontweight='bold', color='#0f172a', pad=14)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor='white', bbox_inches='tight')
    plt.close()
    print(f"Timeline chart generated: {output_path}")

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor('#64748b'))

        if self._pageNumber > 1:
            self.drawString(18*mm, 283*mm, "Dvigrad Stargazing Party — Field Observation Guide (Sep 12, 2026)")
            self.drawRightString(192*mm, 283*mm, "Sky-Watcher 200P Dobsonian (8\" f/6)")
            self.setStrokeColor(colors.HexColor('#cbd5e1'))
            self.setLineWidth(0.6)
            self.line(18*mm, 281*mm, 192*mm, 281*mm)

        self.setStrokeColor(colors.HexColor('#cbd5e1'))
        self.setLineWidth(0.6)
        self.line(18*mm, 12*mm, 192*mm, 12*mm)

        self.drawString(18*mm, 8.5*mm, "Dvigrad Medieval Ruins (Kanfanar, Istria) • Bortle 4 (SQM 21.0) • Lat 45.126° N, Lon 13.813° E")
        self.drawRightString(192*mm, 8.5*mm, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def build_pdf(output_dir=None):
    if output_dir is None:
        output_dir = os.path.join(REPO_ROOT, 'observations', 'dvigrad-2026-09-12')
    
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, 'STARGAZING_PLAN.pdf')
    timeline_img = os.path.join(output_dir, 'timeline_gantt.png')

    generate_timeline_chart(timeline_img)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=18*mm,
        rightMargin=18*mm,
        topMargin=18*mm,
        bottomMargin=16*mm
    )

    styles = getSampleStyleSheet()
    c_primary = colors.HexColor('#0f172a')
    c_sub = colors.HexColor('#475569')
    c_dark = colors.HexColor('#1e293b')

    title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=c_primary, spaceAfter=4)
    subtitle_style = ParagraphStyle('DocSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13.5, textColor=c_sub, spaceAfter=12)
    h1_style = ParagraphStyle('Heading1_Custom', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.HexColor('#1e3a8a'), spaceBefore=8, spaceAfter=5, keepWithNext=True)
    body_style = ParagraphStyle('Body_Custom', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=11.8, textColor=c_dark, spaceAfter=5)
    callout_style = ParagraphStyle('Callout_Text', parent=styles['Normal'], fontName='Helvetica', fontSize=8.2, leading=11.2, textColor=colors.HexColor('#1e293b'))
    table_header_style = ParagraphStyle('TableHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=9.5, textColor=colors.white, alignment=1)
    table_cell_style = ParagraphStyle('TableCell', parent=styles['Normal'], fontName='Helvetica', fontSize=7.6, leading=9.8, textColor=c_dark)
    table_cell_bold = ParagraphStyle('TableCellBold', parent=table_cell_style, fontName='Helvetica-Bold')
    table_cell_center = ParagraphStyle('TableCellCenter', parent=table_cell_style, alignment=1)

    story = []

    # PAGE 1: HEADER, SITE PROFILE & TIMELINE
    story.append(Paragraph("DVIGRAD STARGAZING PARTY — MASTER FIELD GUIDE", title_style))
    story.append(Paragraph("<b>Date:</b> Saturday, September 12, 2026 &nbsp;|&nbsp; <b>Observing Window:</b> 20:00 – 22:30 CEST (UTC+2)<br/>"
                           "<b>Location:</b> Dvigrad Fortress Ruins, Kanfanar, Istria, Croatia (45.12637° N, 13.81296° E, Elev 143 m)<br/>"
                           "<b>Instrument:</b> Sky-Watcher Skyliner Classic 200P Dobsonian (200 mm / 8\" Newtonian Reflector, f/6, 1200 mm FL)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=10))

    site_box_data = [
        [
            Paragraph("<b>LOCATION & LIGHT POLLUTION PROFILE</b><br/>"
                      "• <b>Bortle Class:</b> Class 4 (Rural / Suburban transition)<br/>"
                      "• <b>Zenith Sky Brightness:</b> 20.86 – 21.15 mag/arcsec² (SQM)<br/>"
                      "• <b>Naked-Eye Limiting Mag (NELM):</b> 6.0 – 6.2 mag overhead<br/>"
                      "• <b>Valley Topography:</b> Deep Draga depression blocks coastal light domes (Rovinj & Pula). Limiting tree & terrain obstruction: <b>10°–15° cutoff</b>.", callout_style),
            Paragraph("<b>TELESCOPE & OPTICAL CONFIGURATION</b><br/>"
                      "• <b>200P Dobsonian:</b> 200 mm aperture, f/6, 1200 mm focal length (820× eye)<br/>"
                      "• <b>20 mm Eyepiece (Finder/Wide):</b> 60× mag | 3.3 mm exit pupil | <b>50' (0.83°) TFOV</b><br/>"
                      "• <b>12.5 mm Eyepiece (High Power):</b> 96× mag | 2.1 mm exit pupil | <b>31' (0.52°) TFOV</b><br/>"
                      "• <b>Orientation:</b> Newtonian inverted 180° (up=down, left=right). RACI=upright.", callout_style)
        ]
    ]
    t_site = Table(site_box_data, colWidths=[87*mm, 87*mm])
    t_site.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f0f9ff')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (0, 0), 1.0, colors.HexColor('#0284c7')),
        ('BOX', (1, 0), (1, 0), 1.0, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_site)
    story.append(Spacer(1, 8))

    moon_data = [[
        Paragraph("<b>MOON EPHEMERIS & DARK SKY VERDICT: ZERO LUNAR LIGHT POLLUTION</b><br/>"
                  "On Sep 12, 2026, the Moon is a razor-thin <b>3.1% waxing crescent</b> (1.1 days after New Moon) and <b>sets at 19:38 CEST</b> (prior to start). Throughout the observing party (20:00–22:30 CEST), the Moon is <b>below the horizon (-4° to -30° Alt)</b>. Pristine Bortle 4 contrast for faint deep-sky nebulae and galaxies!", callout_style)
    ]]
    t_moon = Table(moon_data, colWidths=[174*mm])
    t_moon.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecfdf5')),
        ('BOX', (0, 0), (-1, -1), 1.0, colors.HexColor('#10b981')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_moon)
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>ASTRONOMICAL TIMELINE & OBSERVATION SCHEDULE</b>", h1_style))
    story.append(Image(timeline_img, width=174*mm, height=58.5*mm))
    story.append(Spacer(1, 6))

    twilight_data = [
        [Paragraph("Phase", table_header_style), Paragraph("Time Window (CEST)", table_header_style), Paragraph("Sun Alt", table_header_style), Paragraph("Target Program & Operational Guidance", table_header_style)],
        [Paragraph("Setup & Cooldown", table_cell_bold), Paragraph("19:30 – 20:00", table_cell_center), Paragraph("-2° to -8°", table_cell_center), Paragraph("Primary mirror cooldown (30-45 min). Finder alignment on Vega / Arcturus.", table_cell_style)],
        [Paragraph("Nautical Twilight", table_cell_bold), Paragraph("20:00 – 20:26", table_cell_center), Paragraph("-8° to -12°", table_cell_center), Paragraph("Bright double star <b>Albireo</b>. Urgent early sweep for <b>M22</b> before southern trees block it.", table_cell_style)],
        [Paragraph("Astro Twilight", table_cell_bold), Paragraph("20:26 – 21:05", table_cell_center), Paragraph("-12° to -18°", table_cell_center), Paragraph("Sky darkens, Milky Way Great Rift emerges. Hercules globulars <b>M13</b> and <b>M92</b>.", table_cell_style)],
        [Paragraph("<b>True Astro Darkness</b>", table_cell_bold), Paragraph("<b>21:05 – 22:30+</b>", table_cell_center), Paragraph("<b>&lt; -18.0°</b>", table_cell_center), Paragraph("<b>Zero solar glow.</b> Peak deep-sky window: <b>M57</b>, <b>M27</b>, <b>M31 / M32 / M110</b>, <b>Double Cluster</b>.", table_cell_style)],
        [Paragraph("Planetary Finale", table_cell_bold), Paragraph("22:00 – 22:30", table_cell_center), Paragraph("&lt; -24°", table_cell_center), Paragraph("<b>Saturn</b> rises above 20° in ESE. Edge-on ring needle geometry, <b>Titan</b> & icy moons.", table_cell_style)],
    ]
    t_twi = Table(twilight_data, colWidths=[32*mm, 28*mm, 20*mm, 94*mm])
    t_twi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#94a3b8')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 3.5),
    ]))
    story.append(t_twi)

    story.append(PageBreak())

    # PAGE 2: TARGET CATALOG, FIELD TIPS & CHARTS DIRECTORY
    story.append(Paragraph("CURATED TARGET CATALOG (MID-SESSION EPHEMERIS @ 21:15 CEST)", h1_style))
    story.append(Paragraph("Targets selected for high visual impact in 200 mm aperture, respecting the 10°–15° Dvigrad horizon obstruction. Step-by-step star-hopping instructions and inverted eyepiece simulations are on the referenced charts.", body_style))

    cat_data = [
        [Paragraph("#", table_header_style), Paragraph("Target Name", table_header_style), Paragraph("Const", table_header_style), Paragraph("Type", table_header_style), Paragraph("Mag", table_header_style), Paragraph("Size", table_header_style), Paragraph("Difficulty", table_header_style), Paragraph("Chart Ref", table_header_style), Paragraph("Recommended Eyepiece", table_header_style)],
        [Paragraph("1", table_cell_center), Paragraph("<b>Albireo (β Cyg)</b>", table_cell_style), Paragraph("Cyg", table_cell_style), Paragraph("Double Star", table_cell_style), Paragraph("3.1/5.1", table_cell_center), Paragraph("34.3\"", table_cell_center), Paragraph("Very Easy", table_cell_style), Paragraph("Chart 2", table_cell_bold), Paragraph("20mm / 12.5mm", table_cell_style)],
        [Paragraph("2", table_cell_center), Paragraph("<b>M22 (NGC 6656)</b>", table_cell_style), Paragraph("Sgr", table_cell_style), Paragraph("Globular Cl.", table_cell_style), Paragraph("5.1", table_cell_center), Paragraph("32.0'", table_cell_center), Paragraph("Easy", table_cell_style), Paragraph("Full Sky", table_cell_bold), Paragraph("20mm → 12.5mm", table_cell_style)],
        [Paragraph("3", table_cell_center), Paragraph("<b>M13 (Great Globular)</b>", table_cell_style), Paragraph("Her", table_cell_style), Paragraph("Globular Cl.", table_cell_style), Paragraph("5.8", table_cell_center), Paragraph("20.0'", table_cell_center), Paragraph("Easy", table_cell_style), Paragraph("Chart 3", table_cell_bold), Paragraph("12.5mm (96×)", table_cell_style)],
        [Paragraph("4", table_cell_center), Paragraph("<b>M92 (NGC 6341)</b>", table_cell_style), Paragraph("Her", table_cell_style), Paragraph("Globular Cl.", table_cell_style), Paragraph("6.3", table_cell_center), Paragraph("14.0'", table_cell_center), Paragraph("Easy", table_cell_style), Paragraph("Chart 3", table_cell_bold), Paragraph("12.5mm (96×)", table_cell_style)],
        [Paragraph("5", table_cell_center), Paragraph("<b>M11 (Wild Duck)</b>", table_cell_style), Paragraph("Sct", table_cell_style), Paragraph("Open Cluster", table_cell_style), Paragraph("5.8", table_cell_center), Paragraph("14.0'", table_cell_center), Paragraph("Easy", table_cell_style), Paragraph("Chart 6", table_cell_bold), Paragraph("20mm & 12.5mm", table_cell_style)],
        [Paragraph("6", table_cell_center), Paragraph("<b>M57 (Ring Nebula)</b>", table_cell_style), Paragraph("Lyr", table_cell_style), Paragraph("Planetary Neb.", table_cell_style), Paragraph("8.8", table_cell_center), Paragraph("1.4'×1.0'", table_cell_center), Paragraph("Easy", table_cell_style), Paragraph("Chart 1", table_cell_bold), Paragraph("12.5mm (96×)", table_cell_style)],
        [Paragraph("7", table_cell_center), Paragraph("<b>M27 (Dumbbell)</b>", table_cell_style), Paragraph("Vul", table_cell_style), Paragraph("Planetary Neb.", table_cell_style), Paragraph("7.4", table_cell_center), Paragraph("8.0'×5.6'", table_cell_center), Paragraph("Medium", table_cell_style), Paragraph("Chart 2", table_cell_bold), Paragraph("20mm (60×)", table_cell_style)],
        [Paragraph("8", table_cell_center), Paragraph("<b>Double Cluster</b>", table_cell_style), Paragraph("Per", table_cell_style), Paragraph("Dual Open Cl.", table_cell_style), Paragraph("3.7/3.8", table_cell_center), Paragraph("60.0'", table_cell_center), Paragraph("Easy", table_cell_style), Paragraph("Chart 5", table_cell_bold), Paragraph("20mm (60×)", table_cell_style)],
        [Paragraph("9", table_cell_center), Paragraph("<b>M31 (Andromeda)</b>", table_cell_style), Paragraph("And", table_cell_style), Paragraph("Spiral Galaxy", table_cell_style), Paragraph("3.4", table_cell_center), Paragraph("190'×60'", table_cell_center), Paragraph("Easy", table_cell_style), Paragraph("Chart 4", table_cell_bold), Paragraph("20mm (60×)", table_cell_style)],
        [Paragraph("10", table_cell_center), Paragraph("<b>Saturn & Titan</b>", table_cell_style), Paragraph("Aqr", table_cell_style), Paragraph("Planet & Rings", table_cell_style), Paragraph("+0.6", table_cell_center), Paragraph("19.2\"", table_cell_center), Paragraph("Very Easy", table_cell_style), Paragraph("Chart 6", table_cell_bold), Paragraph("12.5mm (96×)", table_cell_style)],
    ]
    t_cat = Table(cat_data, colWidths=[8.5*mm, 33.5*mm, 14*mm, 23*mm, 15*mm, 15*mm, 19*mm, 17*mm, 28*mm])
    t_cat.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#94a3b8')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_cat)
    story.append(Spacer(1, 7))

    # PRACTICAL FIELD PROTOCOLS
    story.append(Paragraph("PRACTICAL FIELD PROTOCOLS FOR DVIGRAD RUINS", h1_style))
    tips_data = [
        [
            Paragraph("<b>FIELD PROTOCOLS & OBSERVING TIPS</b><br/>"
                      "• <b>Primary Mirror Acclimation:</b> Set up the 200P Dobsonian by 19:30 CEST. An 8\" parabolic mirror requires 30–45 min to reach thermal equilibrium. Tube air currents degrade high-power views of M13, M57, and Saturn until fully cooled.<br/>"
                      "• <b>Valley Dew Management:</b> The Draga depression concentrates cool, damp air. Keep unmounted eyepieces in warm jacket pockets or closed cases. Replace the front dust cover on the telescope when taking socializing breaks.<br/>"
                      "• <b>Tracking Near Zenith ('Dobson Hole'):</b> Objects straight overhead (&gt;80° Alt, e.g. M57 & Albireo) are stiff to track in an Alt-Az mount. Observe M57 between 21:15 and 21:45 as it rolls west of the meridian (70°–75° Alt) for effortless manual nudging.<br/>"
                      "• <b>Red Light & Dark Adaptation:</b> Full retinal rod-cell dark adaptation requires 20–30 min. Strict deep red lights only—avoid phone screens to preserve Bortle 4 contrast on faint nebula lobes and galactic dust lanes.<br/>"
                      "• <b>Saturn Elevation Timing:</b> Saturn rises around 20:20 CEST but clears the 15° Dvigrad tree line at 21:40. Reserve 22:00–22:30 for the planetary finale at &gt;20° altitude for stable seeing.", callout_style)
        ]
    ]
    t_tips = Table(tips_data, colWidths=[174*mm])
    t_tips.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fefce8')),
        ('BOX', (0, 0), (-1, -1), 1.0, colors.HexColor('#eab308')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_tips)
    story.append(Spacer(1, 7))

    # CHARTS DIRECTORY
    story.append(Paragraph("PRINTABLE SKY CHARTS & MAPS DIRECTORY (TONER-SAVER NEGATIVE)", h1_style))
    charts_list_data = [
        [Paragraph("Chart / Map Document", table_header_style), Paragraph("Target Objects & Region", table_header_style), Paragraph("Eyepiece Simulation & FOV", table_header_style), Paragraph("File Path", table_header_style)],
        [Paragraph("<b>Full Sky Map</b>", table_cell_bold), Paragraph("All constellations, Milky Way, 15° obstruction ring", table_cell_style), Paragraph("All-sky naked-eye planisphere", table_cell_center), Paragraph("<code>observations/dvigrad-2026-09-12/full_sky_map.pdf</code>", table_cell_style)],
        [Paragraph("<b>Finder Chart 1</b>", table_cell_bold), Paragraph("M57 Ring Nebula in Lyra", table_cell_style), Paragraph("12.5mm (96×, 31' FOV) Inverted Negative", table_cell_center), Paragraph("<code>charts/chart_1_lyra_m57.pdf</code>", table_cell_style)],
        [Paragraph("<b>Finder Chart 2</b>", table_cell_bold), Paragraph("M27 Dumbbell Nebula & Albireo Double", table_cell_style), Paragraph("20mm (60×, 50' FOV) Inverted Negative", table_cell_center), Paragraph("<code>charts/chart_2_vulpecula_m27_albireo.pdf</code>", table_cell_style)],
        [Paragraph("<b>Finder Chart 3</b>", table_cell_bold), Paragraph("Hercules Globulars M13 & M92", table_cell_style), Paragraph("12.5mm (96×, 31' FOV) Inverted Negative", table_cell_center), Paragraph("<code>charts/chart_3_hercules_m13_m92.pdf</code>", table_cell_style)],
        [Paragraph("<b>Finder Chart 4</b>", table_cell_bold), Paragraph("M31 Andromeda Galaxy, M32 & M110", table_cell_style), Paragraph("20mm (60×, 50' FOV) Inverted Negative", table_cell_center), Paragraph("<code>charts/chart_4_andromeda_m31.pdf</code>", table_cell_style)],
        [Paragraph("<b>Finder Chart 5</b>", table_cell_bold), Paragraph("Perseus Double Cluster (NGC 869 / 884)", table_cell_style), Paragraph("20mm (60×, 50' FOV) Inverted Negative", table_cell_center), Paragraph("<code>charts/chart_5_perseus_double_cluster.pdf</code>", table_cell_style)],
        [Paragraph("<b>Finder Chart 6</b>", table_cell_bold), Paragraph("M11 Wild Duck Cluster & Saturn Ring View", table_cell_style), Paragraph("Dual Inset: 12.5mm M11 & Saturn", table_cell_center), Paragraph("<code>charts/chart_6_scutum_m11_and_saturn.pdf</code>", table_cell_style)],
    ]
    t_charts = Table(charts_list_data, colWidths=[30*mm, 52*mm, 44*mm, 48*mm])
    t_charts.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#94a3b8')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 2.8),
    ]))
    story.append(t_charts)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Master Guide PDF successfully created: {pdf_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build Master Guide PDF')
    parser.add_argument('--output-dir', type=str, default=None, help='Output directory for the PDF')
    args = parser.parse_args()
    build_pdf(args.output_dir)

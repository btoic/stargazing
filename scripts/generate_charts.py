#!/usr/bin/env python3
"""
scripts/generate_charts.py - Generates All-Sky Planisphere & Toner-Saver Negative Finder Charts
for observation sessions (B/W Monochrome print-ready edition, strictly formatted for standard A4 paper).
- All-Sky Planisphere: Standard A4 Portrait (210 mm x 297 mm / 595.3 pt x 841.9 pt)
- Star-Hopping Finder Charts (1 to 6): Standard A4 Landscape (297 mm x 210 mm / 841.9 pt x 595.3 pt)
"""

import os
import sys
import math
import json
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
PYLIBS_DIR = os.path.join(REPO_ROOT, '.pylibs')
if PYLIBS_DIR not in sys.path:
    sys.path.insert(0, PYLIBS_DIR)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, Polygon, Wedge, FancyArrowPatch
import numpy as np

from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy.time import Time
import astropy.units as u

CACHE_DIR = os.path.join(REPO_ROOT, '.cache')

# Exact standard A4 dimensions in inches (1 inch = 25.4 mm = 72 pt)
A4_LANDSCAPE = (297.0 / 25.4, 210.0 / 25.4)  # 11.6929" x 8.2677" -> 841.89 pt x 595.28 pt
A4_PORTRAIT  = (210.0 / 25.4, 297.0 / 25.4)  # 8.2677" x 11.6929" -> 595.28 pt x 841.89 pt

# Global datasets
stars_file = os.path.join(CACHE_DIR, 'stars.json')
if not os.path.exists(stars_file):
    stars_file = os.path.join(CACHE_DIR, 'stars.6.json')
with open(stars_file) as f:
    stars_data = json.load(f)

lines_file = os.path.join(CACHE_DIR, 'constellations.lines.json')
with open(lines_file) as f:
    lines_data = json.load(f)

mw_file = os.path.join(CACHE_DIR, 'mw.json')
with open(mw_file) as f:
    mw_data = json.load(f)

# Observation Site & Time Defaults (Dvigrad)
location = EarthLocation(lat=45.12637*u.deg, lon=13.81296*u.deg, height=143*u.m)
obs_time = Time('2026-09-12T19:15:00', scale='utc')
altaz_frame = AltAz(obstime=obs_time, location=location)

def norm_ra(ra):
    return ((ra % 360.0) + 360.0) % 360.0

def d_ra(ra1, ra2):
    diff = norm_ra(ra1) - norm_ra(ra2)
    if diff > 180.0:
        diff -= 360.0
    elif diff < -180.0:
        diff += 360.0
    return diff

def load_field(name):
    path = os.path.join(CACHE_DIR, 'fields', f'{name}.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []

def setup_wide_field(ax, c_ra, c_dec, span_ra, span_dec):
    ax.set_facecolor('#ffffff')
    cos_dec = math.cos(math.radians(c_dec))
    x_min, x_max = -(span_ra / 2.0) * cos_dec, (span_ra / 2.0) * cos_dec
    y_min, y_max = -(span_dec / 2.0), (span_dec / 2.0)
    ax.set_xlim(x_max, x_min)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect('equal')

    # Constellation lines - high contrast dark charcoal
    for feat in lines_data['features']:
        for seg in feat['geometry']['coordinates']:
            for i in range(len(seg)-1):
                p1, p2 = seg[i], seg[i+1]
                ra1, dec1 = norm_ra(p1[0]), p1[1]
                ra2, dec2 = norm_ra(p2[0]), p2[1]
                dra1, dra2 = d_ra(ra1, c_ra), d_ra(ra2, c_ra)
                if abs(dra1) < span_ra*1.2 and abs(dec1 - c_dec) < span_dec*1.1 and abs(dra2) < span_ra*1.2 and abs(dec2 - c_dec) < span_dec*1.1:
                    x1 = dra1 * math.cos(math.radians(dec1))
                    y1 = dec1 - c_dec
                    x2 = dra2 * math.cos(math.radians(dec2))
                    y2 = dec2 - c_dec
                    ax.plot([x1, x2], [y1, y2], color='#475569', linewidth=1.1, linestyle='-', alpha=0.9, zorder=2)

    # Stars - solid black dots, scaled by visual magnitude
    for f in stars_data['features']:
        ra = norm_ra(f['geometry']['coordinates'][0])
        dec = f['geometry']['coordinates'][1]
        mag = f['properties']['mag']
        dra = d_ra(ra, c_ra)
        if abs(dra) < span_ra and abs(dec - c_dec) < span_dec:
            x = dra * math.cos(math.radians(dec))
            y = dec - c_dec
            diff_mag = max(0.0, 6.5 - mag)
            size = max(1.5, (diff_mag)**2.2 * 2.8)
            ax.plot(x, y, 'o', color='#000000', markersize=math.sqrt(size), zorder=5)

    # Orientation Box in top-left corner
    ax.text(0.035, 0.955, "N ↑\n← E", transform=ax.transAxes, fontsize=8.5, fontweight='bold', color='#000000',
            va='top', ha='left', bbox=dict(boxstyle='square,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=20)
    
    # Outer frame
    for spine in ax.spines.values():
        spine.set_color('#000000')
        spine.set_linewidth(1.1)
    ax.set_xticks([]); ax.set_yticks([])
    return x_min, x_max, y_min, y_max

def draw_telrad_reticle(ax, cx, cy, label_pos=(2.1, 1.8)):
    """Draws standardized B/W Telrad & 5-deg Optical Finder rings."""
    # 0.5° inner Telrad ring (solid)
    ax.add_patch(Circle((cx, cy), 0.25, facecolor='none', edgecolor='#000000', linestyle='-', linewidth=1.1, zorder=8))
    # 2.0° middle Telrad ring (dashed)
    ax.add_patch(Circle((cx, cy), 1.0, facecolor='none', edgecolor='#000000', linestyle='--', linewidth=0.9, zorder=8))
    # 4.0° outer Telrad ring (dash-dot)
    ax.add_patch(Circle((cx, cy), 2.0, facecolor='none', edgecolor='#000000', linestyle='-.', linewidth=0.8, zorder=8))
    # 5.0° Optical Finder circle (dotted)
    ax.add_patch(Circle((cx, cy), 2.5, facecolor='none', edgecolor='#333333', linestyle=':', linewidth=1.0, zorder=7))
    
    lx, ly = label_pos
    ax.text(cx + lx, cy + ly, "5° Finder / Telrad FOV", fontsize=7.2, color='#000000', fontweight='bold',
            bbox=dict(boxstyle='square,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=10)

def draw_target_marker(ax, tx, ty):
    """Draws a crisp B/W bullseye target marker with crosshair tick marks."""
    ax.plot(tx, ty, 'o', color='#000000', markersize=3.8, zorder=12)
    ax.plot(tx, ty, 'o', color='none', markeredgecolor='#000000', markeredgewidth=1.1, markersize=9.5, zorder=12)
    ax.plot(tx, ty, 'o', color='none', markeredgecolor='#000000', markeredgewidth=0.9, linestyle='--', markersize=14.5, zorder=12)

def make_full_sky_map(output_dir):
    print("Generating Full Sky Map (A4 Portrait, B/W Toner-Saver)...")
    def project(alt, az):
        r = (90.0 - alt) / 90.0
        az_rad = np.radians(az)
        x = -r * np.sin(az_rad)
        y =  r * np.cos(az_rad)
        return x, y

    star_ras = np.array([norm_ra(f['geometry']['coordinates'][0]) for f in stars_data['features']])
    star_decs = np.array([f['geometry']['coordinates'][1] for f in stars_data['features']])
    star_mags = np.array([f['properties']['mag'] for f in stars_data['features']])

    sc_stars = SkyCoord(ra=star_ras*u.deg, dec=star_decs*u.deg)
    altaz_stars = sc_stars.transform_to(altaz_frame)

    alt_deg = altaz_stars.alt.deg
    az_deg  = altaz_stars.az.deg
    mask = alt_deg > 0.0
    vis_alt = alt_deg[mask]
    vis_az  = az_deg[mask]
    vis_mag = star_mags[mask]
    vis_x, vis_y = project(vis_alt, vis_az)
    sizes = np.clip([max(0.0, 6.2 - m)**2.1 * 1.8 + 1.0 for m in vis_mag], 1.0, 75.0)

    # Standard A4 Portrait: 210mm x 297mm (8.2677" x 11.6929")
    fig = plt.figure(figsize=A4_PORTRAIT, facecolor='white', dpi=300)
    ax = fig.add_axes([0.065, 0.23, 0.87, 0.615], aspect='equal')
    ax.set_facecolor('white')

    r_obs = 75.0 / 90.0
    ax.add_patch(Wedge((0, 0), 1.0, 0, 360, width=1.0 - r_obs, facecolor='#f1f5f9', edgecolor='none', zorder=1))

    ax.add_patch(Circle((0, 0), 1.0, facecolor='none', edgecolor='#000000', linewidth=1.8, zorder=10))
    ax.add_patch(Circle((0, 0), r_obs, facecolor='none', edgecolor='#000000', linestyle='--', linewidth=1.2, zorder=10))
    ax.add_patch(Circle((0, 0), 60/90, facecolor='none', edgecolor='#94a3b8', linestyle=':', linewidth=0.8, zorder=5))
    ax.add_patch(Circle((0, 0), 30/90, facecolor='none', edgecolor='#94a3b8', linestyle=':', linewidth=0.8, zorder=5))

    for az_line in range(0, 360, 45):
        x_end, y_end = project(0, az_line)
        ax.plot([0, x_end], [0, y_end], color='#cbd5e1', linestyle=':', linewidth=0.7, zorder=4)

    ax.plot([0], [0], '+', color='#000000', markersize=10, markeredgewidth=1.4, zorder=6)
    ax.text(0.015, 0.015, 'Zenith (90°)', fontsize=7.5, color='#000000', zorder=6)
    ax.text(0, (60/90)+0.01, '30° Alt', fontsize=6.5, color='#475569', ha='center', va='bottom', zorder=6)
    ax.text(0, (30/90)+0.01, '60° Alt', fontsize=6.5, color='#475569', ha='center', va='bottom', zorder=6)
    ax.text(0, r_obs+0.012, '15° Tree & Terrain Obstruction Line', fontsize=7.5, color='#000000', ha='center', va='bottom', fontweight='bold', zorder=11)

    for feat in mw_data['features']:
        for poly in feat['geometry']['coordinates']:
            for ring in poly:
                if len(ring) < 3: continue
                r_ras = np.array([norm_ra(p[0]) for p in ring])
                r_decs = np.array([p[1] for p in ring])
                sc_ring = SkyCoord(ra=r_ras*u.deg, dec=r_decs*u.deg)
                aa_ring = sc_ring.transform_to(altaz_frame)
                pts = [project(max(0, a), z) for a, z in zip(aa_ring.alt.deg, aa_ring.az.deg) if a > -5]
                if len(pts) >= 3:
                    ax.add_patch(Polygon(pts, closed=True, facecolor='#e2e8f0', edgecolor='none', alpha=0.45, zorder=2))

    for feat in lines_data['features']:
        for seg in feat['geometry']['coordinates']:
            for i in range(len(seg)-1):
                p1, p2 = seg[i], seg[i+1]
                sc1 = SkyCoord(ra=norm_ra(p1[0])*u.deg, dec=p1[1]*u.deg)
                sc2 = SkyCoord(ra=norm_ra(p2[0])*u.deg, dec=p2[1]*u.deg)
                aa1 = sc1.transform_to(altaz_frame)
                aa2 = sc2.transform_to(altaz_frame)
                if aa1.alt.deg > 0 and aa2.alt.deg > 0:
                    x1, y1 = project(aa1.alt.deg, aa1.az.deg)
                    x2, y2 = project(aa2.alt.deg, aa2.az.deg)
                    ax.plot([x1, x2], [y1, y2], color='#475569', linewidth=1.0, linestyle='-', alpha=0.85, zorder=3)

    ax.scatter(vis_x, vis_y, s=sizes, color='#000000', zorder=6)

    # Compass directions with outwards alignment away from circle
    dirs = [(0, 'N (North)', 1.04, 'center', 'bottom'),
            (45, 'NE', 1.04, 'right', 'bottom'),
            (90, 'E (East)', 1.04, 'right', 'center'),
            (135, 'SE', 1.04, 'right', 'top'),
            (180, 'S (South)', 1.04, 'center', 'top'),
            (225, 'SW', 1.04, 'left', 'top'),
            (270, 'W (West)', 1.04, 'left', 'center'),
            (315, 'NW', 1.04, 'left', 'bottom')]
    for az, lbl, r_pos, ha, va in dirs:
        x, y = project(0, az)
        ax.text(x * r_pos, y * r_pos, lbl, fontsize=8.5, fontweight='bold', color='#000000', ha=ha, va=va, zorder=12)

    targets_allsky = [
        ('M57 (Ring)', 283.396, 33.029, 0.02, 0.02),
        ('M27 (Dumbbell)', 299.901, 22.721, 0.02, -0.03),
        ('M13 (Globular)', 250.423, 36.460, 0.02, -0.05),
        ('M92', 258.280, 43.136, 0.02, 0.04),
        ('M31 (Andromeda)', 10.685, 41.269, 0.02, 0.02),
        ('Double Cluster', 35.150, 57.150, 0.02, 0.02),
        ('M11 (Wild Duck)', 282.775, -6.267, -0.04, -0.03),
        ('Saturn', 351.25, -4.85, 0.02, 0.02)
    ]
    for t_name, t_ra, t_dec, ox, oy in targets_allsky:
        sc = SkyCoord(ra=t_ra*u.deg, dec=t_dec*u.deg)
        aa = sc.transform_to(altaz_frame)
        if aa.alt.deg > 0:
            tx, ty = project(aa.alt.deg, aa.az.deg)
            draw_target_marker(ax, tx, ty)
            ax.text(tx + ox, ty + oy, f"{t_name}\n({aa.alt.deg:.0f}° Alt)", fontsize=6.8, fontweight='bold', color='#000000',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=16)

    ax.set_xlim(-1.24, 1.24); ax.set_ylim(-1.24, 1.24); ax.axis('off')

    # Header
    fig.text(0.065, 0.958, "DVIGRAD ALL-SKY PLANISPHERE (OBSERVATION MAP)", fontsize=13.0, fontweight='bold', color='#000000')
    fig.text(0.065, 0.938, "Date: Sep 12, 2026 • 21:15 CEST | Location: Dvigrad Ruins (45.126° N, 13.813° E) | Bortle 4 | B/W Toner-Saver Print Edition", fontsize=7.8, color='#333333')

    # Footer Info Box
    fig.text(0.065, 0.045,
             "HOW TO USE: Hold chart overhead with North facing North. Outer dashed ring marks the 15° Dvigrad Draga valley tree/terrain obstruction.\n"
             "MOON STATUS: Waxing crescent (3.1%) set at 19:38 CEST (below horizon). Genuine zero lunar pollution darkness for entire session.\n"
             "TELESCOPE: Sky-Watcher Skyliner Classic 200P (203mm f/6 Dobsonian) | Eyepieces: 20mm Super (60×, 50' FOV), 12.5mm Plössl (96×, 31' FOV)",
             fontsize=7.2, color='#000000', bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', edgecolor='#000000', linewidth=1.0))

    # Exact A4 page export (NO bbox_inches='tight' so A4 page boundary is strictly preserved)
    plt.savefig(os.path.join(output_dir, 'full_sky_map.png'), dpi=300, facecolor='white')
    plt.savefig(os.path.join(output_dir, 'full_sky_map.pdf'), dpi=300, facecolor='white')
    plt.close()
    print("Full Sky Map generated successfully (A4 Portrait).")

def make_chart_1(charts_dir):
    print("Generating Chart 1: M57 (A4 Landscape, Toner-Saver Negative)...")
    fig = plt.figure(figsize=A4_LANDSCAPE, facecolor='white', dpi=300)
    fig.text(0.035, 0.963, "STAR-HOPPING FINDER CHART 1: M57 (RING NEBULA) — LYRA", fontsize=12, fontweight='bold', color='#000000')
    fig.text(0.035, 0.936, "Location: Dvigrad (Bortle 4, SQM 21.0) | Sep 12, 2026 • 21:15 CEST | Sky-Watcher 200P Dobsonian (8\" f/6, 1200mm FL) | B/W Toner-Saver Edition", fontsize=7.8, color='#333333')

    # VIEWPORT A
    fig.text(0.035, 0.898, "VIEWPORT A: WIDE-FIELD STAR-HOPPING CHART (Upright Naked-Eye / Finder: N ↑, E ←)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_wide = fig.add_axes([0.035, 0.045, 0.485, 0.835])
    c_ra, c_dec = 283.0, 36.0
    setup_wide_field(ax_wide, c_ra, c_dec, 18.0, 18.0)

    stars_lyra = [
        (279.23, 38.78, 'Vega (α Lyr)\nmag 0.03', 0.4, 0.4, 8.5, 'bold'),
        (285.14, 33.36, 'Sheliak (β)\nmag 3.5', 0.4, 0.4, 7.8, 'bold'),
        (286.06, 32.69, 'Sulafat (γ)\nmag 3.2', -0.6, -0.6, 7.8, 'bold'),
        (280.67, 39.67, 'ε Lyr (Double-Double)', -0.5, 0.4, 7.2, 'normal'),
        (283.47, 36.90, 'δ Lyr', 0.4, 0.2, 7.2, 'normal'),
        (281.90, 37.60, 'ζ Lyr', -0.5, -0.4, 7.2, 'normal')
    ]
    for s_ra, s_dec, lbl, ox, oy, fsz, fweight in stars_lyra:
        x = d_ra(s_ra, c_ra) * math.cos(math.radians(s_dec))
        y = s_dec - c_dec
        ax_wide.text(x+ox, y+oy, lbl, fontsize=fsz, fontweight=fweight, color='#000000', zorder=10)

    m57_ra, m57_dec = 283.396, 33.029
    m57_x = d_ra(m57_ra, c_ra) * math.cos(math.radians(m57_dec))
    m57_y = m57_dec - c_dec
    v_x = d_ra(279.23, c_ra) * math.cos(math.radians(38.78))
    v_y = 38.78 - c_dec
    b_x = d_ra(285.14, c_ra) * math.cos(math.radians(33.36))
    b_y = 33.36 - c_dec

    arrow1 = FancyArrowPatch((v_x, v_y), (b_x+0.3, b_y+0.6), arrowstyle='->', mutation_scale=13, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax_wide.add_patch(arrow1)
    ax_wide.text((v_x+b_x)/2 - 0.7, (v_y+b_y)/2, "[STEP 1] Slew 6° South from Vega\nto base stars Sheliak & Sulafat", fontsize=7.2, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=10)

    arrow2 = FancyArrowPatch((b_x, b_y), (m57_x, m57_y), arrowstyle='->', mutation_scale=12, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax_wide.add_patch(arrow2)
    ax_wide.text((b_x+m57_x)/2 - 0.4, (b_y+m57_y)/2 + 0.8, "[STEP 2] Place reticle halfway\nbetween β & γ (closer to γ)", fontsize=7.2, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=10)

    draw_telrad_reticle(ax_wide, m57_x, m57_y, (2.1, 1.8))
    draw_target_marker(ax_wide, m57_x, m57_y)
    ax_wide.text(m57_x - 0.4, m57_y - 0.5, "M57 RING NEBULA\n(Centered in Reticle)", fontsize=7.8, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2), zorder=15)

    # VIEWPORT B: TELESCOPE EYEPIECE SIMULATION
    fig.text(0.545, 0.898, "VIEWPORT B: EYEPIECE SIMULATION (Negative Inverted 180°: N ↓, E →)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_eye = fig.add_axes([0.58, 0.485, 0.35, 0.395])
    ax_eye.set_facecolor('white')
    fov_deg = 0.52
    ax_eye.set_xlim(-fov_deg/2 - 0.02, fov_deg/2 + 0.02)
    ax_eye.set_ylim(-fov_deg/2 - 0.035, fov_deg/2 + 0.02)
    ax_eye.set_aspect('equal')
    ax_eye.add_patch(Circle((0, 0), fov_deg/2, facecolor='#ffffff', edgecolor='#000000', linewidth=1.8, zorder=1))
    ax_eye.plot([0, 0], [-fov_deg/2, fov_deg/2], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)
    ax_eye.plot([-fov_deg/2, fov_deg/2], [0, 0], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)

    m57_field = load_field('m57')
    for st in m57_field:
        dx = d_ra(st['ra'], m57_ra) * math.cos(math.radians(st['dec']))
        dy = st['dec'] - m57_dec
        dx_inv, dy_inv = -dx, -dy
        if math.hypot(dx_inv, dy_inv) < fov_deg/2 - 0.005:
            s_size = max(1.5, max(0.0, 12.5 - st['mag'])**2.2 * 0.9)
            ax_eye.plot(dx_inv, dy_inv, 'o', color='#000000', markersize=math.sqrt(s_size), alpha=0.95, zorder=10)

    ax_eye.add_patch(Ellipse((0, 0), 0.040, 0.029, angle=60, facecolor='#cbd5e1', edgecolor='#334151', linewidth=1.2, zorder=11))
    ax_eye.add_patch(Ellipse((0, 0), 0.022, 0.014, angle=60, facecolor='#ffffff', edgecolor='#475569', linewidth=0.8, zorder=12))
    ax_eye.text(0.025, 0.025, "Smoke Ring\n(Hollow Core)", fontsize=7.0, color='#000000', fontweight='bold', zorder=20)

    ax_eye.text(0, -fov_deg/2 + 0.035, "↓ N (Inverted)", fontsize=7.5, color='#000000', fontweight='bold', ha='center', zorder=25)
    ax_eye.text(fov_deg/2 - 0.035, 0, "E →", fontsize=7.5, color='#000000', fontweight='bold', va='center', ha='right', zorder=25)
    ax_eye.text(0, -fov_deg/2 - 0.022, "12.5mm Eyepiece (96× Magnification, 31' True FOV)", fontsize=7.5, color='#000000', ha='center')
    ax_eye.axis('off')

    # VIEWPORT C: DOSSIER & INSTRUCTIONS
    fig.text(0.545, 0.448, "VIEWPORT C: TARGET DOSSIER & STAR-HOPPING INSTRUCTIONS", fontsize=8.2, fontweight='bold', color='#000000')
    ax_info = fig.add_axes([0.545, 0.045, 0.420, 0.390])
    ax_info.axis('off')
    dossier_text = (
        "OBJECT DOSSIER: M57 (NGC 6720)\n"
        "• Constellation: Lyra | Type: Planetary Nebula\n"
        "• Magnitude: 8.8V | Surface Brightness: 9.3 mag/arcmin²\n"
        "• Apparent Size: 1.4' × 1.0' | Distance: ~2,570 light-years\n"
        "• Tonight's Ephemeris at Dvigrad (Sep 12, 2026):\n"
        "    20:00 CEST: Alt 76.4°, Az 204° (South-Southwest)\n"
        "    21:15 CEST: Alt 75.4°, Az 218° (Zenith Sweet Spot!)\n"
        "    22:30 CEST: Alt 64.3°, Az 237° (Safe > 60° Alt)\n\n"
        "OBSERVING STRATEGY & EYEPIECES:\n"
        "• Finder (20mm / 60×): M57 shows as a tiny, unmistakable\n"
        "  ghostly out-of-focus disk among sharp field stars.\n"
        "• Target (12.5mm / 96×): Resolves the smoke ring shape!\n"
        "  Averted vision clearly reveals the hollow dark core.\n"
        "• Filter: Under Dvigrad's Bortle 4 skies, radiant without filters.\n\n"
        "STEP-BY-STEP STAR HOP NARRATIVE:\n"
        "1. Naked-Eye: Locate brilliant Vega (mag 0.0) near Zenith.\n"
        "2. Identify Lyra's parallelogram ~6° south of Vega. Find the\n"
        "   two base stars: Sheliak (β, mag 3.5) and Sulafat (γ, mag 3.2).\n"
        "3. Slew Telrad / Finder: Place central reticle between β and γ,\n"
        "   slightly closer to Sulafat (about 60% of the distance).\n"
        "4. Eyepiece: Look for the ghostly smoke-ring between two stars!"
    )
    ax_info.text(0.0, 0.98, dossier_text, fontsize=6.8, color='#000000', fontfamily='monospace', va='top',
                 bbox=dict(boxstyle='round,pad=0.45', facecolor='#ffffff', edgecolor='#000000', linewidth=1.1))

    # Exact A4 page export (NO bbox_inches='tight')
    plt.savefig(os.path.join(charts_dir, 'chart_1_lyra_m57.png'), dpi=300, facecolor='white')
    plt.savefig(os.path.join(charts_dir, 'chart_1_lyra_m57.pdf'), dpi=300, facecolor='white')
    plt.close()
    print("Chart 1 saved (A4 Landscape).")

def make_chart_2(charts_dir):
    print("Generating Chart 2: M27 & Albireo (A4 Landscape, Toner-Saver Negative)...")
    fig = plt.figure(figsize=A4_LANDSCAPE, facecolor='white', dpi=300)
    fig.text(0.035, 0.963, "STAR-HOPPING FINDER CHART 2: M27 (DUMBBELL NEBULA) & ALBIREO — VULPECULA / CYGNUS", fontsize=11.5, fontweight='bold', color='#000000')
    fig.text(0.035, 0.936, "Location: Dvigrad (Bortle 4, SQM 21.0) | Sep 12, 2026 • 21:15 CEST | Sky-Watcher 200P Dobsonian (8\" f/6, 1200mm FL) | B/W Toner-Saver Edition", fontsize=7.8, color='#333333')

    # VIEWPORT A
    fig.text(0.035, 0.898, "VIEWPORT A: WIDE-FIELD STAR-HOPPING CHART (Upright Naked-Eye / Finder: N ↑, E ←)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_wide = fig.add_axes([0.035, 0.045, 0.485, 0.835])
    c_ra, c_dec = 296.0, 24.0
    setup_wide_field(ax_wide, c_ra, c_dec, 18.0, 18.0)

    key_stars = [
        (292.68, 27.96, 'β Cygni', -0.5, -0.6, 7.8, 'bold'),
        (299.70, 19.49, 'γ Sge (Arrow Tip)\nmag 3.51', 0.4, 0.3, 7.8, 'bold'),
        (296.79, 18.53, 'δ Sge', -0.3, -0.6, 7.2, 'normal'),
        (294.90, 17.47, 'α & β Sge\n(Arrow Feathers)', -0.6, -0.7, 7.2, 'normal'),
        (291.35, 20.18, 'Coathanger (Cr 399)\nAsterism', 0.4, 0.4, 7.5, 'bold')
    ]
    for s_ra, s_dec, lbl, ox, oy, fsz, fweight in key_stars:
        x = d_ra(s_ra, c_ra) * math.cos(math.radians(s_dec))
        y = s_dec - c_dec
        ax_wide.text(x+ox, y+oy, lbl, fontsize=fsz, fontweight=fweight, color='#000000', zorder=10)

    m27_ra, m27_dec = 299.901, 22.721
    m27_x = d_ra(m27_ra, c_ra) * math.cos(math.radians(m27_dec))
    m27_y = m27_dec - c_dec
    g_x = d_ra(299.70, c_ra) * math.cos(math.radians(19.49))
    g_y = 19.49 - c_dec

    arrow1 = FancyArrowPatch((g_x, g_y), (m27_x, m27_y), arrowstyle='->', mutation_scale=13, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax_wide.add_patch(arrow1)
    ax_wide.text((g_x+m27_x)/2 + 0.6, (g_y+m27_y)/2, "[STEP 1] Slew 3.2° North\nfrom γ Sagittae tip", fontsize=7.2, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=10)

    draw_telrad_reticle(ax_wide, m27_x, m27_y, (2.1, 1.8))
    draw_target_marker(ax_wide, m27_x, m27_y)
    ax_wide.text(m27_x - 0.5, m27_y + 0.6, "M27 DUMBBELL NEBULA", fontsize=7.8, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2), zorder=15)

    alb_x = d_ra(292.68, c_ra) * math.cos(math.radians(27.96))
    alb_y = 27.96 - c_dec
    draw_target_marker(ax_wide, alb_x, alb_y)
    ax_wide.text(alb_x - 0.4, alb_y + 0.8, "BONUS TARGET: ALBIREO\n(Gold & Blue Double Star)", fontsize=7.5, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=15)

    # VIEWPORT B: TELESCOPE EYEPIECE SIMULATION
    fig.text(0.545, 0.898, "VIEWPORT B: EYEPIECE SIMULATION (Negative Inverted 180°: N ↓, E →)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_eye = fig.add_axes([0.58, 0.485, 0.35, 0.395])
    ax_eye.set_facecolor('white')
    fov_deg = 0.83
    ax_eye.set_xlim(-fov_deg/2 - 0.03, fov_deg/2 + 0.03)
    ax_eye.set_ylim(-fov_deg/2 - 0.04, fov_deg/2 + 0.03)
    ax_eye.set_aspect('equal')
    ax_eye.add_patch(Circle((0, 0), fov_deg/2, facecolor='#ffffff', edgecolor='#000000', linewidth=1.8, zorder=1))
    ax_eye.plot([0, 0], [-fov_deg/2, fov_deg/2], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)
    ax_eye.plot([-fov_deg/2, fov_deg/2], [0, 0], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)

    m27_field = load_field('m27')
    for st in m27_field:
        dx = d_ra(st['ra'], m27_ra) * math.cos(math.radians(st['dec']))
        dy = st['dec'] - m27_dec
        dx_inv, dy_inv = -dx, -dy
        if math.hypot(dx_inv, dy_inv) < fov_deg/2 - 0.008:
            s_size = max(1.5, max(0.0, 12.5 - st['mag'])**2.2 * 0.9)
            ax_eye.plot(dx_inv, dy_inv, 'o', color='#000000', markersize=math.sqrt(s_size), alpha=0.95, zorder=10)

    ax_eye.add_patch(Ellipse((0, 0), 0.14, 0.10, angle=25, facecolor='#f1f5f9', edgecolor='#94a3b8', linestyle='--', linewidth=0.8, zorder=10))
    ax_eye.add_patch(Ellipse((-0.025, 0), 0.09, 0.12, angle=25, facecolor='#cbd5e1', edgecolor='#64748b', linestyle='--', linewidth=0.8, zorder=11))
    ax_eye.add_patch(Ellipse(( 0.025, 0), 0.09, 0.12, angle=25, facecolor='#cbd5e1', edgecolor='#64748b', linestyle='--', linewidth=0.8, zorder=11))
    ax_eye.add_patch(Ellipse((0, 0), 0.07, 0.09, angle=25, facecolor='#94a3b8', edgecolor='#334151', linewidth=1.1, zorder=12))
    ax_eye.text(0.12, 0.12, "Hourglass / Apple Core\n(Bright Central Waist)", fontsize=7.0, color='#000000', fontweight='bold', zorder=20)

    ax_eye.text(0, -fov_deg/2 + 0.045, "↓ N (Inverted)", fontsize=7.5, color='#000000', fontweight='bold', ha='center', zorder=25)
    ax_eye.text(fov_deg/2 - 0.045, 0, "E →", fontsize=7.5, color='#000000', fontweight='bold', va='center', ha='right', zorder=25)
    ax_eye.text(0, -fov_deg/2 - 0.022, "20mm Eyepiece (60× Magnification, 50' True FOV)", fontsize=7.5, color='#000000', ha='center')
    ax_eye.axis('off')

    # VIEWPORT C: DOSSIER & INSTRUCTIONS
    fig.text(0.545, 0.448, "VIEWPORT C: TARGET DOSSIER & STAR-HOPPING INSTRUCTIONS", fontsize=8.2, fontweight='bold', color='#000000')
    ax_info = fig.add_axes([0.545, 0.045, 0.420, 0.390])
    ax_info.axis('off')
    dossier_text = (
        "OBJECT DOSSIER: M27 (NGC 6853) & ALBIREO\n"
        "• Constellation: Vulpecula | Type: Planetary Nebula\n"
        "• Magnitude: 7.5V | Surface Brightness: 11.2 mag/arcmin²\n"
        "• Apparent Size: 8.0' × 5.6' | Distance: ~1,360 light-years\n"
        "• Tonight's Ephemeris at Dvigrad (Sep 12, 2026):\n"
        "    20:00 CEST: Alt 60.0°, Az 147° (Southeast)\n"
        "    21:15 CEST: Alt 67.2°, Az 166° (Meridian Sweet Spot!)\n"
        "    22:30 CEST: Alt 65.3°, Az 189° (High & Pristine)\n\n"
        "OBSERVING STRATEGY & EYEPIECES:\n"
        "• Finder (20mm / 60×): Ideal magnification! Frames the entire\n"
        "  classic 'apple-core' dumbbell glow against dark space.\n"
        "• Detail (12.5mm / 96×): Reveals the brighter outer rims\n"
        "  and faint extensions connecting the two main lobes.\n"
        "• Albireo (β Cyg): Split the 34.3\" pair into radiant\n"
        "  topaz-gold (mag 3.1) & sapphire-blue (mag 5.1)!\n\n"
        "STEP-BY-STEP STAR HOP NARRATIVE:\n"
        "1. Naked-Eye: Locate Sagitta the Arrow between Altair\n"
        "   and Albireo. Identify tip star γ Sagittae (mag 3.5).\n"
        "2. Telrad Hop: Place γ Sagittae on the southern outer 4° ring;\n"
        "   the central reticle points directly at M27 (3.2° North).\n"
        "3. Eyepiece confirmation: A striking, bright ethereal\n"
        "   hourglass cloud appears instantly in the 20mm field!"
    )
    ax_info.text(0.0, 0.98, dossier_text, fontsize=6.8, color='#000000', fontfamily='monospace', va='top',
                 bbox=dict(boxstyle='round,pad=0.45', facecolor='#ffffff', edgecolor='#000000', linewidth=1.1))

    # Exact A4 page export (NO bbox_inches='tight')
    plt.savefig(os.path.join(charts_dir, 'chart_2_vulpecula_m27_albireo.png'), dpi=300, facecolor='white')
    plt.savefig(os.path.join(charts_dir, 'chart_2_vulpecula_m27_albireo.pdf'), dpi=300, facecolor='white')
    plt.close()
    print("Chart 2 saved (A4 Landscape).")

def make_chart_3(charts_dir):
    print("Generating Chart 3: M13 & M92 (A4 Landscape, Toner-Saver Negative)...")
    fig = plt.figure(figsize=A4_LANDSCAPE, facecolor='white', dpi=300)
    fig.text(0.035, 0.963, "STAR-HOPPING FINDER CHART 3: M13 & M92 GLOBULAR CLUSTERS — HERCULES", fontsize=11.5, fontweight='bold', color='#000000')
    fig.text(0.035, 0.936, "Location: Dvigrad (Bortle 4, SQM 21.0) | Sep 12, 2026 • 21:15 CEST | Sky-Watcher 200P Dobsonian (8\" f/6, 1200mm FL) | B/W Toner-Saver Edition", fontsize=7.8, color='#333333')

    # VIEWPORT A
    fig.text(0.035, 0.898, "VIEWPORT A: WIDE-FIELD STAR-HOPPING CHART (Upright Naked-Eye / Finder: N ↑, E ←)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_wide = fig.add_axes([0.035, 0.045, 0.485, 0.835])
    c_ra, c_dec = 256.0, 38.0
    setup_wide_field(ax_wide, c_ra, c_dec, 20.0, 20.0)

    key_stars = [
        (250.77, 38.92, 'η Her (NW Corner)\nmag 3.48', 0.4, 0.4, 7.8, 'bold'),
        (250.84, 31.60, 'ζ Her (SW Corner)\nmag 2.81', 0.4, -0.6, 7.8, 'bold'),
        (257.65, 36.81, 'π Her (NE Corner)\nmag 3.16', -0.4, 0.4, 7.8, 'bold'),
        (254.98, 30.92, 'ε Her (SE Corner)\nmag 3.92', -0.4, -0.6, 7.2, 'bold'),
        (264.83, 46.00, 'ι Her (North)\nmag 3.82', 0.4, -0.6, 7.2, 'normal')
    ]
    for s_ra, s_dec, lbl, ox, oy, fsz, fweight in key_stars:
        x = d_ra(s_ra, c_ra) * math.cos(math.radians(s_dec))
        y = s_dec - c_dec
        ax_wide.text(x+ox, y+oy, lbl, fontsize=fsz, fontweight=fweight, color='#000000', zorder=10)

    keystone_coords = [(250.77, 38.92), (257.65, 36.81), (254.98, 30.92), (250.84, 31.60)]
    k_pts = [ (d_ra(ra, c_ra)*math.cos(math.radians(dec)), dec - c_dec) for ra, dec in keystone_coords ]
    ax_wide.add_patch(Polygon(k_pts, closed=True, facecolor='#f8fafc', edgecolor='#000000', linewidth=1.4, linestyle='--', alpha=0.5, zorder=3))
    ax_wide.text((k_pts[0][0]+k_pts[2][0])/2, (k_pts[0][1]+k_pts[2][1])/2, "THE KEYSTONE\nOF HERCULES", fontsize=8.0, fontweight='bold', color='#000000', ha='center', zorder=8)

    m13_ra, m13_dec = 250.423, 36.460
    m13_x = d_ra(m13_ra, c_ra) * math.cos(math.radians(m13_dec))
    m13_y = m13_dec - c_dec
    eta_x = d_ra(250.77, c_ra) * math.cos(math.radians(38.92))
    eta_y = 38.92 - c_dec

    arrow1 = FancyArrowPatch((eta_x, eta_y), (m13_x, m13_y), arrowstyle='->', mutation_scale=13, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax_wide.add_patch(arrow1)
    ax_wide.text(m13_x - 1.3, (eta_y+m13_y)/2, "[STEP 1] 1/3 way from η to ζ\nalong Keystone West side", fontsize=7.2, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=10)

    draw_telrad_reticle(ax_wide, m13_x, m13_y, (2.1, 1.8))
    draw_target_marker(ax_wide, m13_x, m13_y)
    ax_wide.text(m13_x - 1.4, m13_y - 1.2, "M13 GREAT GLOBULAR CLUSTER\n(Visible naked-eye in Bortle 4!)", fontsize=7.8, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2), zorder=15)

    m92_ra, m92_dec = 258.280, 43.136
    m92_x = d_ra(m92_ra, c_ra) * math.cos(math.radians(m92_dec))
    m92_y = m92_dec - c_dec
    pi_x = d_ra(257.65, c_ra) * math.cos(math.radians(36.81))
    pi_y = 36.81 - c_dec

    arrow2 = FancyArrowPatch((pi_x, pi_y), (m92_x, m92_y), arrowstyle='->', mutation_scale=13, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax_wide.add_patch(arrow2)
    ax_wide.text((pi_x+m92_x)/2 + 0.5, (pi_y+m92_y)/2, "[STEP 2] Hop 6.2° North\nfrom π Herculis to M92", fontsize=7.2, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=10)

    draw_target_marker(ax_wide, m92_x, m92_y)
    ax_wide.text(m92_x - 0.5, m92_y + 0.6, "M92 GLOBULAR CLUSTER", fontsize=7.8, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=15)

    # VIEWPORT B: TELESCOPE EYEPIECE SIMULATION
    fig.text(0.545, 0.898, "VIEWPORT B: EYEPIECE SIMULATION (Negative Inverted 180°: N ↓, E →)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_eye = fig.add_axes([0.58, 0.485, 0.35, 0.395])
    ax_eye.set_facecolor('white')
    fov_deg = 0.52
    ax_eye.set_xlim(-fov_deg/2 - 0.02, fov_deg/2 + 0.02)
    ax_eye.set_ylim(-fov_deg/2 - 0.035, fov_deg/2 + 0.02)
    ax_eye.set_aspect('equal')
    ax_eye.add_patch(Circle((0, 0), fov_deg/2, facecolor='#ffffff', edgecolor='#000000', linewidth=1.8, zorder=1))
    ax_eye.plot([0, 0], [-fov_deg/2, fov_deg/2], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)
    ax_eye.plot([-fov_deg/2, fov_deg/2], [0, 0], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)

    m13_field = load_field('m13')
    for st in m13_field:
        dx = d_ra(st['ra'], m13_ra) * math.cos(math.radians(st['dec']))
        dy = st['dec'] - m13_dec
        dx_inv, dy_inv = -dx, -dy
        if math.hypot(dx_inv, dy_inv) < fov_deg/2 - 0.005:
            s_size = max(1.5, max(0.0, 12.5 - st['mag'])**2.2 * 0.9)
            ax_eye.plot(dx_inv, dy_inv, 'o', color='#000000', markersize=math.sqrt(s_size), alpha=0.95, zorder=10)

    ax_eye.add_patch(Circle((0, 0), 0.16, facecolor='#f8fafc', edgecolor='#cbd5e1', linestyle=':', linewidth=0.8, zorder=11))
    ax_eye.add_patch(Circle((0, 0), 0.10, facecolor='#f1f5f9', edgecolor='#94a3b8', linestyle='--', linewidth=0.8, zorder=12))
    ax_eye.add_patch(Circle((0, 0), 0.05, facecolor='#e2e8f0', edgecolor='#64748b', linewidth=1.0, zorder=13))

    np.random.seed(42)
    n_stars = 170
    r_core = np.random.exponential(0.04, n_stars)
    th = np.random.uniform(0, 2*np.pi, n_stars)
    ax_eye.scatter(r_core*np.cos(th), r_core*np.sin(th), s=np.random.uniform(1.5, 8.5, n_stars), color='#000000', alpha=0.9, zorder=14)

    for p_ang in [30, 150, 270]:
        pr_rad = np.radians(p_ang)
        ax_eye.plot([0.008*np.cos(pr_rad), 0.035*np.cos(pr_rad)], [0.008*np.sin(pr_rad), 0.035*np.sin(pr_rad)],
                    color='#ffffff', linewidth=1.8, alpha=0.9, zorder=15)
    ax_eye.text(0.03, -0.05, "Propeller Lane\n(Averted Vision)", fontsize=7.0, color='#000000', fontstyle='italic', zorder=20)

    ax_eye.text(0, -fov_deg/2 + 0.035, "↓ N (Inverted)", fontsize=7.5, color='#000000', fontweight='bold', ha='center', zorder=25)
    ax_eye.text(fov_deg/2 - 0.035, 0, "E →", fontsize=7.5, color='#000000', fontweight='bold', va='center', ha='right', zorder=25)
    ax_eye.text(0, -fov_deg/2 - 0.022, "12.5mm Eyepiece (96× Magnification, 31' True FOV)", fontsize=7.5, color='#000000', ha='center')
    ax_eye.axis('off')

    # VIEWPORT C: DOSSIER & INSTRUCTIONS
    fig.text(0.545, 0.448, "VIEWPORT C: TARGET DOSSIER & STAR-HOPPING INSTRUCTIONS", fontsize=8.2, fontweight='bold', color='#000000')
    ax_info = fig.add_axes([0.545, 0.045, 0.420, 0.390])
    ax_info.axis('off')
    dossier_text = (
        "OBJECT DOSSIER: M13 (NGC 6205) & M92\n"
        "• Constellation: Hercules | Type: Globular Cluster\n"
        "• Magnitude: 5.8V | Surface Brightness: 11.9 mag/arcmin²\n"
        "• Apparent Size: 20' diameter | Stars: ~300,000 | Dist: 22,200 ly\n"
        "• Tonight's Ephemeris at Dvigrad (Sep 12, 2026):\n"
        "    20:00 CEST: Alt 69.3°, Az 256° (High West)\n"
        "    21:15 CEST: Alt 56.2°, Az 271° (Prime Observing!)\n"
        "    22:30 CEST: Alt 43.1°, Az 283° (Well Above Trees)\n\n"
        "OBSERVING STRATEGY & EYEPIECES:\n"
        "• Finder (20mm / 60×): Bright, glowing snowball of light\n"
        "  framed beautifully by two 7th-magnitude field stars.\n"
        "• Target (12.5mm / 96×): Mind-blowing resolution! In the\n"
        "  8\" Dobsonian, the cluster bursts into hundreds of sparkling\n"
        "  star pinpricks with spider-like arms radiating outwards.\n"
        "• Challenge: Spot the 3-bladed 'propeller' lane near the core.\n\n"
        "STEP-BY-STEP STAR HOP NARRATIVE:\n"
        "1. Naked-Eye: Locate the Keystone of Hercules in the West.\n"
        "2. Western side: η (NW corner) and ζ (SW corner).\n"
        "3. Slew Telrad / Finder: Move along the line from η toward ζ;\n"
        "   M13 sits exactly 1/3 of the way down.\n"
        "4. Bonus M92: From π Herculis (NE corner), hop 6.2° due North."
    )
    ax_info.text(0.0, 0.98, dossier_text, fontsize=6.8, color='#000000', fontfamily='monospace', va='top',
                 bbox=dict(boxstyle='round,pad=0.45', facecolor='#ffffff', edgecolor='#000000', linewidth=1.1))

    # Exact A4 page export (NO bbox_inches='tight')
    plt.savefig(os.path.join(charts_dir, 'chart_3_hercules_m13_m92.png'), dpi=300, facecolor='white')
    plt.savefig(os.path.join(charts_dir, 'chart_3_hercules_m13_m92.pdf'), dpi=300, facecolor='white')
    plt.close()
    print("Chart 3 saved (A4 Landscape).")

def make_chart_4(charts_dir):
    print("Generating Chart 4: M31 Andromeda (A4 Landscape, Toner-Saver Negative)...")
    fig = plt.figure(figsize=A4_LANDSCAPE, facecolor='white', dpi=300)
    fig.text(0.035, 0.963, "STAR-HOPPING FINDER CHART 4: M31 (ANDROMEDA GALAXY), M32 & M110 — ANDROMEDA", fontsize=11.5, fontweight='bold', color='#000000')
    fig.text(0.035, 0.936, "Location: Dvigrad (Bortle 4, SQM 21.0) | Sep 12, 2026 • 21:15 CEST | Sky-Watcher 200P Dobsonian (8\" f/6, 1200mm FL) | B/W Toner-Saver Edition", fontsize=7.8, color='#333333')

    # VIEWPORT A
    fig.text(0.035, 0.898, "VIEWPORT A: WIDE-FIELD STAR-HOPPING CHART (Upright Naked-Eye / Finder: N ↑, E ←)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_wide = fig.add_axes([0.035, 0.045, 0.485, 0.835])
    c_ra, c_dec = 12.0, 36.0
    setup_wide_field(ax_wide, c_ra, c_dec, 26.0, 24.0)

    key_stars = [
        (2.10, 29.09, 'Alpheratz (α And)\nmag 2.07', -0.6, -0.6, 7.8, 'bold'),
        (8.54, 30.86, 'δ And\nmag 3.27', 0.4, -0.6, 7.2, 'normal'),
        (17.43, 35.62, 'Mirach (β And)\nmag 2.07 (Red)', -0.6, 0.4, 7.8, 'bold'),
        (17.07, 38.50, 'μ And (Hop 1)\nmag 3.86', -0.5, 0.4, 7.2, 'bold'),
        (14.65, 41.08, 'ν And (Hop 2)\nmag 4.53', 0.4, 0.4, 7.2, 'bold')
    ]
    for s_ra, s_dec, lbl, ox, oy, fsz, fweight in key_stars:
        x = d_ra(s_ra, c_ra) * math.cos(math.radians(s_dec))
        y = s_dec - c_dec
        ax_wide.text(x+ox, y+oy, lbl, fontsize=fsz, fontweight=fweight, color='#000000', zorder=10)

    m31_ra, m31_dec = 10.685, 41.269
    m31_x = d_ra(m31_ra, c_ra) * math.cos(math.radians(m31_dec))
    m31_y = m31_dec - c_dec

    pts = [(2.10, 29.09), (8.54, 30.86), (17.43, 35.62), (17.07, 38.50), (14.65, 41.08), (m31_ra, m31_dec)]
    p_xy = [ (d_ra(ra, c_ra)*math.cos(math.radians(dec)), dec - c_dec) for ra, dec in pts ]

    ax_wide.add_patch(FancyArrowPatch(p_xy[0], p_xy[2], arrowstyle='->', mutation_scale=13, color='#000000', linestyle='--', linewidth=1.4, zorder=6))
    ax_wide.text((p_xy[0][0]+p_xy[2][0])/2, (p_xy[0][1]+p_xy[2][1])/2 + 0.9, "[STEP 1] Hop 14° NE to Mirach", fontsize=7.2, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=10)

    ax_wide.add_patch(FancyArrowPatch(p_xy[2], p_xy[3], arrowstyle='->', mutation_scale=12, color='#000000', linestyle='--', linewidth=1.4, zorder=6))
    ax_wide.add_patch(FancyArrowPatch(p_xy[3], p_xy[4], arrowstyle='->', mutation_scale=12, color='#000000', linestyle='--', linewidth=1.4, zorder=6))
    ax_wide.text(p_xy[3][0] + 0.6, (p_xy[2][1]+p_xy[4][1])/2, "[STEP 2] Turn 90° NW:\nHop to μ, then ν And", fontsize=7.2, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=10)

    ax_wide.add_patch(FancyArrowPatch(p_xy[4], p_xy[5], arrowstyle='->', mutation_scale=13, color='#000000', linestyle='--', linewidth=1.4, zorder=6))
    ax_wide.text((p_xy[4][0]+p_xy[5][0])/2, p_xy[5][1] + 1.0, "[STEP 3] Slew 1.5° NW to M31!", fontsize=7.2, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=10)

    draw_telrad_reticle(ax_wide, m31_x, m31_y, (2.1, 1.8))
    draw_target_marker(ax_wide, m31_x, m31_y)
    ax_wide.text(m31_x - 0.6, m31_y - 0.9, "M31 ANDROMEDA GALAXY\n(Naked-eye oval in Bortle 4)", fontsize=7.8, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2), zorder=15)

    # VIEWPORT B: TELESCOPE EYEPIECE SIMULATION
    fig.text(0.545, 0.898, "VIEWPORT B: EYEPIECE SIMULATION (Negative Inverted 180°: N ↓, E →)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_eye = fig.add_axes([0.58, 0.485, 0.35, 0.395])
    ax_eye.set_facecolor('white')
    fov_deg = 0.83
    ax_eye.set_xlim(-fov_deg/2 - 0.03, fov_deg/2 + 0.03)
    ax_eye.set_ylim(-fov_deg/2 - 0.04, fov_deg/2 + 0.03)
    ax_eye.set_aspect('equal')
    ax_eye.add_patch(Circle((0, 0), fov_deg/2, facecolor='#ffffff', edgecolor='#000000', linewidth=1.8, zorder=1))
    ax_eye.plot([0, 0], [-fov_deg/2, fov_deg/2], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)
    ax_eye.plot([-fov_deg/2, fov_deg/2], [0, 0], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)

    m31_field = load_field('m31')
    for st in m31_field:
        dx = d_ra(st['ra'], m31_ra) * math.cos(math.radians(st['dec']))
        dy = st['dec'] - m31_dec
        dx_inv, dy_inv = -dx, -dy
        if math.hypot(dx_inv, dy_inv) < fov_deg/2 - 0.008:
            s_size = max(1.5, max(0.0, 12.5 - st['mag'])**2.2 * 0.9)
            ax_eye.plot(dx_inv, dy_inv, 'o', color='#000000', markersize=math.sqrt(s_size), alpha=0.95, zorder=10)

    ax_eye.add_patch(Ellipse((0, 0), 0.75, 0.22, angle=38, facecolor='#f8fafc', edgecolor='#cbd5e1', linestyle='--', linewidth=0.8, zorder=11))
    ax_eye.add_patch(Ellipse((0, 0), 0.45, 0.14, angle=38, facecolor='#f1f5f9', edgecolor='#94a3b8', linestyle='--', linewidth=0.8, zorder=12))
    ax_eye.add_patch(Ellipse((0, 0), 0.20, 0.08, angle=38, facecolor='#e2e8f0', edgecolor='#64748b', linewidth=1.0, zorder=13))
    ax_eye.add_patch(Circle((0, 0), 0.03, facecolor='#1e293b', edgecolor='#000000', linewidth=1.0, zorder=14))

    lane_x = np.linspace(-0.25, 0.25, 50)
    lane_y = lane_x * math.tan(math.radians(38)) + 0.055
    ax_eye.plot(lane_x, lane_y, color='#0f172a', linewidth=2.0, alpha=0.85, zorder=15)
    ax_eye.text(0.08, 0.14, "Dark Dust Lane", fontsize=7.0, color='#000000', fontweight='bold', fontstyle='italic', zorder=25)

    m32_x_inv, m32_y_inv = 0.08, 0.26
    ax_eye.add_patch(Circle((m32_x_inv, m32_y_inv), 0.035, facecolor='#475569', edgecolor='#000000', linewidth=1.0, zorder=16))
    ax_eye.text(m32_x_inv+0.04, m32_y_inv, "M32 (Satellite)", fontsize=7.5, color='#000000', fontweight='bold', va='center', zorder=25)

    m110_x_inv, m110_y_inv = -0.15, -0.23
    ax_eye.add_patch(Ellipse((m110_x_inv, m110_y_inv), 0.14, 0.07, angle=20, facecolor='#f1f5f9', edgecolor='#64748b', linestyle='--', linewidth=1.0, zorder=16))
    ax_eye.text(m110_x_inv - 0.02, m110_y_inv + 0.05, "M110 (Dwarf Elliptical)", fontsize=7.5, color='#000000', fontweight='bold', ha='center', zorder=25)

    ax_eye.text(0, -fov_deg/2 + 0.045, "↓ N (Inverted)", fontsize=7.5, color='#000000', fontweight='bold', ha='center', zorder=25)
    ax_eye.text(fov_deg/2 - 0.045, 0, "E →", fontsize=7.5, color='#000000', fontweight='bold', va='center', ha='right', zorder=25)
    ax_eye.text(0, -fov_deg/2 - 0.022, "20mm Eyepiece (60× Magnification, 50' True FOV)", fontsize=7.5, color='#000000', ha='center')
    ax_eye.axis('off')

    # VIEWPORT C: DOSSIER & INSTRUCTIONS
    fig.text(0.545, 0.448, "VIEWPORT C: TARGET DOSSIER & STAR-HOPPING INSTRUCTIONS", fontsize=8.2, fontweight='bold', color='#000000')
    ax_info = fig.add_axes([0.545, 0.045, 0.420, 0.390])
    ax_info.axis('off')
    dossier_text = (
        "OBJECT DOSSIER: M31 (NGC 224), M32 & M110\n"
        "• Constellation: Andromeda | Type: Giant Spiral Galaxy\n"
        "• Magnitude: 3.4V | Surface Brightness: 13.5 mag/arcmin²\n"
        "• Apparent Size: 180' × 63' (~3°) | Distance: 2.54 million ly\n"
        "• Tonight's Ephemeris at Dvigrad (Sep 12, 2026):\n"
        "    20:00 CEST: Alt 24.7°, Az 52° (Rising in ENE)\n"
        "    21:15 CEST: Alt 36.2°, Az 65° (Prime Contrast!)\n"
        "    22:30 CEST: Alt 48.6°, Az 78° (Superb & High)\n\n"
        "OBSERVING STRATEGY & EYEPIECES:\n"
        "• 20mm Eyepiece (60×): Mandatory! With a 50' field, you can\n"
        "  sweep across the immense galactic disk and examine the\n"
        "  starlike active galactic nucleus and companion M32.\n"
        "• Dark Dust Lane: Look just outside the central core along the\n"
        "  northwestern edge; under Dvigrad's Bortle 4 sky, the silhouette\n"
        "  dust absorption lane is unmistakable with averted vision.\n"
        "• Companions: M32 is a bright, compact elliptical 24' south;\n"
        "  M110 is a soft, diffuse oval cloud 35' northwest.\n\n"
        "STEP-BY-STEP STAR HOP NARRATIVE:\n"
        "1. Naked-Eye: Find the Great Square of Pegasus. Identify the\n"
        "   northeast corner star Alpheratz (α And).\n"
        "2. Follow the Andromeda chain: hop 7° to δ And, then 7° to\n"
        "   reddish Mirach (β And, mag 2.1).\n"
        "3. Turn 90° NW: Hop 3.5° to μ And, then 3.5° to ν And.\n"
        "4. Slew 1.5° further NW: M31 fills the finder and eyepiece!"
    )
    ax_info.text(0.0, 0.98, dossier_text, fontsize=6.8, color='#000000', fontfamily='monospace', va='top',
                 bbox=dict(boxstyle='round,pad=0.45', facecolor='#ffffff', edgecolor='#000000', linewidth=1.1))

    # Exact A4 page export (NO bbox_inches='tight')
    plt.savefig(os.path.join(charts_dir, 'chart_4_andromeda_m31.png'), dpi=300, facecolor='white')
    plt.savefig(os.path.join(charts_dir, 'chart_4_andromeda_m31.pdf'), dpi=300, facecolor='white')
    plt.close()
    print("Chart 4 saved (A4 Landscape).")

def make_chart_5(charts_dir):
    print("Generating Chart 5: Double Cluster (A4 Landscape, Toner-Saver Negative)...")
    fig = plt.figure(figsize=A4_LANDSCAPE, facecolor='white', dpi=300)
    fig.text(0.035, 0.963, "STAR-HOPPING FINDER CHART 5: THE DOUBLE CLUSTER (NGC 869 / NGC 884) — PERSEUS", fontsize=11.5, fontweight='bold', color='#000000')
    fig.text(0.035, 0.936, "Location: Dvigrad (Bortle 4, SQM 21.0) | Sep 12, 2026 • 21:15 CEST | Sky-Watcher 200P Dobsonian (8\" f/6, 1200mm FL) | B/W Toner-Saver Edition", fontsize=7.8, color='#333333')

    # VIEWPORT A
    fig.text(0.035, 0.898, "VIEWPORT A: WIDE-FIELD STAR-HOPPING CHART (Upright Naked-Eye / Finder: N ↑, E ←)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_wide = fig.add_axes([0.035, 0.045, 0.485, 0.835])
    c_ra, c_dec = 32.0, 55.0
    setup_wide_field(ax_wide, c_ra, c_dec, 46.0, 22.0)

    key_stars = [
        (14.18, 60.72, 'Navi (γ Cas)\nmag 2.15', 0.4, -0.6, 7.8, 'bold'),
        (20.30, 60.23, 'Ruchbah (δ Cas)\nmag 2.66', -0.6, 0.5, 7.8, 'bold'),
        (26.68, 63.67, 'Segin (ε Cas)\nmag 3.35', -0.5, 0.4, 7.2, 'normal'),
        (51.08, 49.86, 'Mirfak (α Per)\nmag 1.79', -0.6, -0.6, 7.8, 'bold'),
        (43.34, 53.51, 'γ Per\nmag 2.91', -0.4, 0.4, 7.2, 'normal')
    ]
    for s_ra, s_dec, lbl, ox, oy, fsz, fweight in key_stars:
        x = d_ra(s_ra, c_ra) * math.cos(math.radians(s_dec))
        y = s_dec - c_dec
        ax_wide.text(x+ox, y+oy, lbl, fontsize=fsz, fontweight=fweight, color='#000000', zorder=10)

    dc_ra, dc_dec = 35.15, 57.15
    dc_x = d_ra(dc_ra, c_ra) * math.cos(math.radians(dc_dec))
    dc_y = dc_dec - c_dec

    g_x = d_ra(14.18, c_ra) * math.cos(math.radians(60.72))
    g_y = 60.72 - c_dec
    r_x = d_ra(20.30, c_ra) * math.cos(math.radians(60.23))
    r_y = 60.23 - c_dec

    arrow1 = FancyArrowPatch((g_x, g_y), (r_x, r_y), arrowstyle='->', mutation_scale=12, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax_wide.add_patch(arrow1)
    arrow2 = FancyArrowPatch((r_x, r_y), (dc_x, dc_y), arrowstyle='->', mutation_scale=13, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax_wide.add_patch(arrow2)
    ax_wide.text((r_x+dc_x)/2 - 0.2, (r_y+dc_y)/2 - 1.0, "[STEP 1] Extend γ through δ Cas\nby ~6° Southeast into Perseus", fontsize=7.2, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=10)

    draw_telrad_reticle(ax_wide, dc_x, dc_y, (2.1, 1.8))
    draw_target_marker(ax_wide, dc_x, dc_y)
    ax_wide.text(dc_x - 0.5, dc_y - 1.2, "DOUBLE CLUSTER (NGC 869 / 884)\n(Visible to Naked Eye in Bortle 4!)", fontsize=7.8, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2), zorder=15)

    # VIEWPORT B: TELESCOPE EYEPIECE SIMULATION
    fig.text(0.545, 0.898, "VIEWPORT B: EYEPIECE SIMULATION (Negative Inverted 180°: N ↓, E →)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_eye = fig.add_axes([0.58, 0.485, 0.35, 0.395])
    ax_eye.set_facecolor('white')
    fov_deg = 0.83
    ax_eye.set_xlim(-fov_deg/2 - 0.03, fov_deg/2 + 0.03)
    ax_eye.set_ylim(-fov_deg/2 - 0.04, fov_deg/2 + 0.03)
    ax_eye.set_aspect('equal')
    ax_eye.add_patch(Circle((0, 0), fov_deg/2, facecolor='#ffffff', edgecolor='#000000', linewidth=1.8, zorder=1))
    ax_eye.plot([0, 0], [-fov_deg/2, fov_deg/2], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)
    ax_eye.plot([-fov_deg/2, fov_deg/2], [0, 0], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)

    dc_field = load_field('double_cluster')
    for st in dc_field:
        dx = d_ra(st['ra'], dc_ra) * math.cos(math.radians(st['dec']))
        dy = st['dec'] - dc_dec
        dx_inv, dy_inv = -dx, -dy
        if math.hypot(dx_inv, dy_inv) < fov_deg/2 - 0.008:
            s_size = max(1.5, max(0.0, 12.5 - st['mag'])**2.2 * 0.9)
            ax_eye.plot(dx_inv, dy_inv, 'o', color='#000000', markersize=math.sqrt(s_size), alpha=0.95, zorder=10)

    c1_x, c1_y = 0.15, -0.05
    c2_x, c2_y = -0.15, 0.05
    ax_eye.add_patch(Circle((c1_x, c1_y), 0.16, facecolor='#f8fafc', edgecolor='#cbd5e1', linestyle=':', linewidth=0.8, zorder=11))
    ax_eye.add_patch(Circle((c2_x, c2_y), 0.16, facecolor='#f8fafc', edgecolor='#cbd5e1', linestyle=':', linewidth=0.8, zorder=11))

    np.random.seed(99)
    for cx, cy, n_c in [(c1_x, c1_y, 110), (c2_x, c2_y, 100)]:
        r_c = np.random.exponential(0.06, n_c)
        th_c = np.random.uniform(0, 2*np.pi, n_c)
        ax_eye.scatter(cx + r_c*np.cos(th_c), cy + r_c*np.sin(th_c), s=np.random.uniform(1.8, 9.0, n_c), color='#000000', alpha=0.9, zorder=13)

    for rx, ry in [(c2_x+0.02, c2_y+0.02), (c2_x-0.03, c2_y-0.01), (c2_x+0.01, c2_y-0.04)]:
        ax_eye.plot(rx, ry, 'o', color='#000000', markersize=4.5, zorder=15)
        ax_eye.plot(rx, ry, 'o', color='none', markeredgecolor='#000000', markeredgewidth=1.1, markersize=9.5, zorder=15)
    ax_eye.text(c2_x, c2_y-0.12, "Carbon Supergiants\n(Open Circles in NGC 884)", fontsize=7.0, color='#000000', ha='center', fontstyle='italic', zorder=25)

    ax_eye.text(c1_x, c1_y+0.12, "NGC 869", fontsize=7.8, color='#000000', fontweight='bold', ha='center', zorder=25)
    ax_eye.text(c2_x, c2_y+0.12, "NGC 884", fontsize=7.8, color='#000000', fontweight='bold', ha='center', zorder=25)

    ax_eye.text(0, -fov_deg/2 + 0.045, "↓ N (Inverted)", fontsize=7.5, color='#000000', fontweight='bold', ha='center', zorder=25)
    ax_eye.text(fov_deg/2 - 0.045, 0, "E →", fontsize=7.5, color='#000000', fontweight='bold', va='center', ha='right', zorder=25)
    ax_eye.text(0, -fov_deg/2 - 0.022, "20mm Eyepiece (60× Magnification, 50' True FOV)", fontsize=7.5, color='#000000', ha='center')
    ax_eye.axis('off')

    # VIEWPORT C: DOSSIER & INSTRUCTIONS
    fig.text(0.545, 0.448, "VIEWPORT C: TARGET DOSSIER & STAR-HOPPING INSTRUCTIONS", fontsize=8.2, fontweight='bold', color='#000000')
    ax_info = fig.add_axes([0.545, 0.045, 0.420, 0.390])
    ax_info.axis('off')
    dossier_text = (
        "OBJECT DOSSIER: NGC 869 & NGC 884 (CALDWELL 14)\n"
        "• Constellation: Perseus | Type: Twin Open Clusters\n"
        "• Magnitude: 3.7 / 3.8V | Apparent Size: 30' diameter each\n"
        "• Total Stars: ~600 stars | Distance: ~7,500 light-years\n"
        "• Tonight's Ephemeris at Dvigrad (Sep 12, 2026):\n"
        "    20:00 CEST: Alt 24.0°, Az 27° (Northeast)\n"
        "    21:15 CEST: Alt 31.6°, Az 39° (High & Gorgeous)\n"
        "    22:30 CEST: Alt 40.5°, Az 50° (Peak Clarity!)\n\n"
        "OBSERVING STRATEGY & EYEPIECES:\n"
        "• 20mm Eyepiece (60×): The ultimate showstopper eyepiece!\n"
        "  The 50' field of view frames both glittering jewel boxes\n"
        "  side by side in the same jaw-dropping field of view.\n"
        "• Color Contrast: Look for several radiant ruby-red / orange\n"
        "  carbon supergiant stars (marked by open circles) shining\n"
        "  brightly among the diamond blue-white stars in NGC 884.\n"
        "• 12.5mm Eyepiece (96×): Zoom in on each cluster's core.\n\n"
        "STEP-BY-STEP STAR HOP NARRATIVE:\n"
        "1. Naked-Eye: Locate the 'W' of Cassiopeia high in the NE.\n"
        "2. Draw a line from central star Navi (γ Cas) through Ruchbah\n"
        "   (δ Cas, bottom-left vertex of the 'W').\n"
        "3. Extend that line southeast by the same distance (~6°).\n"
        "4. An unmistakable glowing mist is visible naked-eye;\n"
        "   center Telrad or finder scope directly on it!"
    )
    ax_info.text(0.0, 0.98, dossier_text, fontsize=6.8, color='#000000', fontfamily='monospace', va='top',
                 bbox=dict(boxstyle='round,pad=0.45', facecolor='#ffffff', edgecolor='#000000', linewidth=1.1))

    # Exact A4 page export (NO bbox_inches='tight')
    plt.savefig(os.path.join(charts_dir, 'chart_5_perseus_double_cluster.png'), dpi=300, facecolor='white')
    plt.savefig(os.path.join(charts_dir, 'chart_5_perseus_double_cluster.pdf'), dpi=300, facecolor='white')
    plt.close()
    print("Chart 5 saved (A4 Landscape).")

def make_chart_6(charts_dir):
    print("Generating Chart 6: M11 & Saturn (A4 Landscape, Toner-Saver Negative)...")
    fig = plt.figure(figsize=A4_LANDSCAPE, facecolor='white', dpi=300)
    fig.text(0.035, 0.963, "STAR-HOPPING FINDER CHART 6: M11 (WILD DUCK CLUSTER) & SATURN — SCUTUM / AQUARIUS", fontsize=11.5, fontweight='bold', color='#000000')
    fig.text(0.035, 0.936, "Location: Dvigrad (Bortle 4, SQM 21.0) | Sep 12, 2026 • 21:15 CEST | Sky-Watcher 200P Dobsonian (8\" f/6, 1200mm FL) | B/W Toner-Saver Edition", fontsize=7.8, color='#333333')

    # VIEWPORT A
    fig.text(0.035, 0.898, "VIEWPORT A: WIDE-FIELD STAR-HOPPING CHART (Upright Naked-Eye / Finder: N ↑, E ←)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_wide = fig.add_axes([0.035, 0.045, 0.485, 0.835])
    c_ra, c_dec = 288.0, 2.0
    setup_wide_field(ax_wide, c_ra, c_dec, 24.0, 24.0)

    key_stars = [
        (297.70, 8.87, 'Altair (α Aql)\nmag 0.77', 0.4, -0.6, 8.5, 'bold'),
        (286.55, -4.88, 'λ Aql (Spine Base)\nmag 3.43', -0.8, 0.4, 7.8, 'bold'),
        (280.93, -4.75, 'β Sct\nmag 4.22', -0.4, 0.4, 7.2, 'normal'),
        (281.29, -8.24, 'α Sct\nmag 3.85', -0.4, -0.6, 7.2, 'normal')
    ]
    for s_ra, s_dec, lbl, ox, oy, fsz, fweight in key_stars:
        x = d_ra(s_ra, c_ra) * math.cos(math.radians(s_dec))
        y = s_dec - c_dec
        ax_wide.text(x+ox, y+oy, lbl, fontsize=fsz, fontweight=fweight, color='#000000', zorder=10)

    alt_x = d_ra(297.70, c_ra) * math.cos(math.radians(8.87))
    alt_y = 8.87 - c_dec
    lam_x = d_ra(286.55, c_ra) * math.cos(math.radians(-4.88))
    lam_y = -4.88 - c_dec

    m11_ra, m11_dec = 282.775, -6.267
    m11_x = d_ra(m11_ra, c_ra) * math.cos(math.radians(m11_dec))
    m11_y = m11_dec - c_dec

    arrow1 = FancyArrowPatch((alt_x, alt_y), (lam_x, lam_y), arrowstyle='->', mutation_scale=12, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax_wide.add_patch(arrow1)
    ax_wide.text((alt_x+lam_x)/2 + 0.6, (alt_y+lam_y)/2, "[STEP 1] Follow Aquila spine\n14° South to λ Aql", fontsize=7.2, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=10)

    arrow2 = FancyArrowPatch((lam_x, lam_y), (m11_x, m11_y), arrowstyle='->', mutation_scale=13, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax_wide.add_patch(arrow2)
    ax_wide.text((lam_x+m11_x)/2 + 0.2, (lam_y+m11_y)/2 + 1.1, "[STEP 2] Slew 4.5° WSW\ninto Scutum Star Cloud", fontsize=7.2, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=10)

    draw_telrad_reticle(ax_wide, m11_x, m11_y, (2.0, -1.8))
    draw_target_marker(ax_wide, m11_x, m11_y)
    ax_wide.text(m11_x - 0.5, m11_y - 1.2, "M11 WILD DUCK CLUSTER", fontsize=7.8, fontweight='bold', color='#000000',
                 bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2), zorder=15)

    # VIEWPORT B: TWO INSETS (M11 + SATURN)
    fig.text(0.545, 0.898, "VIEWPORT B: TELESCOPE SIMULATIONS (Negative Inverted 180°: N ↓, E →)", fontsize=8.2, fontweight='bold', color='#000000')

    # Inset B1: M11
    ax_eye1 = fig.add_axes([0.550, 0.495, 0.185, 0.380])
    ax_eye1.set_facecolor('white')
    fov_deg = 0.52
    ax_eye1.set_xlim(-fov_deg/2 - 0.015, fov_deg/2 + 0.015)
    ax_eye1.set_ylim(-fov_deg/2 - 0.030, fov_deg/2 + 0.025)
    ax_eye1.set_aspect('equal')
    ax_eye1.add_patch(Circle((0, 0), fov_deg/2, facecolor='#ffffff', edgecolor='#000000', linewidth=1.6, zorder=1))
    ax_eye1.plot([0, 0], [-fov_deg/2, fov_deg/2], color='#e2e8f0', linestyle=':', linewidth=0.7, zorder=2)
    ax_eye1.plot([-fov_deg/2, fov_deg/2], [0, 0], color='#e2e8f0', linestyle=':', linewidth=0.7, zorder=2)

    m11_field = load_field('m11')
    for st in m11_field:
        dx = d_ra(st['ra'], m11_ra) * math.cos(math.radians(st['dec']))
        dy = st['dec'] - m11_dec
        dx_inv, dy_inv = -dx, -dy
        if math.hypot(dx_inv, dy_inv) < fov_deg/2 - 0.005:
            s_size = max(1.5, max(0.0, 12.5 - st['mag'])**2.2 * 0.9)
            ax_eye1.plot(dx_inv, dy_inv, 'o', color='#000000', markersize=math.sqrt(s_size), alpha=0.95, zorder=10)

    ax_eye1.add_patch(Circle((0, 0), 0.11, facecolor='#f8fafc', edgecolor='#cbd5e1', linestyle=':', linewidth=0.8, zorder=11))
    np.random.seed(77)
    n_m11 = 130
    r_m11 = np.random.exponential(0.04, n_m11)
    th_m11 = np.random.uniform(np.pi/4, 5*np.pi/4, n_m11)
    ax_eye1.scatter(r_m11*np.cos(th_m11), r_m11*np.sin(th_m11), s=np.random.uniform(1.5, 7.0, n_m11), color='#000000', alpha=0.9, zorder=13)
    ax_eye1.plot(0.015, -0.01, 'o', color='#000000', markersize=4.5, zorder=16)
    ax_eye1.plot(0.015, -0.01, 'o', color='none', markeredgecolor='#000000', markeredgewidth=1.0, markersize=9.0, zorder=16)

    ax_eye1.text(0, fov_deg/2 + 0.020, "B1: M11 (12.5mm / 96×)", fontsize=7.5, fontweight='bold', color='#000000', ha='center')
    ax_eye1.text(0, -fov_deg/2 - 0.022, "Inverted 180° View", fontsize=6.8, color='#333333', ha='center')
    ax_eye1.axis('off')

    # Inset B2: Saturn
    ax_eye2 = fig.add_axes([0.765, 0.495, 0.185, 0.380])
    ax_eye2.set_facecolor('white')
    ax_eye2.set_xlim(-0.065, 0.065); ax_eye2.set_ylim(-0.075, 0.075); ax_eye2.set_aspect('equal')
    ax_eye2.add_patch(Circle((0, 0), 0.06, facecolor='#ffffff', edgecolor='#000000', linewidth=1.6, zorder=1))

    ax_eye2.add_patch(Circle((0, 0), 0.014, facecolor='#f8fafc', edgecolor='#000000', linewidth=1.1, zorder=12))
    ax_eye2.plot([-0.013, 0.013], [-0.002, -0.002], color='#475569', linewidth=1.0, alpha=0.8, zorder=13)
    ax_eye2.add_patch(Ellipse((0, 0), 0.065, 0.006, angle=-12, facecolor='#ffffff', edgecolor='#000000', linewidth=1.1, zorder=14))
    ax_eye2.plot(0.042, 0.018, 'o', color='#000000', markersize=3.5, zorder=15)
    ax_eye2.text(0.042, 0.024, "Titan (mag 8.5)", fontsize=6.8, color='#000000', fontweight='bold', ha='center', zorder=20)

    ax_eye2.text(0, 0.065, "B2: SATURN (12.5mm / 96×)", fontsize=7.5, fontweight='bold', color='#000000', ha='center')
    ax_eye2.text(0, -0.072, "Shallow Rings & Titan", fontsize=6.8, color='#333333', ha='center')
    ax_eye2.axis('off')

    # VIEWPORT C: DOSSIER & INSTRUCTIONS
    fig.text(0.545, 0.448, "VIEWPORT C: TARGET DOSSIER & STAR-HOPPING INSTRUCTIONS", fontsize=8.2, fontweight='bold', color='#000000')
    ax_info = fig.add_axes([0.545, 0.045, 0.420, 0.390])
    ax_info.axis('off')
    dossier_text = (
        "OBJECT DOSSIER: M11 & SATURN\n"
        "• M11 Wild Duck: Constellation Scutum | Open Cluster\n"
        "  - Magnitude: 5.8V | Size: 14' | Distance: 6,200 ly\n"
        "  - Stars: ~2,900 stars (one of the richest known!)\n"
        "  - Ephemeris: 20:00 Alt 38.2° | 21:15 Alt 37.7° | 22:30 Alt 32.0°\n"
        "• Saturn: The Ringed Planet in Aquarius/Pisces\n"
        "  - Magnitude: +0.6 | Apparent Disk: ~19\" (Rings: ~43\")\n"
        "  - Ring Tilt: Shallow (~2° edge-on profile in late 2026!)\n"
        "  - Rising Schedule at Dvigrad (East-Southeast):\n"
        "      20:20 CEST: Rises above horizon\n"
        "      21:40 CEST: Clears 15° tree line (Alt 15.2°)\n"
        "      22:30 CEST: Peak party altitude (Alt 22.8°, Az 111°)\n\n"
        "OBSERVING STRATEGY & EYEPIECES:\n"
        "• M11 (12.5mm / 96×): Incredible! Resolves a dazzling swarm\n"
        "  resembling a flight of wild ducks in V-formation, anchored\n"
        "  by a 8th-magnitude star near the apex.\n"
        "• Saturn (12.5mm / 96×): Grand finale of the night (observe\n"
        "  from 21:45 to 22:30)! The knife-edge rings, sharp shadow on the\n"
        "  globe, and radiant orange moon Titan make a sublime view.\n\n"
        "STEP-BY-STEP STAR HOP NARRATIVE:\n"
        "1. M11: Locate Altair. Slew 14° South down Aquila's backbone to\n"
        "   λ Aquilae (mag 3.4). Slew 4.5° WSW into the Scutum cloud.\n"
        "2. Saturn: Look low in the ESE after 21:40 CEST. Identify the\n"
        "   brightest golden non-twinkling object below Pegasus!"
    )
    ax_info.text(0.0, 0.98, dossier_text, fontsize=6.8, color='#000000', fontfamily='monospace', va='top',
                 bbox=dict(boxstyle='round,pad=0.45', facecolor='#ffffff', edgecolor='#000000', linewidth=1.1))

    # Exact A4 page export (NO bbox_inches='tight')
    plt.savefig(os.path.join(charts_dir, 'chart_6_scutum_m11_and_saturn.png'), dpi=300, facecolor='white')
    plt.savefig(os.path.join(charts_dir, 'chart_6_scutum_m11_and_saturn.pdf'), dpi=300, facecolor='white')
    plt.close()
    print("Chart 6 saved (A4 Landscape).")

def generate_all_charts(output_dir=None):
    if output_dir is None:
        output_dir = os.path.join(REPO_ROOT, 'observations', 'dvigrad-2026-09-12')
    charts_dir = os.path.join(output_dir, 'charts')
    os.makedirs(charts_dir, exist_ok=True)

    make_full_sky_map(output_dir)
    make_chart_1(charts_dir)
    make_chart_2(charts_dir)
    make_chart_3(charts_dir)
    make_chart_4(charts_dir)
    make_chart_5(charts_dir)
    make_chart_6(charts_dir)
    print(f"ALL CHARTS GENERATED SUCCESSFULLY into: {output_dir}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Stargazing Charts')
    parser.add_argument('--output-dir', type=str, default=None, help='Output directory for charts')
    args = parser.parse_args()
    generate_all_charts(args.output_dir)

#!/usr/bin/env python3
"""
scripts/generate_charts.py - Generates All-Sky Planisphere & Finder Charts
for observation sessions:
1. Standard A4 Printable Edition (for PDF/PNG printing):
   - All-Sky Planisphere: Standard A4 Portrait (210 x 297 mm / 595.3 x 841.9 pt)
   - Star-Hopping Finder Charts (1 to 6): Standard A4 Landscape (297 x 210 mm / 841.9 x 595.3 pt)
2. E-Reader Screen-Optimized Edition (for PocketBook Era & E-Ink Devices):
   - Dedicated Viewport A: Full-screen Wide-Field Star Chart (3:4 portrait aspect ratio, 1264x1680)
   - Dedicated Viewport B + C: Side-by-side Eyepiece Simulation & Target Dossier (4:3 aspect ratio)
   - Deeper star catalog density (up to mag 10.3, telescope limit - 3)
   - Star dot size vs magnitude key/legend in corner
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
from matplotlib.patches import Circle, Ellipse, Polygon, Wedge, FancyArrowPatch, Rectangle
import numpy as np

from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy.time import Time
import astropy.units as u

CACHE_DIR = os.path.join(REPO_ROOT, '.cache')

# Exact standard A4 dimensions in inches (1 inch = 25.4 mm = 72 pt)
A4_LANDSCAPE = (297.0 / 25.4, 210.0 / 25.4)  # 11.6929" x 8.2677" -> 841.89 pt x 595.28 pt
A4_PORTRAIT  = (210.0 / 25.4, 297.0 / 25.4)  # 8.2677" x 11.6929" -> 595.28 pt x 841.89 pt

# PocketBook Era (PB700) screen resolution: 1264 x 1680 (3:4 aspect ratio, 300 ppi)
# Dedicated image dimensions optimized for screen rendering and pinch-to-zoom:
ERA_PORTRAIT_FIGSIZE = (7.5, 10.0)   # 3:4 portrait (1500 x 2000 px @ 200 dpi)
ERA_SIDEBYSIDE_FIGSIZE = (10.0, 7.5) # 4:3 landscape (2000 x 1500 px @ 200 dpi)

# Global datasets - load stars.14.json with fallback
stars_file = os.path.join(CACHE_DIR, 'stars.14.json')
if not os.path.exists(stars_file):
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
    diff = (ra1 - ra2 + 180.0) % 360.0 - 180.0
    return diff

def load_field(name):
    path = os.path.join(CACHE_DIR, 'fields', f'{name}.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []

def star_mag_to_size(mag, max_mag=8.5):
    """Calculates star markersize in points based on visual magnitude up to max_mag."""
    if mag > max_mag:
        return None
    return max(0.8, round((max_mag + 0.2 - mag)**1.7 * 0.14 + 0.7, 2))

def draw_magnitude_legend(ax, loc='lower left', max_mag=8.5):
    """Draws a crisp magnitude legend box (star dot size to magnitude) in the corner of Viewport A."""
    if loc == 'lower left':
        x0, y0 = 0.035, 0.035
    else:
        x0, y0 = 0.585, 0.035
    w, h = 0.38, 0.072
    rect = Rectangle((x0, y0), w, h, transform=ax.transAxes, facecolor='#ffffff', edgecolor='#000000', linewidth=0.8, zorder=20)
    ax.add_patch(rect)
    ax.text(x0 + w/2, y0 + h - 0.015, f'MAGNITUDE KEY (Faintest Stars: {max_mag:.1f} mag)',
            transform=ax.transAxes, fontsize=5.8, fontweight='bold', ha='center', va='top', zorder=21)
    
    mags = [1, 3, 5, 7, 8.5]
    dx = (w - 0.04) / (len(mags) - 1)
    dot_y = y0 + 0.024
    lbl_y = y0 + 0.007
    for i, m in enumerate(mags):
        dot_x = x0 + 0.02 + i * dx
        ms = star_mag_to_size(m, max_mag)
        ax.plot(dot_x, dot_y, 'o', color='#000000', markersize=ms, transform=ax.transAxes, zorder=22)
        lbl_str = f"{m:g}"
        ax.text(dot_x, lbl_y, lbl_str, transform=ax.transAxes, fontsize=5.8, color='#333333', ha='center', va='bottom', zorder=22)

def setup_wide_field(ax, c_ra, c_dec, span_ra, span_dec, max_mag=8.5, show_legend=True, legend_loc='lower left'):
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

    # Stars - solid black dots, scaled by visual magnitude up to max_mag (8.5 mag limit)
    for f in stars_data['features']:
        ra = norm_ra(f['geometry']['coordinates'][0])
        dec = f['geometry']['coordinates'][1]
        mag = f['properties']['mag']
        if mag > max_mag:
            continue
        dra = d_ra(ra, c_ra)
        if abs(dra) < span_ra and abs(dec - c_dec) < span_dec:
            x = dra * math.cos(math.radians(dec))
            y = dec - c_dec
            ms = star_mag_to_size(mag, max_mag)
            ax.plot(x, y, 'o', color='#000000', markersize=ms, zorder=5)

    # Orientation Box in top-left corner
    ax.text(0.035, 0.955, "N ↑\\n← E", transform=ax.transAxes, fontsize=8.5, fontweight='bold', color='#000000',
            va='top', ha='left', bbox=dict(boxstyle='square,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=20)
    
    # Magnitude Legend in bottom corner
    if show_legend:
        draw_magnitude_legend(ax, loc=legend_loc, max_mag=max_mag)

    # Outer frame
    for spine in ax.spines.values():
        spine.set_color('#000000')
        spine.set_linewidth(1.1)
    ax.set_xticks([]); ax.set_yticks([])
    return x_min, x_max, y_min, y_max

def setup_context_field(ax, c_ra, c_dec, span_ra, span_dec,
                        vp_c_ra, vp_c_dec, vp_span_ra, vp_span_dec,
                        constel_labels, star_labels=None, target_coords=None,
                        extra_fn=None):
    """Sets up a zoomed-out regional constellation context chart showing naked-eye stars,
    neighboring constellation outlines, and a dashed box marking the next-page finder viewport.
    """
    ax.set_facecolor('#ffffff')
    cos_dec = math.cos(math.radians(c_dec))
    x_min, x_max = -(span_ra / 2.0) * cos_dec, (span_ra / 2.0) * cos_dec
    y_min, y_max = -(span_dec / 2.0), (span_dec / 2.0)
    ax.set_xlim(x_max, x_min)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect('equal')

    # 1. Constellation lines - high contrast dark charcoal
    for feat in lines_data['features']:
        for seg in feat['geometry']['coordinates']:
            for i in range(len(seg)-1):
                p1, p2 = seg[i], seg[i+1]
                ra1, dec1 = norm_ra(p1[0]), p1[1]
                ra2, dec2 = norm_ra(p2[0]), p2[1]
                dra1, dra2 = d_ra(ra1, c_ra), d_ra(ra2, c_ra)
                if abs(dra1 - dra2) < 35.0 and abs(dra1) < span_ra*0.75 and abs(dec1 - c_dec) < span_dec*0.75 and \
                   abs(dra2) < span_ra*0.75 and abs(dec2 - c_dec) < span_dec*0.75:
                    x1 = dra1 * math.cos(math.radians(dec1))
                    y1 = dec1 - c_dec
                    x2 = dra2 * math.cos(math.radians(dec2))
                    y2 = dec2 - c_dec
                    ax.plot([x1, x2], [y1, y2], color='#475569', linewidth=1.1, linestyle='-', alpha=0.85, zorder=2)

    # 2. Naked-eye stars (mag <= 6.2)
    max_mag = 6.2
    for f in stars_data['features']:
        mag = f['properties']['mag']
        if mag > max_mag:
            continue
        ra = norm_ra(f['geometry']['coordinates'][0])
        dec = f['geometry']['coordinates'][1]
        dra = d_ra(ra, c_ra)
        if abs(dra) < span_ra*0.65 and abs(dec - c_dec) < span_dec*0.65:
            x = dra * math.cos(math.radians(dec))
            y = dec - c_dec
            ms = max(1.0, round((max_mag + 0.5 - mag)**1.8 * 0.45 + 0.8, 2))
            ax.plot(x, y, 'o', color='#000000', markersize=ms, zorder=5)

    # 3. Viewport Boundary Box
    ra_left = vp_c_ra + vp_span_ra / 2.0
    ra_right = vp_c_ra - vp_span_ra / 2.0
    dec_bot = vp_c_dec - vp_span_dec / 2.0
    dec_top = vp_c_dec + vp_span_dec / 2.0

    corners = [
        (ra_left, dec_bot),
        (ra_right, dec_bot),
        (ra_right, dec_top),
        (ra_left, dec_top)
    ]
    corners_xy = []
    for r, d in corners:
        x_pt = d_ra(r, c_ra) * math.cos(math.radians(d))
        y_pt = d - c_dec
        corners_xy.append((x_pt, y_pt))

    vp_poly = Polygon(corners_xy, closed=True, facecolor='#f8fafc', edgecolor='#000000',
                      linestyle='--', linewidth=1.8, alpha=0.4, zorder=6)
    ax.add_patch(vp_poly)
    bx = [pt[0] for pt in corners_xy] + [corners_xy[0][0]]
    by = [pt[1] for pt in corners_xy] + [corners_xy[0][1]]
    ax.plot(bx, by, color='#000000', linestyle='--', linewidth=1.8, zorder=7)

    # Badge for Viewport
    center_x = d_ra(vp_c_ra, c_ra) * math.cos(math.radians(vp_c_dec))
    max_y = max(pt[1] for pt in corners_xy)
    badge_y = max_y + 1.2 if (max_y + 2.0) < y_max else max_y - 1.5
    ax.text(center_x, badge_y, "[NEXT PAGE FINDER VIEWPORT]", fontsize=7.8, fontweight='bold',
            color='#000000', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#000000', linewidth=1.1),
            zorder=20)

    # 4. Target marker(s)
    if target_coords:
        for t_name, t_ra, t_dec, ox, oy in target_coords:
            tx = d_ra(t_ra, c_ra) * math.cos(math.radians(t_dec))
            ty = t_dec - c_dec
            draw_target_marker(ax, tx, ty)
            ax.text(tx + ox, ty + oy, f"Target: {t_name}", fontsize=7.6, fontweight='bold', color='#000000',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9),
                    zorder=22)

    # 5. Constellation Labels
    for c_name, c_ra_lbl, c_dec_lbl in constel_labels:
        dra = d_ra(c_ra_lbl, c_ra)
        x = dra * math.cos(math.radians(c_dec_lbl))
        y = c_dec_lbl - c_dec
        ax.text(x, y, c_name.upper(), fontsize=9.0, fontweight='bold', color='#0f172a',
                ha='center', va='center',
                bbox=dict(boxstyle='square,pad=0.22', facecolor='#ffffff', edgecolor='#94a3b8', linewidth=0.8, alpha=0.9),
                zorder=12)

    # 6. Star Labels
    if star_labels:
        for s_name, s_ra, s_dec, ox, oy, fsz, fweight in star_labels:
            dra = d_ra(s_ra, c_ra)
            x = dra * math.cos(math.radians(s_dec))
            y = s_dec - c_dec
            ax.text(x + ox, y + oy, s_name, fontsize=fsz, fontweight=fweight, color='#000000',
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='#ffffff', edgecolor='none', alpha=0.8),
                    zorder=14)

    # 7. Extra annotations
    if extra_fn:
        extra_fn(ax)

    # 8. Orientation Box (N ↑, ← E)
    ax.text(0.035, 0.955, "N ↑\\n← E", transform=ax.transAxes, fontsize=8.5, fontweight='bold', color='#000000',
            va='top', ha='left', bbox=dict(boxstyle='square,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=25)

    # 9. Naked-Eye Magnitude Note
    ax.text(0.965, 0.035, "Naked-Eye Stars to Mag 6.2\\nBortle 4 Dvigrad Threshold", transform=ax.transAxes,
            fontsize=6.8, color='#333333', ha='right', va='bottom',
            bbox=dict(boxstyle='square,pad=0.25', facecolor='#ffffff', edgecolor='#666666', linewidth=0.8), zorder=25)

    for spine in ax.spines.values():
        spine.set_color('#000000')
        spine.set_linewidth(1.1)
    ax.set_xticks([])
    ax.set_yticks([])

def draw_telrad_reticle(ax, cx, cy, label_pos=(2.1, 1.8)):
    """Draws standardized B/W Telrad & 5-deg Optical Finder rings."""
    ax.add_patch(Circle((cx, cy), 0.25, facecolor='none', edgecolor='#000000', linestyle='-', linewidth=1.1, zorder=8))
    ax.add_patch(Circle((cx, cy), 1.0, facecolor='none', edgecolor='#000000', linestyle='--', linewidth=0.9, zorder=8))
    ax.add_patch(Circle((cx, cy), 2.0, facecolor='none', edgecolor='#000000', linestyle='-.', linewidth=0.8, zorder=8))
    ax.add_patch(Circle((cx, cy), 2.5, facecolor='none', edgecolor='#333333', linestyle=':', linewidth=1.0, zorder=7))
    
    lx, ly = label_pos
    ax.text(cx + lx, cy + ly, "5° Finder / Telrad FOV", fontsize=7.2, color='#000000', fontweight='bold',
            bbox=dict(boxstyle='square,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=10)

def draw_target_marker(ax, tx, ty):
    """Draws a crisp B/W bullseye target marker with crosshair tick marks."""
    ax.plot(tx, ty, 'o', color='#000000', markersize=3.8, zorder=12)
    ax.plot(tx, ty, 'o', color='none', markeredgecolor='#000000', markeredgewidth=1.1, markersize=8.0, zorder=12)
    ax.plot([tx-0.3, tx+0.3], [ty, ty], color='#000000', linewidth=0.9, zorder=12)
    ax.plot([tx, tx], [ty-0.3, ty+0.3], color='#000000', linewidth=0.9, zorder=12)

def make_full_sky_map(output_dir, export_pdf=False):
    """Generates an all-sky planisphere formatted strictly to standard A4 Portrait."""
    print("Generating Full Sky Map (A4 Portrait, B/W Toner-Saver)...")
    fig = plt.figure(figsize=A4_PORTRAIT, facecolor='white', dpi=300)
    ax = fig.add_axes([0.065, 0.080, 0.870, 0.835])
    ax.set_facecolor('white')

    def project(alt, az):
        r = (90.0 - alt) / 90.0
        theta = np.radians(az + 90.0)
        return -r * np.cos(theta), r * np.sin(theta)

    # Stars
    ra_vals = [norm_ra(f['geometry']['coordinates'][0]) for f in stars_data['features']]
    dec_vals = [f['geometry']['coordinates'][1] for f in stars_data['features']]
    mags = [f['properties']['mag'] for f in stars_data['features']]

    sc_stars = SkyCoord(ra=ra_vals*u.deg, dec=dec_vals*u.deg)
    altaz_stars = sc_stars.transform_to(altaz_frame)

    alt_deg = altaz_stars.alt.deg
    az_deg  = altaz_stars.az.deg
    mask_visible = alt_deg > 0

    xs, ys = project(alt_deg[mask_visible], az_deg[mask_visible])
    m_vis = np.array(mags)[mask_visible]

    for x, y, mag in zip(xs, ys, m_vis):
        if mag <= 6.2:
            s_val = max(1.0, (6.2 - mag)**2.1 * 1.8)
            ax.plot(x, y, 'o', color='#000000', markersize=math.sqrt(s_val), zorder=5)

    # Constellation Lines
    for feat in lines_data['features']:
        for seg in feat['geometry']['coordinates']:
            coords = []
            for p in seg:
                sc = SkyCoord(ra=norm_ra(p[0])*u.deg, dec=p[1]*u.deg)
                aa = sc.transform_to(altaz_frame)
                coords.append((aa.alt.deg, aa.az.deg))
            for i in range(len(coords)-1):
                alt1, az1 = coords[i]
                alt2, az2 = coords[i+1]
                if alt1 > 0 and alt2 > 0:
                    x1, y1 = project(alt1, az1)
                    x2, y2 = project(alt2, az2)
                    ax.plot([x1, x2], [y1, y2], color='#475569', linewidth=0.75, linestyle='-', alpha=0.85, zorder=3)

    # Horizon rings
    ax.add_patch(Circle((0, 0), 1.0, facecolor='#ffffff', edgecolor='#000000', linewidth=1.8, fill=False, zorder=8))
    r_obs = (90.0 - 15.0) / 90.0
    ax.add_patch(Circle((0, 0), r_obs, facecolor='none', edgecolor='#000000', linewidth=1.1, linestyle='--', zorder=8))
    ax.text(0, r_obs + 0.022, "15° Valley Obstruction Limit", fontsize=6.8, color='#333333', ha='center', zorder=10)

    for alt in [30, 60]:
        r = (90.0 - alt) / 90.0
        ax.add_patch(Circle((0, 0), r, facecolor='none', edgecolor='#cbd5e1', linewidth=0.6, linestyle=':', zorder=2))
        ax.text(0, r + 0.015, f"{alt}°", fontsize=6.5, color='#64748b', ha='center', zorder=10)

    # Zenith Cross
    ax.plot([-0.03, 0.03], [0, 0], color='#000000', linewidth=1.2, zorder=10)
    ax.plot([0, 0], [-0.03, 0.03], color='#000000', linewidth=1.2, zorder=10)
    ax.text(0.04, 0.04, "ZENITH", fontsize=7.5, fontweight='bold', color='#000000', zorder=10)

    # Compass Directions
    r_lbl = 1.055
    ax.text(0, r_lbl, "NORTH", fontsize=10.0, fontweight='bold', color='#000000', ha='center', va='bottom', zorder=12)
    ax.text(0, -r_lbl, "SOUTH", fontsize=10.0, fontweight='bold', color='#000000', ha='center', va='top', zorder=12)
    ax.text(-r_lbl, 0, "EAST", fontsize=10.0, fontweight='bold', color='#000000', ha='right', va='center', zorder=12)
    ax.text(r_lbl, 0, "WEST", fontsize=10.0, fontweight='bold', color='#000000', ha='left', va='center', zorder=12)

    # Target Markers
    targets_allsky = [
        ('Vega', 279.23, 38.78, 0.03, 0.03),
        ('Deneb', 310.36, 45.28, 0.03, 0.03),
        ('Altair', 297.70, 8.87, 0.03, 0.03),
        ('M57 (Ring)', 283.40, 33.03, -0.02, -0.06),
        ('M27 (Dumbbell)', 299.90, 22.72, 0.03, 0.03),
        ('Albireo', 292.68, 27.96, -0.08, -0.02),
        ('M13 (Hercules)', 250.42, 36.46, -0.03, 0.04),
        ('M92', 258.28, 43.14, 0.03, 0.03),
        ('M31 (Andromeda)', 10.68, 41.27, 0.03, 0.03),
        ('Double Cluster', 35.15, 57.15, 0.03, 0.03),
        ('M11 (Wild Duck)', 282.78, -6.27, -0.02, -0.05),
        ('Saturn', 351.25, -4.85, 0.02, 0.02)
    ]
    for t_name, t_ra, t_dec, ox, oy in targets_allsky:
        sc = SkyCoord(ra=t_ra*u.deg, dec=t_dec*u.deg)
        aa = sc.transform_to(altaz_frame)
        if aa.alt.deg > 0:
            tx, ty = project(aa.alt.deg, aa.az.deg)
            draw_target_marker(ax, tx, ty)
            ax.text(tx + ox, ty + oy, f"{t_name}\\n({aa.alt.deg:.0f}° Alt)", fontsize=6.8, fontweight='bold', color='#000000',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=16)

    ax.set_xlim(-1.24, 1.24); ax.set_ylim(-1.24, 1.24); ax.axis('off')

    # Header
    fig.text(0.065, 0.958, "DVIGRAD ALL-SKY PLANISPHERE (OBSERVATION MAP)", fontsize=13.0, fontweight='bold', color='#000000')
    fig.text(0.065, 0.938, "Date: Sep 12, 2026 • 21:15 CEST | Location: Dvigrad Ruins (45.126° N, 13.813° E) | Bortle 4 | B/W Toner-Saver Print Edition", fontsize=7.8, color='#333333')

    # Footer Info Box
    fig.text(0.065, 0.045,
             "HOW TO USE: Hold chart overhead with North facing North. Outer dashed ring marks the 15° Dvigrad Draga valley tree/terrain obstruction.\\n"
             "MOON STATUS: Waxing crescent (3.1%) set at 19:38 CEST (below horizon). Genuine zero lunar pollution darkness for entire session.\\n"
             "TELESCOPE: Sky-Watcher Skyliner Classic 200P (203mm f/6 Dobsonian) | Eyepieces: 20mm Super (60×, 50' FOV), 12.5mm Plössl (96×, 31' FOV)",
             fontsize=7.2, color='#000000', bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', edgecolor='#000000', linewidth=1.0))

    # Exact A4 page export (NO bbox_inches='tight')
    plt.savefig(os.path.join(output_dir, 'full_sky_map.png'), dpi=300, facecolor='white')
    if export_pdf:
        plt.savefig(os.path.join(output_dir, 'full_sky_map.pdf'), dpi=300, facecolor='white')
    plt.close()
    print("Full Sky Map generated successfully (A4 Portrait).")



# ==============================================================================
# CHART 1: M57 RING NEBULA IN LYRA
# ==============================================================================

def draw_chart_1_widefield(ax):
    c_ra, c_dec = 283.0, 36.0
    setup_wide_field(ax, c_ra, c_dec, 18.0, 18.0, max_mag=8.5, show_legend=True, legend_loc='lower left')

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
        ax.text(x+ox, y+oy, lbl, fontsize=fsz, fontweight=fweight, color='#000000', zorder=10)

    m57_ra, m57_dec = 283.396, 33.029
    m57_x = d_ra(m57_ra, c_ra) * math.cos(math.radians(m57_dec))
    m57_y = m57_dec - c_dec
    v_x = d_ra(279.23, c_ra) * math.cos(math.radians(38.78))
    v_y = 38.78 - c_dec
    b_x = d_ra(285.14, c_ra) * math.cos(math.radians(33.36))
    b_y = 33.36 - c_dec
    g_x = d_ra(286.06, c_ra) * math.cos(math.radians(32.69))
    g_y = 32.69 - c_dec

    arrow1 = FancyArrowPatch((v_x, v_y), (b_x, b_y), arrowstyle='->', mutation_scale=13, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax.add_patch(arrow1)
    ax.text((v_x+b_x)/2 - 0.4, (v_y+b_y)/2 + 0.5, "[STEP 1] Trace Lyra 6° S\nfrom Vega to Sheliak (β)", fontsize=7.2, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=10)

    arrow2 = FancyArrowPatch((b_x, b_y), (g_x, g_y), arrowstyle='->', mutation_scale=12, color='#000000', linestyle=':', linewidth=1.4, zorder=6)
    ax.add_patch(arrow2)
    ax.text((b_x+g_x)/2 + 0.6, (b_y+g_y)/2 - 0.9, "[STEP 2] Center reticle\nbetween β & γ Lyrae", fontsize=7.2, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=10)

    draw_telrad_reticle(ax, m57_x, m57_y, (2.1, 1.8))
    draw_target_marker(ax, m57_x, m57_y)
    ax.text(m57_x - 0.5, m57_y - 1.2, "M57 RING NEBULA", fontsize=7.8, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2), zorder=15)

def draw_chart_1_eyepiece(ax):
    ax.set_facecolor('white')
    fov_deg = 0.52
    ax.set_xlim(-fov_deg/2 - 0.02, fov_deg/2 + 0.02)
    ax.set_ylim(-fov_deg/2 - 0.035, fov_deg/2 + 0.02)
    ax.set_aspect('equal')
    ax.add_patch(Circle((0, 0), fov_deg/2, facecolor='#ffffff', edgecolor='#000000', linewidth=1.8, zorder=1))
    ax.plot([0, 0], [-fov_deg/2, fov_deg/2], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)
    ax.plot([-fov_deg/2, fov_deg/2], [0, 0], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)

    m57_ra, m57_dec = 283.396, 33.029
    m57_field = load_field('m57')
    for st in m57_field:
        dx = d_ra(st['ra'], m57_ra) * math.cos(math.radians(st['dec']))
        dy = st['dec'] - m57_dec
        dx_inv, dy_inv = -dx, -dy
        if math.hypot(dx_inv, dy_inv) < fov_deg/2 - 0.005:
            s_size = max(1.5, max(0.0, 12.5 - st['mag'])**2.2 * 0.9)
            ax.plot(dx_inv, dy_inv, 'o', color='#000000', markersize=math.sqrt(s_size), alpha=0.95, zorder=10)

    ax.add_patch(Ellipse((0, 0), 0.040, 0.029, angle=60, facecolor='#cbd5e1', edgecolor='#334151', linewidth=1.2, zorder=11))
    ax.add_patch(Ellipse((0, 0), 0.022, 0.014, angle=60, facecolor='#ffffff', edgecolor='#475569', linewidth=0.8, zorder=12))
    ax.text(0.025, 0.025, "Smoke Ring\n(Hollow Core)", fontsize=7.0, color='#000000', fontweight='bold', zorder=20)

    ax.text(0, -fov_deg/2 + 0.035, "↓ N (Inverted)", fontsize=7.5, color='#000000', fontweight='bold', ha='center', zorder=25)
    ax.text(fov_deg/2 - 0.035, 0, "E →", fontsize=7.5, color='#000000', fontweight='bold', va='center', ha='right', zorder=25)
    ax.text(0, -fov_deg/2 - 0.022, "12.5mm Eyepiece (96× Magnification, 31' True FOV)", fontsize=7.5, color='#000000', ha='center')
    ax.axis('off')

def get_chart_1_dossier(include_hop=True):
    txt = (
        "OBJECT DOSSIER: M57 (NGC 6720)\n"
        "• Constellation: Lyra | Type: Planetary Nebula\n"
        "• Magnitude: 8.8V | Surface Brightness: 9.3 mag/arcmin²\n"
        "• Apparent Size: 1.4' × 1.0' | Distance: ~2,570 light-years\n"
        "• Tonight's Ephemeris at Dvigrad (Sep 12, 2026):\n"
        "    20:00 CEST: Alt 76.4°, Az 204° (South-Southwest)\n"
        "    21:15 CEST: Alt 75.4°, Az 218° (Zenith Sweet Spot!)\n"
        "    22:30 CEST: Alt 64.3°, Az 237° (Safe > 60° Alt)\n\n"
        "EYEPIECE QUICK REFERENCE & OBSERVING NOTES:\n"
        "• Acquisition (20mm / 60×): Tiny, intense smoky cheerio\n"
        "  disk floating unmistakably between faint field stars.\n"
        "• Resolution (12.5mm / 96×): Crisp oval donut torus\n"
        "  with dark hollow core. Averted vision sharpens the rim!\n"
        "• Filter: Under Dvigrad's Bortle 4 skies, radiant without filters."
    )
    if include_hop:
        txt += (
            "\n\nSTEP-BY-STEP STAR HOP NARRATIVE:\n"
            "1. Naked-Eye: Locate brilliant Vega (mag 0.0) near Zenith.\n"
            "2. Identify Lyra's parallelogram ~6° south of Vega. Find the\n"
            "   two base stars: Sheliak (β, mag 3.5) and Sulafat (γ, mag 3.2).\n"
            "3. Slew Telrad / Finder: Place central reticle between β and γ,\n"
            "   slightly closer to Sulafat (about 60% of the distance).\n"
            "4. Eyepiece: Look for the ghostly smoke-ring between two stars!"
        )
    return txt

def draw_chart_1_context(ax):
    constels = [
        ("Lyra", 281.5, 36.5),
        ("Cygnus", 305.0, 42.0),
        ("Hercules", 262.0, 34.0),
        ("Vulpecula", 298.0, 24.5),
        ("Draco", 274.0, 52.0)
    ]
    stars = [
        ("Vega (mag 0.03)", 279.23, 38.78, 0.6, 0.6, 8.5, 'bold'),
        ("Deneb (mag 1.25)", 310.36, 45.28, 0.6, 0.6, 8.0, 'bold'),
        ("Albireo", 292.68, 27.96, -0.6, -0.6, 7.5, 'normal'),
        ("Eltanin (γ Dra)", 269.15, 51.49, 0.6, 0.4, 7.5, 'normal')
    ]
    targets = [("M57 (Ring)", 283.396, 33.029, 0.5, -1.0)]
    setup_context_field(ax, 285.0, 36.0, 52.0, 48.0,
                        283.0, 36.0, 18.0, 18.0,
                        constels, stars, targets)

def make_chart_1(charts_dir, export_pdf=False):
    print("Generating Chart 1: M57 (A4 Landscape, Toner-Saver Negative)...")
    fig = plt.figure(figsize=A4_LANDSCAPE, facecolor='white', dpi=300)
    fig.text(0.035, 0.963, "STAR-HOPPING FINDER CHART 1: M57 (RING NEBULA) — LYRA", fontsize=12, fontweight='bold', color='#000000')
    fig.text(0.035, 0.936, "Location: Dvigrad (Bortle 4, SQM 21.0) | Sep 12, 2026 • 21:15 CEST | Sky-Watcher 200P Dobsonian (8-inch f/6, 1200mm FL) | B/W Toner-Saver Edition", fontsize=7.8, color='#333333')

    # VIEWPORT A
    fig.text(0.035, 0.898, "VIEWPORT A: WIDE-FIELD STAR-HOPPING CHART (Upright Naked-Eye / Finder: N ↑, E ←)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_wide = fig.add_axes([0.035, 0.045, 0.485, 0.835])
    draw_chart_1_widefield(ax_wide)

    # VIEWPORT B: TELESCOPE EYEPIECE SIMULATION
    fig.text(0.545, 0.898, "VIEWPORT B: EYEPIECE SIMULATION (Negative Inverted 180°: N ↓, E →)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_eye = fig.add_axes([0.58, 0.485, 0.35, 0.395])
    draw_chart_1_eyepiece(ax_eye)

    # VIEWPORT C: DOSSIER & INSTRUCTIONS
    fig.text(0.545, 0.448, "VIEWPORT C: TARGET DOSSIER & STAR-HOPPING INSTRUCTIONS", fontsize=8.2, fontweight='bold', color='#000000')
    ax_info = fig.add_axes([0.545, 0.045, 0.420, 0.390])
    ax_info.axis('off')
    ax_info.text(0.0, 0.98, get_chart_1_dossier(include_hop=True), fontsize=6.8, color='#000000', fontfamily='monospace', va='top',
                 bbox=dict(boxstyle='round,pad=0.45', facecolor='#ffffff', edgecolor='#000000', linewidth=1.1))

    plt.savefig(os.path.join(charts_dir, 'chart_1_lyra_m57.png'), dpi=300, facecolor='white')
    if export_pdf:
        plt.savefig(os.path.join(charts_dir, 'chart_1_lyra_m57.pdf'), dpi=300, facecolor='white')
    plt.close(fig)

    # PocketBook Era Screen-Optimized Assets
    fig_side = plt.figure(figsize=ERA_SIDEBYSIDE_FIGSIZE, facecolor='white', dpi=200)
    fig_side.text(0.05, 0.94, "M57 RING NEBULA — EYEPIECE SIMULATION & TARGET DOSSIER", fontsize=11, fontweight='bold', color='#000000')
    fig_side.text(0.05, 0.905, "Sky-Watcher 200P Dobsonian (12.5mm / 96×) | Negative Inverted 180° | Bortle 4", fontsize=8.2, color='#333333')
    ax_eye_side = fig_side.add_axes([0.05, 0.08, 0.42, 0.78])
    draw_chart_1_eyepiece(ax_eye_side)
    ax_info_side = fig_side.add_axes([0.51, 0.08, 0.44, 0.78])
    ax_info_side.axis('off')
    ax_info_side.text(0.0, 0.98, get_chart_1_dossier(include_hop=False), fontsize=8.2, color='#000000', fontfamily='monospace', va='top',
                      bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2))
    plt.savefig(os.path.join(charts_dir, 'chart_1_lyra_m57_eyepiece_dossier.png'), dpi=200, facecolor='white')
    plt.close(fig_side)

    # Screen 2: Constellation Context Orientation Chart
    fig_ctx = plt.figure(figsize=ERA_PORTRAIT_FIGSIZE, facecolor='white', dpi=200)
    fig_ctx.text(0.05, 0.965, "M57 RING NEBULA — CONSTELLATION CONTEXT & ORIENTATION", fontsize=11, fontweight='bold', color='#000000')
    fig_ctx.text(0.05, 0.942, "Naked-Eye Sky (N ↑, E ←) | Constellation Lines & Next-Page Finder Viewport", fontsize=7.8, color='#333333')
    ax_ctx = fig_ctx.add_axes([0.05, 0.04, 0.90, 0.88])
    draw_chart_1_context(ax_ctx)
    plt.savefig(os.path.join(charts_dir, 'chart_1_lyra_m57_context.png'), dpi=200, facecolor='white')
    plt.close(fig_ctx)

    # Screen 3: Zoomed-in Wide-Field Star-Hopping Chart
    fig_wide = plt.figure(figsize=ERA_PORTRAIT_FIGSIZE, facecolor='white', dpi=200)
    fig_wide.text(0.05, 0.965, "M57 RING NEBULA — WIDE-FIELD STAR-HOPPING CHART", fontsize=11, fontweight='bold', color='#000000')
    fig_wide.text(0.05, 0.942, "Upright Naked-Eye / Finder (N ↑, E ←) | Stars to Mag 8.5 | Telrad Reticle", fontsize=7.8, color='#333333')
    ax_wide_era = fig_wide.add_axes([0.05, 0.04, 0.90, 0.88])
    draw_chart_1_widefield(ax_wide_era)
    plt.savefig(os.path.join(charts_dir, 'chart_1_lyra_m57_widefield.png'), dpi=200, facecolor='white')
    plt.close(fig_wide)
    print("Chart 1 saved (A4 Landscape & PocketBook Era Screen-Optimized).")


# ==============================================================================
# CHART 2: M27 DUMBBELL NEBULA & ALBIREO
# ==============================================================================

def draw_chart_2_widefield(ax):
    c_ra, c_dec = 296.0, 24.0
    setup_wide_field(ax, c_ra, c_dec, 18.0, 18.0, max_mag=8.5, show_legend=True, legend_loc='lower left')

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
        ax.text(x+ox, y+oy, lbl, fontsize=fsz, fontweight=fweight, color='#000000', zorder=10)

    m27_ra, m27_dec = 299.901, 22.721
    m27_x = d_ra(m27_ra, c_ra) * math.cos(math.radians(m27_dec))
    m27_y = m27_dec - c_dec
    g_x = d_ra(299.70, c_ra) * math.cos(math.radians(19.49))
    g_y = 19.49 - c_dec

    arrow1 = FancyArrowPatch((g_x, g_y), (m27_x, m27_y), arrowstyle='->', mutation_scale=13, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax.add_patch(arrow1)
    ax.text((g_x+m27_x)/2 + 0.6, (g_y+m27_y)/2, "[STEP 1] Slew 3.2° North\nfrom γ Sagittae tip", fontsize=7.2, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=10)

    draw_telrad_reticle(ax, m27_x, m27_y, (2.1, 1.8))
    draw_target_marker(ax, m27_x, m27_y)
    ax.text(m27_x - 0.5, m27_y + 0.6, "M27 DUMBBELL NEBULA", fontsize=7.8, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2), zorder=15)

    alb_x = d_ra(292.68, c_ra) * math.cos(math.radians(27.96))
    alb_y = 27.96 - c_dec
    draw_target_marker(ax, alb_x, alb_y)
    ax.text(alb_x - 0.4, alb_y + 0.8, "BONUS TARGET: ALBIREO\n(Gold & Blue Double Star)", fontsize=7.5, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=15)

def draw_chart_2_eyepiece(ax):
    ax.set_facecolor('white')
    fov_deg = 0.83
    ax.set_xlim(-fov_deg/2 - 0.03, fov_deg/2 + 0.03)
    ax.set_ylim(-fov_deg/2 - 0.04, fov_deg/2 + 0.03)
    ax.set_aspect('equal')
    ax.add_patch(Circle((0, 0), fov_deg/2, facecolor='#ffffff', edgecolor='#000000', linewidth=1.8, zorder=1))
    ax.plot([0, 0], [-fov_deg/2, fov_deg/2], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)
    ax.plot([-fov_deg/2, fov_deg/2], [0, 0], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)

    m27_ra, m27_dec = 299.901, 22.721
    m27_field = load_field('m27')
    for st in m27_field:
        dx = d_ra(st['ra'], m27_ra) * math.cos(math.radians(st['dec']))
        dy = st['dec'] - m27_dec
        dx_inv, dy_inv = -dx, -dy
        if math.hypot(dx_inv, dy_inv) < fov_deg/2 - 0.008:
            s_size = max(1.5, max(0.0, 12.5 - st['mag'])**2.2 * 0.9)
            ax.plot(dx_inv, dy_inv, 'o', color='#000000', markersize=math.sqrt(s_size), alpha=0.95, zorder=10)

    ax.add_patch(Ellipse((0, 0), 0.14, 0.10, angle=25, facecolor='#f1f5f9', edgecolor='#94a3b8', linestyle='--', linewidth=0.8, zorder=10))
    ax.add_patch(Ellipse((-0.025, 0), 0.09, 0.12, angle=25, facecolor='#cbd5e1', edgecolor='#64748b', linestyle='--', linewidth=0.8, zorder=11))
    ax.add_patch(Ellipse(( 0.025, 0), 0.09, 0.12, angle=25, facecolor='#cbd5e1', edgecolor='#64748b', linestyle='--', linewidth=0.8, zorder=11))
    ax.add_patch(Ellipse((0, 0), 0.07, 0.09, angle=25, facecolor='#94a3b8', edgecolor='#334151', linewidth=1.1, zorder=12))
    ax.text(0.12, 0.12, "Hourglass / Apple Core\n(Bright Central Waist)", fontsize=7.0, color='#000000', fontweight='bold', zorder=20)

    ax.text(0, -fov_deg/2 + 0.045, "↓ N (Inverted)", fontsize=7.5, color='#000000', fontweight='bold', ha='center', zorder=25)
    ax.text(fov_deg/2 - 0.045, 0, "E →", fontsize=7.5, color='#000000', fontweight='bold', va='center', ha='right', zorder=25)
    ax.text(0, -fov_deg/2 - 0.022, "20mm Eyepiece (60× Magnification, 50' True FOV)", fontsize=7.5, color='#000000', ha='center')
    ax.axis('off')

def get_chart_2_dossier(include_hop=True):
    txt = (
        "OBJECT DOSSIER: M27 (NGC 6853) & ALBIREO\n"
        "• Constellation: Vulpecula / Cygnus | Type: Neb & Binary\n"
        "• M27: Mag 7.5V | Surface Brightness: 11.2 | Size: 8.0' × 5.6'\n"
        "• Albireo (β Cyg): Mag 3.1 / 5.1 (34.3\" sep) | Topaz & Sapphire pair\n"
        "• Tonight's Ephemeris at Dvigrad (Sep 12, 2026):\n"
        "    20:00 CEST: Alt 60.0°, Az 147° | 21:15 CEST: Alt 67.2° (Prime!)\n"
        "    22:30 CEST: Alt 65.3°, Az 189° (High & Pristine)\n\n"
        "EYEPIECE QUICK REFERENCE & OBSERVING NOTES:\n"
        "• Acquisition & Frame (20mm / 60×): Ethereal apple-core\n"
        "  dumbbell glow framed against dark starry space.\n"
        "• Detail & Outer Rims (12.5mm / 96×): Brighter outer lobes\n"
        "  and faint extensions connecting the two main halves.\n"
        "• Albireo (β Cyg): Radiant topaz gold & sapphire blue split!"
    )
    if include_hop:
        txt += (
            "\n\nSTEP-BY-STEP STAR HOP NARRATIVE:\n"
            "1. Naked-Eye: Locate Sagitta the Arrow between Altair\n"
            "   and Albireo. Identify tip star γ Sagittae (mag 3.5).\n"
            "2. Telrad Hop: Place γ Sagittae on the southern outer 4° ring;\n"
            "   the central reticle points directly at M27 (3.2° North).\n"
            "3. Eyepiece confirmation: A striking, bright ethereal\n"
            "   hourglass cloud appears instantly in the 20mm field!"
        )
    return txt

def draw_chart_2_context(ax):
    constels = [
        ("Vulpecula", 302.0, 25.5),
        ("Sagitta", 296.5, 17.5),
        ("Cygnus", 306.0, 41.0),
        ("Lyra", 281.0, 38.0),
        ("Delphinus", 309.0, 15.0),
        ("Aquila", 294.0, 4.5)
    ]
    stars = [
        ("Vega", 279.23, 38.78, 0.6, 0.6, 8.2, 'bold'),
        ("Deneb", 310.36, 45.28, 0.6, 0.6, 8.0, 'bold'),
        ("Altair", 297.70, 8.87, -0.6, 0.4, 8.2, 'bold'),
        ("Albireo (β Cyg)", 292.68, 27.96, -0.8, 0.4, 7.8, 'bold')
    ]
    targets = [
        ("M27 (Dumbbell)", 299.901, 22.721, 0.5, 0.8),
        ("Albireo", 292.68, 27.96, -0.5, -0.8)
    ]
    setup_context_field(ax, 298.0, 25.0, 54.0, 48.0,
                        296.0, 24.0, 18.0, 18.0,
                        constels, stars, targets)

def make_chart_2(charts_dir, export_pdf=False):
    print("Generating Chart 2: M27 & Albireo (A4 Landscape, Toner-Saver Negative)...")
    fig = plt.figure(figsize=A4_LANDSCAPE, facecolor='white', dpi=300)
    fig.text(0.035, 0.963, "STAR-HOPPING FINDER CHART 2: M27 (DUMBBELL NEBULA) & ALBIREO — VULPECULA / CYGNUS", fontsize=11.5, fontweight='bold', color='#000000')
    fig.text(0.035, 0.936, "Location: Dvigrad (Bortle 4, SQM 21.0) | Sep 12, 2026 • 21:15 CEST | Sky-Watcher 200P Dobsonian (8-inch f/6, 1200mm FL) | B/W Toner-Saver Edition", fontsize=7.8, color='#333333')

    # VIEWPORT A
    fig.text(0.035, 0.898, "VIEWPORT A: WIDE-FIELD STAR-HOPPING CHART (Upright Naked-Eye / Finder: N ↑, E ←)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_wide = fig.add_axes([0.035, 0.045, 0.485, 0.835])
    draw_chart_2_widefield(ax_wide)

    # VIEWPORT B: TELESCOPE EYEPIECE SIMULATION
    fig.text(0.545, 0.898, "VIEWPORT B: EYEPIECE SIMULATION (Negative Inverted 180°: N ↓, E →)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_eye = fig.add_axes([0.58, 0.485, 0.35, 0.395])
    draw_chart_2_eyepiece(ax_eye)

    # VIEWPORT C: DOSSIER & INSTRUCTIONS
    fig.text(0.545, 0.448, "VIEWPORT C: TARGET DOSSIER & STAR-HOPPING INSTRUCTIONS", fontsize=8.2, fontweight='bold', color='#000000')
    ax_info = fig.add_axes([0.545, 0.045, 0.420, 0.390])
    ax_info.axis('off')
    ax_info.text(0.0, 0.98, get_chart_2_dossier(include_hop=True), fontsize=6.8, color='#000000', fontfamily='monospace', va='top',
                 bbox=dict(boxstyle='round,pad=0.45', facecolor='#ffffff', edgecolor='#000000', linewidth=1.1))

    plt.savefig(os.path.join(charts_dir, 'chart_2_vulpecula_m27_albireo.png'), dpi=300, facecolor='white')
    if export_pdf:
        plt.savefig(os.path.join(charts_dir, 'chart_2_vulpecula_m27_albireo.pdf'), dpi=300, facecolor='white')
    plt.close(fig)

    # PocketBook Era Screen-Optimized Assets
    fig_side = plt.figure(figsize=ERA_SIDEBYSIDE_FIGSIZE, facecolor='white', dpi=200)
    fig_side.text(0.05, 0.94, "M27 DUMBBELL NEBULA & ALBIREO — EYEPIECE SIMULATION & DOSSIER", fontsize=11, fontweight='bold', color='#000000')
    fig_side.text(0.05, 0.905, "Sky-Watcher 200P Dobsonian (20mm / 60×) | Negative Inverted 180° | Bortle 4", fontsize=8.2, color='#333333')
    ax_eye_side = fig_side.add_axes([0.05, 0.08, 0.42, 0.78])
    draw_chart_2_eyepiece(ax_eye_side)
    ax_info_side = fig_side.add_axes([0.51, 0.08, 0.44, 0.78])
    ax_info_side.axis('off')
    ax_info_side.text(0.0, 0.98, get_chart_2_dossier(include_hop=False), fontsize=8.0, color='#000000', fontfamily='monospace', va='top',
                      bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2))
    plt.savefig(os.path.join(charts_dir, 'chart_2_vulpecula_m27_albireo_eyepiece_dossier.png'), dpi=200, facecolor='white')
    plt.close(fig_side)

    # Screen 2: Constellation Context Orientation Chart
    fig_ctx = plt.figure(figsize=ERA_PORTRAIT_FIGSIZE, facecolor='white', dpi=200)
    fig_ctx.text(0.05, 0.965, "M27 DUMBBELL & ALBIREO — CONSTELLATION CONTEXT & ORIENTATION", fontsize=11, fontweight='bold', color='#000000')
    fig_ctx.text(0.05, 0.942, "Naked-Eye Sky (N ↑, E ←) | Constellation Lines & Next-Page Finder Viewport", fontsize=7.8, color='#333333')
    ax_ctx = fig_ctx.add_axes([0.05, 0.04, 0.90, 0.88])
    draw_chart_2_context(ax_ctx)
    plt.savefig(os.path.join(charts_dir, 'chart_2_vulpecula_m27_albireo_context.png'), dpi=200, facecolor='white')
    plt.close(fig_ctx)

    # Screen 3: Zoomed-in Wide-Field Star-Hopping Chart
    fig_wide = plt.figure(figsize=ERA_PORTRAIT_FIGSIZE, facecolor='white', dpi=200)
    fig_wide.text(0.05, 0.965, "M27 & ALBIREO — WIDE-FIELD STAR-HOPPING CHART", fontsize=11, fontweight='bold', color='#000000')
    fig_wide.text(0.05, 0.942, "Upright Naked-Eye / Finder (N ↑, E ←) | Stars to Mag 8.5 | Telrad Reticle", fontsize=7.8, color='#333333')
    ax_wide_era = fig_wide.add_axes([0.05, 0.04, 0.90, 0.88])
    draw_chart_2_widefield(ax_wide_era)
    plt.savefig(os.path.join(charts_dir, 'chart_2_vulpecula_m27_albireo_widefield.png'), dpi=200, facecolor='white')
    plt.close(fig_wide)
    print("Chart 2 saved (A4 Landscape & PocketBook Era Screen-Optimized).")


# ==============================================================================
# CHART 3: HERCULES GLOBULARS M13 & M92
# ==============================================================================

def draw_chart_3_widefield(ax):
    c_ra, c_dec = 256.0, 38.0
    setup_wide_field(ax, c_ra, c_dec, 20.0, 20.0, max_mag=8.5, show_legend=True, legend_loc='lower left')

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
        ax.text(x+ox, y+oy, lbl, fontsize=fsz, fontweight=fweight, color='#000000', zorder=10)

    eta_x = d_ra(250.77, c_ra) * math.cos(math.radians(38.92))
    eta_y = 38.92 - c_dec
    zeta_x = d_ra(250.84, c_ra) * math.cos(math.radians(31.60))
    zeta_y = 31.60 - c_dec

    m13_ra, m13_dec = 250.422, 36.460
    m13_x = d_ra(m13_ra, c_ra) * math.cos(math.radians(m13_dec))
    m13_y = m13_dec - c_dec

    arrow1 = FancyArrowPatch((eta_x, eta_y), (m13_x, m13_y), arrowstyle='->', mutation_scale=13, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax.add_patch(arrow1)
    ax.text((eta_x+m13_x)/2 + 0.5, (eta_y+m13_y)/2 + 0.4, "[STEP 1] Move 2.5° South\nfrom η toward ζ Herculis", fontsize=7.2, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=10)

    pi_x = d_ra(257.65, c_ra) * math.cos(math.radians(36.81))
    pi_y = 36.81 - c_dec
    m92_ra, m92_dec = 259.280, 43.136
    m92_x = d_ra(m92_ra, c_ra) * math.cos(math.radians(m92_dec))
    m92_y = m92_dec - c_dec

    arrow2 = FancyArrowPatch((pi_x, pi_y), (m92_x, m92_y), arrowstyle='->', mutation_scale=12, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax.add_patch(arrow2)
    ax.text((pi_x+m92_x)/2 + 0.5, (pi_y+m92_y)/2 - 0.2, "[STEP 2] From π Herculis,\nhop 6.3° North to M92", fontsize=7.2, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=10)

    draw_telrad_reticle(ax, m13_x, m13_y, (2.1, 1.8))
    draw_target_marker(ax, m13_x, m13_y)
    ax.text(m13_x - 0.5, m13_y - 1.2, "M13 GREAT GLOBULAR\n(Hercules Cluster, Mag 5.8)", fontsize=7.8, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2), zorder=15)

    draw_target_marker(ax, m92_x, m92_y)
    ax.text(m92_x - 0.5, m92_y + 0.8, "M92 GLOBULAR (Mag 6.3)", fontsize=7.5, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=15)

def draw_chart_3_eyepiece(ax):
    ax.set_facecolor('white')
    fov_deg = 0.52
    ax.set_xlim(-fov_deg/2 - 0.015, fov_deg/2 + 0.015)
    ax.set_ylim(-fov_deg/2 - 0.025, fov_deg/2 + 0.020)
    ax.set_aspect('equal')
    ax.add_patch(Circle((0, 0), fov_deg/2, facecolor='#ffffff', edgecolor='#000000', linewidth=1.6, zorder=1))
    ax.plot([0, 0], [-fov_deg/2, fov_deg/2], color='#e2e8f0', linestyle=':', linewidth=0.7, zorder=2)
    ax.plot([-fov_deg/2, fov_deg/2], [0, 0], color='#e2e8f0', linestyle=':', linewidth=0.7, zorder=2)

    m13_ra, m13_dec = 250.422, 36.460
    m13_field = load_field('m13')
    for st in m13_field:
        dx = d_ra(st['ra'], m13_ra) * math.cos(math.radians(st['dec']))
        dy = st['dec'] - m13_dec
        dx_inv, dy_inv = -dx, -dy
        if math.hypot(dx_inv, dy_inv) < fov_deg/2 - 0.005:
            s_size = max(1.5, max(0.0, 12.5 - st['mag'])**2.2 * 0.9)
            ax.plot(dx_inv, dy_inv, 'o', color='#000000', markersize=math.sqrt(s_size), alpha=0.95, zorder=10)

    ax.add_patch(Circle((0, 0), 0.17, facecolor='#f8fafc', edgecolor='#cbd5e1', linestyle=':', linewidth=0.8, zorder=11))
    ax.add_patch(Circle((0, 0), 0.10, facecolor='#f1f5f9', edgecolor='#94a3b8', linestyle='--', linewidth=0.8, zorder=12))
    ax.add_patch(Circle((0, 0), 0.05, facecolor='#e2e8f0', edgecolor='#64748b', linewidth=1.0, zorder=13))

    np.random.seed(42)
    n_stars = 220
    r_stars = np.random.exponential(0.045, n_stars)
    th_stars = np.random.uniform(0, 2*np.pi, n_stars)
    x_stars = r_stars * np.cos(th_stars)
    y_stars = r_stars * np.sin(th_stars)
    ax.scatter(x_stars, y_stars, s=np.random.uniform(1.2, 5.5, n_stars), color='#000000', alpha=0.95, zorder=14)

    th_prop = [math.radians(35), math.radians(155), math.radians(275)]
    for th in th_prop:
        px = [0.015*math.cos(th), 0.075*math.cos(th)]
        py = [0.015*math.sin(th), 0.075*math.sin(th)]
        ax.plot(px, py, color='#ffffff', linewidth=2.5, zorder=15)
        ax.plot(px, py, color='#475569', linewidth=1.2, linestyle='--', alpha=0.9, zorder=16)
    ax.text(0.06, -0.09, "Propeller Dust Lane\n(3-Bladed Absorption)", fontsize=6.8, color='#000000', fontstyle='italic', zorder=25)

    ax.text(0, -fov_deg/2 + 0.025, "↓ N (Inverted)", fontsize=7.2, color='#000000', fontweight='bold', ha='center', zorder=20)
    ax.text(fov_deg/2 - 0.025, 0, "E →", fontsize=7.2, color='#000000', fontweight='bold', va='center', ha='right', zorder=20)
    ax.text(0, -fov_deg/2 - 0.016, "12.5mm Eyepiece (96× Magnification, 31' True FOV)", fontsize=7.2, color='#000000', ha='center')
    ax.axis('off')

def get_chart_3_dossier(include_hop=True):
    txt = (
        "OBJECT DOSSIER: M13 (NGC 6205) & M92 (NGC 6341)\n"
        "• Constellation: Hercules | Type: Globular Star Clusters\n"
        "• M13: Mag 5.8V | Diameter: 20' (~145 light-years across)\n"
        "• M92: Mag 6.3V | Diameter: 14' | Extremely ancient (~14 Gyr)\n"
        "• Distance: ~22,200 ly (M13) / ~26,700 ly (M92)\n"
        "• Tonight's Ephemeris at Dvigrad (Sep 12, 2026):\n"
        "    20:00 CEST: Alt 65.4°, Az 248° (West, Superb & Steady)\n"
        "    21:15 CEST: Alt 56.2°, Az 271° (Prime Contrast!)\n"
        "    22:30 CEST: Alt 44.1°, Az 287° (Crisp before sinking)\n\n"
        "EYEPIECE QUICK REFERENCE & OBSERVING NOTES:\n"
        "• High Resolution (12.5mm / 96×): Mandatory! Core resolves into\n"
        "  hundreds of glittering diamond points with spider-leg star chains.\n"
        "• Propeller Feature: Search SE quadrant for faint dark 3-bladed 'Y'.\n"
        "• M92 Bonus: Compact, intensely condensed nucleus; higher surface\n"
        "  brightness than M13."
    )
    if include_hop:
        txt += (
            "\n\nSTEP-BY-STEP STAR HOP NARRATIVE:\n"
            "1. Naked-Eye: Locate the Keystone trapezoid of Hercules.\n"
            "2. West edge: Identify η Her (NW corner) and ζ Her (SW corner).\n"
            "3. Hop: Move 2.5° South along the η-ζ line (1/3 the way down).\n"
            "4. M13 glows clearly in finder and 20mm eyepiece!\n"
            "5. Bonus M92: From π Her (NE corner), slew 6.3° due North."
        )
    return txt

def draw_chart_3_context(ax):
    constels = [
        ("Hercules", 255.0, 32.0),
        ("Corona Borealis", 235.0, 30.0),
        ("Lyra", 283.0, 37.0),
        ("Draco", 260.0, 56.0),
        ("Boötes", 222.0, 32.0),
        ("Ophiuchus", 258.0, 6.0)
    ]
    stars = [
        ("Vega", 279.23, 38.78, 0.6, 0.6, 8.2, 'bold'),
        ("Alphecca", 233.67, 26.71, -0.6, 0.4, 7.8, 'bold'),
        ("Rasalhague", 263.73, 12.56, -0.6, -0.6, 7.8, 'bold'),
        ("Kornephoros", 247.55, 21.49, -0.6, -0.6, 7.5, 'normal')
    ]
    targets = [
        ("M13 Keystone", 250.422, 36.460, -0.6, 0.8),
        ("M92 Globular", 259.280, 43.136, 0.6, 0.8)
    ]
    setup_context_field(ax, 252.0, 35.0, 60.0, 52.0,
                        256.0, 38.0, 20.0, 20.0,
                        constels, stars, targets)

def make_chart_3(charts_dir, export_pdf=False):
    print("Generating Chart 3: M13 & M92 (A4 Landscape, Toner-Saver Negative)...")
    fig = plt.figure(figsize=A4_LANDSCAPE, facecolor='white', dpi=300)
    fig.text(0.035, 0.963, "STAR-HOPPING FINDER CHART 3: M13 & M92 (HERCULES GLOBULARS) — HERCULES", fontsize=11.5, fontweight='bold', color='#000000')
    fig.text(0.035, 0.936, "Location: Dvigrad (Bortle 4, SQM 21.0) | Sep 12, 2026 • 21:15 CEST | Sky-Watcher 200P Dobsonian (8-inch f/6, 1200mm FL) | B/W Toner-Saver Edition", fontsize=7.8, color='#333333')

    # VIEWPORT A
    fig.text(0.035, 0.898, "VIEWPORT A: WIDE-FIELD STAR-HOPPING CHART (Upright Naked-Eye / Finder: N ↑, E ←)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_wide = fig.add_axes([0.035, 0.045, 0.485, 0.835])
    draw_chart_3_widefield(ax_wide)

    # VIEWPORT B: TELESCOPE EYEPIECE SIMULATION
    fig.text(0.545, 0.898, "VIEWPORT B: EYEPIECE SIMULATION (Negative Inverted 180°: N ↓, E →)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_eye = fig.add_axes([0.58, 0.485, 0.35, 0.395])
    draw_chart_3_eyepiece(ax_eye)

    # VIEWPORT C: DOSSIER & INSTRUCTIONS
    fig.text(0.545, 0.448, "VIEWPORT C: TARGET DOSSIER & STAR-HOPPING INSTRUCTIONS", fontsize=8.2, fontweight='bold', color='#000000')
    ax_info = fig.add_axes([0.545, 0.045, 0.420, 0.390])
    ax_info.axis('off')
    ax_info.text(0.0, 0.98, get_chart_3_dossier(include_hop=True), fontsize=6.8, color='#000000', fontfamily='monospace', va='top',
                 bbox=dict(boxstyle='round,pad=0.45', facecolor='#ffffff', edgecolor='#000000', linewidth=1.1))

    plt.savefig(os.path.join(charts_dir, 'chart_3_hercules_m13_m92.png'), dpi=300, facecolor='white')
    if export_pdf:
        plt.savefig(os.path.join(charts_dir, 'chart_3_hercules_m13_m92.pdf'), dpi=300, facecolor='white')
    plt.close(fig)

    # PocketBook Era Screen-Optimized Assets
    fig_side = plt.figure(figsize=ERA_SIDEBYSIDE_FIGSIZE, facecolor='white', dpi=200)
    fig_side.text(0.05, 0.94, "HERCULES GLOBULARS M13 & M92 — EYEPIECE SIMULATION & DOSSIER", fontsize=11, fontweight='bold', color='#000000')
    fig_side.text(0.05, 0.905, "Sky-Watcher 200P Dobsonian (12.5mm / 96×) | Negative Inverted 180° | Bortle 4", fontsize=8.2, color='#333333')
    ax_eye_side = fig_side.add_axes([0.05, 0.08, 0.42, 0.78])
    draw_chart_3_eyepiece(ax_eye_side)
    ax_info_side = fig_side.add_axes([0.51, 0.08, 0.44, 0.78])
    ax_info_side.axis('off')
    ax_info_side.text(0.0, 0.98, get_chart_3_dossier(include_hop=False), fontsize=8.0, color='#000000', fontfamily='monospace', va='top',
                      bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2))
    plt.savefig(os.path.join(charts_dir, 'chart_3_hercules_m13_m92_eyepiece_dossier.png'), dpi=200, facecolor='white')
    plt.close(fig_side)

    # Screen 2: Constellation Context Orientation Chart
    fig_ctx = plt.figure(figsize=ERA_PORTRAIT_FIGSIZE, facecolor='white', dpi=200)
    fig_ctx.text(0.05, 0.965, "HERCULES GLOBULARS M13 & M92 — CONSTELLATION CONTEXT & ORIENTATION", fontsize=11, fontweight='bold', color='#000000')
    fig_ctx.text(0.05, 0.942, "Naked-Eye Sky (N ↑, E ←) | Constellation Lines & Next-Page Finder Viewport", fontsize=7.8, color='#333333')
    ax_ctx = fig_ctx.add_axes([0.05, 0.04, 0.90, 0.88])
    draw_chart_3_context(ax_ctx)
    plt.savefig(os.path.join(charts_dir, 'chart_3_hercules_m13_m92_context.png'), dpi=200, facecolor='white')
    plt.close(fig_ctx)

    # Screen 3: Zoomed-in Wide-Field Star-Hopping Chart
    fig_wide = plt.figure(figsize=ERA_PORTRAIT_FIGSIZE, facecolor='white', dpi=200)
    fig_wide.text(0.05, 0.965, "HERCULES M13 & M92 — WIDE-FIELD STAR-HOPPING CHART", fontsize=11, fontweight='bold', color='#000000')
    fig_wide.text(0.05, 0.942, "Upright Naked-Eye / Finder (N ↑, E ←) | Stars to Mag 8.5 | Telrad Reticle", fontsize=7.8, color='#333333')
    ax_wide_era = fig_wide.add_axes([0.05, 0.04, 0.90, 0.88])
    draw_chart_3_widefield(ax_wide_era)
    plt.savefig(os.path.join(charts_dir, 'chart_3_hercules_m13_m92_widefield.png'), dpi=200, facecolor='white')
    plt.close(fig_wide)
    print("Chart 3 saved (A4 Landscape & PocketBook Era Screen-Optimized).")


# ==============================================================================
# CHART 4: M31 ANDROMEDA GALAXY, M32 & M110
# ==============================================================================

def draw_chart_4_widefield(ax):
    c_ra, c_dec = 12.0, 36.0
    setup_wide_field(ax, c_ra, c_dec, 26.0, 24.0, max_mag=8.5, show_legend=True, legend_loc='lower left')

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
        ax.text(x+ox, y+oy, lbl, fontsize=fsz, fontweight=fweight, color='#000000', zorder=10)

    m31_ra, m31_dec = 10.685, 41.269
    m31_x = d_ra(m31_ra, c_ra) * math.cos(math.radians(m31_dec))
    m31_y = m31_dec - c_dec

    pts = [(2.10, 29.09), (8.54, 30.86), (17.43, 35.62), (17.07, 38.50), (14.65, 41.08), (m31_ra, m31_dec)]
    p_xy = [ (d_ra(ra, c_ra)*math.cos(math.radians(dec)), dec - c_dec) for ra, dec in pts ]

    ax.add_patch(FancyArrowPatch(p_xy[0], p_xy[2], arrowstyle='->', mutation_scale=13, color='#000000', linestyle='--', linewidth=1.4, zorder=6))
    ax.text((p_xy[0][0]+p_xy[2][0])/2, (p_xy[0][1]+p_xy[2][1])/2 + 0.9, "[STEP 1] Hop 14° NE to Mirach", fontsize=7.2, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=10)

    ax.add_patch(FancyArrowPatch(p_xy[2], p_xy[3], arrowstyle='->', mutation_scale=12, color='#000000', linestyle='--', linewidth=1.4, zorder=6))
    ax.add_patch(FancyArrowPatch(p_xy[3], p_xy[4], arrowstyle='->', mutation_scale=12, color='#000000', linestyle='--', linewidth=1.4, zorder=6))
    ax.text(p_xy[3][0] + 0.6, (p_xy[2][1]+p_xy[4][1])/2, "[STEP 2] Turn 90° NW:\nHop to μ, then ν And", fontsize=7.2, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=10)

    ax.add_patch(FancyArrowPatch(p_xy[4], p_xy[5], arrowstyle='->', mutation_scale=13, color='#000000', linestyle='--', linewidth=1.4, zorder=6))
    ax.text((p_xy[4][0]+p_xy[5][0])/2, p_xy[5][1] + 1.0, "[STEP 3] Slew 1.5° NW to M31!", fontsize=7.2, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=10)

    draw_telrad_reticle(ax, m31_x, m31_y, (2.1, 1.8))
    draw_target_marker(ax, m31_x, m31_y)
    ax.text(m31_x - 0.6, m31_y - 0.9, "M31 ANDROMEDA GALAXY\n(Naked-eye oval in Bortle 4)", fontsize=7.8, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2), zorder=15)

def draw_chart_4_eyepiece(ax):
    ax.set_facecolor('white')
    fov_deg = 0.83
    ax.set_xlim(-fov_deg/2 - 0.03, fov_deg/2 + 0.03)
    ax.set_ylim(-fov_deg/2 - 0.04, fov_deg/2 + 0.03)
    ax.set_aspect('equal')
    ax.add_patch(Circle((0, 0), fov_deg/2, facecolor='#ffffff', edgecolor='#000000', linewidth=1.8, zorder=1))
    ax.plot([0, 0], [-fov_deg/2, fov_deg/2], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)
    ax.plot([-fov_deg/2, fov_deg/2], [0, 0], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)

    m31_ra, m31_dec = 10.685, 41.269
    m31_field = load_field('m31')
    for st in m31_field:
        dx = d_ra(st['ra'], m31_ra) * math.cos(math.radians(st['dec']))
        dy = st['dec'] - m31_dec
        dx_inv, dy_inv = -dx, -dy
        if math.hypot(dx_inv, dy_inv) < fov_deg/2 - 0.008:
            s_size = max(1.5, max(0.0, 12.5 - st['mag'])**2.2 * 0.9)
            ax.plot(dx_inv, dy_inv, 'o', color='#000000', markersize=math.sqrt(s_size), alpha=0.95, zorder=10)

    ax.add_patch(Ellipse((0, 0), 0.75, 0.22, angle=38, facecolor='#f8fafc', edgecolor='#cbd5e1', linestyle='--', linewidth=0.8, zorder=11))
    ax.add_patch(Ellipse((0, 0), 0.45, 0.14, angle=38, facecolor='#f1f5f9', edgecolor='#94a3b8', linestyle='--', linewidth=0.8, zorder=12))
    ax.add_patch(Ellipse((0, 0), 0.20, 0.08, angle=38, facecolor='#e2e8f0', edgecolor='#64748b', linewidth=1.0, zorder=13))
    ax.add_patch(Circle((0, 0), 0.03, facecolor='#1e293b', edgecolor='#000000', linewidth=1.0, zorder=14))

    lane_x = np.linspace(-0.25, 0.25, 50)
    lane_y = lane_x * math.tan(math.radians(38)) + 0.055
    ax.plot(lane_x, lane_y, color='#0f172a', linewidth=2.0, alpha=0.85, zorder=15)
    ax.text(0.08, 0.14, "Dark Dust Lane", fontsize=7.0, color='#000000', fontweight='bold', fontstyle='italic', zorder=25)

    m32_x_inv, m32_y_inv = 0.08, 0.26
    ax.add_patch(Circle((m32_x_inv, m32_y_inv), 0.035, facecolor='#475569', edgecolor='#000000', linewidth=1.0, zorder=16))
    ax.text(m32_x_inv+0.04, m32_y_inv, "M32 (Satellite)", fontsize=7.5, color='#000000', fontweight='bold', va='center', zorder=25)

    m110_x_inv, m110_y_inv = -0.15, -0.23
    ax.add_patch(Ellipse((m110_x_inv, m110_y_inv), 0.14, 0.07, angle=20, facecolor='#f1f5f9', edgecolor='#64748b', linestyle='--', linewidth=1.0, zorder=16))
    ax.text(m110_x_inv - 0.02, m110_y_inv + 0.05, "M110 (Dwarf Elliptical)", fontsize=7.5, color='#000000', fontweight='bold', ha='center', zorder=25)

    ax.text(0, -fov_deg/2 + 0.045, "↓ N (Inverted)", fontsize=7.5, color='#000000', fontweight='bold', ha='center', zorder=25)
    ax.text(fov_deg/2 - 0.045, 0, "E →", fontsize=7.5, color='#000000', fontweight='bold', va='center', ha='right', zorder=25)
    ax.text(0, -fov_deg/2 - 0.022, "20mm Eyepiece (60× Magnification, 50' True FOV)", fontsize=7.5, color='#000000', ha='center')
    ax.axis('off')

def get_chart_4_dossier(include_hop=True):
    txt = (
        "OBJECT DOSSIER: M31 (NGC 224), M32 & M110\n"
        "• Constellation: Andromeda | Type: Giant Spiral Galaxy\n"
        "• Magnitude: 3.4V | Surface Brightness: 13.5 | Size: 180' × 63'\n"
        "• Distance: 2.54 million ly | Companions: M32 & M110\n"
        "• Tonight's Ephemeris at Dvigrad (Sep 12, 2026):\n"
        "    20:00 CEST: Alt 24.7° | 21:15 CEST: Alt 36.2° (Prime Contrast!)\n"
        "    22:30 CEST: Alt 48.6°, Az 78° (Superb & High)\n\n"
        "EYEPIECE QUICK REFERENCE & OBSERVING NOTES:\n"
        "• Primary Eyepiece (20mm / 60×): Mandatory! Sweeps the\n"
        "  immense galactic disk, bright starlike nucleus, and M32.\n"
        "• Dark Dust Lane: Look outside the core along the NW edge;\n"
        "  silhouette dust absorption lane visible with averted vision.\n"
        "• Companions: M32 (compact south), M110 (diffuse oval NW)."
    )
    if include_hop:
        txt += (
            "\n\nSTEP-BY-STEP STAR HOP NARRATIVE:\n"
            "1. Naked-Eye: Find the Great Square of Pegasus. Identify the\n"
            "   northeast corner star Alpheratz (α And).\n"
            "2. Follow the Andromeda chain: hop 7° to δ And, then 7° to\n"
            "   reddish Mirach (β And, mag 2.1).\n"
            "3. Turn 90° NW: Hop 3.5° to μ And, then 3.5° to ν And.\n"
            "4. Slew 1.5° further NW: M31 fills the finder and eyepiece!"
        )
    return txt

def draw_chart_4_context(ax):
    constels = [
        ("Andromeda", 8.0, 33.0),
        ("Pegasus", 350.0, 22.0),
        ("Cassiopeia", 12.0, 58.0),
        ("Triangulum", 31.0, 33.0),
        ("Perseus", 44.0, 42.0),
        ("Pisces", 8.0, 12.0)
    ]
    stars = [
        ("Alpheratz", 2.10, 29.09, -0.6, -0.6, 7.8, 'bold'),
        ("Mirach", 17.43, 35.62, 0.6, -0.6, 7.8, 'bold'),
        ("Almach", 30.97, 42.33, 0.6, 0.4, 7.5, 'normal'),
        ("Scheat (β Peg)", 346.0, 28.08, -0.6, 0.4, 7.5, 'normal'),
        ("Navi (γ Cas)", 14.18, 60.72, 0.6, -0.8, 7.5, 'normal')
    ]
    targets = [("M31 Andromeda", 10.685, 41.269, 0.5, 0.8)]
    setup_context_field(ax, 10.0, 35.0, 62.0, 52.0,
                        12.0, 36.0, 26.0, 24.0,
                        constels, stars, targets)

def make_chart_4(charts_dir, export_pdf=False):
    print("Generating Chart 4: M31 Andromeda (A4 Landscape, Toner-Saver Negative)...")
    fig = plt.figure(figsize=A4_LANDSCAPE, facecolor='white', dpi=300)
    fig.text(0.035, 0.963, "STAR-HOPPING FINDER CHART 4: M31 (ANDROMEDA GALAXY), M32 & M110 — ANDROMEDA", fontsize=11.5, fontweight='bold', color='#000000')
    fig.text(0.035, 0.936, "Location: Dvigrad (Bortle 4, SQM 21.0) | Sep 12, 2026 • 21:15 CEST | Sky-Watcher 200P Dobsonian (8-inch f/6, 1200mm FL) | B/W Toner-Saver Edition", fontsize=7.8, color='#333333')

    # VIEWPORT A
    fig.text(0.035, 0.898, "VIEWPORT A: WIDE-FIELD STAR-HOPPING CHART (Upright Naked-Eye / Finder: N ↑, E ←)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_wide = fig.add_axes([0.035, 0.045, 0.485, 0.835])
    draw_chart_4_widefield(ax_wide)

    # VIEWPORT B: TELESCOPE EYEPIECE SIMULATION
    fig.text(0.545, 0.898, "VIEWPORT B: EYEPIECE SIMULATION (Negative Inverted 180°: N ↓, E →)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_eye = fig.add_axes([0.58, 0.485, 0.35, 0.395])
    draw_chart_4_eyepiece(ax_eye)

    # VIEWPORT C: DOSSIER & INSTRUCTIONS
    fig.text(0.545, 0.448, "VIEWPORT C: TARGET DOSSIER & STAR-HOPPING INSTRUCTIONS", fontsize=8.2, fontweight='bold', color='#000000')
    ax_info = fig.add_axes([0.545, 0.045, 0.420, 0.390])
    ax_info.axis('off')
    ax_info.text(0.0, 0.98, get_chart_4_dossier(include_hop=True), fontsize=6.8, color='#000000', fontfamily='monospace', va='top',
                 bbox=dict(boxstyle='round,pad=0.45', facecolor='#ffffff', edgecolor='#000000', linewidth=1.1))

    plt.savefig(os.path.join(charts_dir, 'chart_4_andromeda_m31.png'), dpi=300, facecolor='white')
    if export_pdf:
        plt.savefig(os.path.join(charts_dir, 'chart_4_andromeda_m31.pdf'), dpi=300, facecolor='white')
    plt.close(fig)

    # PocketBook Era Screen-Optimized Assets
    fig_side = plt.figure(figsize=ERA_SIDEBYSIDE_FIGSIZE, facecolor='white', dpi=200)
    fig_side.text(0.05, 0.94, "M31 ANDROMEDA GALAXY & SATELLITES — EYEPIECE SIMULATION & DOSSIER", fontsize=11, fontweight='bold', color='#000000')
    fig_side.text(0.05, 0.905, "Sky-Watcher 200P Dobsonian (20mm / 60×) | Negative Inverted 180° | Bortle 4", fontsize=8.2, color='#333333')
    ax_eye_side = fig_side.add_axes([0.05, 0.08, 0.42, 0.78])
    draw_chart_4_eyepiece(ax_eye_side)
    ax_info_side = fig_side.add_axes([0.51, 0.08, 0.44, 0.78])
    ax_info_side.axis('off')
    ax_info_side.text(0.0, 0.98, get_chart_4_dossier(include_hop=False), fontsize=8.0, color='#000000', fontfamily='monospace', va='top',
                      bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2))
    plt.savefig(os.path.join(charts_dir, 'chart_4_andromeda_m31_eyepiece_dossier.png'), dpi=200, facecolor='white')
    plt.close(fig_side)

    # Screen 2: Constellation Context Orientation Chart
    fig_ctx = plt.figure(figsize=ERA_PORTRAIT_FIGSIZE, facecolor='white', dpi=200)
    fig_ctx.text(0.05, 0.965, "M31 ANDROMEDA GALAXY — CONSTELLATION CONTEXT & ORIENTATION", fontsize=11, fontweight='bold', color='#000000')
    fig_ctx.text(0.05, 0.942, "Naked-Eye Sky (N ↑, E ←) | Constellation Lines & Next-Page Finder Viewport", fontsize=7.8, color='#333333')
    ax_ctx = fig_ctx.add_axes([0.05, 0.04, 0.90, 0.88])
    draw_chart_4_context(ax_ctx)
    plt.savefig(os.path.join(charts_dir, 'chart_4_andromeda_m31_context.png'), dpi=200, facecolor='white')
    plt.close(fig_ctx)

    # Screen 3: Zoomed-in Wide-Field Star-Hopping Chart
    fig_wide = plt.figure(figsize=ERA_PORTRAIT_FIGSIZE, facecolor='white', dpi=200)
    fig_wide.text(0.05, 0.965, "M31 ANDROMEDA GALAXY — WIDE-FIELD STAR-HOPPING CHART", fontsize=11, fontweight='bold', color='#000000')
    fig_wide.text(0.05, 0.942, "Upright Naked-Eye / Finder (N ↑, E ←) | Stars to Mag 8.5 | Telrad Reticle", fontsize=7.8, color='#333333')
    ax_wide_era = fig_wide.add_axes([0.05, 0.04, 0.90, 0.88])
    draw_chart_4_widefield(ax_wide_era)
    plt.savefig(os.path.join(charts_dir, 'chart_4_andromeda_m31_widefield.png'), dpi=200, facecolor='white')
    plt.close(fig_wide)
    print("Chart 4 saved (A4 Landscape & PocketBook Era Screen-Optimized).")


# ==============================================================================
# CHART 5: PERSEUS DOUBLE CLUSTER (NGC 869 & NGC 884)
# ==============================================================================

def draw_chart_5_widefield(ax):
    c_ra, c_dec = 32.0, 55.0
    setup_wide_field(ax, c_ra, c_dec, 46.0, 22.0, max_mag=8.5, show_legend=True, legend_loc='lower left')

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
        ax.text(x+ox, y+oy, lbl, fontsize=fsz, fontweight=fweight, color='#000000', zorder=10)

    dc_ra, dc_dec = 35.15, 57.15
    dc_x = d_ra(dc_ra, c_ra) * math.cos(math.radians(dc_dec))
    dc_y = dc_dec - c_dec

    g_x = d_ra(14.18, c_ra) * math.cos(math.radians(60.72))
    g_y = 60.72 - c_dec
    r_x = d_ra(20.30, c_ra) * math.cos(math.radians(60.23))
    r_y = 60.23 - c_dec

    arrow1 = FancyArrowPatch((g_x, g_y), (r_x, r_y), arrowstyle='->', mutation_scale=12, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax.add_patch(arrow1)
    arrow2 = FancyArrowPatch((r_x, r_y), (dc_x, dc_y), arrowstyle='->', mutation_scale=13, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax.add_patch(arrow2)
    ax.text((r_x+dc_x)/2 - 0.2, (r_y+dc_y)/2 - 1.0, "[STEP 1] Extend γ through δ Cas\nby ~6° Southeast into Perseus", fontsize=7.2, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=10)

    draw_telrad_reticle(ax, dc_x, dc_y, (2.1, 1.8))
    draw_target_marker(ax, dc_x, dc_y)
    ax.text(dc_x - 0.5, dc_y - 1.2, "DOUBLE CLUSTER (NGC 869 / 884)\n(Visible to Naked Eye in Bortle 4!)", fontsize=7.8, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2), zorder=15)

def draw_chart_5_eyepiece(ax):
    ax.set_facecolor('white')
    fov_deg = 0.83
    ax.set_xlim(-fov_deg/2 - 0.03, fov_deg/2 + 0.03)
    ax.set_ylim(-fov_deg/2 - 0.04, fov_deg/2 + 0.03)
    ax.set_aspect('equal')
    ax.add_patch(Circle((0, 0), fov_deg/2, facecolor='#ffffff', edgecolor='#000000', linewidth=1.8, zorder=1))
    ax.plot([0, 0], [-fov_deg/2, fov_deg/2], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)
    ax.plot([-fov_deg/2, fov_deg/2], [0, 0], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)

    dc_ra, dc_dec = 35.15, 57.15
    dc_field = load_field('double_cluster')
    for st in dc_field:
        dx = d_ra(st['ra'], dc_ra) * math.cos(math.radians(st['dec']))
        dy = st['dec'] - dc_dec
        dx_inv, dy_inv = -dx, -dy
        if math.hypot(dx_inv, dy_inv) < fov_deg/2 - 0.008:
            s_size = max(1.5, max(0.0, 12.5 - st['mag'])**2.2 * 0.9)
            ax.plot(dx_inv, dy_inv, 'o', color='#000000', markersize=math.sqrt(s_size), alpha=0.95, zorder=10)

    c1_x, c1_y = 0.15, -0.05
    c2_x, c2_y = -0.15, 0.05
    ax.add_patch(Circle((c1_x, c1_y), 0.16, facecolor='#f8fafc', edgecolor='#cbd5e1', linestyle=':', linewidth=0.8, zorder=11))
    ax.add_patch(Circle((c2_x, c2_y), 0.16, facecolor='#f8fafc', edgecolor='#cbd5e1', linestyle=':', linewidth=0.8, zorder=11))

    np.random.seed(99)
    for cx, cy, n_c in [(c1_x, c1_y, 110), (c2_x, c2_y, 100)]:
        r_c = np.random.exponential(0.06, n_c)
        th_c = np.random.uniform(0, 2*np.pi, n_c)
        ax.scatter(cx + r_c*np.cos(th_c), cy + r_c*np.sin(th_c), s=np.random.uniform(1.8, 9.0, n_c), color='#000000', alpha=0.9, zorder=13)

    for rx, ry in [(c2_x+0.02, c2_y+0.02), (c2_x-0.03, c2_y-0.01), (c2_x+0.01, c2_y-0.04)]:
        ax.plot(rx, ry, 'o', color='#000000', markersize=4.5, zorder=15)
        ax.plot(rx, ry, 'o', color='none', markeredgecolor='#000000', markeredgewidth=1.1, markersize=9.5, zorder=15)
    ax.text(c2_x, c2_y-0.12, "Carbon Supergiants\n(Open Circles in NGC 884)", fontsize=7.0, color='#000000', ha='center', fontstyle='italic', zorder=25)

    ax.text(c1_x, c1_y+0.12, "NGC 869", fontsize=7.8, color='#000000', fontweight='bold', ha='center', zorder=25)
    ax.text(c2_x, c2_y+0.12, "NGC 884", fontsize=7.8, color='#000000', fontweight='bold', ha='center', zorder=25)

    ax.text(0, -fov_deg/2 + 0.045, "↓ N (Inverted)", fontsize=7.5, color='#000000', fontweight='bold', ha='center', zorder=25)
    ax.text(fov_deg/2 - 0.045, 0, "E →", fontsize=7.5, color='#000000', fontweight='bold', va='center', ha='right', zorder=25)
    ax.text(0, -fov_deg/2 - 0.022, "20mm Eyepiece (60× Magnification, 50' True FOV)", fontsize=7.5, color='#000000', ha='center')
    ax.axis('off')

def get_chart_5_dossier(include_hop=True):
    txt = (
        "OBJECT DOSSIER: NGC 869 & NGC 884 (CALDWELL 14)\n"
        "• Constellation: Perseus | Type: Twin Open Clusters\n"
        "• Magnitude: 3.7 / 3.8V | Apparent Size: 30' diameter each\n"
        "• Total Stars: ~600 stars | Distance: ~7,500 light-years\n"
        "• Tonight's Ephemeris at Dvigrad (Sep 12, 2026):\n"
        "    20:00 CEST: Alt 24.0° | 21:15 CEST: Alt 31.6° (Clear of trees)\n"
        "    22:30 CEST: Alt 40.5°, Az 50° (Peak Crystalline Clarity)\n\n"
        "EYEPIECE QUICK REFERENCE & OBSERVING NOTES:\n"
        "• Primary Eyepiece (20mm / 60×): The ultimate showstopper!\n"
        "  Frames both glittering jewel boxes side by side in 50' FOV.\n"
        "• Carbon Supergiants: Radiant ruby-red/orange supergiant\n"
        "  stars (open circles) glowing among blue-white stars in NGC 884.\n"
        "• Core Zoom (12.5mm / 96×): Resolves dense center of NGC 869."
    )
    if include_hop:
        txt += (
            "\n\nSTEP-BY-STEP STAR HOP NARRATIVE:\n"
            "1. Naked-Eye: Locate the 'W' of Cassiopeia high in the NE.\n"
            "2. Draw a line from central star Navi (γ Cas) through Ruchbah\n"
            "   (δ Cas, bottom-left vertex of the 'W').\n"
            "3. Extend that line southeast by the same distance (~6°).\n"
            "4. An unmistakable glowing mist is visible naked-eye;\n"
            "   center Telrad or finder scope directly on it!"
        )
    return txt

def draw_chart_5_context(ax):
    constels = [
        ("Perseus", 48.0, 43.0),
        ("Cassiopeia", 10.0, 56.5),
        ("Andromeda", 22.0, 40.0),
        ("Triangulum", 31.0, 32.5),
        ("Camelopardalis", 60.0, 68.0)
    ]
    stars = [
        ("Mirfak (α Per)", 51.08, 49.86, 0.6, -0.6, 7.8, 'bold'),
        ("Algol (β Per)", 46.5, 40.9, 0.6, -0.6, 7.5, 'normal'),
        ("Ruchbah (δ Cas)", 20.30, 60.23, -0.6, -0.6, 7.5, 'normal'),
        ("Navi (γ Cas)", 14.18, 60.72, -0.6, 0.6, 7.5, 'normal')
    ]
    targets = [("Double Cluster", 35.15, 57.15, 0.5, 0.8)]
    setup_context_field(ax, 38.0, 52.0, 65.0, 52.0,
                        32.0, 55.0, 46.0, 22.0,
                        constels, stars, targets)

def make_chart_5(charts_dir, export_pdf=False):
    print("Generating Chart 5: Double Cluster (A4 Landscape, Toner-Saver Negative)...")
    fig = plt.figure(figsize=A4_LANDSCAPE, facecolor='white', dpi=300)
    fig.text(0.035, 0.963, "STAR-HOPPING FINDER CHART 5: THE DOUBLE CLUSTER (NGC 869 / NGC 884) — PERSEUS", fontsize=11.5, fontweight='bold', color='#000000')
    fig.text(0.035, 0.936, "Location: Dvigrad (Bortle 4, SQM 21.0) | Sep 12, 2026 • 21:15 CEST | Sky-Watcher 200P Dobsonian (8-inch f/6, 1200mm FL) | B/W Toner-Saver Edition", fontsize=7.8, color='#333333')

    # VIEWPORT A
    fig.text(0.035, 0.898, "VIEWPORT A: WIDE-FIELD STAR-HOPPING CHART (Upright Naked-Eye / Finder: N ↑, E ←)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_wide = fig.add_axes([0.035, 0.045, 0.485, 0.835])
    draw_chart_5_widefield(ax_wide)

    # VIEWPORT B: TELESCOPE EYEPIECE SIMULATION
    fig.text(0.545, 0.898, "VIEWPORT B: EYEPIECE SIMULATION (Negative Inverted 180°: N ↓, E →)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_eye = fig.add_axes([0.58, 0.485, 0.35, 0.395])
    draw_chart_5_eyepiece(ax_eye)

    # VIEWPORT C: DOSSIER & INSTRUCTIONS
    fig.text(0.545, 0.448, "VIEWPORT C: TARGET DOSSIER & STAR-HOPPING INSTRUCTIONS", fontsize=8.2, fontweight='bold', color='#000000')
    ax_info = fig.add_axes([0.545, 0.045, 0.420, 0.390])
    ax_info.axis('off')
    ax_info.text(0.0, 0.98, get_chart_5_dossier(include_hop=True), fontsize=6.8, color='#000000', fontfamily='monospace', va='top',
                 bbox=dict(boxstyle='round,pad=0.45', facecolor='#ffffff', edgecolor='#000000', linewidth=1.1))

    plt.savefig(os.path.join(charts_dir, 'chart_5_perseus_double_cluster.png'), dpi=300, facecolor='white')
    if export_pdf:
        plt.savefig(os.path.join(charts_dir, 'chart_5_perseus_double_cluster.pdf'), dpi=300, facecolor='white')
    plt.close(fig)

    # PocketBook Era Screen-Optimized Assets
    fig_side = plt.figure(figsize=ERA_SIDEBYSIDE_FIGSIZE, facecolor='white', dpi=200)
    fig_side.text(0.05, 0.94, "PERSEUS DOUBLE CLUSTER — EYEPIECE SIMULATION & TARGET DOSSIER", fontsize=11, fontweight='bold', color='#000000')
    fig_side.text(0.05, 0.905, "Sky-Watcher 200P Dobsonian (20mm / 60×) | Negative Inverted 180° | Bortle 4", fontsize=8.2, color='#333333')
    ax_eye_side = fig_side.add_axes([0.05, 0.08, 0.42, 0.78])
    draw_chart_5_eyepiece(ax_eye_side)
    ax_info_side = fig_side.add_axes([0.51, 0.08, 0.44, 0.78])
    ax_info_side.axis('off')
    ax_info_side.text(0.0, 0.98, get_chart_5_dossier(include_hop=False), fontsize=8.0, color='#000000', fontfamily='monospace', va='top',
                      bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2))
    plt.savefig(os.path.join(charts_dir, 'chart_5_perseus_double_cluster_eyepiece_dossier.png'), dpi=200, facecolor='white')
    plt.close(fig_side)

    # Screen 2: Constellation Context Orientation Chart
    fig_ctx = plt.figure(figsize=ERA_PORTRAIT_FIGSIZE, facecolor='white', dpi=200)
    fig_ctx.text(0.05, 0.965, "PERSEUS DOUBLE CLUSTER — CONSTELLATION CONTEXT & ORIENTATION", fontsize=11, fontweight='bold', color='#000000')
    fig_ctx.text(0.05, 0.942, "Naked-Eye Sky (N ↑, E ←) | Constellation Lines & Next-Page Finder Viewport", fontsize=7.8, color='#333333')
    ax_ctx = fig_ctx.add_axes([0.05, 0.04, 0.90, 0.88])
    draw_chart_5_context(ax_ctx)
    plt.savefig(os.path.join(charts_dir, 'chart_5_perseus_double_cluster_context.png'), dpi=200, facecolor='white')
    plt.close(fig_ctx)

    # Screen 3: Zoomed-in Wide-Field Star-Hopping Chart
    fig_wide = plt.figure(figsize=ERA_PORTRAIT_FIGSIZE, facecolor='white', dpi=200)
    fig_wide.text(0.05, 0.965, "PERSEUS DOUBLE CLUSTER — WIDE-FIELD STAR-HOPPING CHART", fontsize=11, fontweight='bold', color='#000000')
    fig_wide.text(0.05, 0.942, "Upright Naked-Eye / Finder (N ↑, E ←) | Stars to Mag 8.5 | Telrad Reticle", fontsize=7.8, color='#333333')
    ax_wide_era = fig_wide.add_axes([0.05, 0.04, 0.90, 0.88])
    draw_chart_5_widefield(ax_wide_era)
    plt.savefig(os.path.join(charts_dir, 'chart_5_perseus_double_cluster_widefield.png'), dpi=200, facecolor='white')
    plt.close(fig_wide)
    print("Chart 5 saved (A4 Landscape & PocketBook Era Screen-Optimized).")


# ==============================================================================
# CHART 6: M11 WILD DUCK CLUSTER & SATURN
# ==============================================================================

def draw_chart_6_widefield(ax):
    c_ra, c_dec = 288.0, 2.0
    setup_wide_field(ax, c_ra, c_dec, 24.0, 24.0, max_mag=8.5, show_legend=True, legend_loc='lower left')

    key_stars = [
        (297.70, 8.87, 'Altair (α Aql)\nmag 0.77', 0.4, -0.6, 8.5, 'bold'),
        (286.55, -4.88, 'λ Aql (Spine Base)\nmag 3.43', -0.8, 0.4, 7.8, 'bold'),
        (280.93, -4.75, 'β Sct\nmag 4.22', -0.4, 0.4, 7.2, 'normal'),
        (281.29, -8.24, 'α Sct\nmag 3.85', -0.4, -0.6, 7.2, 'normal')
    ]
    for s_ra, s_dec, lbl, ox, oy, fsz, fweight in key_stars:
        x = d_ra(s_ra, c_ra) * math.cos(math.radians(s_dec))
        y = s_dec - c_dec
        ax.text(x+ox, y+oy, lbl, fontsize=fsz, fontweight=fweight, color='#000000', zorder=10)

    alt_x = d_ra(297.70, c_ra) * math.cos(math.radians(8.87))
    alt_y = 8.87 - c_dec
    lam_x = d_ra(286.55, c_ra) * math.cos(math.radians(-4.88))
    lam_y = -4.88 - c_dec

    m11_ra, m11_dec = 282.775, -6.267
    m11_x = d_ra(m11_ra, c_ra) * math.cos(math.radians(m11_dec))
    m11_y = m11_dec - c_dec

    arrow1 = FancyArrowPatch((alt_x, alt_y), (lam_x, lam_y), arrowstyle='->', mutation_scale=12, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax.add_patch(arrow1)
    ax.text((alt_x+lam_x)/2 + 0.6, (alt_y+lam_y)/2, "[STEP 1] Follow Aquila spine\n14° South to λ Aql", fontsize=7.2, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=10)

    arrow2 = FancyArrowPatch((lam_x, lam_y), (m11_x, m11_y), arrowstyle='->', mutation_scale=13, color='#000000', linestyle='--', linewidth=1.4, zorder=6)
    ax.add_patch(arrow2)
    ax.text((lam_x+m11_x)/2 + 0.2, (lam_y+m11_y)/2 + 1.1, "[STEP 2] Slew 4.5° WSW\ninto Scutum Star Cloud", fontsize=7.2, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=10)

    draw_telrad_reticle(ax, m11_x, m11_y, (2.0, -1.8))
    draw_target_marker(ax, m11_x, m11_y)
    ax.text(m11_x - 0.5, m11_y - 1.2, "M11 WILD DUCK CLUSTER", fontsize=7.8, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2), zorder=15)

def draw_chart_6_eyepiece_m11(ax):
    ax.set_facecolor('white')
    fov_deg = 0.52
    ax.set_xlim(-fov_deg/2 - 0.015, fov_deg/2 + 0.015)
    ax.set_ylim(-fov_deg/2 - 0.030, fov_deg/2 + 0.025)
    ax.set_aspect('equal')
    ax.add_patch(Circle((0, 0), fov_deg/2, facecolor='#ffffff', edgecolor='#000000', linewidth=1.6, zorder=1))
    ax.plot([0, 0], [-fov_deg/2, fov_deg/2], color='#e2e8f0', linestyle=':', linewidth=0.7, zorder=2)
    ax.plot([-fov_deg/2, fov_deg/2], [0, 0], color='#e2e8f0', linestyle=':', linewidth=0.7, zorder=2)

    m11_ra, m11_dec = 282.775, -6.267
    m11_field = load_field('m11')
    for st in m11_field:
        dx = d_ra(st['ra'], m11_ra) * math.cos(math.radians(st['dec']))
        dy = st['dec'] - m11_dec
        dx_inv, dy_inv = -dx, -dy
        if math.hypot(dx_inv, dy_inv) < fov_deg/2 - 0.005:
            s_size = max(1.5, max(0.0, 12.5 - st['mag'])**2.2 * 0.9)
            ax.plot(dx_inv, dy_inv, 'o', color='#000000', markersize=math.sqrt(s_size), alpha=0.95, zorder=10)

    ax.add_patch(Circle((0, 0), 0.11, facecolor='#f8fafc', edgecolor='#cbd5e1', linestyle=':', linewidth=0.8, zorder=11))
    np.random.seed(77)
    n_m11 = 130
    r_m11 = np.random.exponential(0.04, n_m11)
    th_m11 = np.random.uniform(np.pi/4, 5*np.pi/4, n_m11)
    ax.scatter(r_m11*np.cos(th_m11), r_m11*np.sin(th_m11), s=np.random.uniform(1.5, 7.0, n_m11), color='#000000', alpha=0.9, zorder=13)
    ax.plot(0.015, -0.01, 'o', color='#000000', markersize=4.5, zorder=16)
    ax.plot(0.015, -0.01, 'o', color='none', markeredgecolor='#000000', markeredgewidth=1.0, markersize=9.0, zorder=16)

    ax.text(0, fov_deg/2 + 0.020, "B1: M11 (12.5mm / 96×)", fontsize=7.5, fontweight='bold', color='#000000', ha='center')
    ax.text(0, -fov_deg/2 - 0.022, "Inverted 180° View", fontsize=6.8, color='#333333', ha='center')
    ax.axis('off')

def draw_chart_6_eyepiece_saturn(ax):
    ax.set_facecolor('white')
    ax.set_xlim(-0.065, 0.065); ax.set_ylim(-0.075, 0.075); ax.set_aspect('equal')
    ax.add_patch(Circle((0, 0), 0.06, facecolor='#ffffff', edgecolor='#000000', linewidth=1.6, zorder=1))

    ax.add_patch(Circle((0, 0), 0.014, facecolor='#f8fafc', edgecolor='#000000', linewidth=1.1, zorder=12))
    ax.plot([-0.013, 0.013], [-0.002, -0.002], color='#475569', linewidth=1.0, alpha=0.8, zorder=13)
    ax.add_patch(Ellipse((0, 0), 0.065, 0.006, angle=-12, facecolor='#ffffff', edgecolor='#000000', linewidth=1.1, zorder=14))
    ax.plot(0.042, 0.018, 'o', color='#000000', markersize=3.5, zorder=15)
    ax.text(0.042, 0.024, "Titan (mag 8.5)", fontsize=6.8, color='#000000', fontweight='bold', ha='center', zorder=20)

    ax.text(0, 0.065, "B2: SATURN (12.5mm / 96×)", fontsize=7.5, fontweight='bold', color='#000000', ha='center')
    ax.text(0, -0.072, "Shallow Rings & Titan", fontsize=6.8, color='#333333', ha='center')
    ax.axis('off')

def get_chart_6_dossier(include_hop=True):
    txt = (
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
        "EYEPIECE QUICK REFERENCE & OBSERVING NOTES:\n"
        "• M11 (12.5mm / 96×): Resolves a dazzling star swarm\n"
        "  resembling wild ducks in V-formation with bright apex star.\n"
        "• Saturn (12.5mm / 96×): Knife-edge shallow rings,\n"
        "  globe shadow and radiant orange moon Titan (21:45–22:30)."
    )
    if include_hop:
        txt += (
            "\n\nSTEP-BY-STEP STAR HOP NARRATIVE:\n"
            "1. M11: Locate Altair. Slew 14° South down Aquila's backbone to\n"
            "   λ Aquilae (mag 3.4). Slew 4.5° WSW into the Scutum cloud.\n"
            "2. Saturn: Look low in the ESE after 21:40 CEST. Identify the\n"
            "   brightest golden non-twinkling object below Pegasus!"
        )
    return txt

def draw_chart_6_context(ax):
    constels = [
        ("Aquila", 293.0, 3.5),
        ("Scutum", 280.0, -12.0),
        ("Sagitta", 297.0, 18.5),
        ("Delphinus", 309.0, 15.0),
        ("Serpens Cauda", 272.0, -4.0),
        ("Ophiuchus", 265.0, 5.0),
        ("Sagittarius", 285.0, -22.0),
        ("Capricornus", 312.0, -18.0)
    ]
    stars = [
        ("Altair (mag 0.77)", 297.70, 8.87, 0.6, 0.4, 8.5, 'bold'),
        ("λ Aquilae", 286.55, -4.88, -0.8, -0.6, 7.8, 'bold'),
        ("Tarazed", 296.5, 10.6, -0.6, 0.4, 7.5, 'normal')
    ]
    targets = [("M11 Wild Duck", 282.775, -6.267, 0.5, -0.9)]
    def extra_chart_6(ax_in):
        ax_in.annotate("→ Saturn Rising in Aquarius\n(Observe after 21:40 CEST)",
                       xy=(0.04, 0.45), xycoords='axes fraction', fontsize=7.2, fontweight='bold', color='#000000',
                       bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#000000', linewidth=1.0),
                       zorder=25)
    setup_context_field(ax, 292.0, 0.0, 62.0, 50.0,
                        288.0, 2.0, 24.0, 24.0,
                        constels, stars, targets, extra_fn=extra_chart_6)

def make_chart_6(charts_dir, export_pdf=False):
    print("Generating Chart 6: M11 & Saturn (A4 Landscape, Toner-Saver Negative)...")
    fig = plt.figure(figsize=A4_LANDSCAPE, facecolor='white', dpi=300)
    fig.text(0.035, 0.963, "STAR-HOPPING FINDER CHART 6: M11 (WILD DUCK CLUSTER) & SATURN — SCUTUM / AQUARIUS", fontsize=11.5, fontweight='bold', color='#000000')
    fig.text(0.035, 0.936, "Location: Dvigrad (Bortle 4, SQM 21.0) | Sep 12, 2026 • 21:15 CEST | Sky-Watcher 200P Dobsonian (8-inch f/6, 1200mm FL) | B/W Toner-Saver Edition", fontsize=7.8, color='#333333')

    # VIEWPORT A
    fig.text(0.035, 0.898, "VIEWPORT A: WIDE-FIELD STAR-HOPPING CHART (Upright Naked-Eye / Finder: N ↑, E ←)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_wide = fig.add_axes([0.035, 0.045, 0.485, 0.835])
    draw_chart_6_widefield(ax_wide)

    # VIEWPORT B: TWO INSETS (M11 + SATURN)
    fig.text(0.545, 0.898, "VIEWPORT B: TELESCOPE SIMULATIONS (Negative Inverted 180°: N ↓, E →)", fontsize=8.2, fontweight='bold', color='#000000')
    ax_eye1 = fig.add_axes([0.550, 0.495, 0.185, 0.380])
    draw_chart_6_eyepiece_m11(ax_eye1)
    ax_eye2 = fig.add_axes([0.765, 0.495, 0.185, 0.380])
    draw_chart_6_eyepiece_saturn(ax_eye2)

    # VIEWPORT C: DOSSIER & INSTRUCTIONS
    fig.text(0.545, 0.448, "VIEWPORT C: TARGET DOSSIER & STAR-HOPPING INSTRUCTIONS", fontsize=8.2, fontweight='bold', color='#000000')
    ax_info = fig.add_axes([0.545, 0.045, 0.420, 0.390])
    ax_info.axis('off')
    ax_info.text(0.0, 0.98, get_chart_6_dossier(include_hop=True), fontsize=6.8, color='#000000', fontfamily='monospace', va='top',
                 bbox=dict(boxstyle='round,pad=0.45', facecolor='#ffffff', edgecolor='#000000', linewidth=1.1))

    plt.savefig(os.path.join(charts_dir, 'chart_6_scutum_m11_and_saturn.png'), dpi=300, facecolor='white')
    if export_pdf:
        plt.savefig(os.path.join(charts_dir, 'chart_6_scutum_m11_and_saturn.pdf'), dpi=300, facecolor='white')
    plt.close(fig)

    # PocketBook Era Screen-Optimized Assets
    fig_side = plt.figure(figsize=ERA_SIDEBYSIDE_FIGSIZE, facecolor='white', dpi=200)
    fig_side.text(0.05, 0.94, "M11 WILD DUCK CLUSTER & SATURN — EYEPIECE SIMULATIONS & DOSSIER", fontsize=11, fontweight='bold', color='#000000')
    fig_side.text(0.05, 0.905, "Sky-Watcher 200P Dobsonian (12.5mm / 96×) | Negative Inverted 180° | Bortle 4", fontsize=8.2, color='#333333')
    ax_eye1_side = fig_side.add_axes([0.05, 0.50, 0.42, 0.38])
    draw_chart_6_eyepiece_m11(ax_eye1_side)
    ax_eye2_side = fig_side.add_axes([0.05, 0.08, 0.42, 0.38])
    draw_chart_6_eyepiece_saturn(ax_eye2_side)
    ax_info_side = fig_side.add_axes([0.51, 0.08, 0.44, 0.80])
    ax_info_side.axis('off')
    ax_info_side.text(0.0, 0.98, get_chart_6_dossier(include_hop=False), fontsize=8.0, color='#000000', fontfamily='monospace', va='top',
                      bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2))
    plt.savefig(os.path.join(charts_dir, 'chart_6_scutum_m11_and_saturn_eyepiece_dossier.png'), dpi=200, facecolor='white')
    plt.close(fig_side)

    # Screen 2: Constellation Context Orientation Chart
    fig_ctx = plt.figure(figsize=ERA_PORTRAIT_FIGSIZE, facecolor='white', dpi=200)
    fig_ctx.text(0.05, 0.965, "M11 WILD DUCK & SATURN — CONSTELLATION CONTEXT & ORIENTATION", fontsize=11, fontweight='bold', color='#000000')
    fig_ctx.text(0.05, 0.942, "Naked-Eye Sky (N ↑, E ←) | Constellation Lines & Next-Page Finder Viewport", fontsize=7.8, color='#333333')
    ax_ctx = fig_ctx.add_axes([0.05, 0.04, 0.90, 0.88])
    draw_chart_6_context(ax_ctx)
    plt.savefig(os.path.join(charts_dir, 'chart_6_scutum_m11_and_saturn_context.png'), dpi=200, facecolor='white')
    plt.close(fig_ctx)

    # Screen 3: Zoomed-in Wide-Field Star-Hopping Chart
    fig_wide = plt.figure(figsize=ERA_PORTRAIT_FIGSIZE, facecolor='white', dpi=200)
    fig_wide.text(0.05, 0.965, "M11 & SATURN — WIDE-FIELD STAR-HOPPING CHART", fontsize=11, fontweight='bold', color='#000000')
    fig_wide.text(0.05, 0.942, "Upright Naked-Eye / Finder (N ↑, E ←) | Stars to Mag 8.5 | Telrad Reticle", fontsize=7.8, color='#333333')
    ax_wide_era = fig_wide.add_axes([0.05, 0.04, 0.90, 0.88])
    draw_chart_6_widefield(ax_wide_era)
    plt.savefig(os.path.join(charts_dir, 'chart_6_scutum_m11_and_saturn_widefield.png'), dpi=200, facecolor='white')
    plt.close(fig_wide)
    print("Chart 6 saved (A4 Landscape & PocketBook Era Screen-Optimized).")


def generate_all_charts(output_dir=None, export_pdf=False):
    if output_dir is None:
        output_dir = os.path.join(REPO_ROOT, 'observations', 'dvigrad-2026-09-12')
    charts_dir = os.path.join(output_dir, 'charts')
    os.makedirs(charts_dir, exist_ok=True)

    make_full_sky_map(output_dir, export_pdf=export_pdf)
    make_chart_1(charts_dir, export_pdf=export_pdf)
    make_chart_2(charts_dir, export_pdf=export_pdf)
    make_chart_3(charts_dir, export_pdf=export_pdf)
    make_chart_4(charts_dir, export_pdf=export_pdf)
    make_chart_5(charts_dir, export_pdf=export_pdf)
    make_chart_6(charts_dir, export_pdf=export_pdf)
    print(f"ALL CHARTS GENERATED SUCCESSFULLY into: {output_dir} (PDF export: {export_pdf})")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Stargazing Charts')
    parser.add_argument('--output-dir', type=str, default=None, help='Output directory for charts')
    parser.add_argument('--pdf', action='store_true', default=False, help='Export printable PDF charts (default: False)')
    args = parser.parse_args()
    generate_all_charts(args.output_dir, export_pdf=args.pdf)

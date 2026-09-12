#!/usr/bin/env python3
"""Batch generator for pre-creating shared observation chart assets for all 110 Messier catalog objects.
Outputs to: shared/m{N}/
  - context.png (50°-65° Naked-eye orientation chart, mag <= 6.5, constellation stick lines, next-page finder box)
  - widefield_<equipment>.png (Screen-optimized 3:4 finder chart, mag <= 8.5, Telrad rings, hop labels, magnitude key)
  - eyepiece_dossier_<equipment>.png (Screen-optimized 4:3 eyepiece simulation pre-inverted 180° & technical dossier)
  - chart_<equipment>.png (Master A4 landscape chart combining Viewports A, B, and C)
"""

import os
import sys
import json
import math
import time
import argparse
from multiprocessing import Pool, cpu_count

# Setup environment & libraries
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
pylibs_dir = os.path.join(repo_root, '.pylibs')
if os.path.isdir(pylibs_dir) and pylibs_dir not in sys.path:
    sys.path.insert(0, pylibs_dir)

os.environ.setdefault('MPLCONFIGDIR', '/tmp/matplotlib')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, Polygon, Rectangle
import numpy as np

# Dimensions
ERA_PORTRAIT_FIGSIZE = (7.5, 10.0)   # 3:4 portrait (1500 x 2000 px @ 200 dpi)
ERA_SIDEBYSIDE_FIGSIZE = (10.0, 7.5) # 4:3 landscape (2000 x 1500 px @ 200 dpi)
A4_LANDSCAPE = (297.0 / 25.4, 210.0 / 25.4) # 11.69" x 8.27" @ 300 dpi

CACHE_DIR = os.path.join(repo_root, '.cache')
SHARED_DIR = os.path.join(repo_root, 'shared')
CATALOG_FILE = os.path.join(repo_root, 'catalogs', 'messier_catalog.json')

# Global dataset holders (populated in worker initializer or main)
stars_ra = None
stars_dec = None
stars_mag = None
stars_id = None
lines_segs = None
constellations_data = None
starnames_data = None

def init_worker():
    """Initializes global datasets in each worker process for efficient shared memory copy-on-write."""
    global stars_ra, stars_dec, stars_mag, stars_id, lines_segs, constellations_data, starnames_data
    stars_file = os.path.join(CACHE_DIR, 'stars.14.json')
    if not os.path.exists(stars_file):
        stars_file = os.path.join(CACHE_DIR, 'stars.json')
    with open(stars_file) as f:
        s_data = json.load(f)

    feats = s_data['features']
    stars_ra = np.array([f['geometry']['coordinates'][0] for f in feats], dtype=np.float32)
    stars_dec = np.array([f['geometry']['coordinates'][1] for f in feats], dtype=np.float32)
    stars_mag = np.array([f['properties']['mag'] for f in feats], dtype=np.float32)
    stars_id = np.array([f['id'] for f in feats], dtype=np.int32)

    with open(os.path.join(CACHE_DIR, 'constellations.lines.json')) as f:
        l_data = json.load(f)

    lines_segs = []
    for feat in l_data['features']:
        for seg in feat['geometry']['coordinates']:
            for i in range(len(seg)-1):
                p1, p2 = seg[i], seg[i+1]
                lines_segs.append((norm_ra(p1[0]), p1[1], norm_ra(p2[0]), p2[1]))

    with open(os.path.join(CACHE_DIR, 'constellations.json')) as f:
        constellations_data = json.load(f)

    starnames_file = os.path.join(CACHE_DIR, 'starnames.json')
    if os.path.exists(starnames_file):
        with open(starnames_file) as f:
            starnames_data = json.load(f)
    else:
        starnames_data = {}

def norm_ra(ra):
    return ((ra % 360.0) + 360.0) % 360.0

def d_ra(ra1, ra2):
    return (ra1 - ra2 + 180.0) % 360.0 - 180.0

def star_mag_to_size(mag, max_mag=8.5):
    if mag > max_mag:
        return None
    return max(0.8, round((max_mag + 0.2 - mag)**1.7 * 0.14 + 0.7, 2))

def draw_magnitude_legend(ax, loc='lower left', max_mag=8.5):
    """Draws standardized magnitude key in bottom corner."""
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

def draw_telrad_reticle(ax, cx, cy, label_pos=(2.1, 1.8)):
    """Draws standardized B/W Telrad & 5-deg Optical Finder rings."""
    ax.add_patch(Circle((cx, cy), 0.25, facecolor='none', edgecolor='#000000', linestyle='-', linewidth=1.1, zorder=8))
    ax.add_patch(Circle((cx, cy), 1.0, facecolor='none', edgecolor='#000000', linestyle='--', linewidth=0.9, zorder=8))
    ax.add_patch(Circle((cx, cy), 2.0, facecolor='none', edgecolor='#000000', linestyle='-.', linewidth=0.8, zorder=8))
    ax.add_patch(Circle((cx, cy), 2.5, facecolor='none', edgecolor='#333333', linestyle=':', linewidth=1.0, zorder=7))
    lx, ly = label_pos
    ax.text(cx + lx, cy + ly, "5° Finder / Telrad FOV", fontsize=7.0, color='#000000', fontweight='bold',
            bbox=dict(boxstyle='square,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=10)

def draw_target_marker(ax, tx, ty):
    """Draws crisp B/W bullseye target marker."""
    ax.plot(tx, ty, 'o', color='#000000', markersize=3.8, zorder=12)
    ax.plot(tx, ty, 'o', color='none', markeredgecolor='#000000', markeredgewidth=1.1, markersize=8.0, zorder=12)
    ax.plot([tx-0.3, tx+0.3], [ty, ty], color='#000000', linewidth=0.9, zorder=12)
    ax.plot([tx, tx], [ty-0.3, ty+0.3], color='#000000', linewidth=0.9, zorder=12)

def get_bright_stars_in_field(c_ra, c_dec, span_ra, span_dec, max_mag=4.5):
    """Finds and formats labels for prominent anchor stars in the field."""
    labeled = []
    cos_dec = math.cos(math.radians(c_dec))
    dra = (stars_ra - c_ra + 180.0) % 360.0 - 180.0
    ddec = stars_dec - c_dec
    mask = (np.abs(dra) < span_ra / 2.0) & (np.abs(ddec) < span_dec / 2.0) & (stars_mag <= max_mag)

    matching_idx = np.where(mask)[0]
    for idx in matching_idx:
        mag = float(stars_mag[idx])
        x = float(dra[idx] * cos_dec)
        y = float(ddec[idx])
        hid = str(int(stars_id[idx]))
        star_info = starnames_data.get(hid, {})
        name = star_info.get('name', '').strip()
        bayer = star_info.get('bayer', '').strip()
        c_code = star_info.get('c', '').strip()
        flam = star_info.get('flam', '').strip()

        if name:
            lbl = f"{name}\nmag {mag:.1f}"
            weight = 'bold'
            fsz = 7.5
        elif bayer:
            lbl = f"{bayer} {c_code}\nmag {mag:.1f}"
            weight = 'bold'
            fsz = 7.2
        elif flam:
            lbl = f"{flam} {c_code}\nmag {mag:.1f}"
            weight = 'normal'
            fsz = 6.8
        else:
            lbl = f"mag {mag:.1f}"
            weight = 'normal'
            fsz = 6.5
        labeled.append((x, y, lbl, fsz, weight))
    return labeled

def draw_context(ax, obj, span_ra=55.0, span_dec=50.0, vp_span=18.0):
    """Draws 50-65 deg naked eye orientation chart with constellation lines and next-page bounding box."""
    c_ra = obj['ra_deg']
    c_dec = obj['dec_deg']
    cos_dec = math.cos(math.radians(c_dec))

    x_min, x_max = -(span_ra / 2.0) * cos_dec, (span_ra / 2.0) * cos_dec
    y_min, y_max = -(span_dec / 2.0), (span_dec / 2.0)
    ax.set_xlim(x_max, x_min)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect('equal')
    ax.set_facecolor('#ffffff')

    # 1. Constellation lines
    for ra1, dec1, ra2, dec2 in lines_segs:
        dra1, dra2 = d_ra(ra1, c_ra), d_ra(ra2, c_ra)
        if abs(dra1) < span_ra*0.75 and abs(dec1 - c_dec) < span_dec*0.75 and \
           abs(dra2) < span_ra*0.75 and abs(dec2 - c_dec) < span_dec*0.75:
            x1 = dra1 * math.cos(math.radians(dec1))
            y1 = dec1 - c_dec
            x2 = dra2 * math.cos(math.radians(dec2))
            y2 = dec2 - c_dec
            ax.plot([x1, x2], [y1, y2], color='#475569', linewidth=1.1, linestyle='-', alpha=0.85, zorder=2)

    # 2. Naked-eye stars (mag <= 6.5)
    dra = (stars_ra - c_ra + 180.0) % 360.0 - 180.0
    ddec = stars_dec - c_dec
    c_mask = (np.abs(dra) < span_ra * 0.65) & (np.abs(ddec) < span_dec * 0.65) & (stars_mag <= 6.5)
    if np.any(c_mask):
        xs = dra[c_mask] * np.cos(np.radians(stars_dec[c_mask]))
        ys = ddec[c_mask]
        ms = np.maximum(1.0, (7.0 - stars_mag[c_mask])**1.8 * 0.45 + 0.8)
        ax.scatter(xs, ys, s=ms**2, color='#000000', zorder=5)

    # 3. Viewport Boundary Box for Next-Page Finder Chart
    vp_w_x = (vp_span / 2.0) * cos_dec
    vp_h_y = vp_span / 2.0
    corners_xy = [
        (-vp_w_x, -vp_h_y),
        ( vp_w_x, -vp_h_y),
        ( vp_w_x,  vp_h_y),
        (-vp_w_x,  vp_h_y)
    ]
    vp_poly = Polygon(corners_xy, closed=True, facecolor='#f8fafc', edgecolor='#000000',
                      linestyle='--', linewidth=1.8, alpha=0.35, zorder=6)
    ax.add_patch(vp_poly)
    bx = [pt[0] for pt in corners_xy] + [corners_xy[0][0]]
    by = [pt[1] for pt in corners_xy] + [corners_xy[0][1]]
    ax.plot(bx, by, color='#000000', linestyle='--', linewidth=1.8, zorder=7)

    badge_y = vp_h_y + 1.3 if (vp_h_y + 2.2) < y_max else vp_h_y - 1.5
    ax.text(0, badge_y, "[NEXT PAGE FINDER VIEWPORT]", fontsize=7.8, fontweight='bold',
            color='#000000', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#000000', linewidth=1.1), zorder=20)

    # 4. Target Marker
    draw_target_marker(ax, 0, 0)
    t_label = f"Target: {obj['m_id']}"
    if obj.get('common_name'):
        t_label += f" ({obj['common_name']})"
    ax.text(0.5, -1.2, t_label, fontsize=7.6, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.9), zorder=22)

    # 5. Neighboring Constellation Labels (kept safely inside frame)
    for feat in constellations_data['features']:
        coords = feat['geometry']['coordinates']
        c_r = norm_ra(coords[0])
        c_d = coords[1]
        dra_c = d_ra(c_r, c_ra)
        if abs(dra_c) < span_ra*0.48 and abs(c_d - c_dec) < span_dec*0.45:
            cx = dra_c * math.cos(math.radians(c_d))
            cy = c_d - c_dec
            if x_min*0.82 <= cx <= x_max*0.82 and y_min*0.82 <= cy <= y_max*0.82:
                cname = feat['properties']['name'].upper()
                ax.text(cx, cy, cname, fontsize=8.5, fontweight='bold', color='#0f172a',
                        ha='center', va='center',
                        bbox=dict(boxstyle='square,pad=0.22', facecolor='#ffffff', edgecolor='#94a3b8', linewidth=0.8, alpha=0.9),
                        zorder=12)

    # 6. Prominent anchor stars
    bright_stars = get_bright_stars_in_field(c_ra, c_dec, span_ra, span_dec, max_mag=3.8)
    for sx, sy, lbl, fsz, weight in bright_stars[:10]:
        if math.hypot(sx, sy) > 3.0: # don't overlap target center badge
            ax.text(sx + 0.4, sy + 0.4, lbl, fontsize=fsz, fontweight=weight, color='#000000',
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='#ffffff', edgecolor='none', alpha=0.8), zorder=14)

    # 7. Orientation indicator (N ↑, ← E)
    ax.text(0.035, 0.955, "N ↑\n← E", transform=ax.transAxes, fontsize=8.5, fontweight='bold', color='#000000',
            va='top', ha='left', bbox=dict(boxstyle='square,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=25)

    # 8. Note
    ax.text(0.965, 0.035, "Naked-Eye Stars to Mag 6.5\nConstellation Orientation Chart", transform=ax.transAxes,
            fontsize=6.8, color='#333333', ha='right', va='bottom',
            bbox=dict(boxstyle='square,pad=0.25', facecolor='#ffffff', edgecolor='#666666', linewidth=0.8), zorder=25)

    for spine in ax.spines.values():
        spine.set_color('#000000')
        spine.set_linewidth(1.1)
    ax.set_xticks([])
    ax.set_yticks([])

def draw_widefield(ax, obj, span_ra=18.0, span_dec=18.0, max_mag=8.5):
    """Draws screen-optimized wide-field finder chart with stars to mag 8.5 and Telrad rings."""
    c_ra = obj['ra_deg']
    c_dec = obj['dec_deg']
    cos_dec = math.cos(math.radians(c_dec))

    x_min, x_max = -(span_ra / 2.0) * cos_dec, (span_ra / 2.0) * cos_dec
    y_min, y_max = -(span_dec / 2.0), (span_dec / 2.0)
    ax.set_xlim(x_max, x_min)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect('equal')
    ax.set_facecolor('#ffffff')

    # 1. Constellation lines
    for ra1, dec1, ra2, dec2 in lines_segs:
        dra1, dra2 = d_ra(ra1, c_ra), d_ra(ra2, c_ra)
        if abs(dra1) < span_ra*1.2 and abs(dec1 - c_dec) < span_dec*1.1 and \
           abs(dra2) < span_ra*1.2 and abs(dec2 - c_dec) < span_dec*1.1:
            x1 = dra1 * math.cos(math.radians(dec1))
            y1 = dec1 - c_dec
            x2 = dra2 * math.cos(math.radians(dec2))
            y2 = dec2 - c_dec
            ax.plot([x1, x2], [y1, y2], color='#475569', linewidth=1.1, linestyle='-', alpha=0.9, zorder=2)

    # 2. Stars to mag 8.5
    dra = (stars_ra - c_ra + 180.0) % 360.0 - 180.0
    ddec = stars_dec - c_dec
    w_mask = (np.abs(dra) < span_ra) & (np.abs(ddec) < span_dec) & (stars_mag <= max_mag)
    if np.any(w_mask):
        xs = dra[w_mask] * np.cos(np.radians(stars_dec[w_mask]))
        ys = ddec[w_mask]
        ms = np.maximum(0.8, (max_mag + 0.2 - stars_mag[w_mask])**1.7 * 0.14 + 0.7)
        ax.scatter(xs, ys, s=ms**2, color='#000000', zorder=5)

    # 3. Telrad rings centered on target (0, 0)
    draw_telrad_reticle(ax, 0, 0, (2.1, 1.8))
    draw_target_marker(ax, 0, 0)

    # 4. Target Label Box
    title_text = f"{obj['m_id']}"
    if obj.get('common_name'):
        title_text += f" {obj['common_name'].upper()}"
    elif obj.get('ngc'):
        title_text += f" ({obj['ngc']})"
    title_text += f"\nMag {obj['v_mag']}V • {obj['type']}"

    ax.text(-0.5, -1.3, title_text, fontsize=7.8, fontweight='bold', color='#000000',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2), zorder=15)

    # 5. Prominent bright stars in the widefield
    bright_stars = get_bright_stars_in_field(c_ra, c_dec, span_ra, span_dec, max_mag=4.8)
    for sx, sy, lbl, fsz, weight in bright_stars[:12]:
        if math.hypot(sx, sy) > 2.2:
            ax.text(sx + 0.35, sy + 0.35, lbl, fontsize=fsz, fontweight=weight, color='#000000',
                    bbox=dict(boxstyle='round,pad=0.18', facecolor='#ffffff', edgecolor='#94a3b8', linewidth=0.6, alpha=0.9), zorder=14)

    # 6. Orientation Indicator
    ax.text(0.035, 0.955, "N ↑\n← E", transform=ax.transAxes, fontsize=8.5, fontweight='bold', color='#000000',
            va='top', ha='left', bbox=dict(boxstyle='square,pad=0.2', facecolor='#ffffff', edgecolor='#000000', linewidth=0.8), zorder=20)

    # 7. Magnitude Legend
    draw_magnitude_legend(ax, loc='lower left', max_mag=max_mag)

    for spine in ax.spines.values():
        spine.set_color('#000000')
        spine.set_linewidth(1.1)
    ax.set_xticks([])
    ax.set_yticks([])

def draw_eyepiece(ax, obj):
    """Draws realistic telescope eyepiece simulation (pre-inverted 180° for Newtonian reflector)."""
    fov_deg = obj['fov_deg']
    fl_mm = obj['eyepiece_fl_mm']
    mag_pow = obj['magnification']

    ax.set_facecolor('white')
    pad = 0.035 * (fov_deg / 0.52)
    ax.set_xlim(-fov_deg/2 - pad, fov_deg/2 + pad)
    ax.set_ylim(-fov_deg/2 - pad*1.2, fov_deg/2 + pad)
    ax.set_aspect('equal')

    # Eyepiece Circular Field Stop
    ax.add_patch(Circle((0, 0), fov_deg/2, facecolor='#ffffff', edgecolor='#000000', linewidth=1.8, zorder=1))
    ax.plot([0, 0], [-fov_deg/2, fov_deg/2], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)
    ax.plot([-fov_deg/2, fov_deg/2], [0, 0], color='#e2e8f0', linestyle=':', linewidth=0.8, zorder=2)

    # Field stars inside FOV - inverted 180°
    c_ra = obj['ra_deg']
    c_dec = obj['dec_deg']
    dra = (stars_ra - c_ra + 180.0) % 360.0 - 180.0
    ddec = stars_dec - c_dec
    dx_inv = -dra * np.cos(np.radians(stars_dec))
    dy_inv = -ddec
    r_arr = np.hypot(dx_inv, dy_inv)
    eye_mask = r_arr < (fov_deg / 2.0 - 0.006)
    if np.any(eye_mask):
        s_size = np.maximum(1.2, np.maximum(0.0, 12.5 - stars_mag[eye_mask])**2.1 * 0.85)
        ax.scatter(dx_inv[eye_mask], dy_inv[eye_mask], s=s_size, color='#000000', alpha=0.95, zorder=10)

    # Optical Morphology Simulation based on Type Category
    cat = obj.get('type_category', 'Other')
    major_deg = obj.get('major_arcmin', 5.0) / 60.0
    minor_deg = obj.get('minor_arcmin', major_deg * 60.0) / 60.0
    angle = obj.get('angle_deg', 0)
    seed = (obj['number'] * 41 + 17) % 100000

    if cat == 'GC':
        # Globular Cluster: Concentric soft core + exponential star swarm
        r_outer = max(0.08, min(fov_deg*0.42, major_deg * 0.8))
        ax.add_patch(Circle((0, 0), r_outer, facecolor='#f8fafc', edgecolor='#cbd5e1', linestyle=':', linewidth=0.8, zorder=11))
        ax.add_patch(Circle((0, 0), r_outer*0.55, facecolor='#f1f5f9', edgecolor='#94a3b8', linestyle='--', linewidth=0.8, zorder=12))
        ax.add_patch(Circle((0, 0), r_outer*0.25, facecolor='#e2e8f0', edgecolor='#64748b', linewidth=1.0, zorder=13))

        np.random.seed(seed)
        n_stars = min(220, max(90, int(180 / max(0.8, obj['v_mag'] / 5.5))))
        r_stars = np.random.exponential(r_outer * 0.28, n_stars)
        r_stars = np.clip(r_stars, 0, r_outer*0.95)
        th_stars = np.random.uniform(0, 2*np.pi, n_stars)
        ax.scatter(r_stars*np.cos(th_stars), r_stars*np.sin(th_stars),
                   s=np.random.uniform(1.2, 5.0, n_stars), color='#000000', alpha=0.92, zorder=14)

    elif cat == 'OC':
        # Open Cluster: Resolved cluster star scatter
        r_cluster = max(0.07, min(fov_deg*0.45, major_deg * 0.75))
        np.random.seed(seed)
        n_stars = min(140, max(35, int(100 / max(0.6, obj['v_mag'] - 3.5))))
        r_scat = np.random.normal(0, r_cluster * 0.42, (n_stars, 2))
        dist = np.hypot(r_scat[:, 0], r_scat[:, 1])
        valid = dist < r_cluster
        ax.scatter(r_scat[valid, 0], r_scat[valid, 1],
                   s=np.random.uniform(2.0, 7.5, np.sum(valid)), color='#000000', alpha=0.95, zorder=13)
        # Highlight central bright stars
        if np.sum(valid) > 0:
            ax.plot(r_scat[valid, 0][:3], r_scat[valid, 1][:3], 'o', color='#000000', markersize=3.8, zorder=15)

    elif cat == 'PN':
        # Planetary Nebula: Shell / ring / elliptical gas halo
        w_deg = max(0.03, min(fov_deg*0.35, major_deg * 1.5))
        h_deg = max(0.02, min(fov_deg*0.30, minor_deg * 1.5))
        ax.add_patch(Ellipse((0, 0), w_deg, h_deg, angle=angle, facecolor='#cbd5e1', edgecolor='#334151', linewidth=1.2, zorder=11))
        # Inner ring / hollow core
        ax.add_patch(Ellipse((0, 0), w_deg*0.55, h_deg*0.55, angle=angle, facecolor='#ffffff', edgecolor='#475569', linewidth=0.8, zorder=12))
        # Central star
        ax.plot(0, 0, 'o', color='#000000', markersize=1.8, zorder=14)

    elif cat == 'Galaxy':
        # Galaxy: Tilted elliptical halo, mid disk, bright nucleus
        w_deg = max(0.06, min(fov_deg*0.82, major_deg * 0.7))
        h_deg = max(0.03, min(fov_deg*0.50, minor_deg * 0.7))
        ax.add_patch(Ellipse((0, 0), w_deg, h_deg, angle=angle, facecolor='#f8fafc', edgecolor='#cbd5e1', linestyle='--', linewidth=0.8, zorder=11))
        ax.add_patch(Ellipse((0, 0), w_deg*0.58, h_deg*0.58, angle=angle, facecolor='#f1f5f9', edgecolor='#94a3b8', linestyle='--', linewidth=0.8, zorder=12))
        ax.add_patch(Ellipse((0, 0), w_deg*0.28, h_deg*0.28, angle=angle, facecolor='#e2e8f0', edgecolor='#64748b', linewidth=1.0, zorder=13))
        ax.add_patch(Circle((0, 0), max(0.012, w_deg*0.06), facecolor='#1e293b', edgecolor='#000000', linewidth=0.9, zorder=14))

    elif cat in ['Nebula', 'SNR']:
        # Diffuse Nebula / SNR: Layered nebulous clouds
        w_deg = max(0.08, min(fov_deg*0.75, major_deg * 0.75))
        h_deg = max(0.05, min(fov_deg*0.65, minor_deg * 0.75))
        ax.add_patch(Ellipse((0, 0), w_deg, h_deg, angle=angle, facecolor='#f1f5f9', edgecolor='#94a3b8', linestyle='--', linewidth=0.8, zorder=11))
        ax.add_patch(Ellipse((0, 0), w_deg*0.6, h_deg*0.6, angle=angle, facecolor='#e2e8f0', edgecolor='#64748b', linewidth=0.9, zorder=12))
        np.random.seed(seed)
        n_emb = 15
        r_emb = np.random.uniform(-w_deg*0.35, w_deg*0.35, n_emb)
        y_emb = np.random.uniform(-h_deg*0.35, h_deg*0.35, n_emb)
        ax.scatter(r_emb, y_emb, s=np.random.uniform(2.0, 5.0, n_emb), color='#000000', zorder=14)

    elif cat == 'Double Star':
        # Double Star (e.g. M40)
        ax.plot(-0.02, -0.015, 'o', color='#000000', markersize=5.5, zorder=15)
        ax.plot(0.02, 0.015, 'o', color='#000000', markersize=4.8, zorder=15)

    elif cat == 'Asterism':
        # Asterism (e.g. M73)
        pts = [(-0.02, -0.015), (0.015, -0.02), (0.025, 0.01), (-0.01, 0.025)]
        for px, py in pts:
            ax.plot(px, py, 'o', color='#000000', markersize=4.2, zorder=15)

    else:
        # Generic DSO fallback: Soft elliptical glow
        w_deg = max(0.05, min(fov_deg*0.5, major_deg * 0.6))
        h_deg = max(0.03, min(fov_deg*0.4, minor_deg * 0.6))
        ax.add_patch(Ellipse((0, 0), w_deg, h_deg, angle=angle, facecolor='#f1f5f9', edgecolor='#64748b', linewidth=1.0, zorder=11))
        ax.plot(0, 0, 'o', color='#000000', markersize=2.5, zorder=13)

    # Inversion Cardinal Markers
    ax.text(0, -fov_deg/2 + 0.035 * (fov_deg/0.52), "↓ N (Inverted)", fontsize=7.5, color='#000000', fontweight='bold', ha='center', zorder=25)
    ax.text(fov_deg/2 - 0.035 * (fov_deg/0.52), 0, "E →", fontsize=7.5, color='#000000', fontweight='bold', va='center', ha='right', zorder=25)
    ax.text(0, -fov_deg/2 - 0.020 * (fov_deg/0.52), f"{fl_mm:g}mm Eyepiece ({mag_pow}× Magnification, {int(fov_deg*60)}' True FOV)",
            fontsize=7.5, color='#000000', ha='center')
    ax.axis('off')

def get_dossier_text(obj, include_hop=True):
    """Generates location- and date-agnostic technical dossier markdown."""
    m_id = obj['m_id']
    ngc = obj.get('ngc', '')
    cname = obj.get('common_name', '')
    title_line = f"OBJECT DOSSIER: {m_id}"
    if ngc:
        title_line += f" ({ngc})"
    if cname:
        title_line += f" — {cname.upper()}"

    lines = [
        title_line,
        f"• Constellation: {obj['constellation']} | Type: {obj['type']}",
        f"• Magnitude: {obj['v_mag']}V | Dimensions: {obj['major_arcmin']}' × {obj['minor_arcmin']}'",
        f"• Distance: {obj['dist_str']}",
        f"• Difficulty: {obj['difficulty']} (Michael Swanson Rating)",
        f"• Telescope: Sky-Watcher Skyliner 200P (203/1200mm f/6 Dobsonian)",
        f"• Recommended Optics: {obj['recommended_eyepiece']}",
        "",
        "EYEPIECE QUICK REFERENCE & OBSERVING NOTES:"
    ]

    cat = obj.get('type_category', '')
    if cat == 'GC':
        lines.append(f"• Acquisition (20mm / 60×): Noticeable circular misty ball with")
        lines.append(f"  bright concentrated core floating against dark starry backdrop.")
        lines.append(f"• Core Resolution (12.5mm / 96×): Outer edges resolve into sharp,")
        lines.append(f"  glittering star chains; averted vision reveals rich granularity.")
    elif cat == 'OC':
        lines.append(f"• Wide Field Framing (20mm / 60×): Gorgeous scattered cluster")
        lines.append(f"  filling the field with diverse star magnitudes and shapes.")
        lines.append(f"• Close Inspection (12.5mm / 96×): Deepens sky contrast and splits")
        lines.append(f"  close stellar pairs within the rich central grouping.")
    elif cat == 'PN':
        lines.append(f"• Detection (20mm / 60×): Distinct smoky disc or oval with crisp")
        lines.append(f"  boundaries, standing out from surrounding point-like stars.")
        lines.append(f"• High Power Contrast (12.5mm / 96×): Outer shell brightens; subtle")
        lines.append(f"  brightness variations and central hollow emerge clearly.")
    elif cat == 'Galaxy':
        lines.append(f"• Primary Eyepiece (20mm / 60×): Ethereal oval glow with bright")
        lines.append(f"  condensed galactic nucleus; best framed in wide 50' field.")
        lines.append(f"• Core Contrast (12.5mm / 96×): Darkens background sky, aiding")
        lines.append(f"  detection of subtle dust lanes and companion structures.")
    else:
        lines.append(f"• Acquisition (20mm / 60×): Sweep field at low power until soft")
        lines.append(f"  contrast signature appears centered in the 50' view.")
        lines.append(f"• High Power (12.5mm / 96×): Center object and adjust focus for")
        lines.append(f"  optimal resolution of fine contrast features.")

    if include_hop:
        lines.append("")
        lines.append("STAR-HOPPING QUICK GUIDE:")
        lines.append(f"1. Locate anchor constellation {obj['constellation']} via Context Chart.")
        lines.append(f"2. Align Telrad reticle to target marker at RA {obj['ra_deg']:.2f}°, Dec {obj['dec_deg']:.2f}°.")
        lines.append(f"3. Center target in 20mm acquisition eyepiece, then swap to 12.5mm.")

    return "\n".join(lines)

def process_single_object(args_tuple):
    """Worker task to generate all 4 shared chart assets for one Messier object."""
    obj, equipment_slug, force, export_pdf = args_tuple
    m_id = obj['m_id']
    m_slug = m_id.lower()
    shared_obj_dir = os.path.join(SHARED_DIR, m_slug)
    os.makedirs(shared_obj_dir, exist_ok=True)

    f_ctx = os.path.join(shared_obj_dir, "context.png")
    f_wf  = os.path.join(shared_obj_dir, f"widefield_{equipment_slug}.png")
    f_ed  = os.path.join(shared_obj_dir, f"eyepiece_dossier_{equipment_slug}.png")
    f_ch  = os.path.join(shared_obj_dir, f"chart_{equipment_slug}.png")

    if not force and os.path.exists(f_ctx) and os.path.exists(f_wf) and os.path.exists(f_ed) and os.path.exists(f_ch):
        return f"[CACHE HIT] {m_id}"

    t0 = time.time()

    # 1. Context Orientation Chart
    if force or not os.path.exists(f_ctx):
        fig_ctx = plt.figure(figsize=ERA_PORTRAIT_FIGSIZE, facecolor='white', dpi=200)
        c_title = f"{m_id}"
        if obj.get('common_name'):
            c_title += f" {obj['common_name'].upper()}"
        c_title += f" — CONSTELLATION CONTEXT & ORIENTATION"
        fig_ctx.text(0.05, 0.965, c_title, fontsize=11, fontweight='bold', color='#000000')
        fig_ctx.text(0.05, 0.942, "Naked-Eye Sky (N ↑, E ←) | Constellation Lines & Next-Page Finder Viewport", fontsize=7.8, color='#333333')
        ax_ctx = fig_ctx.add_axes([0.05, 0.04, 0.90, 0.88])
        draw_context(ax_ctx, obj)
        plt.savefig(f_ctx, dpi=200, facecolor='white')
        plt.close(fig_ctx)

    # 2. Widefield Star-Hopping Chart
    if force or not os.path.exists(f_wf):
        fig_wf = plt.figure(figsize=ERA_PORTRAIT_FIGSIZE, facecolor='white', dpi=200)
        w_title = f"{m_id}"
        if obj.get('common_name'):
            w_title += f" {obj['common_name'].upper()}"
        w_title += f" — WIDE-FIELD STAR-HOPPING CHART"
        fig_wf.text(0.05, 0.965, w_title, fontsize=11, fontweight='bold', color='#000000')
        fig_wf.text(0.05, 0.942, "Upright Naked-Eye / Finder (N ↑, E ←) | Stars to Mag 8.5 | Telrad Reticle", fontsize=7.8, color='#333333')
        ax_wf = fig_wf.add_axes([0.05, 0.04, 0.90, 0.88])
        draw_widefield(ax_wf, obj)
        plt.savefig(f_wf, dpi=200, facecolor='white')
        plt.close(fig_wf)

    # 3. Eyepiece Simulation & Target Dossier Graphic
    if force or not os.path.exists(f_ed):
        fig_ed = plt.figure(figsize=ERA_SIDEBYSIDE_FIGSIZE, facecolor='white', dpi=200)
        ed_title = f"{m_id}"
        if obj.get('common_name'):
            ed_title += f" {obj['common_name'].upper()}"
        ed_title += f" — EYEPIECE SIMULATION & TARGET DOSSIER"
        fig_ed.text(0.05, 0.94, ed_title, fontsize=11, fontweight='bold', color='#000000')
        fig_ed.text(0.05, 0.905, "Sky-Watcher 200P Dobsonian | Negative Inverted 180° View (N ↓, E →)", fontsize=8.2, color='#333333')
        ax_eye = fig_ed.add_axes([0.05, 0.08, 0.42, 0.78])
        draw_eyepiece(ax_eye, obj)
        ax_dos = fig_ed.add_axes([0.51, 0.08, 0.44, 0.78])
        ax_dos.axis('off')
        dossier_str = get_dossier_text(obj, include_hop=False)
        ax_dos.text(0.0, 0.98, dossier_str, fontsize=8.0, color='#000000', fontfamily='monospace', va='top',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', edgecolor='#000000', linewidth=1.2))
        plt.savefig(f_ed, dpi=200, facecolor='white')
        plt.close(fig_ed)

    # 4. Master A4 Landscape Chart
    if force or not os.path.exists(f_ch):
        fig_m = plt.figure(figsize=A4_LANDSCAPE, facecolor='white', dpi=300)
        m_title = f"STAR-HOPPING FINDER CHART: {m_id}"
        if obj.get('common_name'):
            m_title += f" ({obj['common_name'].upper()})"
        m_title += f" — {obj['constellation'].upper()}"
        fig_m.text(0.035, 0.963, m_title, fontsize=11.5, fontweight='bold', color='#000000')
        fig_m.text(0.035, 0.936, "Sky-Watcher 200P Dobsonian (203/1200mm f/6) | Upright Finder (N ↑, E ←) & Negative Eyepiece 180° | B/W Toner-Saver Edition",
                   fontsize=7.8, color='#333333')

        ax_m_wf = fig_m.add_axes([0.035, 0.045, 0.485, 0.835])
        draw_widefield(ax_m_wf, obj)

        ax_m_eye = fig_m.add_axes([0.58, 0.485, 0.35, 0.395])
        draw_eyepiece(ax_m_eye, obj)

        ax_m_dos = fig_m.add_axes([0.545, 0.045, 0.420, 0.390])
        ax_m_dos.axis('off')
        ax_m_dos.text(0.0, 0.98, get_dossier_text(obj, include_hop=True), fontsize=6.8, color='#000000', fontfamily='monospace', va='top',
                      bbox=dict(boxstyle='round,pad=0.45', facecolor='#ffffff', edgecolor='#000000', linewidth=1.1))
        plt.savefig(f_ch, dpi=300, facecolor='white')
        if export_pdf:
            f_pdf = os.path.join(shared_obj_dir, f"chart_{equipment_slug}.pdf")
            plt.savefig(f_pdf, dpi=300, facecolor='white')
        plt.close(fig_m)

    dt = time.time() - t0
    return f"[RENDERED] {m_id} in {dt:.2f}s"

def main():
    parser = argparse.ArgumentParser(description='Pre-generate Shared Charts for all 110 Messier Objects')
    parser.add_argument('--equipment', type=str, default='skywatcher-skyliner-200p', help='Equipment profile slug')
    parser.add_argument('--force', action='store_true', help='Force regeneration of existing charts')
    parser.add_argument('--workers', type=int, default=max(1, min(4, cpu_count())), help='Parallel worker processes')
    parser.add_argument('--objects', type=str, default=None, help='Comma-separated subset of objects (e.g. M1,M42,M51)')
    parser.add_argument('--pdf', action='store_true', help='Also export A4 master PDFs')
    args = parser.parse_args()

    with open(CATALOG_FILE) as f:
        catalog_data = json.load(f)
    objects = catalog_data['objects']

    if args.objects:
        filter_ids = {o.strip().upper() for o in args.objects.split(',')}
        objects = [o for o in objects if o['m_id'].upper() in filter_ids]

    print(f"================================================================================")
    print(f"PRE-GENERATING SHARED ASSETS FOR {len(objects)} MESSIER OBJECTS")
    print(f"Equipment: {args.equipment} | Workers: {args.workers} | Force: {args.force}")
    print(f"================================================================================")

    # Initialize worker data
    init_worker()

    tasks = [(obj, args.equipment, args.force, args.pdf) for obj in objects]

    t_start = time.time()
    if args.workers > 1 and len(tasks) > 1:
        with Pool(processes=args.workers, initializer=init_worker) as pool:
            for res in pool.imap_unordered(process_single_object, tasks):
                print(f"  {res}")
    else:
        for task in tasks:
            res = process_single_object(task)
            print(f"  {res}")

    total_time = time.time() - t_start
    print(f"\n================================================================================")
    print(f"COMPLETED {len(objects)} OBJECTS IN {total_time:.1f}s")
    print(f"================================================================================")

if __name__ == '__main__':
    main()

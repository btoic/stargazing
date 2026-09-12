#!/usr/bin/env python3
"""
scripts/generate_collimation_diagrams.py - Generates visual educational diagrams
for Newtonian Dobsonian collimation tutorials (Sky-Watcher Skyliner 200P).
"""

import os
import sys
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
PYLIBS_DIR = os.path.join(REPO_ROOT, '.pylibs')
if PYLIBS_DIR not in sys.path:
    sys.path.insert(0, PYLIBS_DIR)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge, Rectangle, Polygon, FancyArrowPatch

def make_collimation_views_diagram(output_dir):
    """
    Renders the 4-step sight tube / Cheshire view progression:
    1. Misaligned
    2. Step 1: Secondary centered under focuser
    3. Step 2: Secondary tilt aimed at primary donut
    4. Step 3: Primary tilt aligned (perfect concentricity)
    """
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.4), dpi=300)
    fig.patch.set_facecolor('#ffffff')

    panels = [
        ("A. Initial State: Misaligned", -0.18, 0.12, -0.32, 0.25, -0.22, 0.18, False),
        ("B. Step 1: Secondary Centered", 0.0, 0.0, -0.25, 0.20, -0.20, 0.15, True),
        ("C. Step 2: Secondary Tilt Aligned", 0.0, 0.0, 0.0, 0.0, -0.22, 0.16, True),
        ("D. Step 3: Fully Collimated", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, True),
    ]

    for ax, (title, sec_dx, sec_dy, don_dx, don_dy, pup_dx, pup_dy, show_3_clips) in zip(axes, panels):
        ax.set_facecolor('#f8fafc')
        ax.set_aspect('equal')
        ax.set_xlim(-1.3, 1.3)
        ax.set_ylim(-1.3, 1.3)
        ax.axis('off')

        # 1. Focuser drawtube inner barrel (dark charcoal ring)
        focuser_rim = Circle((0, 0), 1.15, facecolor='#e2e8f0', edgecolor='#0f172a', linewidth=3.5, zorder=1)
        ax.add_patch(focuser_rim)
        inner_empty = Circle((0, 0), 1.05, facecolor='#1e293b', edgecolor='#334155', linewidth=1.5, zorder=2)
        ax.add_patch(inner_empty)

        # Crosshairs of sight tube / cheshire
        ax.axhline(0, color='#64748b', linestyle='--', linewidth=1.0, alpha=0.8, zorder=3)
        ax.axvline(0, color='#64748b', linestyle='--', linewidth=1.0, alpha=0.8, zorder=3)

        # 2. Secondary mirror outline
        sec_center = (sec_dx, sec_dy)
        sec_mirror = Circle(sec_center, 0.90, facecolor='#38bdf8', alpha=0.25, edgecolor='#0284c7', linewidth=2.5, zorder=4)
        ax.add_patch(sec_mirror)

        # 3. Reflection of Primary Mirror
        prim_center = (sec_dx * 0.5 + don_dx * 0.3, sec_dy * 0.5 + don_dy * 0.3)
        prim_refl = Circle(prim_center, 0.72, facecolor='#ffffff', edgecolor='#0284c7', linewidth=1.8, zorder=5)
        ax.add_patch(prim_refl)

        # Primary mirror clips (3 clips at 120 deg)
        if show_3_clips:
            angles = [30, 150, 270]
            for ang in angles:
                rad = np.radians(ang)
                cx = prim_center[0] + 0.72 * np.cos(rad)
                cy = prim_center[1] + 0.72 * np.sin(rad)
                clip = Rectangle((cx - 0.05, cy - 0.04), 0.10, 0.08, angle=ang-90,
                                 facecolor='#0f172a', edgecolor='#000000', linewidth=1.0, zorder=6)
                ax.add_patch(clip)
        else:
            # Misaligned: only 1 or 2 clips visible
            rad = np.radians(30)
            cx = prim_center[0] + 0.72 * np.cos(rad)
            cy = prim_center[1] + 0.72 * np.sin(rad)
            clip = Rectangle((cx - 0.05, cy - 0.04), 0.10, 0.08, angle=-60,
                             facecolor='#0f172a', edgecolor='#000000', linewidth=1.0, zorder=6)
            ax.add_patch(clip)

        # 4. Reflection of Secondary Mirror holder (dark silhouetted ellipse/circle)
        sec_refl_center = (pup_dx * 0.7, pup_dy * 0.7)
        sec_refl = Circle(sec_refl_center, 0.40, facecolor='#475569', alpha=0.6, edgecolor='#1e293b', linewidth=1.5, zorder=7)
        ax.add_patch(sec_refl)

        # 5. Primary Center Marker (Donut Ring)
        donut_pos = (don_dx, don_dy)
        donut_outer = Circle(donut_pos, 0.08, facecolor='#ffffff', edgecolor='#dc2626', linewidth=2.0, zorder=8)
        donut_inner = Circle(donut_pos, 0.03, facecolor='#ffffff', edgecolor='#dc2626', linewidth=1.0, zorder=9)
        ax.add_patch(donut_outer)
        ax.add_patch(donut_inner)

        # 6. Reflection of Eyepiece / Collimation Cap Pupil (dark center spot)
        pupil_pos = (pup_dx, pup_dy)
        pupil_outer = Circle(pupil_pos, 0.05, facecolor='#000000', edgecolor='#ffffff', linewidth=1.2, zorder=10)
        pupil_dot = Circle(pupil_pos, 0.015, facecolor='#ef4444', zorder=11)
        ax.add_patch(pupil_outer)
        ax.add_patch(pupil_dot)

        # Header Title Box
        ax.set_title(title, fontsize=9.5, fontweight='bold', pad=8, color='#0f172a')

    # Add explanatory legend along bottom
    fig.text(0.5, 0.04,
             "Key:  "
             "● Charcoal: Focuser Barrel  |  "
             "● Cyan Circle: Secondary Mirror Edge  |  "
             "● White Circle: Primary Mirror Reflection & 3 Clips\n"
             "● Red Ring: Primary Mirror Center Donut  |  "
             "● Black Spot: Observer Eye / Collimation Cap Pupil Reflection  |  "
             "+ Dashed: Sight Tube Crosshairs",
             ha='center', va='bottom', fontsize=8.2, color='#334155', fontweight='medium',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#f1f5f9', edgecolor='#cbd5e1', linewidth=1.0))

    plt.tight_layout(rect=[0, 0.10, 1, 0.98])
    png_path = os.path.join(output_dir, 'collimation_steps_view.png')
    pdf_path = os.path.join(output_dir, 'collimation_steps_view.pdf')
    plt.savefig(png_path, dpi=300, facecolor='white', bbox_inches='tight')
    plt.savefig(pdf_path, dpi=300, facecolor='white', bbox_inches='tight')
    plt.close()
    print(f"Generated: {png_path} and {pdf_path}")

def make_collimation_hardware_diagram(output_dir):
    """
    Renders mechanical diagrams of:
    1. Secondary spider hub & 3 tilt screws + 1 center bolt
    2. Primary mirror rear cell & 3 pairs of collimation/locking thumbscrews
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=300)
    fig.patch.set_facecolor('#ffffff')

    # Panel 1: Secondary Spider Hub (Looking down optical tube)
    ax1.set_facecolor('#f8fafc')
    ax1.set_aspect('equal')
    ax1.set_xlim(-1.4, 1.4)
    ax1.set_ylim(-1.4, 1.4)
    ax1.axis('off')
    ax1.set_title("SECONDARY MIRROR SPIDER & HUB\n(Front View Down Optical Tube)", fontsize=10, fontweight='bold', color='#0f172a', pad=10)

    # Tube outer rim
    tube_outer = Circle((0, 0), 1.25, facecolor='#e2e8f0', edgecolor='#0f172a', linewidth=3)
    tube_inner = Circle((0, 0), 1.18, facecolor='#1e293b', edgecolor='#475569', linewidth=1.5)
    ax1.add_patch(tube_outer)
    ax1.add_patch(tube_inner)

    # 4 Spider vanes
    ax1.plot([-1.18, 1.18], [0, 0], color='#cbd5e1', linewidth=2.5, zorder=2)
    ax1.plot([0, 0], [-1.18, 1.18], color='#cbd5e1', linewidth=2.5, zorder=2)

    # Central Hub
    hub = Circle((0, 0), 0.35, facecolor='#0f172a', edgecolor='#94a3b8', linewidth=2.0, zorder=3)
    ax1.add_patch(hub)

    # Center screw: Axial Depth / Rotation
    center_bolt = Circle((0, 0), 0.08, facecolor='#fbbf24', edgecolor='#b45309', linewidth=1.5, zorder=4)
    ax1.add_patch(center_bolt)
    ax1.plot([-0.05, 0.05], [0, 0], color='#000000', linewidth=1.5, zorder=5)
    ax1.plot([0, 0], [-0.05, 0.05], color='#000000', linewidth=1.5, zorder=5)

    # 3 Tilt Allen/Phillips screws (at 90, 210, 330 deg)
    angles = [90, 210, 330]
    for ang in angles:
        rad = np.radians(ang)
        sx = 0.22 * np.cos(rad)
        sy = 0.22 * np.sin(rad)
        screw = Circle((sx, sy), 0.045, facecolor='#38bdf8', edgecolor='#0284c7', linewidth=1.2, zorder=4)
        ax1.add_patch(screw)

    # Labels for Panel 1
    ax1.text(0, -0.65, "Center Screw (Phillips/Slotted):\nAxial Depth & Rotation Adjustment",
             ha='center', va='center', fontsize=8.0, color='#92400e', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#fef3c7', edgecolor='#f59e0b', linewidth=1.0))
    ax1.text(0, 0.72, "3× Tilt Screws (2.0/2.5 mm Allen):\nTilts Secondary toward Primary Donut",
             ha='center', va='center', fontsize=8.0, color='#0369a1', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#e0f2fe', edgecolor='#0284c7', linewidth=1.0))

    # Panel 2: Primary Mirror Rear Cell
    ax2.set_facecolor('#f8fafc')
    ax2.set_aspect('equal')
    ax2.set_xlim(-1.4, 1.4)
    ax2.set_ylim(-1.4, 1.4)
    ax2.axis('off')
    ax2.set_title("PRIMARY MIRROR CELL (REAR VIEW)\n(Bottom of Sky-Watcher 200P Tube)", fontsize=10, fontweight='bold', color='#0f172a', pad=10)

    # Rear cell plate
    cell_plate = Circle((0, 0), 1.25, facecolor='#334155', edgecolor='#0f172a', linewidth=3)
    ax2.add_patch(cell_plate)
    center_hub_rear = Circle((0, 0), 0.40, facecolor='#1e293b', edgecolor='#475569', linewidth=1.5)
    ax2.add_patch(center_hub_rear)

    # 3 Pairs of Thumbscrews at 0, 120, 240 deg
    pair_angles = [30, 150, 270]
    for ang in pair_angles:
        rad_col = np.radians(ang - 15)
        rad_lock = np.radians(ang + 15)

        # Collimation thumbscrew (large, silver/white, spring loaded)
        cx = 0.85 * np.cos(rad_col)
        cy = 0.85 * np.sin(rad_col)
        col_knob = Circle((cx, cy), 0.11, facecolor='#ffffff', edgecolor='#0284c7', linewidth=2.0, zorder=3)
        ax2.add_patch(col_knob)

        # Locking thumbscrew (smaller, black)
        lx = 0.85 * np.cos(rad_lock)
        ly = 0.85 * np.sin(rad_lock)
        lock_knob = Circle((lx, ly), 0.08, facecolor='#0f172a', edgecolor='#94a3b8', linewidth=1.5, zorder=3)
        ax2.add_patch(lock_knob)

    # Labels for Panel 2
    ax2.text(0, 0.35, "3× White/Silver Thumbscrews:\nCollimation Adjusters (Spring-Loaded)",
             ha='center', va='center', fontsize=8.0, color='#0284c7', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffff', edgecolor='#0284c7', linewidth=1.2))
    ax2.text(0, -0.35, "3× Small Black Screws:\nLocking Screws (Loosen before adjust!)",
             ha='center', va='center', fontsize=8.0, color='#cbd5e1', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#0f172a', edgecolor='#475569', linewidth=1.2))

    plt.tight_layout()
    png_path = os.path.join(output_dir, 'collimation_hardware_controls.png')
    pdf_path = os.path.join(output_dir, 'collimation_hardware_controls.pdf')
    plt.savefig(png_path, dpi=300, facecolor='white', bbox_inches='tight')
    plt.savefig(pdf_path, dpi=300, facecolor='white', bbox_inches='tight')
    plt.close()
    print(f"Generated: {png_path} and {pdf_path}")

def make_star_test_diagram(output_dir):
    """
    Renders the Star Test diffraction pattern diagnostic chart:
    1. Perfect Collimation (Inside Focus, At Focus Airy Disk, Outside Focus)
    2. Misaligned / Coma (Inside Focus, At Focus, Outside Focus)
    3. Pinched Optics (Astigmatic trefoil distortion)
    """
    fig, axes = plt.subplots(3, 3, figsize=(10.5, 9.8), dpi=300)
    fig.patch.set_facecolor('#ffffff')

    cols = ["Inside Focus (Intra-Focal)", "At Exact Focus (Airy Disk)", "Outside Focus (Extra-Focal)"]

    for row_idx in range(3):
        for col_idx in range(3):
            ax = axes[row_idx, col_idx]
            ax.set_facecolor('#0f172a')
            ax.set_aspect('equal')
            ax.set_xlim(-1.25, 1.25)
            ax.set_ylim(-1.25, 1.25)
            ax.axis('off')

            if row_idx == 0:
                ax.set_title(cols[col_idx], fontsize=9.2, fontweight='bold', color='#1e3a8a', pad=10)

            # ROW 0: PERFECT COLLIMATION
            if row_idx == 0:
                if col_idx == 1:
                    # In-focus Airy disk
                    airy_ring = Circle((0, 0), 0.22, facecolor='none', edgecolor='#ffffff', linewidth=1.0, alpha=0.5)
                    airy_core = Circle((0, 0), 0.08, facecolor='#ffffff', edgecolor='#ffffff')
                    ax.add_patch(airy_ring)
                    ax.add_patch(airy_core)
                    ax.plot([-0.95, 0.95], [0, 0], color='#ffffff', alpha=0.35, linewidth=0.8)
                    ax.plot([0, 0], [-0.95, 0.95], color='#ffffff', alpha=0.35, linewidth=0.8)
                    ax.text(0, -0.90, "Razor-sharp pinpoint\nwith 4 spider spikes", ha='center', va='center', color='#38bdf8', fontsize=7.2, fontweight='bold')
                else:
                    # Defocused concentric rings
                    for r in [0.25, 0.45, 0.65, 0.85, 1.05]:
                        ring = Circle((0, 0), r, facecolor='none', edgecolor='#ffffff', linewidth=1.3, alpha=0.85)
                        ax.add_patch(ring)
                    # Central dark shadow centered
                    sec_shadow = Circle((0, 0), 0.32, facecolor='#0f172a', edgecolor='#64748b', linewidth=1.5, zorder=5)
                    ax.add_patch(sec_shadow)
                    # Spider vanes
                    ax.plot([-1.05, 1.05], [0, 0], color='#0f172a', linewidth=3.0, zorder=4)
                    ax.plot([0, 0], [-1.05, 1.05], color='#0f172a', linewidth=3.0, zorder=4)
                    ax.text(0, -0.88, "Evenly spaced rings\nCentered shadow", ha='center', va='center', color='#4ade80', fontsize=7.2, fontweight='bold')

            # ROW 1: MISCOLLIMATED (COMA / ASYMMETRIC)
            elif row_idx == 1:
                sign = 1 if col_idx == 0 else -1
                if col_idx == 1:
                    # In-focus Coma flare (comet tail)
                    airy_core = Circle((-0.15, 0), 0.09, facecolor='#ffffff', edgecolor='#ffffff')
                    ax.add_patch(airy_core)
                    # Big flared wedge
                    flare = Wedge((-0.15, 0), 0.70, -45, 45, facecolor='#ffffff', alpha=0.45)
                    flare_core = Wedge((-0.15, 0), 0.40, -35, 35, facecolor='#ffffff', alpha=0.65)
                    ax.add_patch(flare)
                    ax.add_patch(flare_core)
                    ax.annotate("Comet-like\ncoma tail", xy=(0.35, 0), xytext=(0.60, 0.50),
                                color='#ef4444', fontsize=7.5, fontweight='bold',
                                arrowprops=dict(arrowstyle="->", color='#ef4444', lw=1.2))
                else:
                    # Defocused asymmetric rings: center shifts with radius!
                    radii = [0.25, 0.45, 0.65, 0.85, 1.05]
                    theta = np.linspace(0, 2*np.pi, 200)
                    shift_direction = sign * 0.35
                    for r in radii:
                        # Rings bunch tightly on one side and stretch on the other
                        cx = (shift_direction * (1.0 - r/1.2))
                        x = cx + r * np.cos(theta) * (1.0 + sign * 0.18 * np.cos(theta))
                        y = r * np.sin(theta)
                        ax.plot(x, y, color='#ffffff', linewidth=1.3, alpha=0.85)

                    # Secondary shadow shifted dramatically towards the bunched side
                    shadow_x = sign * 0.48
                    sec_shadow = Circle((shadow_x, 0), 0.30, facecolor='#0f172a', edgecolor='#ef4444', linewidth=1.8, zorder=5)
                    ax.add_patch(sec_shadow)
                    ax.plot([-1.05, 1.05], [0, 0], color='#0f172a', linewidth=2.5, zorder=4)

                    # Annotations
                    ax.annotate("Shadow offset!", xy=(shadow_x, 0.25), xytext=(shadow_x, 0.70),
                                color='#ef4444', fontsize=7.2, fontweight='bold', ha='center',
                                arrowprops=dict(arrowstyle="->", color='#ef4444', lw=1.2))
                    ax.text(-sign * 0.50, -0.88, "Bunched on one side\nStretched on other", ha='center', va='center', color='#f87171', fontsize=7.0, fontweight='bold')

            # ROW 2: PINCHED OPTICS (TREFOIL DISTORTION)
            elif row_idx == 2:
                if col_idx == 1:
                    # In-focus triangular flare
                    poly = Polygon([(0, 0.22), (-0.18, -0.12), (0.18, -0.12)], facecolor='#ffffff', edgecolor='#ffffff')
                    ax.add_patch(poly)
                    # 3 flared lobes
                    for a in [90, 210, 330]:
                        rad = np.radians(a)
                        ax.plot([0, 0.55*np.cos(rad)], [0, 0.55*np.sin(rad)], color='#ffffff', alpha=0.5, linewidth=2.0)
                    ax.annotate("Triangular star\n(not round)", xy=(0, 0.15), xytext=(0.50, 0.55),
                                color='#fbbf24', fontsize=7.2, fontweight='bold',
                                arrowprops=dict(arrowstyle="->", color='#fbbf24', lw=1.2))
                else:
                    # Defocused 3-lobed trefoil rings
                    theta = np.linspace(0, 2*np.pi, 200)
                    for r in [0.30, 0.55, 0.80, 1.05]:
                        r_trefoil = r * (1.0 + 0.25 * np.cos(3 * theta))
                        x = r_trefoil * np.cos(theta)
                        y = r_trefoil * np.sin(theta)
                        ax.plot(x, y, color='#ffffff', linewidth=1.3, alpha=0.85)

                    sec_shadow = Circle((0, 0), 0.28, facecolor='#0f172a', edgecolor='#fbbf24', linewidth=1.5, zorder=5)
                    ax.add_patch(sec_shadow)
                    ax.plot([-1.05, 1.05], [0, 0], color='#0f172a', linewidth=2.5, zorder=4)
                    ax.plot([0, 0], [-1.05, 1.05], color='#0f172a', linewidth=2.5, zorder=4)
                    ax.text(0, -0.88, "Distinct 3-corner shape\nMirror clips too tight!", ha='center', va='center', color='#fbbf24', fontsize=7.0, fontweight='bold')

        # Row Badges on the left
        row_badges = [
            ("✓ PERFECT COLLIMATION\nConcentric Bullseye", '#15803d', '#dcfce7'),
            ("✗ MISCOLLIMATED (COMA)\nAsymmetric Decentered Flare", '#b91c1c', '#fee2e2'),
            ("✗ PINCHED PRIMARY MIRROR\nTriangular Trefoil Distortion", '#b45309', '#fef3c7'),
        ]
        text_str, border_c, bg_c = row_badges[row_idx]
        axes[row_idx, 0].text(-1.18, 1.15, text_str, fontsize=7.8, fontweight='bold', color=border_c, va='top',
                              bbox=dict(boxstyle='round,pad=0.3', facecolor=bg_c, edgecolor=border_c, linewidth=1.2))

    plt.tight_layout()
    png_path = os.path.join(output_dir, 'star_test_patterns.png')
    pdf_path = os.path.join(output_dir, 'star_test_patterns.pdf')
    plt.savefig(png_path, dpi=300, facecolor='white', bbox_inches='tight')
    plt.savefig(pdf_path, dpi=300, facecolor='white', bbox_inches='tight')
    plt.close()
    print(f"Generated improved: {png_path} and {pdf_path}")

def generate_all():
    img_dir = os.path.join(REPO_ROOT, 'tutorials', 'images')
    os.makedirs(img_dir, exist_ok=True)
    make_collimation_views_diagram(img_dir)
    make_collimation_hardware_diagram(img_dir)
    make_star_test_diagram(img_dir)
    print("All collimation diagrams successfully generated in:", img_dir)

if __name__ == '__main__':
    generate_all()

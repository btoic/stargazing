#!/usr/bin/env python3
"""
scripts/run_observation_planner.py - End-to-End Observation Session Planner

Orchestrates ephemeris calculation, sky chart generation, and 2-page master plan PDF compilation.
"""

import os
import sys
import argparse
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
PYLIBS_DIR = os.path.join(REPO_ROOT, '.pylibs')

def run():
    parser = argparse.ArgumentParser(description="Run Stargazing Observation Planner Pipeline")
    parser.add_argument("--location", type=str, default="dvigrad", help="Location slug (matches locations/<slug>.md)")
    parser.add_argument("--equipment", type=str, default="skywatcher-skyliner-200p", help="Equipment slug (matches equipment/<slug>.md)")
    parser.add_argument("--date", type=str, default="2026-09-12", help="Observation date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory (defaults to observations/<location>-<date>)")

    args = parser.parse_args()

    if args.output_dir is None:
        session_folder = f"{args.location}-{args.date}"
        output_dir = os.path.join(REPO_ROOT, "observations", session_folder)
    else:
        output_dir = os.path.abspath(args.output_dir)

    os.makedirs(output_dir, exist_ok=True)
    charts_dir = os.path.join(output_dir, "charts")
    os.makedirs(charts_dir, exist_ok=True)

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{PYLIBS_DIR}:{env.get('PYTHONPATH', '')}"
    env["MPLCONFIGDIR"] = "/tmp/matplotlib"

    python_bin = sys.executable

    print(f"\n=======================================================")
    print(f"STARGAZING OBSERVATION PLANNER")
    print(f"Location:  {args.location}")
    print(f"Equipment: {args.equipment}")
    print(f"Date:      {args.date}")
    print(f"Output:    {output_dir}")
    print(f"=======================================================\n")

    # Step 1: Calculate ephemeris
    print(">>> Step 1: Calculating solar and lunar ephemeris...")
    cmd_eph = [
        python_bin,
        os.path.join(SCRIPT_DIR, "calculate_ephemeris.py"),
        "--date", args.date
    ]
    subprocess.run(cmd_eph, env=env, check=True)

    # Step 2: Generate all charts
    print(">>> Step 2: Generating All-Sky Planisphere & Toner-Saver Negative Finder Charts...")
    cmd_charts = [
        python_bin,
        os.path.join(SCRIPT_DIR, "generate_charts.py"),
        "--output-dir", output_dir
    ]
    subprocess.run(cmd_charts, env=env, check=True)

    # Step 3: Build Master Plan PDF
    print(">>> Step 3: Compiling 2-Page Master Plan PDF...")
    cmd_pdf = [
        python_bin,
        os.path.join(SCRIPT_DIR, "build_plan_pdf.py"),
        "--output-dir", output_dir
    ]
    subprocess.run(cmd_pdf, env=env, check=True)

    # Step 4: Build EPUB Field Guide for E-Readers
    print(">>> Step 4: Compiling E-Reader EPUB Field Guide...")
    cmd_epub = [
        python_bin,
        os.path.join(SCRIPT_DIR, "build_session_epub.py"),
        "--session-dir", output_dir
    ]
    subprocess.run(cmd_epub, env=env, check=True)

    print(f"\n=======================================================")
    print(f"PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"Master PDF: {os.path.join(output_dir, 'STARGAZING_PLAN.pdf')}")
    print(f"EPUB Book:  {os.path.join(output_dir, 'STARGAZING_FIELD_GUIDE.epub')}")
    print(f"Charts:     {charts_dir}")
    print(f"=======================================================\n")

if __name__ == "__main__":
    run()

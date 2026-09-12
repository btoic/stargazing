#!/usr/bin/env python3
"""Builds a comprehensive, unified Messier catalog JSON file (catalogs/messier_catalog.json)
combining Stellarium DSO data, Astropy coordinates & constellations, and Michael Swanson difficulty ratings.
"""

import os
import sys
import json
import re
import urllib.request

# Insert vendor lib path if available
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
pylibs_dir = os.path.join(repo_root, '.pylibs')
if os.path.isdir(pylibs_dir) and pylibs_dir not in sys.path:
    sys.path.insert(0, pylibs_dir)

from astropy.coordinates import SkyCoord
import astropy.units as u

def get_stellarium_messier():
    url = "https://raw.githubusercontent.com/Stellarium/stellarium/master/nebulae/default/catalog.txt"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (StargazingBot/1.0)"})
    stellarium = {}
    with urllib.request.urlopen(req, timeout=20) as resp:
        for line in resp:
            line = line.decode("utf-8").strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 19:
                m_str = parts[18].strip()
                if m_str and m_str.isdigit():
                    m_num = int(m_str)
                    if 1 <= m_num <= 110:
                        stellarium[m_num] = {
                            "ra": float(parts[1]),
                            "dec": float(parts[2]),
                            "b_mag": float(parts[3]) if parts[3] and parts[3] != "99.0" else None,
                            "v_mag": float(parts[4]) if parts[4] and parts[4] != "99.0" else None,
                            "type_code": parts[5],
                            "morph": parts[6],
                            "major_arcmin": float(parts[7]) if parts[7] else 0.0,
                            "minor_arcmin": float(parts[8]) if parts[8] else 0.0,
                            "angle": int(parts[9]) if parts[9] else 0,
                            "dist_kpc": float(parts[14]) if parts[14] else None,
                            "ngc": int(parts[16]) if parts[16] else None
                        }
    return stellarium

def classify_type(type_code, name_type):
    nt = name_type.lower()
    tc = type_code.upper()
    if "globular" in nt or tc == "GC":
        return "Globular Cluster", "GC"
    if "open" in nt or tc == "OC":
        return "Open Cluster", "OC"
    if "planetary" in nt or tc == "PN":
        return "Planetary Nebula", "PN"
    if "supernova" in nt or tc == "SNR":
        return "Supernova Remnant", "SNR"
    if "galaxy" in nt or tc in ["GX", "G", "SA", "SC"]:
        if "spiral" in nt:
            return "Spiral Galaxy", "Galaxy"
        elif "elliptical" in nt:
            return "Elliptical Galaxy", "Galaxy"
        elif "lenticular" in nt:
            return "Lenticular Galaxy", "Galaxy"
        return "Galaxy", "Galaxy"
    if "nebula" in nt or tc in ["HII", "EN", "RN", "DN", "NB"]:
        return "Diffuse Nebula", "Nebula"
    if "star cloud" in nt:
        return "Star Cloud", "Star Cloud"
    if "double star" in nt:
        return "Double Star", "Double Star"
    if "asterism" in nt or "group" in nt:
        return "Asterism", "Asterism"
    return name_type, "Other"

def main():
    print("Fetching Stellarium DSO catalog...")
    st_data = get_stellarium_messier()
    print(f"Loaded {len(st_data)} Messier objects from Stellarium.")

    ratings_path = os.path.join(repo_root, "catalogs", "messier_difficulty_ratings.json")
    with open(ratings_path) as f:
        ratings_data = json.load(f)

    catalog = []
    for item in ratings_data["objects"]:
        m_num = item["number"]
        m_id = item["m_id"]
        raw_name = item["name"]
        swanson_diff = item["difficulty"]
        raw_type = item["type"]

        st_obj = st_data.get(m_num, {})
        ra = st_obj.get("ra", 0.0)
        dec = st_obj.get("dec", 0.0)
        v_mag = st_obj.get("v_mag", 8.0)
        major = st_obj.get("major_arcmin", 5.0)
        minor = st_obj.get("minor_arcmin", major)
        if minor == 0.0:
            minor = major
        angle = st_obj.get("angle", 0)
        dist_kpc = st_obj.get("dist_kpc")

        # Constellation lookup via Astropy
        sc = SkyCoord(ra=ra*u.deg, dec=dec*u.deg)
        constellation = sc.get_constellation()

        # Parse NGC and Common Name
        m_ngc = re.match(r"^(NGC|IC)\s*(\d+)\s*(.*)", raw_name)
        if m_ngc:
            ngc_str = f"{m_ngc.group(1)} {m_ngc.group(2)}"
            common_name = m_ngc.group(3).strip()
        else:
            ngc_num = st_obj.get("ngc")
            ngc_str = f"NGC {ngc_num}" if ngc_num else ""
            common_name = raw_name.strip()

        # Handle specific well-known names
        if m_id == "M24":
            ngc_str = "IC 4715"
            common_name = "Sagittarius Star Cloud"
        elif m_id == "M40":
            ngc_str = "Winnecke 4"
            common_name = "Double Star"
        elif m_id == "M45":
            ngc_str = "Melotte 22"
            common_name = "Pleiades"
        elif m_id == "M73":
            ngc_str = "NGC 6994"
            common_name = "Four-Star Asterism"
        elif m_id == "M102":
            ngc_str = "NGC 5866"
            common_name = "Spindle Galaxy"

        # Type classification
        type_desc, type_cat = classify_type(st_obj.get("type_code", ""), raw_type)

        # Distance formatting
        if dist_kpc is not None and dist_kpc > 0:
            if dist_kpc >= 1000:
                dist_str = f"~{dist_kpc/1000:.1f} million light-years"
            elif dist_kpc >= 1.0:
                dist_str = f"~{int(dist_kpc*3262):,} light-years"
            else:
                dist_str = f"~{int(dist_kpc*3262)} light-years"
        else:
            dist_str = "Distance varies"

        # Eyepiece recommendation for Sky-Watcher Skyliner 200P (203/1200mm f/6)
        # 20mm Super: 60x, 50' FOV (for objects > 15' or sprawling nebulae/clusters)
        # 12.5mm Plössl: 96x, 31' FOV (for compact clusters, planetary nebulae, compact galaxies)
        if major >= 15.0 or type_cat in ["Nebula", "Star Cloud"] or m_id in ["M31", "M33", "M42", "M44", "M45"]:
            eyepiece_fl = 20.0
            magnification = 60
            fov_deg = 0.83
            eyepiece_label = "20mm Eyepiece (60× Magnification, 50' True FOV)"
        else:
            eyepiece_fl = 12.5
            magnification = 96
            fov_deg = 0.52
            eyepiece_label = "12.5mm Eyepiece (96× Magnification, 31' True FOV)"

        catalog_entry = {
            "m_id": m_id,
            "number": m_num,
            "ngc": ngc_str,
            "common_name": common_name,
            "full_name": f"{m_id} ({common_name})" if common_name else f"{m_id} ({ngc_str})" if ngc_str else m_id,
            "type": type_desc,
            "type_category": type_cat,
            "constellation": constellation,
            "difficulty": swanson_diff,
            "ra_deg": round(ra, 5),
            "dec_deg": round(dec, 5),
            "v_mag": round(v_mag, 1) if v_mag else None,
            "major_arcmin": round(major, 1),
            "minor_arcmin": round(minor, 1),
            "angle_deg": angle,
            "dist_str": dist_str,
            "recommended_eyepiece": eyepiece_label,
            "eyepiece_fl_mm": eyepiece_fl,
            "magnification": magnification,
            "fov_deg": fov_deg
        }
        catalog.append(catalog_entry)

    out_file = os.path.join(repo_root, "catalogs", "messier_catalog.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"count": len(catalog), "objects": catalog}, f, indent=2)

    print(f"Successfully generated {out_file} with {len(catalog)} objects.")

if __name__ == "__main__":
    main()

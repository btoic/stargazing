#!/usr/bin/env python3
"""
scripts/calculate_ephemeris.py - Ephemeris & Twilight Calculator

Calculates sunset, twilight phases, moon phase/rise/set, and target Alt/Az positions
for any given observation location and timeframe.
"""

import os
import sys
import argparse
from datetime import datetime, timezone, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
PYLIBS_DIR = os.path.join(REPO_ROOT, '.pylibs')
if PYLIBS_DIR not in sys.path:
    sys.path.insert(0, PYLIBS_DIR)

from astropy.coordinates import EarthLocation, AltAz, SkyCoord, get_sun, get_body
from astropy.time import Time
import astropy.units as u
import numpy as np

def calculate_session_ephemeris(lat, lon, elevation_m, date_str, tz_offset_hours=2.0):
    """
    Computes solar twilight phases and lunar parameters for a given location and date.
    date_str: 'YYYY-MM-DD'
    tz_offset_hours: hours ahead of UTC (e.g. 2.0 for CEST)
    """
    loc = EarthLocation(lat=lat*u.deg, lon=lon*u.deg, height=elevation_m*u.m)
    
    # 24-hour sweep in 5-minute increments starting at noon local time
    noon_local = datetime.strptime(date_str + ' 12:00:00', '%Y-%m-%d %H:%M:%S')
    noon_utc = noon_local - timedelta(hours=tz_offset_hours)
    
    times_utc = [noon_utc + timedelta(minutes=5*i) for i in range(288)]
    astro_times = Time(times_utc)
    altaz_frame = AltAz(obstime=astro_times, location=loc)
    
    # Solar altitudes
    sun_icrs = get_sun(astro_times)
    sun_coords = sun_icrs.transform_to(altaz_frame)
    sun_alts = sun_coords.alt.deg
    
    # Lunar altitudes and illumination
    moon_icrs = get_body('moon', astro_times)
    moon_coords = moon_icrs.transform_to(altaz_frame)
    moon_alts = moon_coords.alt.deg
    
    # Calculate key transition times
    def find_crossing(alts, threshold, direction='down'):
        for i in range(len(alts)-1):
            if direction == 'down' and alts[i] >= threshold > alts[i+1]:
                frac = (alts[i] - threshold) / (alts[i] - alts[i+1])
                t_cross = times_utc[i] + timedelta(minutes=5*frac) + timedelta(hours=tz_offset_hours)
                return t_cross
            elif direction == 'up' and alts[i] <= threshold < alts[i+1]:
                frac = (threshold - alts[i]) / (alts[i+1] - alts[i])
                t_cross = times_utc[i] + timedelta(minutes=5*frac) + timedelta(hours=tz_offset_hours)
                return t_cross
        return None

    sunset = find_crossing(sun_alts, 0.0, 'down')
    civil_dusk = find_crossing(sun_alts, -6.0, 'down')
    naut_dusk = find_crossing(sun_alts, -12.0, 'down')
    astro_dark = find_crossing(sun_alts, -18.0, 'down')
    moonset = find_crossing(moon_alts, 0.0, 'down')
    
    # Moon phase (illumination fraction)
    elongation = sun_icrs.separation(moon_icrs).deg
    moon_phase_pct = (1.0 - np.cos(np.radians(elongation))) / 2.0 * 100.0
    
    return {
        'sunset': sunset,
        'civil_dusk': civil_dusk,
        'naut_dusk': naut_dusk,
        'astro_darkness': astro_dark,
        'moonset': moonset,
        'moon_illumination_pct': moon_phase_pct[len(moon_phase_pct)//2],
        'times_utc': times_utc,
        'sun_alts': sun_alts,
        'moon_alts': moon_alts
    }

def print_summary(eph, date_str):
    print(f"\n=======================================================")
    print(f"CELESTIAL EPHEMERIS SUMMARY: {date_str}")
    print(f"=======================================================")
    print(f"• Sunset:                  {eph['sunset'].strftime('%H:%M:%S') if eph['sunset'] else 'N/A'} CEST")
    print(f"• Civil Twilight End:      {eph['civil_dusk'].strftime('%H:%M:%S') if eph['civil_dusk'] else 'N/A'} CEST (Sun -6°)")
    print(f"• Nautical Twilight End:   {eph['naut_dusk'].strftime('%H:%M:%S') if eph['naut_dusk'] else 'N/A'} CEST (Sun -12°)")
    print(f"• True Astro Darkness:     {eph['astro_darkness'].strftime('%H:%M:%S') if eph['astro_darkness'] else 'N/A'} CEST (Sun -18°)")
    print(f"• Moonset:                 {eph['moonset'].strftime('%H:%M:%S') if eph['moonset'] else 'N/A'} CEST")
    print(f"• Moon Illumination:       {eph['moon_illumination_pct']:.1f}%")
    print(f"=======================================================\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Calculate solar/lunar ephemeris')
    parser.add_argument('--lat', type=float, default=45.12637, help='Latitude (deg N)')
    parser.add_argument('--lon', type=float, default=13.81296, help='Longitude (deg E)')
    parser.add_argument('--elevation', type=float, default=143.0, help='Elevation (m ASL)')
    parser.add_argument('--date', type=str, default='2026-09-12', help='Date (YYYY-MM-DD)')
    parser.add_argument('--tz-offset', type=float, default=2.0, help='Timezone offset from UTC in hours')
    
    args = parser.parse_args()
    eph = calculate_session_ephemeris(args.lat, args.lon, args.elevation, args.date, args.tz_offset)
    print_summary(eph, args.date)

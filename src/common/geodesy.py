"""WGS84 geodetic <-> ECEF conversions and ECEF-difference-to-ENU rotation.

Standard closed-form formulas (Bowring's method for ECEF->geodetic); no
external geodesy dependency, since this project only needs meter-scale
accuracy (SPP error, thresholds at 2/5/10 m), not survey-grade precision.
"""

import math

WGS84_A = 6378137.0
WGS84_F = 1 / 298.257223563
WGS84_E2 = WGS84_F * (2 - WGS84_F)


def llh2ecef(lat_deg, lon_deg, height_m):
    """Geodetic (lat, lon, height) -> ECEF (x, y, z), all in meters/degrees."""
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    sin_lat, cos_lat = math.sin(lat), math.cos(lat)
    n = WGS84_A / math.sqrt(1 - WGS84_E2 * sin_lat**2)
    x = (n + height_m) * cos_lat * math.cos(lon)
    y = (n + height_m) * cos_lat * math.sin(lon)
    z = (n * (1 - WGS84_E2) + height_m) * sin_lat
    return x, y, z


def ecef2llh(x, y, z):
    """ECEF (x, y, z) -> geodetic (lat_deg, lon_deg, height_m), Bowring's method."""
    lon = math.atan2(y, x)
    p = math.hypot(x, y)
    lat = math.atan2(z, p * (1 - WGS84_E2))
    for _ in range(5):
        sin_lat = math.sin(lat)
        n = WGS84_A / math.sqrt(1 - WGS84_E2 * sin_lat**2)
        height = p / math.cos(lat) - n
        lat = math.atan2(z, p * (1 - WGS84_E2 * n / (n + height)))
    sin_lat = math.sin(lat)
    n = WGS84_A / math.sqrt(1 - WGS84_E2 * sin_lat**2)
    height = p / math.cos(lat) - n
    return math.degrees(lat), math.degrees(lon), height


def ecef_diff_to_enu(dx, dy, dz, ref_lat_deg, ref_lon_deg):
    """Rotate an ECEF difference vector into local East-North-Up at a reference point."""
    lat = math.radians(ref_lat_deg)
    lon = math.radians(ref_lon_deg)
    sin_lat, cos_lat = math.sin(lat), math.cos(lat)
    sin_lon, cos_lon = math.sin(lon), math.cos(lon)

    e = -sin_lon * dx + cos_lon * dy
    n = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
    u = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
    return e, n, u

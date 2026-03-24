from __future__ import annotations

import math


EARTH_RADIUS_METERS = 6_370_997.0
LENGTH_OF_DEGREE = (EARTH_RADIUS_METERS * math.pi) / 180.0

ATS_STANDARD_PARALLEL_1_DEG = 33.0
ATS_STANDARD_PARALLEL_2_DEG = 45.0
ATS_ORIGIN_LAT_DEG = 39.0
ATS_ORIGIN_LON_DEG = -96.0
ATS_MAP_FACTOR_X = 0.000176689948
ATS_MAP_FACTOR_Z = -0.00017706234


def _deg_to_rad(value: float) -> float:
    return value * math.pi / 180.0


def _rad_to_deg(value: float) -> float:
    return value * 180.0 / math.pi


def _lcc_constants() -> tuple[float, float, float]:
    phi1 = _deg_to_rad(ATS_STANDARD_PARALLEL_1_DEG)
    phi2 = _deg_to_rad(ATS_STANDARD_PARALLEL_2_DEG)
    phi0 = _deg_to_rad(ATS_ORIGIN_LAT_DEG)
    m1 = math.cos(phi1)
    m2 = math.cos(phi2)
    t1 = math.tan(math.pi / 4.0 + phi1 / 2.0)
    t2 = math.tan(math.pi / 4.0 + phi2 / 2.0)
    n = math.log(m1 / m2) / math.log(t2 / t1)
    f = (m1 * (t1**n)) / n
    rho0 = EARTH_RADIUS_METERS * f / (math.tan(math.pi / 4.0 + phi0 / 2.0) ** n)
    return n, f, rho0


def ats_coords_to_wgs84(x_m: float, z_m: float) -> tuple[float, float]:
    n, f, rho0 = _lcc_constants()
    projected_x_m = x_m * ATS_MAP_FACTOR_X * LENGTH_OF_DEGREE
    projected_y_m = z_m * ATS_MAP_FACTOR_Z * LENGTH_OF_DEGREE
    rho = math.copysign(math.hypot(projected_x_m, rho0 - projected_y_m), n)
    theta = math.atan2(projected_x_m, rho0 - projected_y_m)
    phi = 2.0 * math.atan((EARTH_RADIUS_METERS * f / rho) ** (1.0 / n)) - math.pi / 2.0
    lam = _deg_to_rad(ATS_ORIGIN_LON_DEG) + theta / n
    return _rad_to_deg(lam), _rad_to_deg(phi)


def wgs84_to_ats_coords(lon_deg: float, lat_deg: float) -> tuple[float, float]:
    n, f, rho0 = _lcc_constants()
    phi = _deg_to_rad(lat_deg)
    lam = _deg_to_rad(lon_deg)
    lam0 = _deg_to_rad(ATS_ORIGIN_LON_DEG)
    rho = EARTH_RADIUS_METERS * f / (math.tan(math.pi / 4.0 + phi / 2.0) ** n)
    theta = n * (lam - lam0)
    projected_x_m = rho * math.sin(theta)
    projected_y_m = rho0 - rho * math.cos(theta)
    x_m = projected_x_m / ATS_MAP_FACTOR_X / LENGTH_OF_DEGREE
    z_m = projected_y_m / ATS_MAP_FACTOR_Z / LENGTH_OF_DEGREE
    return x_m, z_m

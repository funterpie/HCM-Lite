import pytest

from app.rules.geo import haversine_m


def test_same_coordinate_has_zero_distance():
    assert haversine_m(24.8607, 67.0011, 24.8607, 67.0011) == 0


def test_distance_between_equator_points():
    assert haversine_m(0, 0, 0, 1) == pytest.approx(111_194.9, abs=1)


def test_distance_is_symmetric():
    assert haversine_m(24.8607, 67.0011, 31.5204, 74.3587) == pytest.approx(
        haversine_m(31.5204, 74.3587, 24.8607, 67.0011), abs=1e-9
    )

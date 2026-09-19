import pytest
from decimal import Decimal
from app.services.unit_service import UnitService


def test_litre_canonical():
    svc = UnitService()
    assert svc.normalize_unit("L") == "litre"
    assert svc.normalize_unit("litre") == "litre"
    assert svc.normalize_unit("pcs") == "piece"
    assert svc.normalize_unit("pkt") == "packet"


def test_allowed_but_unconvertible_does_not_crash():
    svc = UnitService()
    salt = {"display_name": "Salt", "base_unit": "kg",
            "allowed_units": ["kg", "g", "packet"],
            "conversions": [{"from_unit": "g", "to_unit": "kg", "factor": 0.001}]}
    qty, unit = svc.convert_to_base_unit(salt, Decimal(5), "packet")
    assert qty == Decimal(5)
    assert unit == "packet"


def test_oil_bottle_does_not_crash():
    svc = UnitService()
    oil = {"display_name": "Oil", "base_unit": "litre",
           "allowed_units": ["litre", "ml", "bottle"],
           "conversions": [{"from_unit": "ml", "to_unit": "litre", "factor": 0.001}]}
    assert svc.is_valid_unit(oil, "litre") is True
    qty, unit = svc.convert_to_base_unit(oil, Decimal(2), "bottle")
    assert qty == Decimal(2)


def test_unknown_unit_still_rejected():
    svc = UnitService()
    rice = {"display_name": "Rice", "base_unit": "kg",
            "allowed_units": ["kg", "bag", "g"],
            "conversions": [{"from_unit": "bag", "to_unit": "kg", "factor": 25}]}
    assert svc.is_valid_unit(rice, "carton") is False
    with pytest.raises(ValueError):
        svc.convert_to_base_unit(rice, Decimal(1), "carton")

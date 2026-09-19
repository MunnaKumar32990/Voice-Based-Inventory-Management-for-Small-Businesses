import pytest
from decimal import Decimal
from app.services.unit_service import UnitService

def test_normalize_unit():
    svc = UnitService()
    assert svc.normalize_unit("KILO") == "kg"
    assert svc.normalize_unit("bori") == "bag"

def test_convert_to_base():
    svc = UnitService()
    product = {"name": "Rice", "base_unit": "kg", "conversions": {"bag": 25}}
    qty, unit = svc.convert_to_base_unit(product, Decimal(2), "bag")
    assert qty == Decimal(50)
    assert unit == "kg"

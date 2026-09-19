import pytest
from decimal import Decimal
from app.services.nlp_service import NLPService

@pytest.fixture
def nlp():
    return NLPService()

def test_add_stock_english(nlp):
    res = nlp.parse_command("Add 5 bags of rice")
    assert res.intent == "STOCK_IN"
    assert res.quantity == Decimal(5)
    assert res.unit == "bag"
    assert "rice" in res.product_text

def test_remove_stock(nlp):
    res = nlp.parse_command("Remove 2 cartons soap")
    assert res.intent == "STOCK_OUT"
    assert res.quantity == Decimal(2)
    assert res.unit == "carton"
    assert "soap" in res.product_text

def test_hindi_add(nlp):
    res = nlp.parse_command("चावल 5 बोरी आया")
    assert res.intent == "STOCK_IN"
    assert res.quantity == Decimal(5)
    assert res.unit == "bag"  # बोरी normalizes to canonical 'bag'
    assert "चावल" in res.product_text

def test_mixed_language(nlp):
    res = nlp.parse_command("rice 5 bags add karo")
    assert res.intent == "STOCK_IN"
    assert res.quantity == Decimal(5)
    assert res.unit == "bag"
    assert "rice" in res.product_text

def test_stock_query(nlp):
    res = nlp.parse_command("How much rice is available")
    assert res.intent == "STOCK_QUERY"
    assert "rice" in res.product_text

def test_low_stock_query(nlp):
    res = nlp.parse_command("What is running low")
    assert res.intent == "LOW_STOCK_QUERY"

def test_with_price(nlp):
    res = nlp.parse_command("Add 5 bags rice price 2500")
    assert res.intent == "STOCK_IN"
    assert res.quantity == Decimal(5)
    assert res.unit == "bag"
    assert res.price_total == Decimal(2500)

def test_number_words(nlp):
    res = nlp.parse_command("Add five bags of rice")
    assert res.quantity == Decimal(5)

def test_missing_quantity(nlp):
    res = nlp.parse_command("Add rice")
    assert res.quantity is None
    assert res.confidence < 1.0

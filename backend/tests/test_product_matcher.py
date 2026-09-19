import pytest
from app.services.product_matcher import ProductMatcher


@pytest.mark.asyncio
async def test_normalize():
    matcher = ProductMatcher()
    # Latin text: lowercase, remove punctuation, keep words
    assert matcher._normalize("  RICE (basmati) ") == "rice basmati"
    # Hindi Devanagari: preserved as-is
    assert matcher._normalize("चावल") == "चावल"
    # Telugu: preserved
    assert matcher._normalize("బియ్యం") == "బియ్యం"
    # Mixed: lowercase Latin, keep Devanagari
    assert matcher._normalize("Rice चावल") == "rice चावल"
    # Empty
    assert matcher._normalize("") == ""
    assert matcher._normalize(None) == ""


def test_get_alias_text():
    matcher = ProductMatcher()
    # Dict alias
    assert matcher._get_alias_text({"text": "chawal", "language": "hi"}) == "chawal"
    # String alias (backward compat)
    assert matcher._get_alias_text("chawal") == "chawal"

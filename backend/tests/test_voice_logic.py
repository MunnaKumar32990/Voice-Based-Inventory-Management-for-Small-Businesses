"""NLP + voice-response edge cases (no DB needed)."""
import pytest
from app.services.nlp_service import NLPService
from app.services.speech_service import SpeechService, UnsupportedProviderError
from app.api.voice import _serialize_low_stock


def test_attached_unit():
    n = NLPService()
    r = n.parse_command("Add 5kg rice")
    assert r.intent == "STOCK_IN"
    assert str(r.quantity) == "5"
    assert r.unit == "kg"


def test_query_beats_add_verb():
    n = NLPService()
    # "How much" must win even though "add" logic exists elsewhere
    r = n.parse_command("How much rice is available")
    assert r.intent == "STOCK_QUERY"


def test_no_word_does_not_cancel():
    n = NLPService()
    r = n.parse_command("Add 5 bags rice")
    assert r.intent == "STOCK_IN"


def test_serialize_low_stock_names():
    items = [{"product_id": "p1", "product_name": "Rice", "quantity": 3,
              "unit": "kg", "threshold": 10}]
    out = _serialize_low_stock(items)
    assert out[0]["product_name"] == "Rice"
    assert out[0]["quantity"] == 3


@pytest.mark.asyncio
async def test_webspeech_transcribe_disabled():
    s = SpeechService()
    with pytest.raises(UnsupportedProviderError):
        await s.transcribe(b"fake-audio", "en", provider="webspeech")


def test_azure_lang_mapping():
    assert SpeechService._normalize_lang("hi") == "hi-IN"
    assert SpeechService._normalize_lang("te-IN") == "te-IN"
    assert SpeechService._normalize_lang("en") == "en-IN"


@pytest.mark.asyncio
async def test_azure_needs_keys(monkeypatch):
    from app import config as cfg
    monkeypatch.setattr(cfg.settings, "AZURE_SPEECH_KEY", "")
    monkeypatch.setattr(cfg.settings, "AZURE_SPEECH_REGION", "")
    s = SpeechService()
    with pytest.raises(UnsupportedProviderError, match="not configured"):
        await s.transcribe(b"fake-audio", "en-IN", provider="azure")


def test_dialect_detection_and_responses():
    from app.core.i18n import detect_speech_dialect, get_response

    # Hinglish colloquial input
    d_hi = detect_speech_dialect("5 kg rice add kro")
    assert d_hi == "hinglish"
    resp_hi = get_response("stock_added", d_hi, product="Rice", quantity="5", balance="105", unit="kg")
    assert "add ho gya" in resp_hi
    assert "new quantity 105 kg hai" in resp_hi

    # English input
    d_en = detect_speech_dialect("Add 5 kg of rice")
    assert d_en == "en"
    resp_en = get_response("stock_added", d_en, product="Rice", quantity="5", balance="105", unit="kg")
    assert "added successfully" in resp_en

    # Devanagari Hindi
    d_deva = detect_speech_dialect("चावल 5 बोरी आया")
    assert d_deva == "hi_deva"

    # Telugish
    d_te = detect_speech_dialect("5 kg rice add cheyyi")
    assert d_te == "telugish"


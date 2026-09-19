import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from app.services.nlp_service import NLPService, ParsedCommand
from app.services.llm_parser import LLMParser


def test_is_uncertain_heuristics():
    nlp = NLPService()

    # Certain commands
    assert not nlp.is_uncertain(
        ParsedCommand(intent="STOCK_IN", product_text="rice", quantity=Decimal(5), unit="kg", confidence=0.9)
    )
    assert not nlp.is_uncertain(
        ParsedCommand(intent="LOW_STOCK_QUERY", confidence=1.0)
    )
    assert not nlp.is_uncertain(
        ParsedCommand(intent="CANCEL", confidence=1.0)
    )
    assert not nlp.is_uncertain(
        ParsedCommand(intent="STOCK_QUERY", product_text="sugar", confidence=0.8)
    )

    # Uncertain commands
    assert nlp.is_uncertain(ParsedCommand(intent="UNKNOWN", confidence=0.0))
    assert nlp.is_uncertain(
        ParsedCommand(intent="STOCK_IN", product_text="rice", quantity=None, confidence=0.5)
    )
    assert nlp.is_uncertain(
        ParsedCommand(intent="STOCK_IN", product_text=None, quantity=Decimal(5), confidence=0.5)
    )
    assert nlp.is_uncertain(
        ParsedCommand(intent="STOCK_QUERY", product_text=None, confidence=0.4)
    )
    assert nlp.is_uncertain(
        ParsedCommand(intent="STOCK_IN", product_text="rice", quantity=Decimal(5), confidence=0.4)
    )


@pytest.mark.asyncio
async def test_certain_command_skips_llm():
    nlp = NLPService()
    with patch.object(nlp.llm_parser, "parse_fallback", new_callable=AsyncMock) as mock_llm:
        res = await nlp.parse_command_with_fallback("Add 5 bags of rice")
        assert res.intent == "STOCK_IN"
        assert res.quantity == Decimal(5)
        assert res.unit == "bag"
        # LLM fallback must NOT be called for clean deterministic commands
        mock_llm.assert_not_called()


@pytest.mark.asyncio
async def test_uncertain_command_invokes_llm():
    nlp = NLPService()
    mock_parsed = ParsedCommand(
        intent="STOCK_QUERY",
        product_text="soap",
        quantity=None,
        unit=None,
        confidence=0.95,
    )
    with patch.object(nlp.llm_parser, "parse_fallback", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_parsed
        # Ambiguous colloquial sentence that deterministic regex finds uncertain
        res = await nlp.parse_command_with_fallback("kripya store ka soap status check karein")
        mock_llm.assert_called_once()
        assert res.intent == "STOCK_QUERY"
        assert res.product_text == "soap"



@pytest.mark.asyncio
async def test_llm_failure_falls_back_to_deterministic():
    nlp = NLPService()
    with patch.object(nlp.llm_parser, "parse_fallback", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = None  # Simulate network failure or timeout
        res = await nlp.parse_command_with_fallback("Add rice")
        # Should gracefully return deterministic result
        assert res.intent == "STOCK_IN"
        assert res.quantity is None

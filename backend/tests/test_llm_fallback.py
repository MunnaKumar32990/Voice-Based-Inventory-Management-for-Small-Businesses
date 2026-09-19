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


@pytest.mark.asyncio
async def test_real_world_shop_phrases():
    nlp = NLPService()

    # 1. "bhai rice ka 2 bora aaya hai"
    p1 = await nlp.parse_command_with_fallback("bhai rice ka 2 bora aaya hai")
    assert p1.intent == "STOCK_IN"
    assert p1.product_text == "rice"
    assert p1.quantity == Decimal(2)
    assert p1.unit == "bag"

    # 2. "rice do bora de do"
    p2 = await nlp.parse_command_with_fallback("rice do bora de do")
    assert p2.intent == "STOCK_OUT"
    assert p2.product_text == "rice"
    assert p2.quantity == Decimal(2)
    assert p2.unit == "bag"

    # 3. "5 kilo chawal likh lo"
    p3 = await nlp.parse_command_with_fallback("5 kilo chawal likh lo")
    assert p3.intent == "STOCK_IN"
    assert p3.product_text == "chawal"
    assert p3.quantity == Decimal(5)
    assert p3.unit == "kg"

    # 4. "customer ko 3 packet sugar de diya"
    p4 = await nlp.parse_command_with_fallback("customer ko 3 packet sugar de diya")
    assert p4.intent == "STOCK_OUT"
    assert p4.product_text == "sugar"
    assert p4.quantity == Decimal(3)
    assert p4.unit == "packet"

    # 5. "rice mein aadha quintal aaya"
    p5 = await nlp.parse_command_with_fallback("rice mein aadha quintal aaya")
    assert p5.intent == "STOCK_IN"
    assert p5.product_text == "rice"
    assert p5.quantity == Decimal("0.5")
    assert p5.unit == "quintal"

    # 6. "20 ka biscuit nahi, 10 packet" (negation/correction -> triggers LLM fallback)
    with patch.object(nlp.llm_parser, "parse_fallback", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = ParsedCommand(
            intent="STOCK_IN",
            product_text="biscuit",
            quantity=Decimal(10),
            unit="packet",
            confidence=0.95,
        )
        p6 = await nlp.parse_command_with_fallback("20 ka biscuit nahi, 10 packet")
        assert p6.intent == "STOCK_IN"
        assert p6.product_text == "biscuit"
        assert p6.quantity == Decimal(10)
        assert p6.unit == "packet"


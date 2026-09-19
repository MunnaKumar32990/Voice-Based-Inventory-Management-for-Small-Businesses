"""Gemini Flash LLM parser for inventory voice commands.

Used as a structured-intent fallback when deterministic regex/rule-based NLP
parsing is uncertain (e.g. UNKNOWN intent, low confidence, complex phrasing).
"""
import json
import logging
import asyncio
from decimal import Decimal
from typing import Optional
import httpx

from app.config import settings
from app.services.nlp_service import ParsedCommand

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert NLP parser for an Indian retail inventory management system (VoiceStock).
Your job is to extract structured intent and entities from voice transcripts spoken by Indian shopkeepers.
The input can be in English, Hindi (Devanagari or Romanized Hinglish), Telugu (Telugu script or Romanized Telugish), or code-mixed.

Supported Intents:
- "STOCK_IN": Adding stock, purchases, incoming goods, stock received (e.g., 'Add 5 kg rice', '10 packet maggi aayi', 'bhaiya 20 peti biscuit laya', 'rice 5 bags vachindi').
- "STOCK_OUT": Removing stock, sales, items sold, dispatched (e.g., 'Sold 2 kg sugar', '5 packet becha', '3 packet noodles nikal do', '2 cartons biscuits teeseyyi').
- "STOCK_QUERY": Checking availability or stock balance (e.g., 'How much rice is left?', 'Chawal kitna bacha hai?', 'Sugar stock check karo', 'Biyyam entha undi?').
- "LOW_STOCK_QUERY": Asking which items are running low or need reordering (e.g., 'What is running low?', 'Kaunsa item kam hai?', 'Reorder list dikhao', 'Ee items thakkuva ga unnai?').
- "CANCEL": Cancelling an action (e.g., 'Cancel', 'Ruko mat karo', 'Nahi rehne do', 'Raddhu cheyyi').
- "UNKNOWN": Completely unintelligible, unrelated chatter, or cannot determine any inventory intent.

Entity Rules:
- product_text: The clean name of the product (e.g., "rice", "sugar", "maggi", "sunflower oil"). Strip out polite words ("bhaiya", "please") and quantity words. Set to null if intent is LOW_STOCK_QUERY or CANCEL, or product is unknown.
- quantity: Numeric value as a positive float (e.g., 5.0, 10.0, 0.5, 2.5). null if not specified.
- unit: The unit of measurement in standard form (e.g., "kg", "gram", "packet", "bag", "carton", "box", "piece", "bottle", "litre"). null if not specified.
- price_total: Numeric total monetary value if mentioned in rupees (e.g., 'aur 500 rupaye lage' -> 500.0). null if not specified.
- confidence: Float from 0.0 to 1.0 reflecting how confident you are in this interpretation.

Respond with strictly valid JSON matching this schema:
{
  "intent": "STOCK_IN" | "STOCK_OUT" | "STOCK_QUERY" | "LOW_STOCK_QUERY" | "CANCEL" | "UNKNOWN",
  "product_text": string or null,
  "quantity": number or null,
  "unit": string or null,
  "price_total": number or null,
  "confidence": number
}
"""

INTENT_NORMALIZATION = {
    "STOCK_IN": "STOCK_IN",
    "ADD": "STOCK_IN",
    "ADD_INVENTORY": "STOCK_IN",
    "PURCHASE": "STOCK_IN",
    "STOCK_OUT": "STOCK_OUT",
    "REMOVE": "STOCK_OUT",
    "REMOVE_INVENTORY": "STOCK_OUT",
    "SELL": "STOCK_OUT",
    "SALE": "STOCK_OUT",
    "STOCK_QUERY": "STOCK_QUERY",
    "QUERY": "STOCK_QUERY",
    "CHECK_STOCK": "STOCK_QUERY",
    "LOW_STOCK_QUERY": "LOW_STOCK_QUERY",
    "LOW_STOCK": "LOW_STOCK_QUERY",
    "CANCEL": "CANCEL",
    "UNKNOWN": "UNKNOWN",
}


class LLMParser:
    """Async client for Gemini Flash structured parsing fallback."""

    def __init__(self):
        self._api_key = settings.GEMINI_API_KEY
        self._model = settings.GEMINI_MODEL or "gemini-flash-latest"

    @property
    def is_configured(self) -> bool:
        return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())

    async def parse_fallback(self, transcript: str, language_hint: str = "en") -> Optional[ParsedCommand]:
        """Call Gemini Flash to parse uncertain transcripts into structured intent.
        
        Returns ParsedCommand if successful, or None if the call failed or is unconfigured.
        """
        if not self.is_configured:
            return None

        clean_text = transcript.strip() if transcript else ""
        if not clean_text:
            return None

        api_key = settings.GEMINI_API_KEY.strip()
        primary_model = (settings.GEMINI_MODEL or "gemini-flash-latest").strip()
        models_to_try = [primary_model]
        if "lite" not in primary_model:
            models_to_try.append("gemini-flash-lite-latest")

        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Language hint: {language_hint}\n"
            f"Voice transcript: \"{clean_text}\"\n"
            f"JSON:"
        )

        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1,
            }
        }

        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(
                        url,
                        headers={"Content-Type": "application/json", "X-goog-api-key": api_key},
                        json=body,
                    )
                    if resp.status_code in (429, 503):
                        log.info("Gemini model %s returned %s, trying next model...", model, resp.status_code)
                        continue

                    if resp.status_code != 200:
                        log.warning("Gemini API error (%s) on %s: %s", resp.status_code, model, resp.text[:200])
                        continue

                    data = resp.json()
                    candidates = data.get("candidates") or []
                    if not candidates:
                        continue

                    parts = candidates[0].get("content", {}).get("parts") or []
                    if not parts:
                        continue

                    raw_json = parts[0].get("text", "").strip()
                    if not raw_json:
                        continue

                    parsed_data = json.loads(raw_json)

                    raw_intent = str(parsed_data.get("intent", "UNKNOWN")).upper().strip()
                    intent = INTENT_NORMALIZATION.get(raw_intent, "UNKNOWN")

                    product_text = parsed_data.get("product_text")
                    if product_text and isinstance(product_text, str):
                        product_text = product_text.strip().lower() or None
                    else:
                        product_text = None

                    raw_qty = parsed_data.get("quantity")
                    qty: Optional[Decimal] = None
                    if raw_qty is not None:
                        try:
                            qty = Decimal(str(raw_qty))
                            if qty <= 0:
                                qty = None
                        except Exception:
                            qty = None

                    unit = parsed_data.get("unit")
                    if unit and isinstance(unit, str):
                        unit = unit.strip().lower() or None
                    else:
                        unit = None

                    raw_price = parsed_data.get("price_total")
                    price: Optional[Decimal] = None
                    if raw_price is not None:
                        try:
                            price = Decimal(str(raw_price))
                        except Exception:
                            price = None

                    conf = float(parsed_data.get("confidence", 0.9))

                    return ParsedCommand(
                        intent=intent,
                        product_text=product_text,
                        quantity=qty,
                        unit=unit,
                        price_total=price,
                        confidence=conf,
                    )

            except httpx.TimeoutException:
                log.warning("Gemini API timed out on %s for transcript: %s", model, clean_text)
                continue
            except Exception as e:
                log.warning("Gemini fallback parsing failed on %s: %s", model, e)
                continue

        return None

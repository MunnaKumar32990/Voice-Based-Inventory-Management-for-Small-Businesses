"""Gemini Flash LLM parser for inventory voice commands and analytical queries.

Used as a structured-intent fallback when deterministic regex/rule-based NLP
parsing is uncertain (e.g. UNKNOWN intent, low confidence, complex phrasing, or analytical questions).
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
--- Inventory Mutations ---
- "STOCK_IN": Adding stock, purchases, incoming goods, stock received (e.g., 'Add 5 kg rice', '10 packet maggi aayi', 'bhaiya 20 peti biscuit laya', 'rice 5 bags vachindi').
- "STOCK_OUT": Removing stock, sales, items sold, dispatched (e.g., 'Sold 2 kg sugar', '5 packet becha', '3 packet noodles nikal do', '2 cartons biscuits teeseyyi').

--- Database-Aware Analytical & Information Queries ---
- "LIST_PRODUCTS": Asking to list, name, or show all products in inventory (e.g., 'Name all the products we have in our inventory', 'List all products', 'What products do we have?', 'Show all products', 'Sare products ke naam batao', 'Dukan me kya kya saman hai?', 'All products list').
- "COUNT_PRODUCTS": Asking for total number of products (e.g., 'How many products are there?', 'Total kitne products hain?', 'How many products do I have?', 'Kul kitne products hain?').
- "COUNT_PRODUCTS_ADDED": Asking how many products were added in a time range (e.g., 'How many products were added today?', 'Aaj kitne product add huye?', 'How many products were added this week?').
- "LIST_PRODUCTS_ADDED": Asking which products were added (e.g., 'Which products were added today?', 'What products got added this week?', 'Aaj kaunse product add huye?').
- "COUNT_TRANSACTIONS": Asking for transaction counts (e.g., 'How many stock-in transactions happened today?', 'How many stock-out transactions today?', 'How many items were sold today?', 'Aaj kitna stock in hua?').
- "GET_TODAY_ACTIVITY": Asking for today's overall activity/movement (e.g., 'What happened to my inventory today?', 'Today activity', 'Aaj inventory me kya hua?').
- "LIST_LOW_STOCK": Asking which items are running low or need reordering (e.g., 'What products are low in stock?', 'Kaunse product kam hain?', 'Reorder list dikhao').
- "LIST_OUT_OF_STOCK": Asking which items are completely out of stock (e.g., 'Which products are out of stock?', 'Kaunsa item khatam ho gaya?', 'Out of stock items').
- "GET_PRODUCT_STOCK": Checking stock level of a specific product (e.g., 'How much rice is currently available?', 'Chawal kitna bacha hai?', 'Sugar stock check karo').
- "GET_TOP_STOCK_PRODUCTS": Asking for highest or lowest stock items (e.g., 'Which product has the highest stock?', 'Sabse jyada stock kiska hai?', 'Which product has the lowest stock?').
- "GET_RECENT_TRANSACTIONS": Asking for latest or recent transactions (e.g., 'Show me the latest transactions', 'Aakhiri transactions dikhao', 'Recent activity').

--- General ---
- "CANCEL": Cancelling an action (e.g., 'Cancel', 'Ruko mat karo', 'Nahi rehne do', 'Raddhu cheyyi').
- "UNKNOWN": Unintelligible, unrelated chatter, or unresolvable.

Entity Rules:
- product_text: Clean product name (e.g. "rice", "sugar", "maggi"). null if not applicable.
- quantity: Numeric float (e.g. 5.0, 10.0, 0.5). null if not specified.
- unit: Measurement unit (e.g. "kg", "gram", "packet", "bag", "carton", "box", "piece", "bottle", "litre"). null if not specified.
- price_total: Monetary value in rupees if mentioned (e.g. '500 rupaye' -> 500.0). null if not specified.
- time_range: "today" | "yesterday" | "this_week" | "this_month" | "last_7_days" | "last_30_days" | "all_time" | null. (e.g. 'today' -> "today", 'aaj' -> "today", 'is hafte' -> "this_week").
- operation: "STOCK_IN" | "STOCK_OUT" | "ALL" | null (for transaction queries).
- order: "highest" | "lowest" | null (for top stock query).
- confidence: Float from 0.0 to 1.0.

Respond with strictly valid JSON matching this schema:
{
  "intent": string,
  "product_text": string or null,
  "quantity": number or null,
  "unit": string or null,
  "price_total": number or null,
  "time_range": string or null,
  "operation": string or null,
  "order": string or null,
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
    "STOCK_QUERY": "GET_PRODUCT_STOCK",
    "GET_PRODUCT_STOCK": "GET_PRODUCT_STOCK",
    "GET_CURRENT_STOCK": "GET_PRODUCT_STOCK",
    "CHECK_STOCK": "GET_PRODUCT_STOCK",
    "LOW_STOCK_QUERY": "LIST_LOW_STOCK",
    "LIST_LOW_STOCK": "LIST_LOW_STOCK",
    "LOW_STOCK": "LIST_LOW_STOCK",
    "LIST_OUT_OF_STOCK": "LIST_OUT_OF_STOCK",
    "OUT_OF_STOCK": "LIST_OUT_OF_STOCK",
    "LIST_PRODUCTS": "LIST_PRODUCTS",
    "LIST_ALL_PRODUCTS": "LIST_PRODUCTS",
    "NAME_PRODUCTS": "LIST_PRODUCTS",
    "SHOW_PRODUCTS": "LIST_PRODUCTS",
    "LIST_ITEMS": "LIST_PRODUCTS",
    "COUNT_PRODUCTS": "COUNT_PRODUCTS",
    "TOTAL_PRODUCTS": "COUNT_PRODUCTS",
    "COUNT_PRODUCTS_ADDED": "COUNT_PRODUCTS_ADDED",
    "LIST_PRODUCTS_ADDED": "LIST_PRODUCTS_ADDED",
    "COUNT_TRANSACTIONS": "COUNT_TRANSACTIONS",
    "GET_TODAY_ACTIVITY": "GET_TODAY_ACTIVITY",
    "GET_STOCK_MOVEMENT": "GET_TODAY_ACTIVITY",
    "GET_TOP_STOCK_PRODUCTS": "GET_TOP_STOCK_PRODUCTS",
    "GET_RECENT_TRANSACTIONS": "GET_RECENT_TRANSACTIONS",
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

                    time_range = parsed_data.get("time_range")
                    if time_range and isinstance(time_range, str):
                        time_range = time_range.strip().lower()
                    else:
                        time_range = None

                    operation = parsed_data.get("operation")
                    if operation and isinstance(operation, str):
                        operation = operation.strip().upper()
                    else:
                        operation = None

                    order = parsed_data.get("order")
                    if order and isinstance(order, str):
                        order = order.strip().lower()
                    else:
                        order = None

                    conf = float(parsed_data.get("confidence", 0.9))

                    return ParsedCommand(
                        intent=intent,
                        product_text=product_text,
                        quantity=qty,
                        unit=unit,
                        price_total=price,
                        time_range=time_range,
                        operation=operation,
                        order=order,
                        confidence=conf,
                    )

            except httpx.TimeoutException:
                log.warning("Gemini API timed out on %s for transcript: %s", model, clean_text)
                continue
            except Exception as e:
                log.warning("Gemini fallback parsing failed on %s: %s", model, e)
                continue

        return None

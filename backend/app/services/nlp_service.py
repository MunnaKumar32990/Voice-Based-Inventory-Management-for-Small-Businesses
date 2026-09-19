import re
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedCommand:
    intent: str
    product_text: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    price_total: Optional[Decimal] = None
    direction: Optional[str] = None
    reason: Optional[str] = None
    confidence: float = 0.0


# Intent keywords — English, Hindi (romanized + Devanagari), Telugu
INTENT_KEYWORDS = {
    "STOCK_IN": [
        # English
        "add", "added", "stock in", "purchase", "received", "came", "arrived",
        # Hindi romanized
        "aaya", "aagaya", "aaye", "laya", "kharid", "kharida", "dal", "daal", "dalo", "daalo",
        "jod", "jodo", "add karo", "add kro", "kro", "karo", "kardo", "dal do",
        # Hindi Devanagari
        "आया", "आगया", "आये", "लाया", "खरीद", "खरीदा", "डाल", "डालो", "जोड़", "जोड़ो",
        # Telugu
        "వచ్చింది", "చేర్చు", "కలుపు", "చేయ్", "add cheyyi", "cheyyi",
    ],
    "STOCK_OUT": [
        # English
        "remove", "removed", "sold", "sale", "dispatch", "dispatched", "took", "gave",
        # Hindi romanized
        "becha", "bech", "bikha", "gaya", "nikal", "nikala", "nikalo", "hatao", "remove karo", "remove kro", "de diya", "diya",
        # Hindi Devanagari
        "बेचा", "बेच", "गया", "निकाल", "निकाला", "निकालो", "हटाओ", "दे दिया",
        # Telugu
        "అమ్మాను", "తీసేయి", "తీసు", "అమ్మినది", "తీసెయ్యి", "remove cheyyi",
    ],
    "STOCK_QUERY": [
        # English
        "how much", "how many", "stock", "available", "balance", "check", "what is",
        # Hindi
        "kitna", "kitne", "कितना", "कितने", "स्टॉक",
        # Telugu
        "ఎంత", "ఉంది", "ఎంతు",
    ],
    "LOW_STOCK_QUERY": [
        # English
        "low", "running low", "reorder", "what is low", "need to order", "shortage",
        # Hindi
        "kam", "कम", "कम है",
        # Telugu
        "తక్కువ", "తక్కువగా",
    ],
    "CANCEL": ["cancel", "nahi", "नहीं", "undo", "రద్దు", "వద్దు"],
}

# Number words: English + Hindi (romanized + Devanagari) + Telugu (romanized + Telugu script)
NUMBER_WORDS = {
    # English
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "half": 0.5, "quarter": 0.25,
    # Hindi romanized
    "ek": 1, "do": 2, "teen": 3, "chaar": 4, "paanch": 5,
    "chhe": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
    "gyarah": 11, "barah": 12, "terah": 13, "chaudah": 14, "pandrah": 15,
    "solah": 16, "satrah": 17, "athaarah": 18, "unnis": 19, "bees": 20,
    "aadha": 0.5, "paav": 0.25,
    # Hindi Devanagari
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5,
    "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
    "डेढ़": 1.5, "सवा": 1.25, "ढाई": 2.5, "आधा": 0.5, "पाव": 0.25,
    # Telugu romanized
    "okati": 1, "rendu": 2, "moodu": 3, "nalugu": 4, "aidu": 5,
    "aaru": 6, "edu": 7, "enimidi": 8, "tommidi": 9, "padi": 10,
    # Telugu script
    "ఒకటి": 1, "రెండు": 2, "మూడు": 3, "నాలుగు": 4, "ఐదు": 5,
    "ఆరు": 6, "ఏడు": 7, "ఎనిమిది": 8, "తొమ్మిది": 9, "పది": 10,
}

# Unit keywords — canonical form + variants (including plurals)
# Maps variant -> canonical
UNIT_ALIASES = {
    # Weight
    "kg": "kg", "kgs": "kg", "kilogram": "kg", "kilograms": "kg", "kilo": "kg", "kilos": "kg",
    "g": "g", "gm": "g", "gms": "g", "gram": "g", "grams": "g",
    "quintal": "quintal", "quintals": "quintal",
    # Volume
    "l": "litre", "ltr": "litre", "liter": "litre", "litre": "litre", "litres": "litre", "liters": "litre",
    "ml": "ml", "milliliter": "ml", "millilitre": "ml",
    # Count
    "piece": "piece", "pieces": "piece", "pc": "piece", "pcs": "piece",
    "dozen": "dozen", "dozens": "dozen", "darjan": "dozen", "darzan": "dozen",
    # Packages
    "bag": "bag", "bags": "bag", "bori": "bag", "bora": "bag",
    "carton": "carton", "cartons": "carton",
    "box": "box", "boxes": "box",
    "packet": "packet", "packets": "packet", "pkt": "packet", "pkts": "packet",
    "bottle": "bottle", "bottles": "bottle",
    "can": "can", "cans": "can",
    "bundle": "bundle", "bundles": "bundle",
    # Hindi unit words
    "किलो": "kg", "किलोग्राम": "kg", "ग्राम": "g",
    "लीटर": "litre", "बोरी": "bag", "बोरा": "bag",
    "पैकेट": "packet", "दर्जन": "dozen", "बॉक्स": "box",
    "बोतल": "bottle", "डब्बा": "box", "कार्टन": "carton", "थैला": "bag",
    # Telugu unit words
    "కిలో": "kg", "కిలోలు": "kg", "గ్రాములు": "g",
    "లీటర్": "litre", "బస్తా": "bag", "బస్తాలు": "bag",
    "పెట్టె": "box", "డజన్": "dozen", "పాకెట్": "packet",
}

# Build list of all unit variant strings for regex matching (sorted longest first)
_UNIT_VARIANTS = sorted(UNIT_ALIASES.keys(), key=len, reverse=True)


class NLPService:
    """Deterministic NLP parser for inventory voice commands, with optional LLM fallback.
    
    Extracts intent, product, quantity, unit, and price from natural
    language input in English, Hindi, and Telugu (including code-mixing).
    """

    def __init__(self):
        self._llm_parser = None

    @property
    def llm_parser(self):
        if self._llm_parser is None:
            from app.services.llm_parser import LLMParser
            self._llm_parser = LLMParser()
        return self._llm_parser

    def is_uncertain(self, parsed: ParsedCommand) -> bool:
        """Determines if deterministic parsing was uncertain and would benefit from LLM fallback."""
        if parsed.intent == "UNKNOWN":
            return True
        if parsed.confidence < 0.6:
            return True
        if parsed.intent in ("STOCK_IN", "STOCK_OUT"):
            if not parsed.product_text or parsed.quantity is None:
                return True
            if len(parsed.product_text.split()) > 3:
                return True
        if parsed.intent == "STOCK_QUERY":
            if not parsed.product_text or len(parsed.product_text.split()) > 3:
                return True
        return False

    async def parse_command_with_fallback(self, transcript: str, language: str = "en") -> ParsedCommand:
        """Parse transcript with deterministic rules first, falling back to LLM if uncertain."""
        deterministic = self.parse_command(transcript, language)

        if not self.is_uncertain(deterministic):
            return deterministic

        # Deterministic parsing was uncertain — try LLM fallback if configured
        if self.llm_parser.is_configured:
            llm_result = await self.llm_parser.parse_fallback(transcript, language)
            if llm_result:
                # Use LLM result if it provided a clearer interpretation
                if llm_result.intent != "UNKNOWN" or deterministic.intent == "UNKNOWN":
                    return llm_result

        return deterministic

    def parse_command(self, transcript: str, language: str = "en") -> ParsedCommand:
        text = transcript.strip()
        if not text:
            return ParsedCommand(intent="UNKNOWN", confidence=0.0)

        # Normalize: lowercase for Latin chars, keep Devanagari/Telugu as-is
        text_lower = text.lower()
        # Remove common punctuation but keep Devanagari (0900-097F) and Telugu (0C00-0C7F)
        text_clean = re.sub(r'[^\w\s\u0900-\u097F\u0C00-\u0C7F₹]', '', text_lower)

        # 1. Detect intent
        intent = self._detect_intent(text_clean)

        # Short-circuit for intents that don't need entities
        if intent in ("LOW_STOCK_QUERY", "CANCEL"):
            return ParsedCommand(intent=intent, confidence=1.0)

        # Working copy for entity extraction (we'll remove matched tokens)
        working = text_clean

        # 2. Extract price FIRST (before quantity, so "price 2500" doesn't become quantity)
        price_total, working = self._extract_price(working)

        # 3. Extract quantity
        quantity, working = self._extract_quantity(working)

        # 4. Extract unit
        unit, working = self._extract_unit(working)

        # 5. Remove intent keywords to isolate product name
        working = self._remove_intent_keywords(working, intent)

        # 6. Clean up product text
        # Remove common filler words
        filler = {"of", "the", "a", "an", "is", "are", "ka", "ke", "ki", "ko", "se", "me", "karo", "no", "price", "please"}
        words = working.split()
        product_words = [w for w in words if w not in filler and len(w) > 0]
        product_text = " ".join(product_words).strip()

        # 7. Calculate confidence
        confidence = self._calculate_confidence(intent, product_text, quantity, unit)

        return ParsedCommand(
            intent=intent,
            product_text=product_text if product_text else None,
            quantity=quantity,
            unit=unit,
            price_total=price_total,
            confidence=confidence,
        )

    def _detect_intent(self, text: str) -> str:
        """Detect intent from keywords. More specific intents are checked first."""
        # CANCEL only on explicit cancel words (bare "no" removed — too many false positives).
        # Other intents in specificity order.
        priority_order = ["LOW_STOCK_QUERY", "STOCK_QUERY", "STOCK_IN", "STOCK_OUT", "CANCEL"]
        
        for intent_name in priority_order:
            keywords = INTENT_KEYWORDS.get(intent_name, [])
            # Sort keywords by length descending to match longer phrases first
            for kw in sorted(keywords, key=len, reverse=True):
                if re.search(r'(?:^|\s)' + re.escape(kw) + r'(?:\s|$)', text):
                    return intent_name

        return "UNKNOWN"

    def _extract_price(self, text: str) -> tuple[Optional[Decimal], str]:
        """Extract price amounts like 'price 2500', 'rs 840', '₹1200'."""
        patterns = [
            r'(?:price|rs|rupees|rupee|₹)\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*(?:rupees|rs|₹)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                price = Decimal(match.group(1))
                text = text[:match.start()] + text[match.end():]
                return price, text.strip()
        return None, text

    def _extract_quantity(self, text: str) -> tuple[Optional[Decimal], str]:
        """Extract numeric quantity — digits first (incl. attached units like 5kg), then number words."""
        # Attached or spaced digits: "5kg", "5 bags", "2.5 litres"
        num_match = re.search(r'(?:^|\s)(\d+(?:\.\d+)?)(?=\s|$|[a-z\u0900-\u097F\u0C00-\u0C7F])', text)
        if num_match:
            quantity = Decimal(num_match.group(1))
            text = text[:num_match.start()] + " " + text[num_match.end():]
            return quantity, text.strip()

        # Try number words (sorted longest first to avoid partial matches)
        for word, val in sorted(NUMBER_WORDS.items(), key=lambda x: len(x[0]), reverse=True):
            pattern = r'(?:^|\s)' + re.escape(word) + r'(?:\s|$)'
            if re.search(pattern, text):
                text = re.sub(pattern, ' ', text, count=1)
                return Decimal(str(val)), text.strip()

        return None, text

    def _extract_unit(self, text: str) -> tuple[Optional[str], str]:
        """Extract and normalize unit."""
        for variant in _UNIT_VARIANTS:
            pattern = r'(?:^|\s)' + re.escape(variant) + r'(?:\s|$)'
            if re.search(pattern, text):
                canonical = UNIT_ALIASES[variant]
                text = re.sub(pattern, ' ', text, count=1)
                return canonical, text.strip()
        return None, text

    def _remove_intent_keywords(self, text: str, intent: str) -> str:
        """Remove intent keywords from text to isolate product name."""
        keywords = INTENT_KEYWORDS.get(intent, [])
        for kw in sorted(keywords, key=len, reverse=True):
            pattern = r'(?:^|\s)' + re.escape(kw) + r'(?:\s|$)'
            text = re.sub(pattern, ' ', text)

        # Also strip common auxiliary verbs & particles from product candidate
        aux_tokens = [
            "add kro", "remove kro", "kro", "karo", "kardo", "kar do", "kar", "do",
            "diya", "de diya", "gaya", "gaye", "gayi", "hai", "hain", "tha", "thi",
            "ka", "ki", "ke", "ko", "se", "me", "mein", "bhi", "aur", "pe", "par",
            "करो", "कर दो", "कर", "दो", "दिया", "गया", "गए", "गई", "है", "हैं", "का", "की", "के",
            "cheyyi", "chey", "chesi", "undi", "unnai", "mariyu",
            "please", "pls", "the", "of", "in", "from", "and"
        ]
        for aux in sorted(aux_tokens, key=len, reverse=True):
            pattern = r'(?:^|\s)' + re.escape(aux) + r'(?:\s|$)'
            text = re.sub(pattern, ' ', text)

        return re.sub(r'\s+', ' ', text).strip()

    def _calculate_confidence(self, intent: str, product_text: Optional[str],
                              quantity: Optional[Decimal], unit: Optional[str]) -> float:
        """Calculate confidence score based on extracted entities."""
        score = 0.0

        if intent != "UNKNOWN":
            score += 0.3

        if intent in ("STOCK_QUERY",):
            # Queries only need product
            if product_text:
                score += 0.5
            return min(score, 1.0)

        if product_text:
            score += 0.25
        if quantity is not None:
            score += 0.25
        if unit:
            score += 0.15
        if intent in ("STOCK_IN", "STOCK_OUT"):
            score += 0.05

        return min(score, 1.0)

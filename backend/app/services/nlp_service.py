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
    time_range: Optional[str] = None
    operation: Optional[str] = None
    order: Optional[str] = None
    limit: Optional[int] = None


# Intent keywords — English, Hindi (romanized + Devanagari), Telugu
INTENT_KEYWORDS = {
    "STOCK_IN": [
        # English
        "add", "added", "stock in", "purchase", "received", "came", "arrived",
        # Hindi romanized
        "aaya", "aagaya", "aaye", "laya", "kharid", "kharida", "dal", "daal", "dalo", "daalo",
        "jod", "jodo", "add karo", "add kro", "kro", "karo", "kardo", "dal do",
        "likh lo", "likh do", "likho", "likhna", "entry karo", "chadha lo",
        # Hindi Devanagari
        "आया", "आगया", "आये", "लाया", "खरीद", "खरीदा", "डाल", "डालो", "जोड़", "जोड़ो", "लिख लो", "लिख दो",
        # Telugu
        "వచ్చింది", "చేర్చు", "కలుపు", "చేయ్", "add cheyyi", "cheyyi",
    ],
    "STOCK_OUT": [
        # English
        "remove", "removed", "sold", "sale", "dispatch", "dispatched", "took", "gave",
        # Hindi romanized
        "becha", "bech", "bikha", "gaya", "nikal", "nikala", "nikalo", "hatao", "remove karo", "remove kro",
        "de diya", "diya", "de do", "dedo", "de dena",
        # Hindi Devanagari
        "बेचा", "बेच", "गया", "निकाल", "निकाला", "निकालो", "हटाओ", "दे दिया", "दे दो",
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

_UNIT_VARIANTS = sorted(UNIT_ALIASES.keys(), key=len, reverse=True)


def extract_time_range(text: str) -> Optional[str]:
    """Extract standard time range identifier from natural language text."""
    t = text.lower()
    if re.search(r'\b(today|aaj|eroju)\b', t):
        return "today"
    if re.search(r'\b(yesterday|kal|ninna)\b', t):
        return "yesterday"
    if re.search(r'\b(this\s+week|is\s+hafte|ee\s+vaaram)\b', t):
        return "this_week"
    if re.search(r'\b(this\s+month|is\s+mahine|ee\s+nela)\b', t):
        return "this_month"
    if re.search(r'\b(last\s+7\s+days|pichle\s+7\s+din)\b', t):
        return "last_7_days"
    if re.search(r'\b(last\s+30\s+days|pichle\s+30\s+din)\b', t):
        return "last_30_days"
    return None


META_PRODUCT_WORDS = {
    "total", "products", "product", "item", "items", "saman", "all",
    "sab", "sabhi", "overall", "inventory", "dukan", "everything",
    "list", "status", "category", "categories"
}


class NLPService:
    """Deterministic NLP parser for inventory voice commands, with optional LLM fallback.
    
    Extracts intent, product, quantity, unit, price, and analytical query parameters
    from natural language input in English, Hindi, and Telugu (including code-mixing).
    """

    def __init__(self):
        self._llm_parser = None

    @property
    def llm_parser(self):
        if self._llm_parser is None:
            from app.services.llm_parser import LLMParser
            self._llm_parser = LLMParser()
        return self._llm_parser

    def is_uncertain(self, parsed: ParsedCommand, raw_text: str = "") -> bool:
        """Determines if deterministic parsing was uncertain and would benefit from LLM fallback."""
        if parsed.intent == "UNKNOWN":
            return True
        
        # Analytical and reporting queries with high confidence do not need quantity/price
        analytical_intents = {
            "COUNT_PRODUCTS",
            "LIST_PRODUCTS",
            "LIST_ALL_PRODUCTS",
            "COUNT_PRODUCTS_ADDED",
            "LIST_PRODUCTS_ADDED",
            "COUNT_TRANSACTIONS",
            "GET_TODAY_ACTIVITY",
            "LIST_LOW_STOCK",
            "LOW_STOCK_QUERY",
            "LIST_OUT_OF_STOCK",
            "GET_TOP_STOCK_PRODUCTS",
            "GET_RECENT_TRANSACTIONS",
        }
        if parsed.intent in analytical_intents:
            return parsed.confidence < 0.8

        if parsed.confidence < 0.7:
            return True

        if parsed.intent in ("STOCK_IN", "STOCK_OUT"):
            if not parsed.product_text or parsed.quantity is None:
                return True
            if len(parsed.product_text.split()) > 2:
                return True

        if parsed.intent in ("STOCK_QUERY", "GET_PRODUCT_STOCK"):
            if not parsed.product_text:
                return True
            p_words = set(parsed.product_text.lower().split())
            if p_words.issubset(META_PRODUCT_WORDS) or any(w in p_words for w in ("total", "all", "sabhi", "overall", "everything")):
                return True
            if len(parsed.product_text.split()) > 3:
                return True

        if parsed.intent == "CANCEL" and raw_text:
            if re.search(r'\d', raw_text) or len(raw_text.split()) > 3:
                return True

        return False

    async def parse_command_with_fallback(self, transcript: str, language: str = "en") -> ParsedCommand:
        """Parse transcript with deterministic rules first, falling back to LLM if uncertain."""
        deterministic = self.parse_command(transcript, language)

        if not self.is_uncertain(deterministic, transcript):
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
        text_clean = re.sub(r'[^\w\s\u0900-\u097F\u0C00-\u0C7F₹]', ' ', text_lower)
        text_clean = re.sub(r'\s+', ' ', text_clean).strip()

        # 0. Check analytical / database-aware queries first
        analytical = self._detect_analytical_query(text_clean)
        if analytical:
            return analytical

        # 1. Detect mutation/stock intent
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
        filler = {
            "of", "the", "a", "an", "is", "are", "ka", "ke", "ki", "ko", "se", "me", "mein",
            "karo", "no", "price", "please", "pls", "bhai", "bhaiya", "bhaiji", "customer",
            "grahak", "sahab", "sir", "arre", "are", "mera", "meri", "mere", "hum", "hume",
            "unhe", "unko", "de", "do", "lo", "hai", "hain", "tha", "thi", "gaya", "gayi",
            "aur", "bhi"
        }
        words = working.split()
        product_words = [w for w in words if w not in filler and len(w) > 0]
        product_text = " ".join(product_words).strip()

        # 7. Calculate confidence
        confidence = self._calculate_confidence(intent, product_text, quantity, unit)

        # Meta-word guard: phrases like "total products" or "all items" are NEVER a single product
        if intent in ("STOCK_QUERY", "GET_PRODUCT_STOCK") and product_text:
            p_words = set(product_text.lower().split())
            if p_words.issubset(META_PRODUCT_WORDS) or any(w in p_words for w in ("total", "all", "sabhi", "overall", "everything")):
                if any(w in p_words for w in ("total", "kitna", "kitne", "kitni", "count", "kul", "motham")):
                    return ParsedCommand(intent="COUNT_PRODUCTS", time_range=None, confidence=1.0)
                else:
                    return ParsedCommand(intent="UNKNOWN", confidence=0.0)

        return ParsedCommand(
            intent=intent,
            product_text=product_text if product_text else None,
            quantity=quantity,
            unit=unit,
            price_total=price_total,
            confidence=confidence,
        )

    def _detect_analytical_query(self, text: str) -> Optional[ParsedCommand]:
        """Recognize analytical/reporting query patterns against the database."""
        time_range = extract_time_range(text)

        # 1. Today Activity / Inventory movement
        if re.search(r'\b(what\s+happened\s+to\s+(?:my\s+)?inventory|today(?:\x27s|\s+)?activity|inventory\s+activity|inventory\s+updates|inventory\s+me\s+kya\s+hua|aaj\s+kya\s+hua|aaj\s+ki\s+activity|eroju\s+activity|inventory\s+lo\s+em\s+jarigindi)\b', text):
            return ParsedCommand(intent="GET_TODAY_ACTIVITY", time_range="today", confidence=1.0)

        # 2. Recent Transactions
        if re.search(r'\b(show\s+(?:me\s+)?(?:the\s+)?(?:latest|recent)\s+transactions?|(?:latest|recent|last)\s+transactions?|aakhiri\s+transactions?|chivari\s+transactions?)\b', text):
            return ParsedCommand(intent="GET_RECENT_TRANSACTIONS", limit=5, confidence=1.0)

        # 3. Top Stock Products (Highest / Lowest)
        if re.search(r'\b(highest\s+stock|maximum\s+stock|most\s+stock|sabse\s+jyada\s+stock|sabse\s+adhik\s+stock|ekkuva\s+stock)\b', text):
            return ParsedCommand(intent="GET_TOP_STOCK_PRODUCTS", order="highest", confidence=1.0)
        if re.search(r'\b(lowest\s+stock|minimum\s+stock|least\s+stock|sabse\s+kam\s+stock|thakkuva\s+stock)\b', text):
            return ParsedCommand(intent="GET_TOP_STOCK_PRODUCTS", order="lowest", confidence=1.0)

        # 4. Out of Stock
        if re.search(r'\b(out\s+of\s+stock|khatam\s+ho\s+gaya|khatam\s+ho\s+gaye|aiypoyindi)\b', text):
            return ParsedCommand(intent="LIST_OUT_OF_STOCK", confidence=1.0)

        # 5. Low in Stock (Analytical phrasing)
        if re.search(r'\b(what\s+products\s+are\s+low\s+in\s+stock|which\s+products\s+are\s+low|what\s+is\s+low\s+in\s+stock|products\s+low\s+in\s+stock|low\s+in\s+stock|running\s+low|shortage\s+items|kaunse\s+product\s+kam\s+hain|kam\s+stock|thakkuva\s+stock)\b', text):
            return ParsedCommand(intent="LOW_STOCK_QUERY", confidence=1.0)

        # 6. List Products Added (which/what products added ...)
        if re.search(r'\b(which\s+products|what\s+products|what\s+was|kaunse\s+product|kaun\s+kaun\s+se\s+product|kya\s+add\s+hua|ae\s+products)\b.*?\b(added|add|entered|jode|aaye)\b', text):
            return ParsedCommand(intent="LIST_PRODUCTS_ADDED", time_range=time_range or "today", confidence=1.0)

        # 7. Count Products Added (how many products added / total products entered ...)
        if re.search(r'\b(how\s+many\s+products|how\s+many\s+items|kitne\s+product|kitne\s+items?|enni\s+products?|total\s+products?|total\s+items?|total\s+saman).*?\b(added|add|entered|jode|chadhe|aaye)\b', text):
            return ParsedCommand(intent="COUNT_PRODUCTS_ADDED", time_range=time_range or "today", confidence=1.0)

        # 8. Count Transactions (Stock-in / Stock-out)
        if re.search(r'\b(stock[\s-]?in\s+transactions?|stock[\s-]?in\s+hua|kitna\s+stock[\s-]?in|kitne\s+stock[\s-]?in|enni\s+stock[\s-]?in)\b', text):
            return ParsedCommand(intent="COUNT_TRANSACTIONS", operation="STOCK_IN", time_range=time_range or "today", confidence=1.0)
        if re.search(r'\b(stock[\s-]?out\s+transactions?|items?\s+were\s+sold|items?\s+sold|items?\s+beche|kitna\s+saman\s+becha|kitna\s+stock[\s-]?out|kitne\s+stock[\s-]?out|enni\s+ammaru)\b', text):
            return ParsedCommand(intent="COUNT_TRANSACTIONS", operation="STOCK_OUT", time_range=time_range or "today", confidence=1.0)
        if re.search(r'\b(how\s+many\s+transactions|kitne\s+transactions|motham\s+enni\s+transactions)\b', text):
            return ParsedCommand(intent="COUNT_TRANSACTIONS", operation="ALL", time_range=time_range or "today", confidence=1.0)

        # 8b. List All Products (name/list/show all products/items in inventory)
        if re.search(
            r'\b(name\s+all(?:\s+the)?\s+products?|list\s+all(?:\s+the)?\s+products?|list\s+all\s+items?|'
            r'list\s+of\s+(?:all\s+)?(?:products?|items?)|(?:show|tell\s+me)\s+(?:all\s+)?(?:the\s+)?(?:names\s+of\s+)?(?:products?|items?)|'
            r'what\s+(?:are\s+all\s+the\s+)?products?\s+(?:do\s+we\s+have|are\s+in|in\s+(?:our\s+)?inventory)|'
            r'what\s+do\s+we\s+have\s+in\s+inventory|all\s+products\s+list|products?\s+list|all\s+products\s+in\s+(?:our\s+)?inventory|'
            r'sare\s+products?\s+ke\s+naam|sare\s+saman\s+ke\s+naam|sabhi\s+products?\s+ke\s+naam|'
            r'dukan\s+me\s+kya\s+kya\s+(?:saman|product|item)|dukan\s+me\s+kaun\s+kaun\s+se\s+product|'
            r'inventory\s+me\s+kya\s+kya\s+hai|inventory\s+me\s+kaun\s+se\s+product|sare\s+product\s+dikhao|'
            r'sare\s+saman\s+dikhao|products?\s+ki\s+list|saman\s+ki\s+list|anni\s+products\s+perlu|'
            r'products\s+list\s+chupinchu|inventory\s+lo\s+em\s+products\s+unnai)\b',
            text
        ):
            return ParsedCommand(intent="LIST_PRODUCTS", confidence=1.0)

        # 9. Count Total Products
        if re.search(r'\b(total\s+(?:kitna|kitne|kitni)?\s*products?|total\s+products?|how\s+many\s+(?:total\s+)?products?|how\s+many\s+(?:total\s+)?items?|(?:total|kul|motham)\s+(?:kitna|kitne|kitni|enni)?\s*(?:products?|items?|saman)|(?:products?|items?)\s+count|(?:kitna|kitne|kitni)\s+(?:products?|items?|saman))\b', text):
            # Only if not asking for "added"
            if not re.search(r'\b(added|add|aaye|jode|chadhe)\b', text):
                return ParsedCommand(intent="COUNT_PRODUCTS", time_range=time_range, confidence=1.0)

        # 10. Specific Product Stock Query (e.g. "How much rice is currently available?", "rice kitna hai")
        stock_query_match = re.search(r'\b(?:how\s+much|how\s+many)\s+([a-z\u0900-\u097F\u0C00-\u0C7F]+)\s+(?:is\s+)?(?:currently\s+)?(?:available|left|in\s+stock)\b', text)
        if stock_query_match:
            prod_name = stock_query_match.group(1).strip()
            return ParsedCommand(intent="STOCK_QUERY", product_text=prod_name, confidence=1.0)

        hindi_stock_match = re.search(r'([a-z\u0900-\u097F\u0C00-\u0C7F]+)\s+(?:kitna|kitne)\s+(?:hai|hain|bacha\s+hai|stock\s+hai)', text)
        if hindi_stock_match:
            prod_name = hindi_stock_match.group(1).strip()
            if prod_name not in ("stock", "item", "product", "total", "aaj"):
                return ParsedCommand(intent="STOCK_QUERY", product_text=prod_name, confidence=1.0)

        return None

    def _detect_intent(self, text: str) -> str:
        """Detect intent from keywords. More specific intents are checked first."""
        priority_order = ["LOW_STOCK_QUERY", "STOCK_QUERY", "STOCK_IN", "STOCK_OUT", "CANCEL"]
        
        for intent_name in priority_order:
            keywords = INTENT_KEYWORDS.get(intent_name, [])
            for kw in sorted(keywords, key=len, reverse=True):
                if re.search(r'(?:^|\s)' + re.escape(kw) + r'(?:\s|$)', text):
                    if intent_name == "CANCEL":
                        if re.search(r'\d', text) or any(u in text for u in ("kg", "packet", "bora", "bori", "bag", "carton", "box")):
                            continue
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
        num_match = re.search(r'(?:^|\s)(\d+(?:\.\d+)?)(?=\s|$|[a-z\u0900-\u097F\u0C00-\u0C7F])', text)
        if num_match:
            quantity = Decimal(num_match.group(1))
            text = text[:num_match.start()] + " " + text[num_match.end():]
            return quantity, text.strip()

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

        if intent in ("STOCK_QUERY", "GET_PRODUCT_STOCK"):
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

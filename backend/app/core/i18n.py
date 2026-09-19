import re
from collections import defaultdict

RESPONSES = {
    "hinglish": {
        "stock_added": "{quantity} {unit} {product} add ho gya, aur new quantity {balance} {balance_unit} hai.",
        "stock_removed": "{quantity} {unit} {product} remove ho gya, aur new quantity {balance} {balance_unit} hai.",
        "stock_query_response": "Aapke paas {product} ka stock {balance} {unit} hai.",
        "low_stock_response": "In items ka stock kam chal raha hai: {items}.",
        "product_not_found": "Maaf karein, {product} nahi mila.",
        "insufficient_stock": "Stock kam hai. Aapke paas sirf {balance} {unit} {product} hai.",
        "confirmation_prompt": "{quantity} {unit} {product} {action} karna hai, confirm karein?"
    },
    "hi_deva": {
        "stock_added": "{quantity} {unit} {product} जोड़ दिया गया, और नई मात्रा {balance} {balance_unit} है।",
        "stock_removed": "{quantity} {unit} {product} निकाल दिया गया, और नई मात्रा {balance} {balance_unit} है।",
        "stock_query_response": "आपके पास {product} का {balance} {unit} स्टॉक उपलब्ध है।",
        "low_stock_response": "इन items का स्टॉक कम है: {items}।",
        "product_not_found": "माफ़ करें, मुझे {product} नहीं मिला।",
        "insufficient_stock": "स्टॉक कम है। आपके पास केवल {balance} {unit} {product} है।",
        "confirmation_prompt": "क्या आप {quantity} {unit} {product} {action} करना चाहते हैं?"
    },
    "hi": {
        "stock_added": "{quantity} {unit} {product} add ho gya, aur new quantity {balance} {balance_unit} hai.",
        "stock_removed": "{quantity} {unit} {product} remove ho gya, aur new quantity {balance} {balance_unit} hai.",
        "stock_query_response": "Aapke paas {product} ka stock {balance} {unit} hai.",
        "low_stock_response": "In items ka stock kam hai: {items}.",
        "product_not_found": "Maaf karein, mujhe {product} nahi mila.",
        "insufficient_stock": "Stock kam hai. Aapke paas sirf {balance} {unit} {product} hai.",
        "confirmation_prompt": "Kya aap {quantity} {unit} {product} {action} karna chahte hain?"
    },
    "telugish": {
        "stock_added": "{quantity} {unit} {product} add aindi, mariyu kotha quantity {balance} {balance_unit} undi.",
        "stock_removed": "{quantity} {unit} {product} remove aindi, mariyu kotha quantity {balance} {balance_unit} undi.",
        "stock_query_response": "Mee daggara {product} {balance} {unit} stock undi.",
        "low_stock_response": "Ee items stock thakkuva ga unnai: {items}.",
        "product_not_found": "Kshaminchandi, {product} dorakaledu.",
        "insufficient_stock": "Stock chalu kadu. Mee daggara kevalam {balance} {unit} {product} undi.",
        "confirmation_prompt": "{product} {quantity} {unit} {action} cheyala?"
    },
    "te_script": {
        "stock_added": "{quantity} {unit} {product} విజయవంతంగా జోడించబడింది, మరియు కొత్త పరిమాణం {balance} {balance_unit}.",
        "stock_removed": "{quantity} {unit} {product} విజయవంతంగా తీసివేయబడింది, మరియు కొత్త పరిమాణం {balance} {balance_unit}.",
        "stock_query_response": "మీ దగ్గర {product} {balance} {unit} స్టాక్ ఉంది.",
        "low_stock_response": "ఈ items స్టాక్ తక్కువగా ఉన్నాయి: {items}.",
        "product_not_found": "క్షమించండి, {product} దొరకలేదు.",
        "insufficient_stock": "స్టాక్ సరిపోదు. మీ దగ్గర కేవలం {balance} {unit} {product} ఉంది.",
        "confirmation_prompt": "{product} {quantity} {unit} {action} చేయాలా?"
    },
    "te": {
        "stock_added": "{quantity} {unit} {product} add aindi, mariyu kotha quantity {balance} {balance_unit} undi.",
        "stock_removed": "{quantity} {unit} {product} remove aindi, mariyu kotha quantity {balance} {balance_unit} undi.",
        "stock_query_response": "Mee daggara {product} {balance} {unit} stock undi.",
        "low_stock_response": "Ee items stock thakkuva ga unnai: {items}.",
        "product_not_found": "Kshaminchandi, {product} dorakaledu.",
        "insufficient_stock": "Stock chalu kadu. Mee daggara kevalam {balance} {unit} {product} undi.",
        "confirmation_prompt": "{product} {quantity} {unit} {action} cheyala?"
    },
    "en": {
        "stock_added": "{quantity} {unit} {product} added successfully. New quantity is {balance} {balance_unit}.",
        "stock_removed": "{quantity} {unit} {product} removed successfully. New quantity is {balance} {balance_unit}.",
        "stock_query_response": "You have {balance} {unit} of {product} in stock.",
        "low_stock_response": "The following items are low in stock: {items}.",
        "product_not_found": "Sorry, I could not find {product}.",
        "insufficient_stock": "Not enough stock. You only have {balance} {unit} of {product}.",
        "confirmation_prompt": "Are you sure you want to {action} {quantity} {unit} of {product}?"
    }
}


def detect_speech_dialect(transcript: str, fallback_lang: str = "en") -> str:
    """Detects whether spoken input is:
    - 'hinglish': Romanized Hindi/English mix (e.g. '5 kg rice add kro', 'chawal kitna hai')
    - 'hi_deva': Hindi in Devanagari script (e.g. 'चावल 5 बोरी आया')
    - 'telugish': Romanized Telugu (e.g. '5 kg rice add cheyyi')
    - 'te_script': Telugu in Telugu script (e.g. 'బియ్యం 5 బస్తాలు')
    - 'en': Pure English (e.g. 'Add 5 kg of rice')
    """
    if not transcript or not transcript.strip():
        return fallback_lang or "en"

    # 1. Devanagari Unicode block check
    if re.search(r'[\u0900-\u097F]', transcript):
        return "hi_deva"

    # 2. Telugu Unicode block check
    if re.search(r'[\u0C00-\u0C7F]', transcript):
        return "te_script"

    text_lower = transcript.lower()
    words = re.findall(r'\b\w+\b', text_lower)

    # Hinglish / Hindi colloquial markers
    hinglish_markers = {
        "kro", "karo", "kardo", "kar", "aaya", "aayi", "aaye", "aagaya", "aagayi",
        "becha", "becho", "bech", "diya", "gaya", "gayi", "nikal", "nikalo",
        "nikala", "hatao", "dal", "daal", "dalo", "daalo", "jod", "jodo",
        "kitna", "kitne", "kitni", "bacha", "bache", "bachi", "hai", "hain",
        "kam", "laya", "kharid", "kharida", "chahiye", "dedo", "lelo", "batao", "btao",
        "ka", "ki", "ke", "me", "mein", "se", "aur", "bhi", "itna", "chawal",
        "chini", "tel", "atta", "namak", "chai", "doodh", "pyaz", "alu", "aloo"
    }

    # Telugish markers
    telugish_markers = {
        "cheyyi", "chesi", "chey", "vachindi", "vachayi", "ammeyyi", "ammamu",
        "ammali", "teesuko", "teeseyyi", "entha", "undi", "unnai", "thakkuva",
        "mariyu", "daggara", "kavali", "kotha", "biyyam", "panchadara", "nune",
        "pappu", "uppu", "paalu", "ullipaya"
    }

    h_count = sum(1 for w in words if w in hinglish_markers)
    t_count = sum(1 for w in words if w in telugish_markers)

    if h_count > 0 and h_count >= t_count:
        return "hinglish"
    if t_count > 0:
        return "telugish"

    # Fallback to provided language preference if set
    if fallback_lang in ("hi", "hindi"):
        return "hinglish"
    if fallback_lang in ("te", "telugu"):
        return "telugish"
    return "en"


def get_response(key: str, language: str, **kwargs) -> str:
    lang_key = (language or "en").lower()
    lang_responses = RESPONSES.get(lang_key)
    if not lang_responses:
        if "hi" in lang_key:
            lang_responses = RESPONSES["hinglish"]
        elif "te" in lang_key:
            lang_responses = RESPONSES["telugish"]
        else:
            lang_responses = RESPONSES["en"]

    template = lang_responses.get(key, RESPONSES["en"].get(key, ""))
    if not template:
        return ""

    # Map balance <-> quantity automatically for flexibility
    if "quantity" in kwargs and "balance" not in kwargs:
        kwargs["balance"] = kwargs["quantity"]
    if "balance" in kwargs and "quantity" not in kwargs:
        kwargs["quantity"] = kwargs["balance"]
    if "balance_unit" not in kwargs and "unit" in kwargs:
        kwargs["balance_unit"] = kwargs["unit"]

    try:
        return template.format(**kwargs)
    except KeyError:
        return template.format_map(defaultdict(str, kwargs))

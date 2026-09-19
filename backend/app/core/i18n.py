RESPONSES = {
    "en": {
        "stock_added": "{quantity} {unit} {product} added successfully. New balance is {balance} {balance_unit}.",
        "stock_removed": "{quantity} {unit} {product} removed successfully. New balance is {balance} {balance_unit}.",
        "stock_query_response": "You have {balance} {unit} of {product} in stock.",
        "low_stock_response": "The following items are low in stock: {items}.",
        "product_not_found": "Sorry, I could not find {product}.",
        "insufficient_stock": "Not enough stock. You only have {balance} {unit} of {product}.",
        "confirmation_prompt": "Are you sure you want to {action} {quantity} {unit} of {product}?"
    },
    "hi": {
        "stock_added": "{quantity} {unit} {product} सफलतापूर्वक जोड़ दिया गया। नया बैलेंस {balance} {balance_unit} है।",
        "stock_removed": "{quantity} {unit} {product} सफलतापूर्वक निकाल दिया गया। नया बैलेंस {balance} {balance_unit} है।",
        "stock_query_response": "आपके पास {product} का {balance} {unit} स्टॉक में है।",
        "low_stock_response": "इन items का स्टॉक कम है: {items}।",
        "product_not_found": "माफ़ करें, मुझे {product} नहीं मिला।",
        "insufficient_stock": "स्टॉक कम है। आपके पास सिर्फ {balance} {unit} {product} है।",
        "confirmation_prompt": "क्या आप {quantity} {unit} {product} {action} करना चाहते हैं?"
    },
    "te": {
        "stock_added": "{quantity} {unit} {product} విజయవంతంగా జోడించబడింది. కొత్త బ్యాలెన్స్ {balance} {balance_unit}.",
        "stock_removed": "{quantity} {unit} {product} విజయవంతంగా తీసివేయబడింది. కొత్త బ్యాలెన్స్ {balance} {balance_unit}.",
        "stock_query_response": "Mee daggara {product} {balance} {unit} stock undi.",
        "low_stock_response": "Ee items stock thakkuva ga unnai: {items}.",
        "product_not_found": "Kshaminchandi, {product} dorakaledu.",
        "insufficient_stock": "Stock chalu kadu. Mee daggara kevalam {balance} {unit} {product} undi.",
        "confirmation_prompt": "Meeru kachitanga {product} {quantity} {unit} {action} cheyalani anukuntunnara?"
    }
}

from collections import defaultdict

def get_response(key: str, language: str, **kwargs) -> str:
    lang_responses = RESPONSES.get(language, RESPONSES["en"])
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

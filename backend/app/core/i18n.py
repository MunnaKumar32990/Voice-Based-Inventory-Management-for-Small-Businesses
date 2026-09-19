RESPONSES = {
    "en": {
        "stock_added": "Added {quantity} {unit} of {product}. New balance is {balance} {balance_unit}.",
        "stock_removed": "Removed {quantity} {unit} of {product}. New balance is {balance} {balance_unit}.",
        "stock_query_response": "You have {balance} {unit} of {product} in stock.",
        "low_stock_response": "The following items are low in stock: {items}.",
        "product_not_found": "Sorry, I could not find the product {product}.",
        "insufficient_stock": "Not enough stock. You only have {balance} {unit} of {product}.",
        "confirmation_prompt": "Are you sure you want to {action} {quantity} {unit} of {product}?"
    },
    "hi": {
        "stock_added": "{product} ka {quantity} {unit} jod diya gaya. Naya balance {balance} {balance_unit} hai.",
        "stock_removed": "{product} ka {quantity} {unit} nikal liya gaya. Naya balance {balance} {balance_unit} hai.",
        "stock_query_response": "Aapke paas {product} ka {balance} {unit} stock mein hai.",
        "low_stock_response": "In items ka stock kam hai: {items}.",
        "product_not_found": "Maaf karein, mujhe {product} nahi mila.",
        "insufficient_stock": "Stock kam hai. Aapke paas sirf {balance} {unit} {product} hai.",
        "confirmation_prompt": "Kya aap waqai {product} ka {quantity} {unit} {action} chahte hain?"
    },
    "te": {
        "stock_added": "{product} {quantity} {unit} jodincha badindi. Kotta balance {balance} {balance_unit}.",
        "stock_removed": "{product} {quantity} {unit} tisiveya badindi. Kotta balance {balance} {balance_unit}.",
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

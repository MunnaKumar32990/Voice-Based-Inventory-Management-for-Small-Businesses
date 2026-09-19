from decimal import Decimal

# Canonical units must match nlp_service.UNIT_ALIASES canonical forms:
# kg, g, quintal, litre, ml, piece, dozen, bag, carton, box, packet, bottle, can, bundle
UNIT_ALIASES = {
    "kg": "kg", "kgs": "kg", "kilogram": "kg", "kilograms": "kg", "kilo": "kg", "kilos": "kg",
    "g": "g", "gm": "g", "gms": "g", "gram": "g", "grams": "g",
    "quintal": "quintal", "quintals": "quintal",
    "l": "litre", "ltr": "litre", "liter": "litre", "litre": "litre", "litres": "litre", "liters": "litre",
    "ml": "ml", "milliliter": "ml", "millilitre": "ml", "milliliters": "ml", "millilitres": "ml",
    "piece": "piece", "pieces": "piece", "pc": "piece", "pcs": "piece",
    "box": "box", "boxes": "box",
    "bag": "bag", "bags": "bag", "bori": "bag", "bora": "bag",
    "dozen": "dozen", "dozens": "dozen", "darjan": "dozen", "darzan": "dozen",
    "carton": "carton", "cartons": "carton",
    "packet": "packet", "packets": "packet", "pkt": "packet", "pkts": "packet",
    "bottle": "bottle", "bottles": "bottle",
    "can": "can", "cans": "can",
    "bundle": "bundle", "bundles": "bundle",
}

class UnitService:
    def normalize_unit(self, unit_text: str) -> str:
        if not unit_text:
            return ""
        return UNIT_ALIASES.get(unit_text.lower(), unit_text.lower())

    def is_valid_unit(self, product: dict, unit: str) -> bool:
        if not unit:
            return True
        base_unit = product.get("base_unit")
        if unit == base_unit:
            return True
        allowed_units = product.get("allowed_units", [])
        if unit in allowed_units:
            return True
        conversions = product.get("conversions", [])
        if isinstance(conversions, dict):
            return unit in conversions
        if isinstance(conversions, list):
            return any(c.get("from_unit") == unit for c in conversions)
        return False

    def convert_to_base_unit(self, product: dict, quantity: Decimal, unit: str):
        base_unit = product.get("base_unit")
        if not unit or unit == base_unit:
            return quantity, base_unit

        conversions = product.get("conversions", [])
        if isinstance(conversions, dict) and unit in conversions:
            factor = Decimal(str(conversions[unit]))
            return quantity * factor, base_unit
        elif isinstance(conversions, list):
            for c in conversions:
                if c.get("from_unit") == unit:
                    # to_unit should equal base_unit, but accept any factor regardless
                    factor = Decimal(str(c.get("factor", 1)))
                    return quantity * factor, base_unit

        # Standard conversions (product-independent)
        if unit == "g" and base_unit == "kg":
            return quantity * Decimal("0.001"), base_unit
        if unit == "kg" and base_unit == "g":
            return quantity * Decimal("1000"), base_unit
        if unit == "ml" and base_unit == "litre":
            return quantity * Decimal("0.001"), base_unit
        if unit == "litre" and base_unit == "ml":
            return quantity * Decimal("1000"), base_unit
        if unit == "quintal" and base_unit == "kg":
            return quantity * Decimal("100"), base_unit
        if unit == "dozen" and base_unit == "piece":
            return quantity * Decimal("12"), base_unit
        if unit == "bag" and base_unit == "kg":
            # Product-specific bag size preferred; fallback to 25kg default
            return quantity * Decimal("25"), base_unit

        # Allowed-but-unconvertible packaging units (packet, bottle, piece, box...)
        # Track in the spoken unit instead of crashing — balance stores effective unit.
        allowed_units = product.get("allowed_units", []) or []
        norm_allowed = [self.normalize_unit(a) for a in allowed_units]
        if unit in norm_allowed or unit == self.normalize_unit(base_unit or ""):
            return quantity, unit

        raise ValueError(f"Unknown unit conversion from {unit} to {base_unit} for product {product.get('name', product.get('display_name'))}")

    def get_unit_display(self, unit: str, quantity: Decimal) -> str:
        if quantity == 1 or unit in ["kg", "g", "litre", "ml"]:
            return unit
        if unit == "piece": return "pieces"
        if unit == "box": return "boxes"
        return f"{unit}s"

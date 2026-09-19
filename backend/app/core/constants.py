from enum import Enum

class OperationType(str, Enum):
    STOCK_IN = "STOCK_IN"
    STOCK_OUT = "STOCK_OUT"
    ADJUSTMENT = "ADJUSTMENT"

class IntentType(str, Enum):
    STOCK_IN = "STOCK_IN"
    STOCK_OUT = "STOCK_OUT"
    STOCK_QUERY = "STOCK_QUERY"
    LOW_STOCK_QUERY = "LOW_STOCK_QUERY"
    REORDER_QUERY = "REORDER_QUERY"
    PRODUCT_CREATE = "PRODUCT_CREATE"
    CANCEL = "CANCEL"
    HELP = "HELP"
    UNKNOWN = "UNKNOWN"

class TransactionSource(str, Enum):
    VOICE = "VOICE"
    MANUAL = "MANUAL"
    IMPORT = "IMPORT"

class UserRole(str, Enum):
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    STAFF = "STAFF"

class AlertType(str, Enum):
    LOW_STOCK = "LOW_STOCK"

class AlertStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"

SUPPORTED_UNITS = {
    "kg": "Kilograms",
    "g": "Grams",
    "quintal": "Quintals",
    "litre": "Litres",
    "ml": "Millilitres",
    "piece": "Pieces",
    "dozen": "Dozens",
    "bag": "Bags",
    "carton": "Cartons",
    "box": "Boxes",
    "packet": "Packets",
    "bottle": "Bottles",
    "can": "Cans",
    "bundle": "Bundles",
}

UNIT_CATEGORIES = {
    "weight": ["kg", "g", "quintal"],
    "volume": ["litre", "ml"],
    "count": ["piece", "dozen"],
    "package": ["bag", "carton", "box", "packet", "bottle", "can", "bundle"],
}

NUMBER_WORDS = {
    "en": {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10},
    "hi": {"ek": 1, "do": 2, "teen": 3, "chaar": 4, "paanch": 5, "chhah": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10},
    "te": {"okati": 1, "rendu": 2, "moodu": 3, "nalugu": 4, "aidu": 5, "aru": 6, "edu": 7, "enimidi": 8, "tommidi": 9, "padi": 10}
}

DIRECTION_KEYWORDS = {
    "en": {"add": IntentType.STOCK_IN, "remove": IntentType.STOCK_OUT},
    "hi": {"dalo": IntentType.STOCK_IN, "nikalo": IntentType.STOCK_OUT},
    "te": {"veyi": IntentType.STOCK_IN, "tiyi": IntentType.STOCK_OUT}
}

UNIT_KEYWORDS = {
    "en": {"kilo": "kg", "gram": "g", "liter": "litre", "litre": "litre", "piece": "piece", "packet": "packet", "bag": "bag", "box": "box", "carton": "carton"},
    "hi": {"kilo": "kg", "gram": "g", "liter": "litre", "litre": "litre", "piece": "piece", "packet": "packet", "bag": "bag", "box": "box", "carton": "carton"},
    "te": {"kilo": "kg", "gram": "g", "liter": "litre", "litre": "litre", "piece": "piece", "packet": "packet", "bag": "bag", "box": "box", "carton": "carton"}
}

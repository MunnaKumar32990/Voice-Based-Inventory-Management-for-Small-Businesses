"""Unit tests for QueryService, date resolution, and analytical query parsing."""
import pytest
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from app.services.nlp_service import NLPService
from app.services.query_service import QueryService, resolve_date_range


class FakeCursor:
    def __init__(self, docs):
        self._docs = docs

    def sort(self, *args, **kwargs):
        return self

    def limit(self, n):
        self._docs = self._docs[:n]
        return self

    async def to_list(self, length=100):
        return self._docs[:length]


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    async def count_documents(self, filt):
        return len(self._filter_docs(filt))

    async def find_one(self, filt, session=None):
        matched = self._filter_docs(filt)
        return dict(matched[0]) if matched else None

    def find(self, filt):
        matched = self._filter_docs(filt)
        return FakeCursor(matched)

    def _filter_docs(self, filt):
        out = []
        for d in self.docs:
            match = True
            for k, v in filt.items():
                if k == "$or":
                    continue
                if k == "created_at" and isinstance(v, dict):
                    # Check date range
                    dt = d.get("created_at")
                    if dt:
                        if "$gte" in v and dt < v["$gte"]:
                            match = False
                            break
                        if "$lte" in v and dt > v["$lte"]:
                            match = False
                            break
                elif d.get(k) != v:
                    match = False
                    break
            if match:
                out.append(d)
        return out


class FakeDB:
    def __init__(self, shop_id: str):
        self.shop_id = shop_id
        now = datetime.now(timezone.utc)
        self.p1_id = str(ObjectId())
        self.p2_id = str(ObjectId())
        self.p3_id = str(ObjectId())

        self.shops = FakeCollection([
            {"_id": shop_id, "name": "Test Shop", "timezone": "Asia/Kolkata"}
        ])
        self.products = FakeCollection([
            {"_id": self.p1_id, "shop_id": shop_id, "display_name": "Rice", "name": "Rice", "normalized_name": "rice", "base_unit": "kg", "reorder_threshold": 50, "active": True, "created_at": now},
            {"_id": self.p2_id, "shop_id": shop_id, "display_name": "Sugar", "name": "Sugar", "normalized_name": "sugar", "base_unit": "kg", "reorder_threshold": 20, "active": True, "created_at": now},
            {"_id": self.p3_id, "shop_id": shop_id, "display_name": "Cooking Oil", "name": "Cooking Oil", "normalized_name": "oil", "base_unit": "litre", "reorder_threshold": 10, "active": True, "created_at": now - timedelta(days=2)},
        ])
        self.stock_balances = FakeCollection([
            {"shop_id": shop_id, "product_id": self.p1_id, "quantity": 100.0, "unit": "kg"},
            {"shop_id": shop_id, "product_id": self.p2_id, "quantity": 8.0, "unit": "kg"},  # low stock (8 <= 20)
            {"shop_id": shop_id, "product_id": self.p3_id, "quantity": 0.0, "unit": "litre"}, # out of stock
        ])
        self.transactions = FakeCollection([
            {"_id": str(ObjectId()), "shop_id": shop_id, "product_id": self.p1_id, "operation": "STOCK_IN", "quantity": 25.0, "unit": "kg", "timestamp": now, "created_at": now},
            {"_id": str(ObjectId()), "shop_id": shop_id, "product_id": self.p2_id, "operation": "STOCK_OUT", "quantity": 2.0, "unit": "kg", "timestamp": now, "created_at": now},
        ])


@pytest.fixture
def nlp():
    return NLPService()


@pytest.fixture
def query_svc():
    return QueryService()


def test_date_range_resolution():
    today = resolve_date_range("today")
    assert today is not None
    start, end = today
    assert start < end
    assert (end - start).total_seconds() >= 86399

    week = resolve_date_range("this_week")
    assert week is not None
    assert week[0] < week[1]

    none_range = resolve_date_range("invalid_time_range_123")
    assert none_range is None


def test_nlp_analytical_query_detection(nlp):
    # 1. Total products
    c1 = nlp.parse_command("How many products are there?")
    assert c1.intent == "COUNT_PRODUCTS"

    # 2. Products added today
    c2 = nlp.parse_command("How many products were added today?")
    assert c2.intent == "COUNT_PRODUCTS_ADDED"
    assert c2.time_range == "today"

    # 3. Which products added today
    c3 = nlp.parse_command("Which products were added today?")
    assert c3.intent == "LIST_PRODUCTS_ADDED"
    assert c3.time_range == "today"

    # 4. Stock in transactions today
    c4 = nlp.parse_command("How many stock-in transactions happened today?")
    assert c4.intent == "COUNT_TRANSACTIONS"
    assert c4.operation == "STOCK_IN"
    assert c4.time_range == "today"

    # 5. Stock out transactions today
    c5 = nlp.parse_command("How many stock-out transactions happened today?")
    assert c5.intent == "COUNT_TRANSACTIONS"
    assert c5.operation == "STOCK_OUT"
    assert c5.time_range == "today"

    # 6. Low stock products
    c6 = nlp.parse_command("What products are low in stock?")
    assert c6.intent == "LOW_STOCK_QUERY"

    # 7. Out of stock products
    c7 = nlp.parse_command("Which products are out of stock?")
    assert c7.intent == "LIST_OUT_OF_STOCK"

    # 8. Rice available
    c8 = nlp.parse_command("How much rice is currently available?")
    assert c8.intent == "STOCK_QUERY"
    assert "rice" in c8.product_text

    # 9. Today's inventory activity
    c9 = nlp.parse_command("What happened to my inventory today?")
    assert c9.intent == "GET_TODAY_ACTIVITY"

    # 10. Latest transactions
    c10 = nlp.parse_command("Show me the latest transactions.")
    assert c10.intent == "GET_RECENT_TRANSACTIONS"

    # 11. Products added this week
    c11 = nlp.parse_command("How many products were added this week?")
    assert c11.intent == "COUNT_PRODUCTS_ADDED"
    assert c11.time_range == "this_week"

    # 12. Multilingual queries (Hindi/Hinglish)
    c12_a = nlp.parse_command("aaj kitne product add huye")
    assert c12_a.intent == "COUNT_PRODUCTS_ADDED"
    assert c12_a.time_range == "today"

    c12_b = nlp.parse_command("aaj kitna stock in hua")
    assert c12_b.intent == "COUNT_TRANSACTIONS"
    assert c12_b.operation == "STOCK_IN"

    c12_c = nlp.parse_command("chawal kitna bacha hai")
    assert c12_c.intent == "STOCK_QUERY"
    assert "chawal" in c12_c.product_text

    c12_d = nlp.parse_command("aaj inventory me kya hua")
    assert c12_d.intent == "GET_TODAY_ACTIVITY"

    c12_e = nlp.parse_command("sabse jyada stock kiska hai")
    assert c12_e.intent == "GET_TOP_STOCK_PRODUCTS"
    assert c12_e.order == "highest"


@pytest.mark.asyncio
async def test_query_service_execution(query_svc):
    shop_id = "test_shop_1"
    db = FakeDB(shop_id)

    # 1. Total products
    res1 = await query_svc.execute_query(db, shop_id, "COUNT_PRODUCTS", {})
    assert res1["status"] == "answered"
    assert res1["structured_data"]["count"] == 3
    assert "3" in res1["message"]

    # 2. Low stock query (Sugar is 8 <= 20)
    res2 = await query_svc.execute_query(db, shop_id, "LOW_STOCK_QUERY", {})
    assert res2["status"] == "answered"
    assert res2["structured_data"]["count"] == 1
    assert res2["structured_data"]["items"][0]["product_name"] == "Sugar"

    # 3. Out of stock query (Cooking Oil is 0)
    res3 = await query_svc.execute_query(db, shop_id, "LIST_OUT_OF_STOCK", {})
    assert res3["status"] == "answered"
    assert res3["structured_data"]["count"] == 1
    assert res3["structured_data"]["items"][0]["product_name"] == "Cooking Oil"

    # 4. Top stock query
    res4 = await query_svc.execute_query(db, shop_id, "GET_TOP_STOCK_PRODUCTS", {"order": "highest"})
    assert res4["status"] == "answered"
    assert res4["structured_data"]["items"][0]["product_name"] == "Rice"
    assert res4["structured_data"]["items"][0]["quantity"] == 100.0

    # 5. Multilingual output test (Hindi)
    res5_hi = await query_svc.execute_query(db, shop_id, "COUNT_PRODUCTS", {}, language="hinglish")
    assert "kul 3 products hain" in res5_hi["message"]


def test_meta_product_words_and_total_kitna_queries(nlp):
    # Bug reported in screenshot: 'total kitna products hai' failing with 'Maaf karein, total products nahi mila'
    queries = [
        "total kitna products hai",
        "total kitne products hain",
        "meri dukan me kitna products hai",
        "total products kitna hai",
        "kitne products hain",
        "total items kitne hain",
        "dukan me total kitne products hai",
    ]
    for q in queries:
        parsed = nlp.parse_command(q)
        assert parsed.intent == "COUNT_PRODUCTS", f"Failed for '{q}': got intent {parsed.intent}"


@pytest.mark.asyncio
async def test_ask_database_assistant_fallback(query_svc):
    shop_id = "test_shop_1"
    db = FakeDB(shop_id)

    # 1. Broad category inquiry
    cat_res = await query_svc.ask_database_assistant(db, shop_id, "dukan me kya categories hai", "hinglish")
    assert cat_res["status"] == "answered"
    assert cat_res["query_type"] == "CATEGORY_QUERY"
    assert "Categories" in cat_res["title"]

    # 2. Total count inquiry via database assistant fallback
    count_res = await query_svc.ask_database_assistant(db, shop_id, "total kitna products hai", "hinglish")
    assert count_res["status"] == "answered"
    assert count_res["structured_data"]["count"] == 3

    # 3. Name/list all products inquiry via database assistant fallback
    list_res = await query_svc.ask_database_assistant(db, shop_id, "name all the products we have in our inventory", "en")
    assert list_res["status"] == "answered"
    assert list_res["query_type"] == "LIST_PRODUCTS"
    assert list_res["structured_data"]["count"] == 3
    assert len(list_res["structured_data"]["items"]) == 3


def test_list_products_parsing_and_execution(nlp):
    queries = [
        "name all the products we have in our inventory",
        "list all the products",
        "list all products",
        "list all items",
        "show all products",
        "what products do we have in our inventory",
        "sare products ke naam batao",
        "dukan me kya kya saman hai",
        "sabhi products ke naam",
        "anni products perlu cheppu",
    ]
    for q in queries:
        parsed = nlp.parse_command(q)
        assert parsed.intent == "LIST_PRODUCTS", f"Failed for '{q}': got intent {parsed.intent}"


@pytest.mark.asyncio
async def test_query_service_list_products(query_svc):
    shop_id = "test_shop_1"
    db = FakeDB(shop_id)

    res = await query_svc.execute_query(db, shop_id, "LIST_PRODUCTS", {})
    assert res["status"] == "answered"
    assert res["query_type"] == "LIST_PRODUCTS"
    assert res["structured_data"]["count"] == 3
    assert len(res["structured_data"]["items"]) == 3
    names = [i["product_name"] for i in res["structured_data"]["items"]]
    assert "Rice" in names
    assert "Sugar" in names
    assert "Cooking Oil" in names



"""Inventory commit logic tested against an in-memory fake DB (no Mongo needed)."""
import pytest
from decimal import Decimal
from bson import ObjectId
from app.services.inventory_service import InventoryService


class FakeResult:
    def __init__(self, inserted_id=None, modified_count=0, upserted_id=None):
        self.inserted_id = inserted_id
        self.modified_count = modified_count
        self.upserted_id = upserted_id


class FakeCollection:
    def __init__(self):
        self.docs = {}

    async def find_one(self, filt, session=None):
        for d in self.docs.values():
            if all(d.get(k) == v for k, v in filt.items() if k != "_id" or "_id" in d):
                # handle _id specially (ObjectId equality)
                ok = True
                for k, v in filt.items():
                    if d.get(k) != v:
                        ok = False
                        break
                if ok:
                    return dict(d)
        return None

    async def insert_one(self, doc, session=None):
        _id = doc.get("_id", ObjectId())
        doc = dict(doc)
        doc["_id"] = _id
        self.docs[str(_id)] = doc
        return FakeResult(inserted_id=_id)

    async def update_one(self, filt, update, upsert=False, session=None):
        existing = await self.find_one(filt)
        if existing:
            _id = existing["_id"]
            set_data = update.get("$set", {})
            existing.update(set_data)
            if "$inc" in update:
                for k, v in update["$inc"].items():
                    existing[k] = existing.get(k, 0) + v
            self.docs[str(_id)] = existing
            return FakeResult(modified_count=1)
        if upsert:
            doc = dict(filt)
            doc.update(update.get("$set", {}))
            _id = ObjectId()
            doc["_id"] = _id
            self.docs[str(_id)] = doc
            return FakeResult(modified_count=0, upserted_id=_id)
        return FakeResult(modified_count=0)

    async def update_many(self, filt, update, session=None):
        n = 0
        for _id, d in list(self.docs.items()):
            if all(d.get(k) == v for k, v in filt.items()):
                d.update(update.get("$set", {}))
                n += 1
        return FakeResult(modified_count=n)

    def find(self, filt):
        matched = [dict(d) for d in self.docs.values()
                   if all(d.get(k) == v for k, v in filt.items())]
        return FakeCursor(matched)


class FakeCursor:
    def __init__(self, docs):
        self._docs = docs

    def sort(self, *a, **k):
        return self

    def skip(self, n):
        self._docs = self._docs[n:]
        return self

    def limit(self, n):
        self._docs = self._docs[:n]
        return self

    async def to_list(self, length=None):
        return self._docs


class FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def start_transaction(self):
        return self


class FakeClient:
    async def start_session(self):
        return FakeSession()


class FakeDB:
    def __init__(self):
        self.products = FakeCollection()
        self.stock_balances = FakeCollection()
        self.transactions = FakeCollection()
        self.alerts = FakeCollection()
        self.client = FakeClient()

    def __getitem__(self, name):
        return getattr(self, name)


@pytest.fixture
def db():
    d = FakeDB()
    pid = ObjectId()
    d.products.docs[str(pid)] = {
        "_id": pid, "shop_id": "shop1", "display_name": "Rice", "name": "Rice",
        "normalized_name": "rice", "base_unit": "kg",
        "allowed_units": ["kg", "bag", "g"],
        "conversions": [{"from_unit": "bag", "to_unit": "kg", "factor": 25}],
        "reorder_threshold": 50, "active": True,
    }
    d._pid = str(pid)
    return d


@pytest.mark.asyncio
async def test_stock_in_and_out(db):
    svc = InventoryService()
    r1 = await svc.commit_transaction(db, "shop1", "u1", db._pid, "STOCK_IN",
                                      Decimal(5), "bag", "purchase", "manual", "k1")
    assert r1["new_balance"] == 125.0
    r2 = await svc.commit_transaction(db, "shop1", "u1", db._pid, "STOCK_OUT",
                                      Decimal(25), "kg", "sale", "manual", "k2")
    assert r2["new_balance"] == 100.0


@pytest.mark.asyncio
async def test_insufficient_stock_blocked(db):
    svc = InventoryService()
    with pytest.raises(ValueError, match="Insufficient stock"):
        await svc.commit_transaction(db, "shop1", "u1", db._pid, "STOCK_OUT",
                                     Decimal(9999), "kg", "sale", "manual", "k3")


@pytest.mark.asyncio
async def test_idempotent_retry(db):
    svc = InventoryService()
    r1 = await svc.commit_transaction(db, "shop1", "u1", db._pid, "STOCK_IN",
                                      Decimal(1), "kg", "", "manual", "same-key")
    r2 = await svc.commit_transaction(db, "shop1", "u1", db._pid, "STOCK_IN",
                                      Decimal(1), "kg", "", "manual", "same-key")
    assert r2["status"] == "already_processed"
    assert r2["transaction_id"] == r1["transaction_id"]
    # Only one ledger entry
    assert len(db.transactions.docs) == 1


@pytest.mark.asyncio
async def test_adjustment_sets_absolute_level(db):
    svc = InventoryService()
    r = await svc.commit_transaction(db, "shop1", "u1", db._pid, "ADJUSTMENT",
                                     Decimal(42), "kg", "correction", "manual", "adj1")
    assert r["new_balance"] == 42.0


@pytest.mark.asyncio
async def test_cross_shop_product_rejected(db):
    svc = InventoryService()
    with pytest.raises(ValueError, match="Product not found"):
        await svc.commit_transaction(db, "other-shop", "u1", db._pid, "STOCK_IN",
                                     Decimal(1), "kg", "", "manual", "x1")

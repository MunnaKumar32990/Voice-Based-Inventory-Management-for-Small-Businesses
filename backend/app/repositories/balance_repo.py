from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
from decimal import Decimal

class BalanceRepository:
    async def find_by_product(self, db: AsyncIOMotorDatabase, shop_id: str, product_id: str, session=None):
        return await db.stock_balances.find_one({"shop_id": shop_id, "product_id": str(product_id)}, session=session)

    async def find_all(self, db: AsyncIOMotorDatabase, shop_id: str):
        cursor = db.stock_balances.find({"shop_id": shop_id})
        return await cursor.to_list(length=1000)

    async def find_low_stock(self, db: AsyncIOMotorDatabase, shop_id: str):
        """Products whose balance is at/below their reorder threshold (Python-side join; avoids $toObjectId crashes)."""
        balances = await self.find_all(db, shop_id)
        if not balances:
            return []
        products = await db.products.find({"shop_id": shop_id, "active": True}).to_list(length=2000)
        pmap = {str(p["_id"]): p for p in products}
        # Also index by string _id in case product_id stored as ObjectId string variant
        low = []
        for b in balances:
            pid = str(b.get("product_id", ""))
            product = pmap.get(pid)
            if not product:
                continue
            threshold = product.get("reorder_threshold", product.get("low_stock_threshold", 0))
            try:
                qty = float(b.get("quantity", 0))
                thr = float(threshold or 0)
            except (TypeError, ValueError):
                continue
            if qty <= thr:
                low.append({
                    "product_id": pid,
                    "product_name": product.get("display_name", product.get("name", "")),
                    "quantity": qty,
                    "unit": b.get("unit", product.get("base_unit", "piece")),
                    "threshold": thr,
                    "category": product.get("category", ""),
                })
        return low

    async def upsert(self, db: AsyncIOMotorDatabase, shop_id: str, product_id: str, quantity: Decimal, unit: str, session=None):
        now = datetime.now(timezone.utc)
        result = await db.stock_balances.update_one(
            {"shop_id": shop_id, "product_id": str(product_id)},
            {
                "$set": {"quantity": float(quantity), "unit": unit, "updated_at": now},
                "$setOnInsert": {"created_at": now},
                "$inc": {"version": 1},
            },
            upsert=True,
            session=session
        )
        return result.modified_count > 0 or result.upserted_id is not None

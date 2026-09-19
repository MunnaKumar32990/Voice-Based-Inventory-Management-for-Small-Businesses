from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId

class AlertRepository:
    async def find_open(self, db: AsyncIOMotorDatabase, shop_id: str):
        cursor = db.alerts.find({"shop_id": shop_id, "status": "OPEN"})
        return await cursor.to_list(length=100)

    async def upsert_low_stock(self, db: AsyncIOMotorDatabase, shop_id: str, product_id: str, current_qty: float, threshold: float, session=None):
        now = datetime.now(timezone.utc)
        await db.alerts.update_one(
            {"shop_id": shop_id, "product_id": str(product_id), "status": "OPEN"},
            {"$set": {
                "current_quantity": current_qty,
                "threshold": threshold,
                "status": "OPEN",
                "type": "LOW_STOCK",
                "alert_type": "LOW_STOCK",
                "last_notified_at": now,
                "updated_at": now,
            },
             "$setOnInsert": {"created_at": now}},
            upsert=True,
            session=session
        )

    async def resolve(self, db: AsyncIOMotorDatabase, shop_id: str, product_id: str, session=None):
        now = datetime.now(timezone.utc)
        await db.alerts.update_many(
            {"shop_id": shop_id, "product_id": str(product_id), "status": "OPEN"},
            {"$set": {"status": "RESOLVED", "updated_at": now, "resolved_at": now}},
            session=session
        )

    async def resolve_by_id(self, db: AsyncIOMotorDatabase, shop_id: str, alert_id: str):
        """Resolve a single alert by its _id. Returns True if resolved."""
        try:
            oid = ObjectId(str(alert_id))
        except (InvalidId, TypeError, ValueError):
            oid = None
        filt = {"shop_id": shop_id, "status": "OPEN"}
        if oid is not None:
            # Match either ObjectId or string _id
            filt = {"shop_id": shop_id, "status": "OPEN",
                    "$or": [{"_id": oid}, {"_id": str(alert_id)}]}
        else:
            filt["_id"] = str(alert_id)
        now = datetime.now(timezone.utc)
        result = await db.alerts.update_one(
            filt, {"$set": {"status": "RESOLVED", "updated_at": now, "resolved_at": now}}
        )
        return result.modified_count > 0

    async def count_open(self, db: AsyncIOMotorDatabase, shop_id: str):
        return await db.alerts.count_documents({"shop_id": shop_id, "status": "OPEN"})

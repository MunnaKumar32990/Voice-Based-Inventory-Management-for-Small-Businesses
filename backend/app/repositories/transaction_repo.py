from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timezone

class TransactionRepository:
    async def insert(self, db: AsyncIOMotorDatabase, txn_doc: dict, session=None):
        result = await db.transactions.insert_one(txn_doc, session=session)
        return str(result.inserted_id)

    async def find_by_shop(self, db: AsyncIOMotorDatabase, shop_id: str, product_id: str = None, limit: int = 50, skip: int = 0):
        query = {"shop_id": shop_id}
        if product_id:
            query["product_id"] = product_id
        cursor = db.transactions.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def find_by_idempotency_key(self, db: AsyncIOMotorDatabase, shop_id: str, key: str):
        return await db.transactions.find_one({"shop_id": shop_id, "idempotency_key": key})

    async def count_today(self, db: AsyncIOMotorDatabase, shop_id: str, operation: str = None):
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        query = {"shop_id": shop_id, "timestamp": {"$gte": today}}
        if operation:
            query["operation"] = operation
        return await db.transactions.count_documents(query)

    async def find_recent(self, db: AsyncIOMotorDatabase, shop_id: str, limit: int = 10):
        cursor = db.transactions.find({"shop_id": shop_id}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

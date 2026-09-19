from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from bson.errors import InvalidId
import re


def _safe_object_id(value):
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError, ValueError):
        return None


class ProductRepository:
    async def find_by_id(self, db: AsyncIOMotorDatabase, shop_id: str, product_id: str):
        oid = _safe_object_id(product_id)
        if oid is not None:
            doc = await db.products.find_one({"_id": oid, "shop_id": shop_id})
            if doc:
                return doc
        # Fallback: product_id stored as plain string
        return await db.products.find_one({"_id": str(product_id), "shop_id": shop_id})

    async def find_all(self, db: AsyncIOMotorDatabase, shop_id: str, active_only: bool = True, search: str = None):
        query = {"shop_id": shop_id}
        if active_only:
            query["active"] = True
        if search:
            escaped = re.escape(search)
            search_cond = [
                {"name": {"$regex": escaped, "$options": "i"}},
                {"display_name": {"$regex": escaped, "$options": "i"}},
                {"normalized_name": {"$regex": escaped, "$options": "i"}},
                {"aliases.text": {"$regex": escaped, "$options": "i"}},
                {"aliases.normalized": {"$regex": escaped, "$options": "i"}},
            ]
            query = {"$and": [query, {"$or": search_cond}]}
        cursor = db.products.find(query)
        return await cursor.to_list(length=1000)

    async def find_by_normalized_name(self, db: AsyncIOMotorDatabase, shop_id: str, name: str):
        return await db.products.find_one({"shop_id": shop_id, "normalized_name": name})

    async def find_by_alias(self, db: AsyncIOMotorDatabase, shop_id: str, alias_text: str):
        cursor = db.products.find({
            "shop_id": shop_id,
            "$or": [
                {"aliases.text": alias_text},
                {"aliases.normalized": alias_text},
            ],
        })
        return await cursor.to_list(length=100)

    async def create(self, db: AsyncIOMotorDatabase, product_doc: dict):
        result = await db.products.insert_one(product_doc)
        return str(result.inserted_id)

    async def update(self, db: AsyncIOMotorDatabase, shop_id: str, product_id: str, update_fields: dict):
        oid = _safe_object_id(product_id)
        filt = {"shop_id": shop_id}
        if oid is not None:
            filt["_id"] = oid
        else:
            filt["_id"] = str(product_id)
        result = await db.products.update_one(filt, {"$set": update_fields})
        return result.modified_count > 0

    async def search_products(self, db: AsyncIOMotorDatabase, shop_id: str, query_text: str):
        regex = re.compile(re.escape(query_text), re.IGNORECASE)
        cursor = db.products.find({
            "shop_id": shop_id,
            "$or": [
                {"name": regex},
                {"display_name": regex},
                {"normalized_name": regex},
                {"aliases.text": regex},
                {"aliases.normalized": regex},
            ]
        })
        return await cursor.to_list(length=50)

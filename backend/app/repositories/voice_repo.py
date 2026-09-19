from motor.motor_asyncio import AsyncIOMotorDatabase

class VoiceRepository:
    """Voice interactions use string UUID _ids (see api/voice.py), never ObjectId."""

    async def insert(self, db: AsyncIOMotorDatabase, interaction_doc: dict):
        result = await db.voice_interactions.insert_one(interaction_doc)
        return str(result.inserted_id)

    async def find_by_id(self, db: AsyncIOMotorDatabase, interaction_id: str, shop_id: str = None):
        filt = {"_id": str(interaction_id)}
        if shop_id:
            filt["shop_id"] = shop_id
        return await db.voice_interactions.find_one(filt)

    async def update_status(self, db: AsyncIOMotorDatabase, interaction_id: str, status: str, shop_id: str = None, **extra):
        update_data = {"status": status}
        update_data.update(extra)
        filt = {"_id": str(interaction_id)}
        if shop_id:
            filt["shop_id"] = shop_id
        result = await db.voice_interactions.update_one(filt, {"$set": update_data})
        return result.modified_count > 0

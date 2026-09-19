from motor.motor_asyncio import AsyncIOMotorClient

class MongoDBManager:
    client: AsyncIOMotorClient = None
    db = None

    async def connect(self, uri: str, db_name: str):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        print(f"Connected to MongoDB: {db_name}")

    async def disconnect(self):
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    def get_database(self):
        if self.db is None:
            from app.config import settings
            self.client = AsyncIOMotorClient(settings.MONGODB_URI)
            self.db = self.client[settings.DB_NAME]
        return self.db

    async def create_indexes(self):
        if self.db is None:
            return
        
        # Products
        await self.db["products"].create_index([("shop_id", 1), ("normalized_name", 1)])
        await self.db["products"].create_index([("shop_id", 1), ("active", 1)])
        await self.db["products"].create_index([("aliases.normalized", 1)])
        await self.db["products"].create_index([("aliases.text", 1)])
        
        # Stock Balances
        await self.db["stock_balances"].create_index([("shop_id", 1), ("product_id", 1)], unique=True)
        
        # Transactions (ledger) — field is `timestamp`; idempotency must be unique per shop
        await self.db["transactions"].create_index([("shop_id", 1), ("product_id", 1), ("timestamp", -1)])
        await self.db["transactions"].create_index([("shop_id", 1), ("timestamp", -1)])
        await self.db["transactions"].create_index(
            [("shop_id", 1), ("idempotency_key", 1)], unique=True, sparse=True
        )
        
        # Alerts
        await self.db["alerts"].create_index([("shop_id", 1), ("status", 1), ("created_at", -1)])
        await self.db["alerts"].create_index([("shop_id", 1), ("product_id", 1), ("status", 1)])

        # Voice interactions — TTL cleanup for expired confirmations
        await self.db["voice_interactions"].create_index([("shop_id", 1), ("status", 1)])
        try:
            await self.db["voice_interactions"].create_index(
                [("expires_at", 1)], expireAfterSeconds=0
            )
        except Exception:
            pass  # TTL index may already exist or standalone may restrict; non-fatal
        
        print("Indexes created.")

mongo_db = MongoDBManager()

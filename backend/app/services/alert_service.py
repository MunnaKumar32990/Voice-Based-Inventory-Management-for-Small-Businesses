from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.alert_repo import AlertRepository

class AlertService:
    def __init__(self):
        self.repo = AlertRepository()

    async def check_and_create_alerts(self, db: AsyncIOMotorDatabase, shop_id: str, product_id: str, new_quantity: float, session=None):
        pass # Integrated into InventoryService for atomicity

    async def get_open_alerts(self, db: AsyncIOMotorDatabase, shop_id: str):
        return await self.repo.find_open(db, shop_id)

    async def resolve_alert(self, db: AsyncIOMotorDatabase, shop_id: str, alert_id: str):
        resolved = await self.repo.resolve_by_id(db, shop_id, alert_id)
        if not resolved:
            raise ValueError("Alert not found or already resolved")
        return True

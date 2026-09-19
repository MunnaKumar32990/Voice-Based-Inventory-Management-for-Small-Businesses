from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services.inventory_service import InventoryService
from app.dependencies import get_current_user, get_database

router = APIRouter()
svc = InventoryService()

def get_db(request=None) -> AsyncIOMotorDatabase:
    return get_database(request)

@router.get("/summary")
async def get_summary(
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get dashboard summary: today's transactions, low stock count, product list."""
    shop_id = user["shop_id"]
    summary = await svc.get_dashboard_summary(db, shop_id)

    # Also get all products with their balances for the dashboard
    products = []
    async for product in db.products.find({"shop_id": shop_id, "active": True}):
        balance = await db.stock_balances.find_one({
            "shop_id": shop_id,
            "product_id": str(product["_id"]),
        })
        qty = balance["quantity"] if balance else 0
        threshold = product.get("reorder_threshold", 0)
        status = "OK"
        if qty <= 0:
            status = "OUT"
        elif qty <= threshold:
            status = "LOW"

        products.append({
            "id": str(product["_id"]),
            "name": product.get("display_name", product.get("name", "")),
            "quantity": qty,
            "unit": product.get("base_unit", "piece"),
            "reorder_threshold": threshold,
            "category": product.get("category", ""),
            "status": status,
        })

    return {
        "today_stock_in": summary.get("today_stock_in", 0),
        "today_stock_out": summary.get("today_stock_out", 0),
        "low_stock_count": summary.get("open_alerts", 0),
        "total_products": len(products),
        "products": products,
    }

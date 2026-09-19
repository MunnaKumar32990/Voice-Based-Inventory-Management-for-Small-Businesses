from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services.alert_service import AlertService
from app.dependencies import get_current_user, get_database
from bson import ObjectId
from bson.errors import InvalidId

router = APIRouter()
svc = AlertService()


def _safe_oid(value):
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError, ValueError):
        return None


async def _find_product(db, shop_id: str, product_id: str):
    oid = _safe_oid(product_id)
    if oid is not None:
        doc = await db.products.find_one({"_id": oid, "shop_id": shop_id})
        if doc:
            return doc
    return await db.products.find_one({"_id": str(product_id), "shop_id": shop_id})


def get_db(request=None) -> AsyncIOMotorDatabase:
    return get_database(request)


@router.get("/")
async def list_alerts(
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List all open low-stock alerts for the shop."""
    shop_id = user["shop_id"]
    alerts = await svc.get_open_alerts(db, shop_id)

    # Enrich with product names
    result = []
    for alert in alerts:
        product = await _find_product(db, shop_id, alert.get("product_id", ""))

        result.append({
            "id": str(alert["_id"]),
            "product_id": alert.get("product_id", ""),
            "product_name": product.get("display_name", product.get("name", "")) if product else "Unknown",
            "type": alert.get("type", alert.get("alert_type", "LOW_STOCK")),
            "status": alert.get("status", "OPEN"),
            "current_quantity": alert.get("current_quantity", 0),
            "threshold": alert.get("threshold", 0),
            "created_at": str(alert.get("created_at", "")),
        })

    return {"alerts": result, "total": len(result)}


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Resolve a low-stock alert."""
    try:
        await svc.resolve_alert(db, user["shop_id"], alert_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "resolved", "message": "Alert resolved"}

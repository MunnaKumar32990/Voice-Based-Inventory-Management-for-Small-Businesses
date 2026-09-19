from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services.inventory_service import InventoryService
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.balance_repo import BalanceRepository
from app.dependencies import get_current_user, get_database
from app.websocket.manager import manager as ws_manager
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from bson import ObjectId
from bson.errors import InvalidId
import uuid

router = APIRouter()
svc = InventoryService()
txn_repo = TransactionRepository()
balance_repo = BalanceRepository()


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


class ManualTransactionRequest(BaseModel):
    product_id: str
    operation: str = Field(pattern="^(STOCK_IN|STOCK_OUT|ADJUSTMENT)$")
    quantity: float = Field(gt=0, le=1000000)
    unit: str = Field(min_length=1, max_length=30)
    reason: str = ""
    price_total: Optional[float] = None
    client_request_id: Optional[str] = None


@router.post("/transactions")
async def create_transaction(
    req: ManualTransactionRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create a manual inventory transaction (non-voice fallback)."""
    shop_id = user["shop_id"]
    user_id = user["sub"]
    idempotency_key = req.client_request_id or f"manual_{uuid.uuid4()}"

    try:
        result = await svc.commit_transaction(
            db=db,
            shop_id=shop_id,
            user_id=user_id,
            product_id=req.product_id,
            operation=req.operation,
            quantity=Decimal(str(req.quantity)),
            unit=req.unit,
            reason=req.reason,
            source="manual",
            idempotency_key=idempotency_key,
            price_total=Decimal(str(req.price_total)) if req.price_total else None,
        )
        try:
            await ws_manager.send_to_shop(shop_id, {
                "type": "STOCK_UPDATED",
                "product_id": req.product_id,
                "quantity": result.get("new_balance", 0),
                "operation": req.operation,
            })
        except Exception:
            pass
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transactions")
async def list_transactions(
    product_id: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    skip: int = Query(default=0, ge=0),
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List inventory transactions with optional product filter."""
    shop_id = user["shop_id"]
    transactions = await txn_repo.find_by_shop(db, shop_id, product_id=product_id, limit=limit, skip=skip)

    # Enrich with product names
    result = []
    for txn in transactions:
        product = await _find_product(db, shop_id, txn.get("product_id", ""))

        result.append({
            "id": str(txn["_id"]),
            "product_id": txn.get("product_id", ""),
            "product_name": product.get("display_name", product.get("name", "")) if product else "Unknown",
            "operation": txn.get("operation", ""),
            "quantity": txn.get("quantity", 0),
            "unit": txn.get("unit", ""),
            "reason": txn.get("reason", ""),
            "source": txn.get("source", "manual"),
            "price_total": txn.get("price_total"),
            "created_at": str(txn.get("timestamp", txn.get("created_at", ""))),
        })

    return {"transactions": result, "total": len(result)}


@router.post("/transactions/{txn_id}/reverse")
async def reverse_transaction(
    txn_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Reverse a transaction by creating a compensating entry."""
    shop_id = user["shop_id"]
    user_id = user["sub"]
    oid = _safe_oid(txn_id)
    orig = None
    if oid is not None:
        orig = await db.transactions.find_one({"_id": oid, "shop_id": shop_id})
    if not orig:
        orig = await db.transactions.find_one({"_id": str(txn_id), "shop_id": shop_id})
    if not orig:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if orig.get("reversed_by"):
        raise HTTPException(status_code=400, detail="Transaction already reversed")
    orig_op = orig.get("operation", "")
    reverse_op = "STOCK_OUT" if orig_op == "STOCK_IN" else "STOCK_IN" if orig_op == "STOCK_OUT" else None
    if not reverse_op:
        raise HTTPException(status_code=400, detail="Only STOCK_IN/STOCK_OUT transactions can be reversed")
    try:
        result = await svc.commit_transaction(
            db=db, shop_id=shop_id, user_id=user_id,
            product_id=str(orig.get("product_id", "")),
            operation=reverse_op,
            quantity=Decimal(str(orig.get("quantity", 0))),
            unit=orig.get("unit", "piece"),
            reason=f"reversal_of_{txn_id}", source="manual",
            idempotency_key=f"reverse_{txn_id}_{shop_id}",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await db.transactions.update_one(
        {"_id": orig["_id"]}, {"$set": {"reversed_by": str(result.get("transaction_id", ""))}}
    )
    return {"status": "reversed", "transaction_id": str(result.get("transaction_id", "")),
            "new_balance": result.get("new_balance")}


@router.get("/balances")
async def get_balances(
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get all stock balances for the shop."""
    shop_id = user["shop_id"]
    balances = await balance_repo.find_all(db, shop_id)

    result = []
    for b in balances:
        product = await _find_product(db, shop_id, b.get("product_id", ""))

        result.append({
            "product_id": b.get("product_id", ""),
            "product_name": product.get("display_name", product.get("name", "")) if product else "Unknown",
            "quantity": b.get("quantity", 0),
            "unit": b.get("unit", "piece"),
            "reorder_threshold": product.get("reorder_threshold", 0) if product else 0,
            "status": "LOW" if product and b.get("quantity", 0) <= product.get("reorder_threshold", 0) else "OK",
        })

    return {"balances": result}

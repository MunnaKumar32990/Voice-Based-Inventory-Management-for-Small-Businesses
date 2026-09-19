from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.product_repo import ProductRepository
from app.dependencies import get_current_user, get_database
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone

router = APIRouter()
repo = ProductRepository()


def get_db(request=None) -> AsyncIOMotorDatabase:
    return get_database(request)


class AliasInput(BaseModel):
    text: str
    language: str = "en"


class ConversionInput(BaseModel):
    from_unit: str
    to_unit: str
    factor: float


class ProductCreateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)
    category: str = ""
    base_unit: str = "piece"
    allowed_units: List[str] = []
    reorder_threshold: float = 10
    aliases: List[AliasInput] = []
    conversions: List[ConversionInput] = []
    opening_balance: float = 0


class ProductUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    category: Optional[str] = None
    base_unit: Optional[str] = None
    reorder_threshold: Optional[float] = None
    aliases: Optional[List[AliasInput]] = None


@router.get("/")
async def list_products(
    search: str = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List all active products for the shop."""
    shop_id = user["shop_id"]
    products = await repo.find_all(db, shop_id, search=search)

    # Enrich with current stock balance
    result = []
    for p in products:
        balance = await db.stock_balances.find_one({
            "shop_id": shop_id,
            "product_id": str(p["_id"]),
        })
        qty = balance["quantity"] if balance else 0
        threshold = p.get("reorder_threshold", 0)
        status = "OUT" if qty <= 0 else ("LOW" if qty <= threshold else "OK")

        result.append({
            "id": str(p["_id"]),
            "display_name": p.get("display_name", p.get("name", "")),
            "normalized_name": p.get("normalized_name", ""),
            "category": p.get("category", ""),
            "base_unit": p.get("base_unit", "piece"),
            "allowed_units": p.get("allowed_units", []),
            "reorder_threshold": threshold,
            "aliases": p.get("aliases", []),
            "conversions": p.get("conversions", []),
            "quantity": qty,
            "status": status,
        })

    return {"products": result, "total": len(result)}


@router.post("/")
async def create_product(
    req: ProductCreateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create a new product."""
    shop_id = user["shop_id"]

    # Build the product document
    normalized = req.display_name.lower().strip()
    product_doc = {
        "shop_id": shop_id,
        "display_name": req.display_name,
        "name": req.display_name,  # backward compat
        "normalized_name": normalized,
        "category": req.category,
        "base_unit": req.base_unit,
        "allowed_units": req.allowed_units or [req.base_unit],
        "reorder_threshold": req.reorder_threshold,
        "aliases": [{"text": a.text, "normalized": a.text.lower(), "language": a.language} for a in req.aliases],
        "conversions": [{"from_unit": c.from_unit, "to_unit": c.to_unit, "factor": c.factor} for c in req.conversions],
        "active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    product_id = await repo.create(db, product_doc)

    # Create opening balance if specified
    if req.opening_balance > 0:
        await db.stock_balances.insert_one({
            "shop_id": shop_id,
            "product_id": str(product_id),
            "quantity": req.opening_balance,
            "unit": req.base_unit,
            "updated_at": datetime.now(timezone.utc),
            "version": 1,
        })

    return {"id": str(product_id), "message": "Product created successfully"}


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Get a single product by ID."""
    product = await repo.find_by_id(db, user["shop_id"], product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    balance = await db.stock_balances.find_one({
        "shop_id": user["shop_id"],
        "product_id": str(product["_id"]),
    })
    product["quantity"] = balance["quantity"] if balance else 0
    product["id"] = str(product.pop("_id"))
    # Ensure JSON-serializable (ObjectId/datetime safe)
    for k, v in list(product.items()):
        try:
            from bson import ObjectId as _OID
            if isinstance(v, _OID):
                product[k] = str(v)
        except Exception:
            pass
    return product


@router.patch("/{product_id}")
async def update_product(
    product_id: str,
    req: ProductUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Update a product."""
    update_fields = {k: v for k, v in req.model_dump().items() if v is not None}
    if update_fields:
        update_fields["updated_at"] = datetime.now(timezone.utc)
    success = await repo.update(db, user["shop_id"], product_id, update_fields)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product updated successfully"}

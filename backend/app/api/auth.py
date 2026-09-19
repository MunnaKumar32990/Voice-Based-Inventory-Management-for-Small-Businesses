from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services.auth_service import AuthService
from app.dependencies import get_current_user, get_database
from app.db.seed import seed_demo_data
from pydantic import BaseModel

router = APIRouter()
auth_service = AuthService()


class DemoLoginRequest(BaseModel):
    shop_name: str = "Kumar General Store"


def get_db(request=None) -> AsyncIOMotorDatabase:
    return get_database(request)


@router.post("/demo-login")
async def demo_login(req: DemoLoginRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Demo login: creates a shop + demo user if they don't exist,
    seeds products, and returns a JWT token.
    """
    result = await auth_service.demo_login(db, req.shop_name)

    # Auto-seed demo data if shop is new (no products yet)
    product_count = await db.products.count_documents({"shop_id": result["shop_id"]})
    if product_count == 0:
        await seed_demo_data(db, result["shop_id"])

    return result


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current authenticated user info."""
    return {
        "user_id": user.get("sub", ""),
        "shop_id": user.get("shop_id", ""),
        "role": user.get("role", "owner"),
    }

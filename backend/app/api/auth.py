from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services.auth_service import AuthService
from app.dependencies import get_current_user, get_database
from app.db.seed import seed_demo_data
from app.core.exceptions import AuthenticationError, ValidationError
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

router = APIRouter()
auth_service = AuthService()


class DemoLoginRequest(BaseModel):
    shop_name: str = "Kumar General Store"


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    shop_name: Optional[str] = ""


class LoginRequest(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


def get_db(request=None) -> AsyncIOMotorDatabase:
    return get_database(request)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(req: SignupRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Register a new user with their own isolated shop workspace."""
    try:
        result = await auth_service.register_user(
            db=db,
            name=req.name,
            email=req.email,
            password=req.password,
            shop_name=req.shop_name or "",
        )
        return result
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/login")
async def login(req: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Authenticate user with email and password, returning a JWT token."""
    try:
        result = await auth_service.login_user(
            db=db,
            email=req.email,
            password=req.password,
        )
        return result
    except (AuthenticationError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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
async def get_me(user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get current authenticated user info."""
    user_id = user.get("sub", "")
    shop_id = user.get("shop_id", "")
    
    # Try fetching fresh user record
    name = user.get("name", "")
    email = user.get("email", "")
    shop_name = ""
    
    if shop_id:
        try:
            from bson import ObjectId
            shop = await db.shops.find_one({"_id": ObjectId(shop_id)})
            if not shop:
                shop = await db.shops.find_one({"_id": shop_id})
            if shop:
                shop_name = shop.get("name", "")
        except Exception:
            pass

    return {
        "user_id": user_id,
        "shop_id": shop_id,
        "name": name or "Owner",
        "email": email,
        "shop_name": shop_name,
        "role": user.get("role", "owner"),
    }


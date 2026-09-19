from jose import jwt
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import AuthenticationError, ValidationError


class AuthService:
    """Authentication service for registration, login, and demo login with JWT tokens."""

    async def register_user(
        self,
        db: AsyncIOMotorDatabase,
        name: str,
        email: str,
        password: str,
        shop_name: str = "",
    ) -> dict:
        name = name.strip()
        email = email.strip().lower()
        if not name:
            raise ValidationError("Name is required")
        if not email or "@" not in email:
            raise ValidationError("Valid email is required")
        if not password or len(password) < 6:
            raise ValidationError("Password must be at least 6 characters")

        # Check if user with this email already exists
        existing = await db.users.find_one({"email": email})
        if existing:
            raise ValidationError("Email is already registered")

        final_shop_name = shop_name.strip() if shop_name and shop_name.strip() else f"{name}'s Store"

        # Create isolated shop for this user
        shop_res = await db.shops.insert_one({
            "name": final_shop_name,
            "default_language": "en",
            "currency": "INR",
            "timezone": "Asia/Kolkata",
            "created_at": datetime.now(timezone.utc),
        })
        shop_id = str(shop_res.inserted_id)

        # Hash password and create user
        pwd_hash = hash_password(password)
        user_res = await db.users.insert_one({
            "shop_id": shop_id,
            "name": name,
            "email": email,
            "password_hash": pwd_hash,
            "shop_name": final_shop_name,
            "role": "owner",
            "active": True,
            "created_at": datetime.now(timezone.utc),
        })
        user_id = str(user_res.inserted_id)

        # Generate JWT token
        token_data = {
            "sub": user_id,
            "shop_id": shop_id,
            "role": "owner",
            "email": email,
            "name": name,
        }
        token = create_access_token(token_data)

        return {
            "access_token": token,
            "token_type": "bearer",
            "shop_id": shop_id,
            "user_id": user_id,
            "name": name,
            "email": email,
            "shop_name": final_shop_name,
        }

    async def login_user(
        self,
        db: AsyncIOMotorDatabase,
        email: str,
        password: str,
    ) -> dict:
        email = email.strip().lower()
        if not email or not password:
            raise AuthenticationError("Email and password are required")

        user = await db.users.find_one({"email": email})
        if not user or not user.get("password_hash"):
            raise AuthenticationError("Invalid email or password")

        if not verify_password(password, user["password_hash"]):
            raise AuthenticationError("Invalid email or password")

        user_id = str(user["_id"])
        shop_id = str(user.get("shop_id", ""))

        # Fetch shop details
        shop = None
        if shop_id:
            try:
                shop = await db.shops.find_one({"_id": ObjectId(shop_id)})
            except Exception:
                shop = await db.shops.find_one({"_id": shop_id})
        shop_name = shop.get("name", user.get("shop_name", "My Store")) if shop else user.get("shop_name", "My Store")

        token_data = {
            "sub": user_id,
            "shop_id": shop_id,
            "role": user.get("role", "owner"),
            "email": email,
            "name": user.get("name", ""),
        }
        token = create_access_token(token_data)

        return {
            "access_token": token,
            "token_type": "bearer",
            "shop_id": shop_id,
            "user_id": user_id,
            "name": user.get("name", ""),
            "email": email,
            "shop_name": shop_name,
        }

    async def demo_login(self, db: AsyncIOMotorDatabase, shop_name: str) -> dict:
        """
        Create or find a demo shop + user and return a JWT access token.
        Preserved for demo testing and hackathon judging.
        """
        # Find or create shop
        shop = await db.shops.find_one({"name": shop_name})
        if not shop:
            result = await db.shops.insert_one({
                "name": shop_name,
                "default_language": "en",
                "currency": "INR",
                "timezone": "Asia/Kolkata",
                "created_at": datetime.now(timezone.utc),
            })
            shop_id = str(result.inserted_id)
        else:
            shop_id = str(shop["_id"])

        # Find or create demo user
        user = await db.users.find_one({"shop_id": shop_id, "name": "Demo Owner"})
        if not user:
            result = await db.users.insert_one({
                "shop_id": shop_id,
                "name": "Demo Owner",
                "phone": "+919999999999",
                "role": "owner",
                "active": True,
                "created_at": datetime.now(timezone.utc),
            })
            user_id = str(result.inserted_id)
        else:
            user_id = str(user["_id"])

        # Generate JWT token
        token_data = {
            "sub": user_id,
            "shop_id": shop_id,
            "role": "owner",
            "name": "Demo Owner",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        token = jwt.encode(token_data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        return {
            "access_token": token,
            "token_type": "bearer",
            "shop_id": shop_id,
            "user_id": user_id,
            "name": "Demo Owner",
            "shop_name": shop_name,
        }


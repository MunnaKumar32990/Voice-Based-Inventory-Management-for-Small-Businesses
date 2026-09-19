from jose import jwt
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.config import settings


class AuthService:
    """Authentication service for demo login with JWT tokens."""

    async def demo_login(self, db: AsyncIOMotorDatabase, shop_name: str) -> dict:
        """
        Create or find a demo shop + user and return a JWT access token.
        For production, replace with OTP-based auth.
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
            "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        token = jwt.encode(token_data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        return {
            "access_token": token,
            "token_type": "bearer",
            "shop_id": shop_id,
            "user_id": user_id,
            "shop_name": shop_name,
        }

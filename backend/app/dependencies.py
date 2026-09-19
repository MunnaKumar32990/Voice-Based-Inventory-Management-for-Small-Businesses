from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.mongodb import mongo_db
from app.core.security import verify_token
from app.core.exceptions import AuthenticationError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/demo-login", auto_error=False)

def get_database(request: Request = None) -> AsyncIOMotorDatabase:
    """Single source of truth for DB access. Prefers request.app.state.db (lifespan), else shared client."""
    if request is not None and hasattr(request.app.state, "db") and request.app.state.db is not None:
        return request.app.state.db
    return mongo_db.get_database()

# Backwards-compat alias (older api modules import get_db)
def get_db(request: Request = None) -> AsyncIOMotorDatabase:
    return get_database(request)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise AuthenticationError("Not authenticated")
    payload = verify_token(token)
    if not payload or not payload.get("sub") or not payload.get("shop_id"):
        raise AuthenticationError("Invalid or expired token")
    return payload

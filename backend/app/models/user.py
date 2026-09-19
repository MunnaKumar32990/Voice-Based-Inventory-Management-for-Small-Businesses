from datetime import datetime, timezone
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from app.core.constants import UserRole

OidStr = Annotated[str, BeforeValidator(lambda v: str(v))]

class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: OidStr = Field(alias="_id")
    shop_id: str
    name: str
    email: str = ""
    password_hash: str = ""
    shop_name: str = ""
    phone: str = ""
    role: str = "owner"
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

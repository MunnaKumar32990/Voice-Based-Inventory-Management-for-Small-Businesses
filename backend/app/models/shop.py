from datetime import datetime, timezone
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator

OidStr = Annotated[str, BeforeValidator(lambda v: str(v))]

class Shop(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: OidStr = Field(alias="_id")
    name: str
    default_language: str = "en"
    currency: str = "INR"
    timezone: str = "Asia/Kolkata"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

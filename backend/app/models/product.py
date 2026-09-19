from datetime import datetime, timezone
from typing import List, Optional, Annotated
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator

OidStr = Annotated[str, BeforeValidator(lambda v: str(v))]

class Alias(BaseModel):
    text: str
    normalized: str
    language: str = "en"

class Conversion(BaseModel):
    from_unit: str
    to_unit: str
    factor: float

class Product(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: OidStr = Field(alias="_id")
    shop_id: str
    display_name: str
    normalized_name: str
    aliases: List[Alias] = []
    category: Optional[str] = None
    base_unit: str
    allowed_units: List[str] = []
    conversions: List[Conversion] = []
    reorder_threshold: float = 0.0
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

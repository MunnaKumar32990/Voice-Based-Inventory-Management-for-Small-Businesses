from datetime import datetime, timezone
from typing import Annotated, Optional
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator

OidStr = Annotated[str, BeforeValidator(lambda v: str(v))]

class StockBalance(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: OidStr = Field(alias="_id") # shop_id + "_" + product_id
    shop_id: str
    product_id: str
    quantity: float
    unit: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: Optional[datetime] = None
    version: int = 1

from datetime import datetime, timezone
from typing import Optional, Annotated
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator

OidStr = Annotated[str, BeforeValidator(lambda v: str(v))]

class Alert(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: OidStr = Field(alias="_id")
    shop_id: str
    product_id: str
    alert_type: str = "LOW_STOCK"
    type: str = "LOW_STOCK"
    status: str = "OPEN"
    current_quantity: float = 0
    threshold: float = 0
    last_notified_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

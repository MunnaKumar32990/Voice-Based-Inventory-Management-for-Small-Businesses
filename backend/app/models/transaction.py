from datetime import datetime, timezone
from typing import Optional, Annotated
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from app.core.constants import OperationType, TransactionSource

OidStr = Annotated[str, BeforeValidator(lambda v: str(v))]

class Transaction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: OidStr = Field(alias="_id")
    shop_id: str
    product_id: str
    operation: OperationType
    quantity: float
    unit: str
    base_quantity: Optional[float] = None
    base_unit: Optional[str] = None
    normalized_quantity: Optional[float] = None
    normalized_unit: Optional[str] = None
    price_total: Optional[float] = None
    reason: Optional[str] = None
    source: str = "manual"
    interaction_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_by: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reversed_transaction_id: Optional[str] = None
    reversed_by: Optional[str] = None

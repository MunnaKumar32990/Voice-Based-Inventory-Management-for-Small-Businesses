from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel
from app.core.constants import OperationType

class TransactionCreate(BaseModel):
    product_id: str
    operation: OperationType
    quantity: Decimal
    unit: str
    reason: Optional[str] = None
    price_total: Optional[Decimal] = None
    client_request_id: Optional[str] = None

class TransactionResponse(BaseModel):
    id: str
    product_name: str
    operation: str
    quantity: float
    unit: str
    new_balance: float
    created_at: datetime

class StockBalanceResponse(BaseModel):
    product_id: str
    product_name: str
    quantity: float
    unit: str
    reorder_threshold: float
    status: str

class DashboardSummary(BaseModel):
    today_in: int
    today_out: int
    low_stock_count: int
    total_products: int
    products: List[StockBalanceResponse]

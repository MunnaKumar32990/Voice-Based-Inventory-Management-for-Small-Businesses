from typing import List, Optional
from pydantic import BaseModel
from app.schemas.inventory import StockBalanceResponse

class DashboardProduct(BaseModel):
    id: str
    name: str
    quantity: float
    unit: str
    reorder_threshold: float
    category: Optional[str] = ""
    status: str

class DashboardSummaryResponse(BaseModel):
    """Matches GET /api/v1/dashboard/summary."""
    today_stock_in: int
    today_stock_out: int
    low_stock_count: int
    total_products: int
    products: List[DashboardProduct]

    # Backwards-compat alias for older docs/code
    @property
    def low_stock_products(self) -> List[DashboardProduct]:
        return [p for p in self.products if p.status in ("LOW", "OUT")]

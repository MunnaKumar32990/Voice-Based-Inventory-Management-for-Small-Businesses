from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.product import Alias, Conversion

class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    display_name: str
    category: Optional[str] = ""
    base_unit: str = "piece"
    allowed_units: List[str] = []
    reorder_threshold: float = 10.0
    aliases: List[Alias] = []
    conversions: List[Conversion] = []
    opening_balance: float = 0.0

class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    display_name: Optional[str] = None
    category: Optional[str] = None
    base_unit: Optional[str] = None
    allowed_units: Optional[List[str]] = None
    reorder_threshold: Optional[float] = None
    aliases: Optional[List[Alias]] = None
    conversions: Optional[List[Conversion]] = None

class ProductResponse(BaseModel):
    id: str
    display_name: str
    normalized_name: str
    category: Optional[str]
    base_unit: str
    allowed_units: List[str]
    reorder_threshold: float
    aliases: List[Alias]
    active: bool

class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int

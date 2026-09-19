from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class ParsedCommandSchema(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    intent: str
    product_text: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    price_total: Optional[float] = None
    confidence: float = 0.0

class VoiceCommandResponse(BaseModel):
    interaction_id: str
    status: str
    transcript: str
    language: str
    command: ParsedCommandSchema
    confirmation_text: Optional[str] = None

class VoiceCommitRequest(BaseModel):
    confirmed: bool = True
    product_id: Optional[str] = None
    operation: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None

class VoiceCommitResponse(BaseModel):
    status: str = "committed"
    transaction_id: Optional[str] = None
    product_name: Optional[str] = None
    new_balance: Optional[float] = None
    message: str

class CandidateSchema(BaseModel):
    id: str
    name: str

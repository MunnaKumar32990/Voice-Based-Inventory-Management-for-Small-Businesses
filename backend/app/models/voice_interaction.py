from datetime import datetime, timezone
from typing import Optional, Dict, Any, Annotated
from pydantic import BaseModel, Field, ConfigDict, BeforeValidator

OidStr = Annotated[str, BeforeValidator(lambda v: str(v))]

class VoiceInteraction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: OidStr = Field(alias="_id")
    shop_id: str
    user_id: str
    status: str = "NEEDS_CONFIRMATION" # NEEDS_CONFIRMATION, COMMITTED, CANCELLED, EXPIRED
    transcript: str = ""
    language: str = "en"
    parsed_command: Dict[str, Any] = {}
    confidence: float = 0.0
    provider: str = "webspeech"
    latency_ms: int = 0
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

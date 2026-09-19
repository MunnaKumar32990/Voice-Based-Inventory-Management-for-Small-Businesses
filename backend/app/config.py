from typing import List, Union, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "voice_inventory"
    
    JWT_SECRET: str = "dev-only-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    CORS_ORIGINS: List[str] = ["*"]

    # Speech-to-text provider. Default needs ZERO keys:
    #   webspeech = browser Web Speech API transcript (default, free)
    #   sarvam    = Sarvam AI (needs SARVAM_API_KEY)
    #   google    = Google Cloud Speech (needs GOOGLE_SPEECH_API_KEY)
    #   azure     = Azure AI Speech (needs AZURE_SPEECH_KEY + AZURE_SPEECH_REGION)
    SPEECH_PROVIDER: str = "webspeech"
    SARVAM_API_KEY: str = ""
    SARVAM_API_URL: str = "https://api.sarvam.ai/speech-to-text"
    GOOGLE_SPEECH_API_KEY: str = ""
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = ""
    MAX_AUDIO_MB: int = 10

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return ["*"]
            # Try JSON list first: '["http://a","http://b"]'
            if s.startswith("["):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return [str(x) for x in parsed]
                except (json.JSONDecodeError, ValueError):
                    pass
            # Comma-separated: "http://a,http://b"
            return [p.strip() for p in s.split(",") if p.strip()]
        return ["*"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

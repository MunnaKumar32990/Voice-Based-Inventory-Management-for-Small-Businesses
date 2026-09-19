"""Text-to-speech helper.

Default: the web app speaks via the browser SpeechSynthesis API (free,
offline, per-language voices) — see VoiceModal. No keys needed.

With Azure AI Speech keys configured, the backend can synthesize real audio:
POST /api/v1/voice/speak {text, language} -> audio/mpeg. Same Key1/Key2 and
region as STT (e.g. uaenorth) work for TTS.
"""
import logging
from xml.sax.saxutils import escape

import httpx

from app.config import settings

log = logging.getLogger(__name__)

# Neural voices per language (Azure AI Speech voice gallery)
VOICES = {
    "en": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural",
    "te": "te-IN-ShrutiNeural",
}


class TTSService:
    def generate_speech_text(self, text: str, language: str = "en") -> str:
        if not text:
            return ""
        return " ".join(text.strip().split())

    async def synthesize(self, text: str, language: str = "en") -> bytes:
        """Synthesize MP3 audio via Azure TTS. Raises ValueError if unconfigured."""
        clean = self.generate_speech_text(text, language)
        if not clean:
            raise ValueError("Nothing to speak")
        if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
            raise ValueError("AZURE_SPEECH_KEY / AZURE_SPEECH_REGION are not configured")
        lang = (language or "en").lower()
        base = "en-IN"
        if lang.startswith("hi"):
            base = "hi-IN"
        elif lang.startswith("te"):
            base = "te-IN"
        voice = VOICES.get(lang[:2], VOICES["en"])
        ssml = (
            f"<speak version='1.0' xml:lang='{base}'>"
            f"<voice xml:lang='{base}' name='{voice}'>{escape(clean)}</voice>"
            "</speak>"
        )
        url = (
            f"https://{settings.AZURE_SPEECH_REGION.strip()}"
            ".tts.speech.microsoft.com/cognitiveservices/v1"
        )
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    url,
                    headers={
                        "Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY,
                        "Content-Type": "application/ssml+xml",
                        "X-Microsoft-OutputFormat": "audio-16khz-32kbitrate-mono-mp3",
                        "User-Agent": "VoiceStock",
                    },
                    content=ssml.encode("utf-8"),
                )
                resp.raise_for_status()
                return resp.content
        except httpx.HTTPError as e:
            log.warning("Azure TTS failed: %s", e)
            raise ValueError(f"Speech provider error: {e}") from e

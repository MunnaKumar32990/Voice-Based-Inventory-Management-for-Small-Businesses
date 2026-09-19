"""Speech-to-text provider adapter.

Default (`webspeech`) needs ZERO API keys: the browser's Web Speech API
produces the transcript and the frontend POSTs `{transcript, language}`.
Only if you want server-side transcription from raw audio do you need keys:

  SPEECH_PROVIDER=sarvam  + SARVAM_API_KEY=...                         (Indian-language coverage)
  SPEECH_PROVIDER=google  + GOOGLE_SPEECH_API_KEY=...                  (Google Cloud Speech)
  SPEECH_PROVIDER=azure   + AZURE_SPEECH_KEY=... + AZURE_SPEECH_REGION=uaenorth  (Azure AI Speech)

The rest of the backend always receives the same TranscriptResult.
"""
from dataclasses import dataclass
from typing import Optional
import logging

import httpx

from app.config import settings

log = logging.getLogger(__name__)


@dataclass
class TranscriptResult:
    text: str
    language: str = "en"
    confidence: float = 1.0
    provider_request_id: Optional[str] = None


class UnsupportedProviderError(ValueError):
    pass


class SpeechService:
    async def transcribe(
        self,
        audio_bytes: bytes,
        language_hint: Optional[str] = None,
        provider: Optional[str] = None,
        mime_type: str = "audio/webm",
    ) -> TranscriptResult:
        name = (provider or settings.SPEECH_PROVIDER or "webspeech").lower()
        if name == "webspeech":
            raise UnsupportedProviderError(
                "Server-side transcription is disabled for 'webspeech'. "
                "Send the browser transcript to POST /api/v1/voice/commands instead."
            )
        if name == "sarvam":
            return await self._sarvam_transcribe(audio_bytes, language_hint, mime_type)
        if name == "google":
            return await self._google_transcribe(audio_bytes, language_hint, mime_type)
        if name == "azure":
            return await self._azure_transcribe(audio_bytes, language_hint, mime_type)
        raise UnsupportedProviderError(f"Unknown speech provider '{name}'")

    async def _sarvam_transcribe(
        self, audio_bytes: bytes, language_hint: Optional[str], mime_type: str
    ) -> TranscriptResult:
        if not settings.SARVAM_API_KEY:
            raise UnsupportedProviderError("SARVAM_API_KEY is not configured")
        # Sarvam STT: multipart with model saarika:v2.5, language_code like hi-IN.
        lang = self._normalize_lang(language_hint)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    settings.SARVAM_API_URL,
                    headers={"api-subscription-key": settings.SARVAM_API_KEY},
                    files={"file": ("audio.webm", audio_bytes, mime_type)},
                    data={"model": "saarika:v2.5", "language_code": lang},
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            log.warning("Sarvam STT failed: %s", e)
            raise UnsupportedProviderError(f"Speech provider error: {e}") from e
        text = data.get("transcript") or data.get("text") or ""
        if not text.strip():
            raise UnsupportedProviderError("Speech provider returned an empty transcript")
        return TranscriptResult(
            text=text.strip(),
            language=language_hint or "en",
            confidence=float(data.get("confidence", 0.9) or 0.9),
            provider_request_id=data.get("request_id"),
        )

    async def _google_transcribe(
        self, audio_bytes: bytes, language_hint: Optional[str], mime_type: str
    ) -> TranscriptResult:
        if not settings.GOOGLE_SPEECH_API_KEY:
            raise UnsupportedProviderError("GOOGLE_SPEECH_API_KEY is not configured")
        import base64

        lang = self._normalize_lang(language_hint)
        encoding = "WEBM_OPUS" if "webm" in (mime_type or "") else "ENCODING_UNSPECIFIED"
        body = {
            "config": {"encoding": encoding, "languageCode": lang, "enableAutomaticPunctuation": True},
            "audio": {"content": base64.b64encode(audio_bytes).decode()},
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://speech.googleapis.com/v1/speech:recognize",
                    params={"key": settings.GOOGLE_SPEECH_API_KEY},
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            log.warning("Google STT failed: %s", e)
            raise UnsupportedProviderError(f"Speech provider error: {e}") from e
        results = data.get("results") or []
        if not results:
            raise UnsupportedProviderError("Speech provider returned an empty transcript")
        alt = (results[0].get("alternatives") or [{}])[0]
        return TranscriptResult(
            text=(alt.get("transcript") or "").strip(),
            language=language_hint or "en",
            confidence=float(alt.get("confidence", 0.9) or 0.9),
        )

    async def _azure_transcribe(
        self, audio_bytes: bytes, language_hint: Optional[str], mime_type: str
    ) -> TranscriptResult:
        """Azure AI Speech STT via REST (no SDK needed).

        Endpoint: POST https://{region}.stt.speech.microsoft.com/speech/recognition/
        conversation/cognitiveservices/v1?language={lang}&format=detailed
        Auth: Ocp-Apim-Subscription-Key header (Key1 or Key2 from Azure portal).
        """
        if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
            raise UnsupportedProviderError(
                "AZURE_SPEECH_KEY / AZURE_SPEECH_REGION are not configured"
            )
        region = settings.AZURE_SPEECH_REGION.strip()
        lang = self._normalize_lang(language_hint)
        url = (
            f"https://{region}.stt.speech.microsoft.com/speech/recognition/"
            f"conversation/cognitiveservices/v1?language={lang}&format=detailed"
        )
        # Pass the browser mime through; Azure decodes wav/ogg/webm-opus.
        # If Azure returns 415, re-record as wav (see frontend audio notes).
        content_type = mime_type or "audio/webm"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    url,
                    headers={
                        "Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY,
                        "Content-Type": content_type,
                        "Accept": "application/json",
                    },
                    content=audio_bytes,
                )
                if resp.status_code == 415:
                    raise UnsupportedProviderError(
                        f"Azure rejected audio format '{content_type}'. "
                        "Try recording as audio/wav (16kHz PCM) and retry."
                    )
                resp.raise_for_status()
                data = resp.json()
        except UnsupportedProviderError:
            raise
        except httpx.HTTPError as e:
            log.warning("Azure STT failed: %s", e)
            raise UnsupportedProviderError(f"Speech provider error: {e}") from e
        if str(data.get("RecognitionStatus", "")).lower() != "success":
            reason = data.get("RecognitionStatus", "Unknown")
            raise UnsupportedProviderError(f"Azure could not recognize speech ({reason})")
        text = data.get("DisplayText") or ""
        if not text.strip():
            nbest = data.get("NBest") or []
            if nbest:
                text = nbest[0].get("Display", "") or ""
        if not text.strip():
            raise UnsupportedProviderError("Speech provider returned an empty transcript")
        conf = 0.9
        try:
            nbest = data.get("NBest") or []
            if nbest and nbest[0].get("Confidence") is not None:
                conf = float(nbest[0]["Confidence"])
        except (TypeError, ValueError):
            pass
        return TranscriptResult(
            text=text.strip(),
            language=language_hint or "en",
            confidence=conf,
        )

    @staticmethod
    def _normalize_lang(hint: Optional[str]) -> str:
        h = (hint or "en").lower()
        if h.startswith("hi"):
            return "hi-IN"
        if h.startswith("te"):
            return "te-IN"
        if h.startswith("en"):
            return "en-IN"
        return hint or "en-IN"

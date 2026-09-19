from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services.nlp_service import NLPService, ParsedCommand
from app.services.product_matcher import ProductMatcher
from app.services.inventory_service import InventoryService
from app.services.speech_service import SpeechService, UnsupportedProviderError
from app.services.tts_service import TTSService
from app.dependencies import get_current_user, get_database
from app.config import settings
from app.core.i18n import get_response, detect_speech_dialect
from app.websocket.manager import manager as ws_manager
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from bson.errors import InvalidId
import uuid

router = APIRouter()
nlp = NLPService()
matcher = ProductMatcher()
inv = InventoryService()
speech = SpeechService()
tts = TTSService()


def _format_qty(val) -> str:
    try:
        f = float(val)
        return str(int(f)) if f.is_integer() else str(f)
    except Exception:
        return str(val)


def _safe_oid(value):
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError, ValueError):
        return None


async def _find_product(db, shop_id: str, product_id: str):
    oid = _safe_oid(product_id)
    if oid is not None:
        doc = await db.products.find_one({"_id": oid, "shop_id": shop_id})
        if doc:
            return doc
    return await db.products.find_one({"_id": str(product_id), "shop_id": shop_id})


class VoiceCommandRequest(BaseModel):
    """Accept transcript text from browser Web Speech API."""
    transcript: str = Field(min_length=1, max_length=500)
    language: str = "en"


class VoiceCommitRequest(BaseModel):
    """Confirm and commit a prepared voice command.

    quantity/unit/product_id/operation are optional Edit overrides — when
    provided they are re-validated server-side and recorded on the
    interaction before commit.
    """
    confirmed: bool = True
    product_id: Optional[str] = None
    operation: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None


def get_db(request=None) -> AsyncIOMotorDatabase:
    return get_database(request)


def _serialize_low_stock(items: list) -> list:
    out = []
    for it in items or []:
        if isinstance(it, dict) and "product_name" in it:
            out.append({
                "product_id": str(it.get("product_id", "")),
                "product_name": it.get("product_name", ""),
                "quantity": it.get("quantity", 0),
                "unit": it.get("unit", "piece"),
                "threshold": it.get("threshold", 0),
            })
        else:
            # Fallback for legacy raw aggregation docs
            out.append({
                "product_id": str(it.get("product_id", "")),
                "product_name": str(it.get("product_id", "")),
                "quantity": it.get("quantity", 0),
                "unit": it.get("unit", "piece"),
                "threshold": 0,
            })
    return out


@router.post("/commands")
async def handle_voice_command(
    req: VoiceCommandRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Process a voice transcript: parse intent, match product, return preview.
    No stock change happens here — the user must confirm first.
    """
    shop_id = user["shop_id"]
    user_id = user["sub"]

    # Detect speech dialect (e.g. hinglish, telugish, hi_deva, te_script, en)
    detected_lang = detect_speech_dialect(req.transcript, req.language)

    # 1. Parse the transcript (deterministic first, LLM fallback if uncertain)
    parsed = await nlp.parse_command_with_fallback(req.transcript, detected_lang)

    # 2. Handle query intents directly (no confirmation needed)
    if parsed.intent == "LOW_STOCK_QUERY":
        low_items = await inv.get_low_stock_items(db, shop_id)
        items = _serialize_low_stock(low_items if isinstance(low_items, list) else [])
        names = ", ".join([i["product_name"] for i in items]) if items else ""
        return {
            "status": "answered",
            "intent": "LOW_STOCK_QUERY",
            "transcript": req.transcript,
            "detected_language": detected_lang,
            "answer": items if items else "All items are well stocked!",
            "message": get_response("low_stock_response", detected_lang,
                                     items=names if names else "none") if items
                       else ("Sabhi items stock me hain!" if detected_lang in ("hinglish", "hi", "hi_deva") else "All items are well stocked!"),
        }

    if parsed.intent == "STOCK_QUERY":
        if not parsed.product_text:
            return {"status": "error", "message": "Which product do you want to check?", "detected_language": detected_lang}
        match_res = await matcher.match_product(db, shop_id, parsed.product_text)
        if not match_res.product:
            return {
                "status": "error",
                "detected_language": detected_lang,
                "message": get_response("product_not_found", detected_lang, product=parsed.product_text),
            }
        balance = await db.stock_balances.find_one({
            "shop_id": shop_id,
            "product_id": str(match_res.product["_id"]),
        })
        qty = balance["quantity"] if balance else 0
        unit = match_res.product.get("base_unit", "piece")
        product_name = match_res.product.get("display_name", match_res.product.get("name", ""))
        return {
            "status": "answered",
            "intent": "STOCK_QUERY",
            "transcript": req.transcript,
            "detected_language": detected_lang,
            "product_name": product_name,
            "quantity": qty,
            "unit": unit,
            "message": get_response("stock_query_response", detected_lang,
                                     product=product_name, quantity=_format_qty(qty),
                                     balance=_format_qty(qty), unit=unit),
        }

    if parsed.intent == "CANCEL":
        cancel_msg = "Action cancelled."
        if detected_lang in ("hinglish", "hi", "hi_deva"):
            cancel_msg = "Cancel kar diya gaya."
        elif detected_lang in ("telugish", "te", "te_script"):
            cancel_msg = "Raddhu cheyabadindi."
        return {"status": "cancelled", "message": cancel_msg, "detected_language": detected_lang}

    if parsed.intent == "UNKNOWN":
        unk_msg = "I didn't understand that. Try saying 'Add 5 bags of rice' or 'How much sugar is available?'"
        if detected_lang in ("hinglish", "hi", "hi_deva"):
            unk_msg = "Samajh nahi aaya. Kripya '5 kg rice add kro' ya 'chawal kitna hai' boliye."
        return {
            "status": "error",
            "detected_language": detected_lang,
            "message": unk_msg,
        }

    # 3. For stock mutations (STOCK_IN / STOCK_OUT), find product and prepare preview
    if not parsed.product_text:
        return {"status": "error", "message": "I couldn't identify the product. Please try again.", "detected_language": detected_lang}

    match_res = await matcher.match_product(db, shop_id, parsed.product_text)

    # Multiple candidates take precedence over "not found" (matcher returns
    # product=None + candidates list when several partial matches exist).
    if match_res.candidates and len(match_res.candidates) > 1 and not match_res.product:
        return {
            "status": "clarification_needed",
            "detected_language": detected_lang,
            "message": "Multiple products matched. Please choose one:",
            "candidates": [
                {"id": str(c["_id"]), "name": c.get("display_name", c.get("name", ""))}
                for c in match_res.candidates
            ],
        }

    if not match_res.product:
        return {
            "status": "error",
            "detected_language": detected_lang,
            "message": get_response("product_not_found", detected_lang, product=parsed.product_text),
            "candidates": [
                {"id": str(c["_id"]), "name": c.get("display_name", c.get("name", ""))}
                for c in (match_res.candidates or [])
            ],
        }

    product = match_res.product
    product_id = str(product["_id"])
    product_name = product.get("display_name", product.get("name", ""))

    if parsed.quantity is None:
        clarify_msg = f"How many {product_name}? Please specify the quantity."
        if detected_lang in ("hinglish", "hi", "hi_deva"):
            clarify_msg = f"{product_name} kitna? Kripya quantity batayein."
        return {
            "status": "clarification_needed",
            "detected_language": detected_lang,
            "message": clarify_msg,
        }

    # 4. Prepare the transaction preview
    unit = parsed.unit or product.get("base_unit", "piece")
    try:
        preview = await inv.prepare_transaction(
            db, shop_id, product_id, parsed.intent, parsed.quantity, unit
        )
    except ValueError as e:
        return {"status": "error", "message": str(e), "detected_language": detected_lang}

    # 5. Store the voice interaction for later commit
    interaction_id = str(uuid.uuid4())
    await db.voice_interactions.insert_one({
        "_id": interaction_id,
        "shop_id": shop_id,
        "user_id": user_id,
        "status": "NEEDS_CONFIRMATION",
        "transcript": req.transcript,
        "language": detected_lang,
        "parsed_command": {
            "intent": parsed.intent,
            "product_text": parsed.product_text,
            "product_id": product_id,
            "quantity": float(parsed.quantity),
            "unit": unit,
            "price_total": float(parsed.price_total) if parsed.price_total else None,
            "confidence": parsed.confidence,
        },
        "confidence": parsed.confidence,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        "created_at": datetime.now(timezone.utc),
    })

    # 6. Build confirmation text
    action_label = "Add stock" if parsed.intent == "STOCK_IN" else "Remove stock"
    if detected_lang in ("hinglish", "hi", "hi_deva"):
        action_label = "add" if parsed.intent == "STOCK_IN" else "remove"
    confirmation_text = get_response(
        "confirmation_prompt", detected_lang,
        action=action_label, product=product_name,
        quantity=_format_qty(parsed.quantity), unit=unit,
    )

    return {
        "status": "needs_confirmation",
        "interaction_id": interaction_id,
        "transcript": req.transcript,
        "detected_language": detected_lang,
        "command": {
            "intent": parsed.intent,
            "product_text": parsed.product_text,
            "product_id": product_id,
            "product_name": product_name,
            "quantity": float(parsed.quantity),
            "unit": unit,
            "price_total": float(parsed.price_total) if parsed.price_total else None,
            "confidence": parsed.confidence,
        },
        "preview": preview,
        "confirmation_text": confirmation_text,
    }


@router.post("/commands/{interaction_id}/commit")
async def commit_voice_command(
    interaction_id: str,
    req: VoiceCommitRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Confirm and execute a prepared voice command."""
    shop_id = user["shop_id"]
    user_id = user["sub"]

    # Load the interaction
    interaction = await db.voice_interactions.find_one({
        "_id": interaction_id,
        "shop_id": shop_id,
    })

    if not interaction:
        raise HTTPException(status_code=404, detail="Voice command not found or expired")

    expires_at = interaction.get("expires_at")
    if expires_at:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            await db.voice_interactions.update_one(
                {"_id": interaction_id},
                {"$set": {"status": "EXPIRED"}},
            )
            raise HTTPException(status_code=410, detail="Confirmation expired. Please try again.")

    # Idempotent retry: already committed -> return original result instead of 400
    if interaction["status"] == "COMMITTED":
        cmd = interaction["parsed_command"]
        txn = await db.transactions.find_one({"shop_id": shop_id, "idempotency_key": f"voice_{interaction_id}"})
        language = interaction.get("language") or detect_speech_dialect(interaction.get("transcript", ""), "en")
        return {
            "status": "committed",
            "transaction_id": str(txn["_id"]) if txn else "",
            "product_name": cmd.get("product_text", ""),
            "new_balance": txn.get("new_balance") if txn else None,
            "balance_unit": txn.get("base_unit") if txn else cmd.get("unit", ""),
            "detected_language": language,
            "message": "Already processed.",
        }

    if interaction["status"] != "NEEDS_CONFIRMATION":
        raise HTTPException(status_code=400, detail=f"Command is already {interaction['status']}")

    if not req.confirmed:
        await db.voice_interactions.update_one(
            {"_id": interaction_id},
            {"$set": {"status": "CANCELLED"}},
        )
        return {"status": "cancelled", "message": "Command cancelled."}

    # Use command from interaction (server-side) with optional validated Edit overrides
    cmd = dict(interaction["parsed_command"])
    if req.product_id and req.product_id != cmd.get("product_id"):
        override_product = await _find_product(db, shop_id, req.product_id)
        if not override_product:
            raise HTTPException(status_code=400, detail="Override product not found")
        cmd["product_id"] = str(override_product["_id"])
        cmd["product_text"] = override_product.get("display_name", override_product.get("name", ""))
    if req.operation and req.operation in ("STOCK_IN", "STOCK_OUT"):
        cmd["intent"] = req.operation
    if req.quantity is not None:
        if req.quantity <= 0 or req.quantity > 1000000:
            raise HTTPException(status_code=400, detail="Quantity must be between 0 and 1000000")
        cmd["quantity"] = float(req.quantity)
    if req.unit:
        cmd["unit"] = req.unit[:30]
    if any([req.product_id, req.operation, req.quantity is not None, req.unit]):
        await db.voice_interactions.update_one(
            {"_id": interaction_id}, {"$set": {"parsed_command": cmd}}
        )
    idempotency_key = f"voice_{interaction_id}"

    try:
        result = await inv.commit_transaction(
            db=db,
            shop_id=shop_id,
            user_id=user_id,
            product_id=cmd["product_id"],
            operation=cmd["intent"],
            quantity=Decimal(str(cmd["quantity"])),
            unit=cmd["unit"],
            reason="voice_command",
            source="voice",
            idempotency_key=idempotency_key,
            price_total=Decimal(str(cmd["price_total"])) if cmd.get("price_total") else None,
            interaction_id=interaction_id,
        )
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    # Update interaction status
    await db.voice_interactions.update_one(
        {"_id": interaction_id},
        {"$set": {"status": "COMMITTED"}},
    )

    # Live update for other devices on the same shop
    try:
        await ws_manager.send_to_shop(shop_id, {
            "type": "STOCK_UPDATED",
            "product_id": cmd["product_id"],
            "quantity": result.get("new_balance", 0),
            "unit": cmd["unit"],
        })
    except Exception:
        pass

    # Get product name for response
    product = await _find_product(db, shop_id, cmd["product_id"])
    product_name = product.get("display_name", product.get("name", "")) if product else cmd.get("product_text", "")

    action_key = "stock_added" if cmd["intent"] == "STOCK_IN" else "stock_removed"
    language = interaction.get("language") or detect_speech_dialect(interaction.get("transcript", ""), "en")

    return {
        "status": "committed",
        "transaction_id": str(result.get("transaction_id", "")),
        "product_name": product_name,
        "new_balance": result.get("new_balance", 0),
        "balance_unit": result.get("balance_unit", cmd["unit"]),
        "detected_language": language,
        "message": get_response(action_key, language,
                                 product=product_name,
                                 quantity=_format_qty(cmd["quantity"]),
                                 balance=_format_qty(result.get("new_balance", 0)),
                                 unit=cmd["unit"],
                                 balance_unit=result.get("balance_unit", cmd["unit"])),
    }


@router.post("/commands/{interaction_id}/cancel")
async def cancel_voice_command(
    interaction_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Cancel a pending voice command."""
    shop_id = user["shop_id"]
    result = await db.voice_interactions.update_one(
        {"_id": interaction_id, "shop_id": shop_id, "status": "NEEDS_CONFIRMATION"},
        {"$set": {"status": "CANCELLED"}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Command not found or already processed")
    return {"status": "cancelled", "message": "Command cancelled."}


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language_hint: str = "en",
    db: AsyncIOMotorDatabase = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Transcribe uploaded audio via the configured server-side STT provider.

    Default provider is `webspeech` (no server transcription) — the browser
    should POST transcripts to /voice/commands instead. Configure
    SPEECH_PROVIDER=sarvam|google|azure + API key to enable this endpoint.
    Azure uses AZURE_SPEECH_KEY + AZURE_SPEECH_REGION (e.g. uaenorth).
    """
    allowed = {"audio/webm", "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", "audio/mp4", "audio/ogg"}
    if file.content_type and file.content_type not in allowed and not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail=f"Invalid audio type {file.content_type}")
    audio = await file.read()
    if not audio:
        raise HTTPException(status_code=400, detail="Empty audio file")
    max_bytes = settings.MAX_AUDIO_MB * 1024 * 1024
    if len(audio) > max_bytes:
        raise HTTPException(status_code=400, detail=f"Audio too large (max {settings.MAX_AUDIO_MB} MB)")
    try:
        result = await speech.transcribe(audio, language_hint, mime_type=file.content_type or "audio/webm")
    except UnsupportedProviderError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"transcript": result.text, "language": result.language,
            "confidence": result.confidence, "provider": settings.SPEECH_PROVIDER}


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    language: str = "en"


@router.post("/speak")
async def speak_text(
    req: SpeakRequest,
    user: dict = Depends(get_current_user),
):
    """Synthesize speech via Azure TTS (needs AZURE_SPEECH_KEY + REGION).

    Returns audio/mpeg bytes the browser can play. Without Azure keys,
    the frontend falls back to free browser SpeechSynthesis.
    """
    try:
        audio = await tts.synthesize(req.text, req.language)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(content=audio, media_type="audio/mpeg")

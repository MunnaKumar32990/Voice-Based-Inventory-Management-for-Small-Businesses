from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.mongodb import mongo_db
from app.core.exceptions import (
    ProductNotFoundError, InsufficientStockError,
    DuplicateRequestError, InvalidAudioError,
    UnknownIntentError, AuthenticationError, AuthorizationError,
    SpeechProviderError, ConfirmationExpiredError
)
from app.core.security import verify_token
from app.websocket.manager import manager as ws_manager
from app.api import auth, products, inventory, voice, dashboard, alerts
import uuid

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect to MongoDB, create indexes. Shutdown: disconnect."""
    await mongo_db.connect(settings.MONGODB_URI, settings.DB_NAME)
    await mongo_db.create_indexes()
    # Make DB available on app.state for route handlers
    app.state.db = mongo_db.db
    yield
    await mongo_db.disconnect()

app = FastAPI(
    title="VoiceStock — Voice Inventory API",
    description="Voice-first inventory management API for Indian small businesses",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: credentials + wildcard "*" is rejected by browsers, so only send
# credentials when origins are explicitly configured.
_cors_origins = settings.CORS_ORIGINS
_allow_credentials = not (len(_cors_origins) == 1 and _cors_origins[0] == "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# ── Global Exception Handlers ──────────────────────────────────────
@app.exception_handler(ProductNotFoundError)
async def product_not_found_handler(request: Request, exc: ProductNotFoundError):
    return JSONResponse(status_code=404, content={"error": {"code": "PRODUCT_NOT_FOUND", "message": str(exc)}})

@app.exception_handler(InsufficientStockError)
async def insufficient_stock_handler(request: Request, exc: InsufficientStockError):
    return JSONResponse(status_code=400, content={"error": {"code": "INSUFFICIENT_STOCK", "message": str(exc)}})

@app.exception_handler(DuplicateRequestError)
async def duplicate_request_handler(request: Request, exc: DuplicateRequestError):
    return JSONResponse(status_code=409, content={"error": {"code": "DUPLICATE_REQUEST", "message": str(exc)}})

@app.exception_handler(UnknownIntentError)
async def unknown_intent_handler(request: Request, exc: UnknownIntentError):
    return JSONResponse(status_code=400, content={"error": {"code": "UNKNOWN_INTENT", "message": str(exc)}})

@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(status_code=401, content={"error": {"code": "AUTH_REQUIRED", "message": str(exc)}})

@app.exception_handler(AuthorizationError)
async def authz_error_handler(request: Request, exc: AuthorizationError):
    return JSONResponse(status_code=403, content={"error": {"code": "FORBIDDEN", "message": str(exc)}})

@app.exception_handler(InvalidAudioError)
async def invalid_audio_handler(request: Request, exc: InvalidAudioError):
    return JSONResponse(status_code=400, content={"error": {"code": "INVALID_AUDIO", "message": str(exc)}})

@app.exception_handler(SpeechProviderError)
async def speech_provider_handler(request: Request, exc: SpeechProviderError):
    return JSONResponse(status_code=502, content={"error": {"code": "SPEECH_PROVIDER_ERROR", "message": str(exc)}})

@app.exception_handler(ConfirmationExpiredError)
async def confirmation_expired_handler(request: Request, exc: ConfirmationExpiredError):
    return JSONResponse(status_code=410, content={"error": {"code": "CONFIRMATION_EXPIRED", "message": str(exc)}})

# ── Health Check ───────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "VoiceStock API",
        "database": "connected" if mongo_db.db is not None else "disconnected"
    }

# ── Register API Routers ──────────────────────────────────────────
app.include_router(auth.router,      prefix="/api/v1/auth",      tags=["Authentication"])
app.include_router(products.router,  prefix="/api/v1/products",  tags=["Products"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory"])
app.include_router(voice.router,     prefix="/api/v1/voice",     tags=["Voice Commands"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(alerts.router,    prefix="/api/v1/alerts",    tags=["Alerts"])


# ── Live updates (optional; dashboard also works via polling) ──────
@app.websocket("/ws/events")
async def events_socket(websocket: WebSocket):
    """Authenticated live channel. Connect with ?token=<JWT>; events are shop-scoped."""
    token = websocket.query_params.get("token", "")
    payload = verify_token(token) if token else {}
    if not payload or not payload.get("shop_id"):
        await websocket.close(code=4401)
        return
    shop_id = payload["shop_id"]
    await ws_manager.connect(shop_id, websocket)
    await ws_manager.send_to_shop(shop_id, {"event": "connected"})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(shop_id, websocket)

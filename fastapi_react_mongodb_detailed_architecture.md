# Detailed Technical Architecture
## Voice-Based Inventory Management System

**Stack requested:** React frontend, FastAPI backend, MongoDB database, regional-language speech and NLP integrations.

## 1. Recommended Architecture

Use a modular monolith for the first release:

```text
                         ┌──────────────────────────────┐
                         │   Android Chrome / Desktop    │
                         │ React PWA + TypeScript        │
                         │ Mic, Dashboard, Forms, TTS    │
                         └──────────────┬───────────────┘
                                        │ HTTPS / JSON
                                        │ WebSocket for progress/events
                                        v
                         ┌──────────────────────────────┐
                         │ FastAPI Application            │
                         │ Auth, REST, WebSocket, RBAC    │
                         │ Validation, orchestration     │
                         └───┬──────────┬──────────┬─────┘
                             │          │          │
                             │          │          └──────────────┐
                             │          │                         │
                             v          v                         v
                    ┌────────────┐ ┌─────────────┐      ┌────────────────┐
                    │ MongoDB    │ │ Redis       │      │ Speech/NLP     │
                    │ Atlas      │ │ cache/queue │      │ Provider APIs  │
                    │ data/audit │ │ optional    │      │ STT/TTS/LLM    │
                    └────────────┘ └─────────────┘      └────────────────┘
                             │
                             v
                    ┌────────────────────┐
                    │ Worker process     │
                    │ Celery/RQ/Arq      │
                    │ alerts, TTS, jobs  │
                    └────────────────────┘
```

FastAPI exposes REST endpoints for normal request-response operations and WebSockets for live processing status or stock updates. FastAPI officially supports WebSockets, and its built-in background-task mechanism is intended for work that can run after a response; for durable or long-running work, use a separate worker and queue. [web:34][web:37][web:38]

React manages presentation and client state. Keep server data, such as products and stock, separate from temporary UI state, such as microphone recording and confirmation dialogs. React documentation recommends structuring state carefully and lifting shared state to a suitable common owner instead of keeping duplicate state in unrelated components. [web:32][web:41]

MongoDB stores tenant-scoped documents, immutable inventory events, product aliases, and current stock projections. Use schema validation and transactions where an operation updates multiple documents; MongoDB schema validation is designed to prevent unintended field types and schema changes. [web:39]

## 2. Responsibilities by Layer

### 2.1 React frontend

The React application is responsible for:

- Rendering dashboard, products, transactions, alerts, settings, and help screens.
- Requesting microphone permission.
- Recording audio with `MediaRecorder`.
- Displaying processing stages.
- Sending audio to FastAPI over HTTPS or an upload URL.
- Showing the transcript and parsed action.
- Requesting explicit confirmation before inventory mutation.
- Calling APIs and updating cached server state.
- Playing translated text through browser speech synthesis or a TTS audio response.
- Providing manual fallback when voice fails.
- Caching safe read-only data for poor connectivity.

React must not:

- Store provider API keys.
- Directly access MongoDB.
- Decide whether stock can become negative.
- Trust an LLM result without server validation.
- Calculate the authoritative balance locally.

### 2.2 FastAPI backend

FastAPI is the system’s trusted application boundary. It is responsible for:

- Authentication and authorization.
- Tenant isolation.
- Input validation using Pydantic models.
- Audio validation and forwarding to speech services.
- Intent/entity orchestration.
- Product matching.
- Unit conversion.
- Transactional stock updates.
- Idempotency protection.
- Querying current stock and alerts.
- Audit logging.
- WebSocket status events.
- Calling asynchronous workers for non-critical tasks.

### 2.3 MongoDB

MongoDB is responsible for persistent state:

- Shops and users.
- Products and aliases.
- Inventory ledger events.
- Current stock projection.
- Voice interaction audit records.
- Alerts.
- Idempotency records.
- Optional audio metadata.

### 2.4 Redis and workers

Redis is optional for the initial demo but useful for:

- Caching product aliases and dashboard summaries.
- Rate limiting.
- Queueing transcription, TTS, alert, and export jobs.
- Pub/sub for multi-instance WebSocket events.

Do not use Redis as the only source of truth for inventory.

## 3. Deployment Architecture

### 3.1 Development

```text
React Vite dev server      localhost:5173
FastAPI/Uvicorn             localhost:8000
MongoDB Docker/Atlas        localhost:27017 or cloud URI
Redis Docker                localhost:6379 optional
Worker                      local process optional
```

### 3.2 Production MVP

```text
User -> CDN/HTTPS -> React static hosting
                 -> FastAPI HTTPS service
                      -> MongoDB Atlas private/secured connection
                      -> Redis managed service
                      -> Worker service
                      -> STT/TTS/NLP providers
```

Use separate environments:

- Development: local data and test keys.
- Staging: production-like infrastructure and synthetic speech data.
- Production: restricted secrets, backups, monitoring, and real users.

### 3.3 Suggested repository

```text
voice-inventory/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/auth/
│   │   ├── features/dashboard/
│   │   ├── features/inventory/
│   │   ├── features/voice/
│   │   ├── features/alerts/
│   │   ├── lib/api.ts
│   │   ├── lib/audio.ts
│   │   ├── stores/
│   │   └── i18n/
│   ├── package.json
│   └── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── voice.py
│   │   │   ├── inventory.py
│   │   │   ├── products.py
│   │   │   └── alerts.py
│   │   ├── schemas/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── services/
│   │   │   ├── speech_service.py
│   │   │   ├── nlp_service.py
│   │   │   ├── product_matcher.py
│   │   │   ├── inventory_service.py
│   │   │   ├── unit_service.py
│   │   │   └── event_service.py
│   │   ├── db/mongodb.py
│   │   ├── workers/tasks.py
│   │   └── websocket/manager.py
│   ├── requirements.txt
│   └── .env.example
├── infra/
│   ├── docker-compose.yml
│   └── nginx.conf
└── README.md
```

## 4. End-to-End Communication Flows

## 4.1 Login flow

```text
1. User enters phone/email in React.
2. React sends POST /api/v1/auth/request-otp.
3. FastAPI validates and sends OTP through an auth provider.
4. User enters OTP.
5. React sends POST /api/v1/auth/verify-otp.
6. FastAPI returns a short-lived access token and refresh token strategy.
7. React stores the access token in memory or a secure cookie strategy.
8. Every later request includes Authorization: Bearer <token>.
9. FastAPI dependency validates token and loads user/shop/role context.
```

For a one-day prototype, use a seeded demo user. For production, never hardcode user identity in the frontend.

## 4.2 Dashboard flow

```text
React Dashboard
   -> GET /api/v1/dashboard/summary
FastAPI
   -> validate JWT and shop_id
   -> query MongoDB stock projections and alerts
   -> return summary JSON
React
   -> stores response in server-state cache
   -> renders cards and product table
```

Example response:

```json
{
  "today": {
    "stock_in_transactions": 4,
    "stock_out_transactions": 9
  },
  "low_stock_count": 3,
  "products": [
    {
      "id": "p1",
      "name": "Rice",
      "quantity": 18,
      "unit": "bag",
      "reorder_threshold": 20,
      "status": "LOW"
    }
  ]
}
```

## 4.3 Voice mutation flow

This is the most important system flow.

```text
A. React records audio
B. React uploads audio to FastAPI
C. FastAPI authenticates and validates audio
D. FastAPI calls speech-to-text provider
E. Provider returns transcript and language metadata
F. FastAPI normalizes transcript
G. NLP parser extracts intent and entities
H. Product matcher resolves product candidates
I. Unit service validates/converts units
J. FastAPI returns a preview; no stock change yet
K. React displays confirmation
L. User clicks Confirm
M. React sends commit request with idempotency key
N. FastAPI revalidates everything against current MongoDB state
O. MongoDB transaction inserts ledger event and updates balance
P. FastAPI returns committed result
Q. React refreshes dashboard and displays response
R. Background worker generates alert/TTS/analytics if needed
```

### 4.3.1 Audio upload request

```http
POST /api/v1/voice/commands
Authorization: Bearer <token>
Content-Type: multipart/form-data
X-Request-ID: req_123

file=<audio blob>
language_hint=te-IN
client_request_id=client_456
```

Response:

```json
{
  "interaction_id": "vi_123",
  "status": "NEEDS_CONFIRMATION",
  "transcript": "Add five bags of rice",
  "language": "en-IN",
  "command": {
    "intent": "STOCK_IN",
    "product_text": "rice",
    "product_id": "p1",
    "quantity": 5,
    "unit": "bag",
    "confidence": 0.94
  },
  "confirmation_text": "Add 5 bags of Rice?"
}
```

### 4.3.2 Commit request

```http
POST /api/v1/voice/commands/vi_123/commit
Authorization: Bearer <token>
Content-Type: application/json
Idempotency-Key: client_456
```

```json
{
  "confirmed": true,
  "product_id": "p1",
  "operation": "STOCK_IN",
  "quantity": 5,
  "unit": "bag"
}
```

The backend must not trust the browser’s product ID or quantity. It re-loads the interaction, confirms that it belongs to the current user/shop, checks expiry, validates the current balance, and compares the confirmation payload with the prepared command.

## 4.4 Stock query flow

```text
User says: “How much rice is available?”
React records and uploads audio
FastAPI -> STT
FastAPI -> parser: STOCK_QUERY, product_text=rice
FastAPI -> MongoDB products search
FastAPI -> MongoDB stock_balances lookup
FastAPI -> response formatter in selected language
FastAPI -> optional TTS
React displays and speaks:
“Rice: 18 bags available.”
```

For stock questions, use deterministic MongoDB queries. An LLM may identify the user’s intent, but it must not invent the quantity.

## 4.5 Live WebSocket status flow

Use WebSocket only when streaming progress is valuable. Normal MVP voice processing can use HTTP polling or one upload request.

```text
React opens:
ws://api.example.com/ws/voice?token=<short-lived-token>

FastAPI sends:
{"event":"connected"}
{"event":"recording_received"}
{"event":"transcription_started"}
{"event":"transcription_partial","text":"add five..."}
{"event":"transcription_completed","text":"Add five bags of rice"}
{"event":"understanding_completed","confidence":0.94}
{"event":"needs_confirmation","interaction_id":"vi_123"}
```

When deploying multiple FastAPI instances, store connection/event routing in Redis pub/sub or use a managed realtime service. Otherwise an event published by instance A may not reach a browser connected to instance B.

## 5. FastAPI Application Design

### 5.1 Application startup

```python
# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.mongodb import connect_mongo, close_mongo

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_mongo()
    yield
    await close_mongo()

app = FastAPI(title="Voice Inventory API", version="1.0.0", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

Use the lifespan hook to create and close shared clients. Do not create a new MongoDB client for every request.

### 5.2 Configuration

```python
# backend/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    mongodb_uri: str
    mongodb_database: str = "voice_inventory"
    jwt_secret: str
    speech_provider: str = "sarvam"
    speech_api_key: str = ""
    redis_url: str = "redis://localhost:6379/0"
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
```

`.env` must never be committed:

```text
MONGODB_URI=mongodb+srv://...
MONGODB_DATABASE=voice_inventory
JWT_SECRET=use-a-long-random-secret
SPEECH_API_KEY=server-only-key
REDIS_URL=redis://...
FRONTEND_ORIGIN=http://localhost:5173
```

### 5.3 Pydantic request schemas

```python
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class CommitTransaction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: str
    operation: Literal["STOCK_IN", "STOCK_OUT", "ADJUSTMENT"]
    quantity: Decimal = Field(gt=0, le=1000000)
    unit: str = Field(min_length=1, max_length=30)
    reason: str | None = Field(default=None, max_length=100)
    confirmed: bool
```

Use `extra="forbid"` for security-sensitive request bodies. Validate quantities before business logic.

### 5.4 Dependency-based authentication

```python
from fastapi import Depends, HTTPException

async def current_context(token=Depends(oauth2_scheme)):
    claims = decode_and_verify_token(token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return {
        "user_id": claims["sub"],
        "shop_id": claims["shop_id"],
        "role": claims["role"]
    }
```

Every repository method receives `shop_id`; do not rely on a client-supplied shop ID.

### 5.5 Router example

```python
@router.post("/inventory/transactions", response_model=TransactionResponse)
async def create_transaction(
    body: CommitTransaction,
    context=Depends(current_context),
    service: InventoryService = Depends(get_inventory_service),
):
    require_role(context["role"], {"owner", "manager", "staff"})
    return await service.commit(
        shop_id=context["shop_id"],
        user_id=context["user_id"],
        body=body,
        idempotency_key=get_idempotency_key(),
    )
```

### 5.6 Service and repository separation

```text
Router
  -> Service: business rules and orchestration
      -> Repository: MongoDB queries
      -> Provider adapter: STT/TTS/NLP
      -> Event publisher: WebSocket/Redis
```

Do not put MongoDB queries, provider calls, and business decisions directly inside route functions. Separation makes testing and provider replacement easier.

## 6. MongoDB Data Model

Use collections rather than one giant inventory document. Large embedded arrays make updates and document growth difficult.

### 6.1 Collection: shops

```json
{
  "_id": "shop_001",
  "name": "Kumar General Store",
  "default_language": "te-IN",
  "response_language": "te-IN",
  "currency": "INR",
  "timezone": "Asia/Kolkata",
  "created_at": "ISODate"
}
```

### 6.2 Collection: users

```json
{
  "_id": "user_001",
  "shop_id": "shop_001",
  "name": "Abhishek Kumar",
  "phone": "+91...",
  "role": "owner",
  "active": true,
  "created_at": "ISODate"
}
```

### 6.3 Collection: products

```json
{
  "_id": "product_001",
  "shop_id": "shop_001",
  "display_name": "Rice",
  "normalized_name": "rice",
  "aliases": [
    {"text": "rice", "normalized": "rice", "language": "en"},
    {"text": "చెక్కెర", "normalized": "చెక్కెర", "language": "te"}
  ],
  "base_unit": "kg",
  "allowed_units": ["kg", "bag"],
  "conversions": [{"from": "bag", "to": "kg", "factor": 25}],
  "reorder_threshold": 20,
  "active": true,
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

For simpler first development, store aliases in a separate `product_aliases` collection. Keeping them embedded is convenient when the list is small; a separate collection is better when alias search becomes large or heavily indexed.

### 6.4 Collection: inventory_transactions

This is an immutable ledger.

```json
{
  "_id": "txn_001",
  "shop_id": "shop_001",
  "product_id": "product_001",
  "operation": "STOCK_IN",
  "quantity": 5,
  "unit": "bag",
  "normalized_quantity": 125,
  "normalized_unit": "kg",
  "price_total": 2500,
  "reason": "purchase",
  "source": "voice",
  "interaction_id": "voice_001",
  "idempotency_key": "client_456",
  "created_by": "user_001",
  "created_at": "ISODate"
}
```

### 6.5 Collection: stock_balances

This is a read-optimized projection.

```json
{
  "_id": "shop_001_product_001",
  "shop_id": "shop_001",
  "product_id": "product_001",
  "quantity": 18,
  "unit": "bag",
  "updated_at": "ISODate",
  "version": 42
}
```

### 6.6 Collection: voice_interactions

```json
{
  "_id": "voice_001",
  "shop_id": "shop_001",
  "user_id": "user_001",
  "status": "NEEDS_CONFIRMATION",
  "transcript": "Add five bags of rice",
  "language": "en-IN",
  "parsed_command": {
    "intent": "STOCK_IN",
    "product_text": "rice",
    "product_id": "product_001",
    "quantity": 5,
    "unit": "bag"
  },
  "confidence": 0.94,
  "provider": "speech-provider",
  "latency_ms": 1860,
  "expires_at": "ISODate",
  "created_at": "ISODate"
}
```

Never store an unbounded raw audio blob in the interaction document. Store object-storage metadata or a short-lived reference if audio retention is explicitly enabled.

### 6.7 Collection: alerts

```json
{
  "_id": "alert_001",
  "shop_id": "shop_001",
  "product_id": "product_001",
  "type": "LOW_STOCK",
  "status": "OPEN",
  "current_quantity": 18,
  "threshold": 20,
  "last_notified_at": "ISODate",
  "created_at": "ISODate"
}
```

### 6.8 Collection: idempotency_keys

```json
{
  "_id": "shop_001_client_456",
  "shop_id": "shop_001",
  "key": "client_456",
  "request_hash": "sha256...",
  "status": "COMPLETED",
  "response": {"transaction_id": "txn_001"},
  "created_at": "ISODate",
  "expires_at": "ISODate"
}
```

## 7. MongoDB Indexes and Validation

Create indexes at startup or through migrations:

```python
await db.products.create_index([("shop_id", 1), ("normalized_name", 1)])
await db.products.create_index([("shop_id", 1), ("active", 1)])
await db.inventory_transactions.create_index(
    [("shop_id", 1), ("product_id", 1), ("created_at", -1)]
)
await db.inventory_transactions.create_index(
    [("shop_id", 1), ("idempotency_key", 1)], unique=True
)
await db.stock_balances.create_index(
    [("shop_id", 1), ("product_id", 1)], unique=True
)
await db.alerts.create_index(
    [("shop_id", 1), ("status", 1), ("created_at", -1)]
)
```

Add MongoDB JSON schema validation for required fields, numeric types, enumerated operations, and non-negative thresholds. Schema validation prevents accidental type drift; application validation still remains necessary because business rules depend on the current stock and user role. [web:39]

## 8. Atomic Inventory Commit

### 8.1 Why transactions are needed

A stock change updates at least two pieces of data:

1. The immutable ledger event.
2. The current balance projection.

If the ledger succeeds but the balance fails, the dashboard becomes wrong. If the balance succeeds but the ledger fails, audit history is lost. A MongoDB transaction keeps these writes together.

### 8.2 Commit algorithm

```text
1. Verify authenticated shop and role.
2. Check idempotency key.
3. Start MongoDB session and transaction.
4. Lock/read the stock balance with a transaction context.
5. Validate product, unit, conversion, and quantity.
6. For STOCK_OUT, check sufficient stock.
7. Compute new balance using Decimal-like numeric handling.
8. Insert immutable transaction.
9. Update stock_balances with version increment.
10. Insert/update low-stock alert.
11. Store completed idempotency response.
12. Commit transaction.
13. Publish stock-updated event after successful commit.
```

### 8.3 Python/Motor-style pseudocode

```python
async def commit_stock(cmd, shop_id, user_id, idem_key):
    existing = await idempotency.find_one({
        "shop_id": shop_id,
        "key": idem_key
    })
    if existing:
        return existing["response"]

    async with await client.start_session() as session:
        async with session.start_transaction():
            product = await products.find_one(
                {"_id": cmd.product_id, "shop_id": shop_id, "active": True},
                session=session,
            )
            if not product:
                raise ProductNotFound()

            balance = await balances.find_one(
                {"shop_id": shop_id, "product_id": cmd.product_id},
                session=session,
            )
            old_qty = balance["quantity"] if balance else 0
            delta = convert_to_base_unit(product, cmd.quantity, cmd.unit)
            new_qty = old_qty + delta if cmd.operation == "STOCK_IN" else old_qty - delta

            if new_qty < 0 and not cmd.allow_negative:
                raise InsufficientStock()

            txn = build_ledger_document(...)
            await transactions.insert_one(txn, session=session)
            await balances.update_one(
                {"shop_id": shop_id, "product_id": cmd.product_id},
                {"$set": {"quantity": new_qty, "updated_at": now()},
                 "$inc": {"version": 1}},
                upsert=True,
                session=session,
            )

            response = {"transaction_id": txn["_id"], "new_quantity": new_qty}
            await idempotency.insert_one(build_idempotency(...), session=session)
            return response
```

Use a MongoDB deployment that supports multi-document transactions, such as a replica set or MongoDB Atlas. If a local standalone MongoDB does not support the required transaction configuration, run a replica-set Docker configuration or use Atlas.

## 9. Voice Processing Services

### 9.1 Speech service adapter

```python
class SpeechService:
    def __init__(self, provider):
        self.provider = provider

    async def transcribe(self, audio_bytes: bytes, language_hint: str | None):
        if self.provider == "sarvam":
            return await self._sarvam_transcribe(audio_bytes, language_hint)
        if self.provider == "bhashini":
            return await self._bhashini_transcribe(audio_bytes, language_hint)
        raise UnsupportedProvider()
```

Keep provider-specific authentication, endpoint formats, retries, and response mapping inside the adapter. The rest of the backend should receive a common result:

```json
{
  "text": "Add five bags of rice",
  "language": "en-IN",
  "segments": [],
  "provider_request_id": "provider-123"
}
```

### 9.2 Parsing strategy

Use the following order:

1. Normalize whitespace, punctuation, and number words.
2. Detect obvious command keywords and units with dictionaries.
3. Match products and aliases from MongoDB.
4. Use a deterministic parser for common command patterns.
5. Use a structured LLM only when deterministic parsing is inconclusive.
6. Validate the LLM JSON against Pydantic.
7. Never let the LLM directly commit a transaction.

### 9.3 Structured parser result

```python
class ParsedCommand(BaseModel):
    intent: Literal[
        "STOCK_IN", "STOCK_OUT", "STOCK_QUERY",
        "LOW_STOCK_QUERY", "REORDER_QUERY", "CANCEL", "UNKNOWN"
    ]
    product_text: str | None = None
    quantity: Decimal | None = Field(default=None, gt=0)
    unit: str | None = None
    price_total: Decimal | None = Field(default=None, ge=0)
    reason: str | None = None
    confidence: float = Field(ge=0, le=1)
```

### 9.4 Product resolution

```text
Input text
 -> normalize Unicode
 -> lower-case/transliterate where appropriate
 -> exact product match
 -> alias match
 -> token similarity
 -> candidate list
 -> one candidate: continue
 -> multiple candidates: ask user
 -> none: offer create-product flow
```

Do not store only English names. Store original script, transliteration, language, and aliases.

## 10. React Architecture

### 10.1 Component tree

```text
App
├── AuthProvider
├── I18nProvider
├── QueryClientProvider
└── AppRouter
    ├── LoginPage
    └── ProtectedLayout
        ├── DashboardPage
        │   ├── VoiceButton
        │   ├── StockSummaryCards
        │   ├── LowStockList
        │   └── RecentTransactions
        ├── ProductsPage
        ├── ProductFormPage
        ├── TransactionsPage
        ├── AlertsPage
        └── SettingsPage
```

### 10.2 State categories

Local UI state:

- Is microphone recording?
- Current modal open?
- Selected product filter?
- Confirmation dialog visibility?

Server state:

- Products.
- Stock balances.
- Alerts.
- Transactions.
- User/shop profile.

Workflow state:

- Recording.
- Uploading.
- Transcribing.
- Awaiting confirmation.
- Committing.
- Completed/error.

Use a server-state library such as TanStack Query for cache, loading, invalidation, and retries. Use a small store such as Zustand only for cross-page UI/workflow state if needed. Avoid copying the same product list into multiple React states; duplicate state can become inconsistent. [web:32]

### 10.3 API client

```ts
// frontend/src/lib/api.ts
const API_URL = import.meta.env.VITE_API_URL;

export async function apiFetch<T>(path: string, options: RequestInit = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error?.error?.message || "Request failed");
  }
  return response.json() as Promise<T>;
}
```

### 10.4 Audio capture

```ts
export async function recordAudio(
  onStop: (blob: Blob) => void,
  onState: (state: string) => void
) {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const recorder = new MediaRecorder(stream);
  const chunks: Blob[] = [];

  recorder.onstart = () => onState("recording");
  recorder.ondataavailable = (event) => {
    if (event.data.size > 0) chunks.push(event.data);
  };
  recorder.onstop = () => {
    stream.getTracks().forEach((track) => track.stop());
    onStop(new Blob(chunks, { type: recorder.mimeType }));
  };

  recorder.start();
  return () => recorder.stop();
}
```

The browser’s MediaRecorder API provides recording of a media stream. Test MIME type support on target Android browsers; do not assume every browser accepts the same codec. [web:3][web:11]

### 10.5 Voice hook

```ts
function useVoiceCommand() {
  const [state, setState] = useState("idle");
  const [preview, setPreview] = useState<VoicePreview | null>(null);

  async function submitAudio(blob: Blob) {
    setState("uploading");
    const form = new FormData();
    form.append("file", blob, "voice.webm");

    const response = await fetch(`${API_URL}/api/v1/voice/commands`, {
      method: "POST",
      body: form,
      credentials: "include",
    });

    if (!response.ok) throw new Error("Voice processing failed");
    const data = await response.json();
    setPreview(data);
    setState(data.status.toLowerCase());
  }

  return { state, preview, submitAudio };
}
```

### 10.6 Confirmation component

```tsx
function VoiceConfirmation({ preview, onConfirm, onCancel }) {
  return (
    <section role="dialog" aria-modal="true">
      <h2>I understood</h2>
      <p>Action: {preview.command.intent}</p>
      <p>Product: {preview.product_name}</p>
      <p>Quantity: {preview.command.quantity} {preview.command.unit}</p>
      <button onClick={onConfirm}>Confirm</button>
      <button onClick={onCancel}>Cancel</button>
    </section>
  );
}
```

## 11. REST Endpoint Catalogue

```text
POST /api/v1/auth/request-otp
POST /api/v1/auth/verify-otp
GET  /api/v1/me

GET  /api/v1/dashboard/summary
GET  /api/v1/products
POST /api/v1/products
GET  /api/v1/products/{id}
PATCH /api/v1/products/{id}

POST /api/v1/inventory/transactions
GET  /api/v1/inventory/transactions
POST /api/v1/inventory/transactions/{id}/reverse
GET  /api/v1/inventory/balances

POST /api/v1/voice/commands
GET  /api/v1/voice/commands/{interaction_id}
POST /api/v1/voice/commands/{interaction_id}/commit
POST /api/v1/voice/commands/{interaction_id}/cancel

GET  /api/v1/alerts
POST /api/v1/alerts/{id}/resolve

GET  /api/v1/settings
PATCH /api/v1/settings
GET  /api/v1/languages
```

## 12. Error and Retry Design

### 12.1 Error categories

```text
AUTH_REQUIRED
FORBIDDEN
INVALID_AUDIO
AUDIO_TOO_LARGE
SPEECH_PROVIDER_TIMEOUT
TRANSCRIPT_EMPTY
UNKNOWN_INTENT
PRODUCT_NOT_FOUND
MULTIPLE_PRODUCT_MATCHES
MISSING_QUANTITY
INVALID_UNIT
INSUFFICIENT_STOCK
CONFIRMATION_EXPIRED
IDEMPOTENCY_CONFLICT
DATABASE_UNAVAILABLE
RATE_LIMITED
```

### 12.2 Retry rules

- Retry STT provider timeout up to two times with exponential backoff.
- Retry GET requests when safe.
- Retry mutation only with the exact same idempotency key and request hash.
- Do not retry invalid audio, missing fields, forbidden operations, or insufficient stock.
- Show a manual form after voice failure.

## 13. Background Jobs

Use FastAPI `BackgroundTasks` only for short, non-critical work, such as recording an analytics event after returning a response. FastAPI documents that these tasks run after the response is sent. For reliable retries, long TTS generation, exports, or alert delivery, use Redis plus a worker such as Celery, RQ, or Arq. [web:34][web:37]

### 13.1 Worker jobs

```text
transcribe_audio_job
synthesize_response_audio_job
send_low_stock_notification_job
rebuild_stock_projection_job
daily_inventory_summary_job
export_transactions_job
cleanup_expired_voice_interactions_job
```

### 13.2 Job safety

- Each job has a unique job ID.
- Jobs are idempotent.
- Retryable and non-retryable errors are separated.
- Dead-letter jobs are visible to administrators.
- Worker logs include shop ID, job ID, and request ID but not secrets or unnecessary audio.

## 14. WebSocket Design

### 14.1 When to use WebSockets

Use WebSockets for:

- Partial transcription.
- Long audio processing progress.
- Live stock updates when several staff use the same shop.
- Push alerts.

Use normal HTTP for:

- Product CRUD.
- Confirmed transactions.
- Dashboard reads.
- Reports.

### 14.2 FastAPI WebSocket example

```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/events")
async def events_socket(websocket: WebSocket):
    await websocket.accept()
    context = await authenticate_websocket(websocket)
    await manager.connect(context["shop_id"], websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(context["shop_id"], websocket)
```

Do not keep an unlimited in-memory connection list in a multi-instance production deployment. Use Redis pub/sub or a managed event service for cross-instance delivery. FastAPI’s WebSocket interface supports receiving from and sending to connected clients. [web:38]

### 14.3 Event format

```json
{
  "event_id": "evt_001",
  "type": "STOCK_UPDATED",
  "shop_id": "shop_001",
  "data": {
    "product_id": "product_001",
    "quantity": 23,
    "unit": "bag"
  },
  "created_at": "ISODate"
}
```

React receives this event and invalidates the relevant product/balance query rather than manually guessing all derived values.

## 15. Latency Optimization for This Stack

### 15.1 Request path budget

```text
React click feedback             0–150 ms perceived
Audio encoding/upload             network dependent
STT provider                      largest variable
Parser/product match              50–300 ms target
MongoDB preview queries           20–100 ms target
Commit transaction                 30–200 ms target
React cache invalidation           under 100 ms perceived
```

### 15.2 Practical optimizations

1. Use a short recording limit, such as 8–12 seconds.
2. Stop on silence after a configurable threshold.
3. Upload compressed browser audio instead of large raw files.
4. Put FastAPI and MongoDB in a nearby region.
5. Reuse a global async MongoDB client.
6. Create compound indexes with `shop_id` first.
7. Cache product aliases and language dictionaries in Redis.
8. Use one preview endpoint that performs transcription, parsing, matching, and validation server-side.
9. Avoid an LLM call for simple commands already handled by deterministic patterns.
10. Run TTS and alert notifications after commit in workers.
11. Stream progress to React using WebSockets or server-sent events.
12. Return only the fields needed by the dashboard.
13. Use pagination for transaction history.
14. Compress responses and avoid repeated full-list reloads.
15. Use `stale-while-revalidate` behavior in the frontend server-state cache.

### 15.3 Latency instrumentation

Add a timer for:

```text
recording_duration_ms
upload_ms
stt_ms
language_detection_ms
parsing_ms
product_matching_ms
mongodb_preview_ms
mongodb_commit_ms
tts_ms
total_ms
```

Store aggregates, not necessarily every raw transcript, for performance analysis. Alert when p95 exceeds the target.

## 16. Security and Tenant Isolation

### 16.1 Request security

- Use HTTPS.
- Validate JWT or session on every protected request.
- Derive `shop_id` from the authenticated token.
- Reject client-supplied shop IDs that differ from token context.
- Apply role checks to every mutation.
- Rate-limit voice uploads and login attempts.
- Limit audio size, duration, MIME type, and file extension.
- Keep STT/TTS/LLM keys exclusively in FastAPI environment variables.
- Use CORS with a fixed frontend origin.
- Add security headers and Content Security Policy.

### 16.2 MongoDB security

- Use a dedicated database user with only required permissions.
- Require TLS for Atlas connections.
- Restrict network access through IP allowlists/private networking.
- Do not expose MongoDB directly to React.
- Encrypt backups and restrict access.
- Add schema validation.
- Use audit logs for owner-level changes.

### 16.3 Voice privacy

- Show microphone status clearly.
- Ask permission before recording.
- Do not record in the background.
- Delete raw audio quickly by default.
- Document provider data processing.
- Allow the shop owner to delete transcripts and voice history where appropriate.

## 17. Testing Strategy

### 17.1 Backend tests

- Pydantic validation tests.
- Unit conversion tests.
- Product matching tests.
- Role/tenant isolation tests.
- MongoDB repository tests using a test database.
- Transaction rollback tests.
- Idempotency tests.
- Provider adapter mock tests.
- API contract tests.

### 17.2 Frontend tests

- Voice state-machine tests.
- Confirmation and cancel tests.
- API error rendering.
- Dashboard loading/empty/error states.
- Language switching.
- Mobile responsive tests.
- Microphone permission denial.

### 17.3 End-to-end tests

```text
Login -> dashboard -> record audio -> preview -> confirm
-> transaction committed -> balance updated -> low-stock status updated
```

### 17.4 Load tests

Simulate:

- 50–100 dashboard requests per second.
- Concurrent short voice uploads.
- Multiple users updating the same product.
- Repeated idempotent commit retries.

Measure p50/p95/p99 latency, error rate, MongoDB CPU, connection pool usage, and provider throttling.

## 18. Build Sequence

### Day-one build order

1. Create React and FastAPI projects.
2. Connect FastAPI to MongoDB Atlas or replica-set MongoDB.
3. Implement products and stock balances.
4. Implement immutable transactions and atomic commit.
5. Build React dashboard and manual transaction form.
6. Add microphone capture.
7. Add one STT provider adapter.
8. Implement deterministic parser for five demo phrases.
9. Add confirmation and commit flow.
10. Add low-stock query.
11. Add error handling and manual fallback.
12. Deploy and test on Android.

### Production build order

1. Authentication and RBAC.
2. Tenant isolation and security review.
3. Regional language dictionaries and native-speaker evaluation.
4. Provider fallback and queue workers.
5. WebSocket live updates.
6. Audit, exports, backups, monitoring.
7. Offline read cache and safe pending transaction queue.
8. Performance/load testing.

## 19. Complete Example: One Command Across All Layers

User says: “Remove two cartons of soap.”

```text
React:
  MediaRecorder captures audio blob.

React -> FastAPI:
  multipart POST /api/v1/voice/commands.

FastAPI:
  authenticates user and identifies shop_001.
  validates audio size and type.
  calls STT provider.

STT provider -> FastAPI:
  "Remove two cartons of soap", en-IN.

FastAPI NLP:
  intent = STOCK_OUT
  product_text = soap
  quantity = 2
  unit = carton

FastAPI MongoDB:
  finds soap product and current balance.
  finds permitted carton unit.
  prepares preview; no write.

FastAPI -> React:
  status = NEEDS_CONFIRMATION.

React:
  shows “Remove 2 cartons of Soap?”

User clicks Confirm.

React -> FastAPI:
  POST commit with interaction ID and idempotency key.

FastAPI:
  revalidates interaction and current stock.
  starts MongoDB transaction.
  inserts STOCK_OUT ledger event.
  updates stock_balances.
  creates/updates low-stock alert.
  stores idempotency response.
  commits.

FastAPI -> React:
  new quantity, transaction ID, alert status.

FastAPI -> Redis/worker:
  publishes STOCK_UPDATED and optional TTS/notification task.

React:
  invalidates product and dashboard queries.
  displays success in selected language.
```

## 20. Definition of Technical Completion

The architecture is technically complete when:

- React communicates only with FastAPI, never directly with MongoDB.
- FastAPI authenticates, validates, authorizes, and logs every request.
- MongoDB contains an immutable ledger and a current balance projection.
- Stock changes are atomic and idempotent.
- Voice commands always pass through transcript, structured parsing, product matching, confirmation, and server-side revalidation.
- Provider APIs are hidden behind adapters and server-side secrets.
- WebSockets are optional for progress and realtime updates, with Redis support when horizontally scaled.
- Long or retryable tasks run in workers instead of blocking API requests.
- All tenant-scoped queries include authenticated `shop_id`.
- Mobile, low-network, language, accessibility, and failure scenarios are tested.

**Key principle:** React collects intent, FastAPI enforces business rules, MongoDB records truth, workers handle slow work, and speech/LLM services provide interpretation—not authority over inventory.

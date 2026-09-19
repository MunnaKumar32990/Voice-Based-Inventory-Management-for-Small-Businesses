# Voice-Based Inventory Management System

Voice-first stock management for Indian kirana shops. Speak in **English, Hindi, or Telugu** (mixed) to add/remove/check stock. Built with **React + TypeScript + Tailwind** (frontend), **FastAPI + Motor** (backend), **MongoDB** (ledger + balances).

## Your only task: API keys (optional)

The app runs end-to-end with **zero keys**: browser Web Speech API handles voice, demo login seeds the shop.

| Key | Where | Needed for |
|---|---|---|
| none | — | Demo: mic transcript → parse → confirm → commit |
| `SARVAM_API_KEY` | `backend/.env` + `SPEECH_PROVIDER=sarvam` | Server-side Sarvam AI transcription (POST `/api/v1/voice/transcribe`) |
| `GOOGLE_SPEECH_API_KEY` | `backend/.env` + `SPEECH_PROVIDER=google` | Server-side Google Cloud Speech transcription |
| `AZURE_SPEECH_KEY` + `AZURE_SPEECH_REGION` | `backend/.env` + `SPEECH_PROVIDER=azure` | Azure AI Speech STT (`/voice/transcribe`) + TTS (`/voice/speak`) |

### Azure AI Speech setup (your keys)

You have a Cognitive Services Speech resource (region `uaenorth`, endpoint `https://uaenorth.api.cognitive.microsoft.com/`). Either Key1 or Key2 works.

1. **Backend** — in `backend/.env`:
   - `SPEECH_PROVIDER=azure`
   - `AZURE_SPEECH_KEY=<paste Key1 or Key2>`
   - `AZURE_SPEECH_REGION=uaenorth`
   - restart: `uvicorn app.main:app --reload`
2. **Frontend** — in `frontend/.env`:
   - `VITE_SPEECH_PROVIDER=azure`
   - restart: `npm run dev`
3. **Use it:** tap mic → speak → tap again to stop → audio uploads to `POST /api/v1/voice/transcribe` (Azure STT with `en-IN`/`hi-IN`/`te-IN` from your UI language) → same confirm/commit flow. Confirmations play via `POST /api/v1/voice/speak` (Azure neural voices: `en-IN-NeerjaNeural`, `hi-IN-SwaraNeural`, `te-IN-ShrutiNeural`); without keys it falls back to free browser voices.
4. **Never** put these keys in frontend code — they stay server-side in `backend/.env` (gitignored).

## Quickstart (local)

1. **Database:** from repo root `docker compose up -d mongodb` (replica-set; required for atomic commits).
2. **Backend:**
   - `cd backend`
   - `python -m venv venv`; `venv\Scripts\activate` (Windows) or `source venv/bin/activate`
   - `pip install -r requirements.txt`
   - copy `.env.example` → `.env` (works as-is; only add keys above if needed)
   - `uvicorn app.main:app --reload` → http://localhost:8000/health
3. **Frontend:**
   - `cd frontend`
   - `npm install`
   - copy `.env.example` → `.env` (default `VITE_API_URL=http://localhost:8000` works)
   - `npm run dev` → http://localhost:5173
4. **Demo:** Start Demo as *Kumar General Store* → mic → “Add five bags of rice” → Confirm → balance updates. Fallback when voice/mic fails: `/manual`.

Or run everything: `docker compose up --build` (mongodb + backend + frontend).

## Tests & checks

- Backend: `cd backend; python -m pytest tests/ -v` (26 tests: NLP, units, matcher, inventory commit/idempotency/tenant isolation, voice logic)
- Frontend: `cd frontend; npm run build` (`tsc -b && vite build`); `npm run lint`; `npm run typecheck`
- Demo script: `scripts/demo_commands.md` (acceptance A1–A10). Seed directly: `cd backend; python -m app.db.seed`.

## API map

- `POST /api/v1/auth/demo-login` → `{access_token, shop_id, ...}` (seeds shop on first login)
- `GET /api/v1/dashboard/summary`, `GET /api/v1/products/`, `POST /api/v1/products/`, `PATCH /api/v1/products/{id}`
- `POST /api/v1/inventory/transactions` (manual, idempotent via `client_request_id`), `GET /api/v1/inventory/transactions`, `POST /api/v1/inventory/transactions/{id}/reverse`, `GET /api/v1/inventory/balances`
- `POST /api/v1/voice/commands` (transcript → preview, no write), `POST /api/v1/voice/commands/{id}/commit` (supports quantity/unit edit overrides), `POST .../cancel`, `POST /api/v1/voice/transcribe` (audio, needs provider key)
- `GET /api/v1/alerts/`, `POST /api/v1/alerts/{id}/resolve`
- `WS /ws/events?token=<JWT>` — shop-scoped `STOCK_UPDATED` fan-out

## Notes

- Every stock mutation needs confirmation; the server re-validates product/unit/balance and never trusts client math.
- Retries with the same idempotency key return the original entry (`already_processed`).
- `STOCK_OUT` beyond balance is blocked; `ADJUSTMENT` sets an absolute level.
- Packaging units without a configured conversion (packet/bottle/piece) are tracked as-is instead of crashing.

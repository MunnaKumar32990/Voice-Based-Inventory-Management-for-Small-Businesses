# Voice-Based Inventory Management for Small Businesses
## Complete Project Requirements Blueprint

**Version:** 1.0  
**Prepared for:** Voice-first inventory solution for Indian small businesses  
**Target delivery:** 1-day prototype/MVP; architecture supports later production scaling  
**Primary users:** Kirana shops, wholesalers, pharmacies, retailers, small warehouses, and micro-enterprises  
**Initial language example:** Telugu + Hindi + English code-mixing; design must support additional Indian languages.

> Important scope note: the supplied plan contains approximately 24 hours of listed work but the stated duration is one day. A reliable production system cannot be completed in one day. This blueprint separates a demonstrable MVP from production hardening. For the one-day submission, build a narrow vertical slice: login/demo shop, product creation, voice add/remove, stock dashboard, low-stock alert, and a short demo flow.

## 1. Executive Summary

The product is a voice-first inventory web application that lets a shop owner maintain stock with natural speech instead of typing. A user can say, for example:

- “Add five bags of rice.”
- “Remove two cartons of soap.”
- “చెక్కెర పది కిలోలు వచ్చింది” (ten kilograms of sugar arrived).
- “How much rice is left?”
- “ఏవి తక్కువగా ఉన్నాయి?” (Which items are low?)

The application converts speech to text, identifies the user’s intent, extracts product, quantity, unit, price, and operation, validates the command, requests confirmation when confidence is low, writes an auditable stock transaction, recalculates current stock, and responds in the user’s chosen language.

The central design principle is **safe voice automation**: speech must never silently create a damaging inventory change. Every mutation should be previewed or confirmed unless the user has explicitly enabled trusted mode.

### 1.1 Product objectives

1. Reduce typing and literacy barriers.
2. Support regional-language and mixed-language speech.
3. Handle practical trade units such as pieces, kilograms, grams, litres, bags, cartons, boxes, dozens, and quintals.
4. Make stock status understandable at a glance and by voice.
5. Preserve a transaction history for correction and audit.
6. Work acceptably on low-cost Android phones and unstable networks.
7. Keep the first interaction fast, with visible progress and graceful fallback.

### 1.2 Non-goals for MVP

- Full accounting, GST invoicing, supplier payment management, or payroll.
- Automatic product recognition from camera images.
- Fully offline speech recognition for every Indian language.
- Autonomous purchasing or supplier ordering.
- Complex multi-warehouse transfer workflows.
- Medical, financial, or legally binding advice.

## 2. Users, Context, and Personas

### 2.1 Primary persona: shop owner

The owner may have limited experience with software, may prefer Telugu, Hindi, Tamil, or another local language, and may use familiar units rather than standardized units. They need immediate answers during a busy sale.

**Needs:** fast entry, minimal screens, correction, clear totals, audible responses, no technical terminology.

### 2.2 Secondary persona: helper or employee

The employee records incoming stock and sales but should not necessarily delete transactions or change settings.

**Needs:** quick access, role-based permissions, simple confirmation, user attribution.

### 2.3 Administrator

The administrator configures shop details, languages, units, reorder thresholds, users, exports, and integrations.

### 2.4 Operating conditions

- Android Chrome or a lightweight Android app.
- Low-end microphones, background noise, fans, traffic, and multiple speakers.
- Intermittent mobile data.
- Product names with local pronunciation, English brand names, abbreviations, and spelling variation.
- Mixed units and phrases such as “2 dozen,” “half bag,” “one and a quarter kilo,” or “₹1,200 worth.”

## 3. MVP Scope and Acceptance Criteria

### 3.1 One-day demonstrable MVP

The MVP should include:

- Demo login or simple shop profile.
- Product list with product name, current quantity, base unit, and reorder threshold.
- Add-stock and remove-stock operations.
- Microphone button using recorded audio.
- Speech-to-text integration for one primary regional language plus English mixing.
- Intent extraction for add, remove, query, and low-stock requests.
- Confirmation card showing parsed command before mutation.
- Stock ledger and current balance.
- Low-stock indicator.
- Text response and optional text-to-speech response.
- Responsive web UI.
- Seed data and a five-command demo script.

### 3.2 MVP acceptance tests

| ID | Test | Expected result |
|---|---|---|
| A1 | Add “5 bags rice” | Rice balance increases by 5 bags and ledger records an inbound transaction |
| A2 | Remove “2 cartons soap” | Soap balance decreases by 2 cartons if sufficient stock exists |
| A3 | Remove more than available | Operation is blocked or explicitly requires override; negative balance is not silently created |
| A4 | Ask “How much rice?” | Current rice balance and unit are displayed and optionally spoken |
| A5 | Ask “What is low?” | Products at or below threshold are listed |
| A6 | Unknown product name | User receives a product-selection or create-product prompt |
| A7 | Ambiguous quantity | System asks a clarification question instead of writing data |
| A8 | Duplicate request | Same client request ID does not create two ledger entries |
| A9 | Network failure | Audio/transcription error is shown with retry and manual-entry fallback |
| A10 | Language switch | UI and response language change without corrupting stored product data |

## 4. Functional Requirements

### 4.1 Authentication and shop setup

- FR-001: A user can create or enter a shop profile.
- FR-002: The profile stores shop name, owner name, country, default language, timezone, and currency.
- FR-003: The MVP may use a demo login; production must use passwordless OTP or a secure authentication provider.
- FR-004: Sessions must expire and be revocable.
- FR-005: A shop must be isolated from every other shop using tenant IDs and database policies.
- FR-006: Roles shall include owner, manager, and staff.

### 4.2 Product management

- FR-010: Create product with name, aliases, category, default unit, current opening balance, reorder threshold, optional SKU, and optional price.
- FR-011: Search products by normalized name, alias, transliteration, SKU, or barcode in later versions.
- FR-012: Support aliases such as “sugar,” “cheeni,” “చక్కెర,” and local pronunciation variants.
- FR-013: Product names must preserve the original display name and a normalized search form.
- FR-014: A product can be archived but not physically deleted if transactions exist.
- FR-015: A product can have a preferred unit and permitted alternate units.

### 4.3 Inventory operations

- FR-020: Record inbound stock.
- FR-021: Record outbound stock due to sale, damage, consumption, or adjustment.
- FR-022: Record manual correction with a mandatory reason.
- FR-023: Store quantity as a precise numeric value, not a floating-point binary value.
- FR-024: Store both the spoken unit and normalized base-unit quantity.
- FR-025: Prevent negative stock by default.
- FR-026: Permit owner override only with explicit reason and audit record.
- FR-027: Show current stock, reserved stock if added later, available stock, and reorder status.
- FR-028: Support transaction reversal by creating a compensating transaction rather than editing history.
- FR-029: Allow filtering by date, product, user, operation, and source.

### 4.4 Voice interaction

- FR-030: A large microphone control shall start and stop recording.
- FR-031: Show recording, uploading, transcribing, understanding, confirmation, and completed states.
- FR-032: The system shall accept regional-language, English, and code-mixed speech.
- FR-033: The system shall extract intent, product, quantity, unit, price, direction, and reason when present.
- FR-034: The system shall display the recognized transcript before mutation.
- FR-035: The user can edit extracted fields manually.
- FR-036: The user can say “cancel,” “no,” or “undo” where the interaction state permits it.
- FR-037: The system shall keep audio retention disabled by default or delete raw audio after a configurable period.

### 4.5 Questions and alerts

- FR-040: Ask stock by product.
- FR-041: Ask for all low-stock products.
- FR-042: Ask what must be reordered.
- FR-043: Ask recent stock movement.
- FR-044: Answer from database data, not from an LLM’s unsupported guess.
- FR-045: Use deterministic query functions for quantities and thresholds.
- FR-046: Generate alerts when stock is at or below a threshold.
- FR-047: Avoid duplicate alerts by storing alert state and last-notified timestamp.

### 4.6 Localization

- FR-050: UI labels shall be translated through locale files.
- FR-051: Response templates shall be translated and reviewed by native speakers.
- FR-052: Product names shall remain searchable across scripts and transliteration.
- FR-053: Number words and units shall be mapped per language.
- FR-054: Support code mixing such as “rice five bags add cheyyi.”
- FR-055: Users can select input language, output language, or automatic detection.

## 5. Voice/NLP Design

### 5.1 Pipeline

```text
Microphone
  -> audio capture and compression
  -> speech-to-text
  -> language detection / code-mix metadata
  -> text normalization
  -> intent and entity extraction
  -> product/alias matching
  -> unit and quantity conversion
  -> validation
  -> confirmation UI
  -> transactional database write
  -> refreshed stock and response generation
  -> optional text-to-speech
```

For Indian-language coverage, evaluate a provider such as Sarvam AI, which documents speech-to-text for Indian languages, code-mixing, streaming and batch modes, and text-to-speech capabilities. BHASHINI is another ecosystem to evaluate for Indian-language services and APIs. Treat provider coverage, price, quotas, data handling, and latency as items to verify during implementation rather than assumptions. [web:14][web:15][web:17]

### 5.2 Example command interpretation

Input: “Add two cartons of Surf, price 840.”

```json
{
  "intent": "STOCK_IN",
  "product_text": "Surf",
  "quantity": 2,
  "unit": "carton",
  "unit_quantity": 2,
  "price_total": 840,
  "currency": "INR",
  "confidence": 0.94,
  "language": "en-IN",
  "requires_confirmation": true
}
```

Input: “Rice five bags came.”

```json
{
  "intent": "STOCK_IN",
  "product_text": "rice",
  "quantity": 5,
  "unit": "bag",
  "confidence": 0.90,
  "requires_confirmation": true
}
```

### 5.3 Intent catalogue

- STOCK_IN: incoming purchase or restock.
- STOCK_OUT: sale, dispatch, or removal.
- STOCK_QUERY: quantity for one product.
- LOW_STOCK_QUERY: items at or below threshold.
- REORDER_QUERY: items requiring purchase.
- PRODUCT_CREATE: create a new item.
- STOCK_ADJUST: correction, damage, wastage, or counting adjustment.
- CANCEL: cancel current voice action.
- HELP: explain available commands.
- UNKNOWN: request clarification.

### 5.4 Entity extraction rules

Extract the following entities:

- `product_name`: noun phrase or recognized alias.
- `quantity`: integer, decimal, fraction, or number word.
- `unit`: piece, kg, gram, litre, bag, carton, box, dozen, quintal, etc.
- `direction`: add, receive, came, sale, sold, remove, went out.
- `price`: amount and whether per unit or total.
- `reason`: sale, damaged, returned, adjustment, transfer.
- `date`: optional past-date transaction.

The NLP model must not invent a missing quantity or unit. Missing required fields cause clarification.

### 5.5 Product matching

Use a staged matcher:

1. Exact normalized match.
2. Alias match.
3. Transliteration match.
4. Token similarity using a database trigram index or application-side fuzzy matching.
5. Phonetic/embedding match only as a later fallback.
6. If multiple products match, show a numbered choice.

Example: “sugar,” “cheeni,” “chini,” and “చెక్కెర” can resolve to one product if configured as aliases. Never automatically map a low-confidence match when two products are plausible.

### 5.6 Confidence policy

- Confidence ≥ 0.90 and one product match: show compact confirmation.
- 0.70–0.89: show all parsed fields and ask confirmation.
- < 0.70: ask the user to repeat or choose fields.
- Any missing product, quantity, or direction: clarification required.
- Any high-risk operation such as large adjustment or negative-stock override: owner confirmation required regardless of confidence.

### 5.7 Prompt-injection and hallucination resistance

The LLM, if used, is an interpreter—not the authority for inventory values. Give it a strict JSON schema and tools such as `find_product`, `get_stock`, and `prepare_transaction`. The server independently validates every field, product ID, unit conversion, role, and balance. Do not allow free-form model output to execute SQL or mutate stock.

## 6. Units and Quantity Model

### 6.1 Supported units

MVP units:

- piece / pcs
- kilogram / kg
- gram / g
- litre / L
- millilitre / ml
- bag
- carton
- box
- dozen
- quintal

### 6.2 Unit policy

A unit is not universally convertible. One bag of rice may weigh 25 kg, while one bag of fertilizer may weigh 50 kg. Therefore:

- Countable units such as dozen can convert to pieces: 1 dozen = 12 pieces.
- Weight and volume units convert only when configured for a product.
- Bag, carton, and box conversions are product-specific.
- The database stores the original unit and normalized quantity where a conversion exists.
- If no conversion exists, stock is tracked in that unit independently.

Example product configuration:

```json
{
  "product": "Rice",
  "base_unit": "kg",
  "conversions": [{"from": "bag", "to": "kg", "factor": 25}]
}
```

A command “add 2 bags rice” then records original quantity 2 bags and normalized quantity 50 kg. If the user has not configured bag size, ask: “How many kilograms are in one bag of rice?”

### 6.3 Numeric safety

Use PostgreSQL `numeric`, decimal arithmetic in application code, and validation limits. Reject NaN, infinity, negative quantities, and unreasonable values. Store quantities with a sensible scale, such as three decimal places for weight and volume.

## 7. Data and Database Design

A PostgreSQL backend is recommended for the MVP because inventory needs transactions, constraints, history, and reliable queries. Supabase can provide Postgres, authentication, Realtime, backups, and Edge Functions; its Realtime service can stream database changes, although event design and authorization must be configured carefully. [web:5][web:6][web:8]

### 7.1 Core tables

```text
shops
- id UUID primary key
- name
- default_language
- currency
- timezone
- created_at

users
- id UUID primary key
- shop_id foreign key
- name
- role
- phone
- created_at

products
- id UUID primary key
- shop_id foreign key
- display_name
- normalized_name
- category
- base_unit
- reorder_threshold numeric
- active boolean
- created_at
- updated_at

product_aliases
- id UUID primary key
- product_id foreign key
- alias_text
- normalized_alias
- language

unit_conversions
- id UUID primary key
- product_id foreign key
- from_unit
- to_unit
- factor numeric

inventory_transactions
- id UUID primary key
- shop_id foreign key
- product_id foreign key
- operation enum
- quantity numeric
- unit
- normalized_quantity numeric nullable
- normalized_unit nullable
- price_total numeric nullable
- reason
- source enum manual, voice, import, adjustment
- client_request_id unique
- created_by
- created_at
- reversed_transaction_id nullable

stock_balances
- shop_id
- product_id
- quantity numeric
- unit
- updated_at
- primary key(shop_id, product_id)

voice_interactions
- id UUID primary key
- shop_id
- user_id
- language
- transcript
- parsed_json
- confidence
- latency_ms
- provider
- error_code
- created_at

alerts
- id UUID primary key
- shop_id
- product_id
- alert_type
- status
- last_notified_at
- created_at
```

### 7.2 Inventory consistency

Use one database transaction for:

1. Locking the product balance row.
2. Checking available quantity.
3. Inserting the immutable ledger transaction.
4. Updating `stock_balances`.
5. Creating or resolving a low-stock alert.

Use an idempotency key such as `client_request_id`. A retry after a timeout must return the original result rather than applying the same stock change twice.

### 7.3 Ledger versus calculated balance

The ledger is the source of truth for audit. A balance table is a performance projection. A scheduled reconciliation job can compare the balance with the ledger and flag discrepancies. Never allow a normal user to edit a historical transaction directly.

### 7.4 Security policies

- Every row includes `shop_id` where tenant isolation is needed.
- Row-level security restricts reads and writes to the authenticated user’s shop.
- Staff cannot change shop settings or delete users.
- Service keys stay only on the server and are never sent to the browser.
- Voice-provider keys are proxied through a backend endpoint.
- Export links are short-lived and scoped to the shop.

## 8. API Contract

### 8.1 REST endpoints

```text
POST   /api/v1/voice/transcribe
POST   /api/v1/voice/interpret
POST   /api/v1/inventory/transactions/prepare
POST   /api/v1/inventory/transactions/commit
GET    /api/v1/inventory/products
POST   /api/v1/inventory/products
PATCH  /api/v1/inventory/products/:id
GET    /api/v1/inventory/summary
GET    /api/v1/inventory/transactions
GET    /api/v1/inventory/alerts
POST   /api/v1/inventory/transactions/:id/reverse
GET    /api/v1/settings/languages
```

### 8.2 Commit request example

```json
{
  "client_request_id": "01J-unique-request-id",
  "product_id": "product-uuid",
  "operation": "STOCK_IN",
  "quantity": 5,
  "unit": "bag",
  "price_total": 2500,
  "reason": "purchase",
  "source": "voice",
  "confirmed_transcript": "Add five bags of rice"
}
```

### 8.3 Error format

```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Only 3 cartons are available.",
    "fields": {"quantity": "Reduce quantity or confirm an override."},
    "request_id": "request-id"
  }
}
```

Errors must be user-friendly in the UI and structured for logs. Do not expose stack traces, provider tokens, SQL, or internal prompts.

## 9. Frontend and UX Blueprint

### 9.1 Screens

1. Welcome/login.
2. Shop setup.
3. Home dashboard.
4. Voice action sheet.
5. Parsed-command confirmation.
6. Product list.
7. Add/edit product.
8. Transaction history.
9. Alerts and reorder list.
10. Language and settings.
11. Help/examples.

### 9.2 Dashboard

The dashboard should show:

- One primary microphone button.
- Today’s inbound and outbound counts.
- Low-stock count.
- Search field as fallback.
- Recent transactions.
- Large, readable quantities and units.
- Color plus text indicators; do not rely on color alone.

### 9.3 Voice action states

```text
Idle -> Listening -> Recording -> Uploading -> Transcribing
-> Understanding -> Needs confirmation -> Committing -> Completed
                                      \-> Needs clarification
Any state -> Error -> Retry / Manual entry
```

Each state needs a visible label and accessible status announcement. The user should know whether the app is listening, because accidental recording is a privacy risk.

### 9.4 Confirmation card example

```text
I understood:
Action: Add stock
Product: Rice
Quantity: 5 bags
Price: ₹2,500 total

[Confirm] [Edit] [Cancel]
```

For a query, confirmation is unnecessary unless the product match is ambiguous. For a mutation, confirmation is the default.

### 9.5 Accessibility and usability

- Minimum large touch targets.
- High contrast and readable typography.
- Hindi/Telugu/local-script rendering tested on Android.
- Screen-reader labels for buttons.
- Keyboard fallback.
- No critical information communicated only through color.
- Short, non-technical language such as “Stock is low” rather than “threshold breached.”
- Provide example commands on the microphone screen.

## 10. Technology Stack and Connections

### 10.1 Recommended MVP stack

| Layer | Recommendation | Reason |
|---|---|---|
| Frontend | Next.js or React + TypeScript + Tailwind | Fast responsive web delivery |
| Audio | `getUserMedia` + MediaRecorder | Browser capture with a broad modern-browser baseline; MediaRecorder records a MediaStream. [web:3][web:11] |
| Speech-to-text | Sarvam AI or BHASHINI evaluation path | Indian-language and code-mixed support; verify quotas and latency. [web:14][web:17] |
| NLP | Deterministic parser + structured LLM fallback | Lower latency and safer mutations |
| Backend | FastAPI or Node.js/NestJS | Clear API and validation layer |
| Database | PostgreSQL/Supabase | Transactions, constraints, RLS, backups, realtime options. [web:5][web:6] |
| Authentication | Supabase Auth or managed OTP provider | Avoid custom password security |
| Storage | Object storage with short-lived URLs | Optional audio/debug artifacts |
| Deployment | Vercel/Cloudflare for frontend; Render/Fly.io/AWS for API | Simple MVP deployment |
| Monitoring | Sentry + structured logs + provider metrics | Fast diagnosis |

The browser Web Speech API can be useful as a quick fallback or demo, but it depends on browser support and an underlying recognition service. For a controlled regional-language product, use a server or provider integration as the primary path and retain manual text entry as a fallback. [web:4][web:13]

### 10.2 Integration diagram

```text
Browser/PWA
  | HTTPS
  v
API Gateway / Backend
  |-- Auth provider
  |-- STT provider: Sarvam/BHASHINI adapter
  |-- NLP parser / optional LLM
  |-- PostgreSQL/Supabase
  |-- TTS provider
  |-- Object storage
  |-- Monitoring and audit logs
```

Create a provider adapter interface:

```ts
interface SpeechProvider {
  transcribe(audio: Buffer, options: SpeechOptions): Promise<TranscriptResult>
  stream?(chunks: AsyncIterable<Buffer>, options: SpeechOptions): AsyncIterable<PartialTranscript>
}
```

This avoids locking the application to one speech vendor and allows fallback providers.

## 11. Latency Optimization

### 11.1 Target budgets

Set measurable targets rather than promising an exact response time:

- Microphone start feedback: under 150 ms after button press.
- Audio upload begins while recording stops.
- Short-command transcription: target p50 under 2 seconds on a good mobile connection.
- Parse and validate: target p95 under 500 ms.
- Database commit: target p95 under 300 ms.
- Dashboard refresh: target p95 under 500 ms after commit.
- End-to-end confirmed mutation: target p50 under 3 seconds plus user confirmation time.

Actual provider performance must be benchmarked from India on representative networks.

### 11.2 Techniques

1. Use short utterances and automatic stop after silence, with a maximum recording duration.
2. Compress audio to a provider-supported format and sample rate; do not upload raw video or unnecessarily large PCM.
3. Use streaming speech recognition when the provider supports it; update partial transcript while the user is speaking.
4. Start NLP parsing as soon as a stable partial transcript is available, but never commit until final transcript and confirmation.
5. Keep API and database region close to the user base.
6. Cache product aliases, units, language configuration, and dashboard summary.
7. Use one backend call to prepare and validate a command rather than multiple sequential round trips.
8. Use database indexes on `shop_id`, `normalized_name`, `product_id`, and timestamps.
9. Debounce search and cancel stale requests.
10. Use optimistic UI only for non-critical display changes; the server remains authoritative.
11. Use background jobs for TTS, analytics, and alert notifications.
12. Avoid sending full inventory data to an LLM; send only the required product candidates or use deterministic SQL.
13. Reuse HTTP connections and enable compression for JSON.
14. Add request IDs and timing spans for audio capture, upload, STT, parsing, DB, and TTS.

### 11.3 Perceived latency

While processing, show the recognized transcript and stage-specific progress. A user tolerates a visible three-second process better than a silent spinner. For a query, render a provisional “Checking your stock…” message and then replace it with the database result.

### 11.4 Offline and poor-network behavior

- Cache the shell and product list with a service worker.
- Permit manual transactions to queue locally only if the user understands they are pending.
- Store an idempotency key for every queued operation.
- Never claim a transaction is completed until the server acknowledges it.
- Display “Pending sync” clearly.
- Avoid offline voice claims unless an on-device model has been tested for the target languages.

## 12. Reliability, Security, and Privacy

### 12.1 Reliability requirements

- Retry transient provider failures with exponential backoff and jitter.
- Do not retry a mutation without an idempotency key.
- Use circuit breakers for unavailable speech providers.
- Provide manual text entry when voice fails.
- Add database backups and restore testing before production.
- Use health endpoints for API, database, and provider status.

### 12.2 Security requirements

- HTTPS everywhere.
- Secure, HTTP-only session cookies where applicable.
- Rate-limit authentication, transcription, and mutation endpoints.
- Validate MIME type, file size, duration, and content for uploaded audio.
- Restrict CORS to known origins.
- Sanitize product names for display and exports.
- Protect against SQL injection through parameterized queries/ORM.
- Use CSP, secure headers, and dependency scanning.
- Keep secrets in environment variables or a secret manager.
- Log security events without storing raw speech unnecessarily.

### 12.3 Privacy requirements

Speech can contain personal or business information. Define:

- Whether raw audio is stored.
- Retention period for transcripts.
- Which provider receives audio.
- Whether data is used for provider training.
- How a shop exports or deletes its data.
- How staff consent and notification are handled.

Default policy: process audio, retain only transcript/structured result for a limited period, and delete raw audio unless the owner explicitly enables debugging retention.

## 13. Testing and Quality Assurance

### 13.1 Test layers

- Unit tests: number parsing, unit conversion, language normalization, threshold calculation.
- Parser tests: commands across languages and code-mix patterns.
- Integration tests: STT adapter mock, API, database transaction, idempotency.
- End-to-end tests: microphone permission, confirmation, commit, dashboard update.
- Security tests: tenant isolation, role restrictions, rate limits, malicious input.
- Load tests: concurrent voice requests and dashboard reads.
- Device tests: low-end Android Chrome, desktop Chrome, Firefox, Safari where supported.
- Accessibility tests: keyboard, screen reader, contrast, touch size.

### 13.2 Speech evaluation set

Build a consented test set covering:

- Telugu, Hindi, English, and code-mixed speech.
- Male/female/older/younger speakers.
- Quiet shop and noisy shop.
- Product names, brand names, local pronunciation.
- Units, number words, decimals, fractions, and prices.
- Add, remove, query, low-stock, cancel, and correction commands.

Track:

- Word error rate for transcription.
- Intent accuracy.
- Product-match accuracy.
- Quantity/unit extraction accuracy.
- Safe-mutation rate.
- Clarification rate.
- End-to-end latency p50/p95.

The most important business metric is not raw transcription accuracy; it is whether the correct inventory mutation is safely completed.

### 13.3 Adversarial cases

- “Add rice” with no quantity.
- “Remove all rice” when stock is unknown.
- “Add 1000 bags” due to recognition error.
- “Two dozen” where the product is weight-based.
- Similar products: rice 25 kg and rice 50 kg.
- Duplicate tap or repeated audio.
- User says “yes” after the screen has expired.
- Network timeout after database commit.
- Another user changes the balance during confirmation.

## 14. Implementation Plan

### Phase 0: 30-minute setup

- Create repository and environment files.
- Create database project and migrations.
- Add authentication/demo user.
- Define language, unit, product, transaction, and role enums.
- Add provider keys only to server environment.

### Phase 1: One-day vertical slice

1. Build dashboard and product list.
2. Add product and manual transaction forms.
3. Implement ledger plus balance transaction.
4. Add microphone recording using MediaRecorder.
5. Connect one STT provider.
6. Add deterministic parser for add/remove/query examples.
7. Add confirmation card and commit endpoint.
8. Add low-stock query and alert badge.
9. Seed 8–10 products and record demo commands.
10. Deploy and verify from a mobile device.

### Phase 2: Hardening

- Alias and transliteration management.
- Regional-language UI translation.
- TTS responses.
- Better clarification dialogue.
- Provider fallback.
- Offline shell and pending queue.
- Role management, audit screens, export, monitoring.

### Phase 3: Production evolution

- Barcode scanning.
- Supplier and purchase order workflows.
- Sales/POS integration.
- Multi-shop and multi-warehouse support.
- Forecasting based on historical demand.
- WhatsApp integration only with explicit consent and a compliant business setup.
- On-device or edge speech options where language quality and device capability permit.

## 15. Demo Script and Deliverables

### 15.1 Recommended demo

1. Open the dashboard in Telugu/Hindi/English mode.
2. Say: “Add five bags of rice.”
3. Show transcript and parsed confirmation.
4. Confirm and show balance increase.
5. Say: “Remove two bags of rice.”
6. Ask: “How much rice is available?”
7. Ask: “Which items are low?”
8. Say a mixed-language command with a brand name.
9. Demonstrate ambiguous product clarification.
10. Demonstrate network retry or manual fallback.

### 15.2 Submission package

- Requirements document.
- Functional requirements document.
- Technical architecture document and diagram.
- UI/UX prototype or deployed URL.
- Source repository with README and `.env.example`.
- Database schema/migrations.
- Working web application or APK.
- Demo video.
- Presentation deck.
- Business pitch deck.
- Test report with speech examples and latency measurements.

## 16. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Regional speech recognition errors | Wrong stock entry | Confirmation, aliases, native test set, manual edit |
| Ambiguous trade units | Incorrect quantity | Product-specific conversions and clarification |
| Provider outage | Voice unavailable | Manual input, provider adapter, retry and fallback |
| Duplicate requests | Inflated/deflated stock | Idempotency key and unique constraint |
| Negative inventory | Incorrect business decisions | Block by default; controlled override |
| Low digital literacy | Abandonment | Few screens, examples, voice output, local language |
| Poor connectivity | Delayed action | Compression, progress states, pending sync for safe operations |
| Data leakage | Business/privacy harm | RLS, encrypted transport, minimal audio retention |
| LLM hallucination | Unsafe mutation | Structured extraction plus deterministic server validation |
| One-day scope pressure | Incomplete product | Narrow vertical slice and explicit non-goals |

## 17. Definition of Done

The project is done for MVP when:

- A real or seeded shop can create products and configure thresholds.
- A user can add and remove stock using at least one regional language and English mixing.
- Every mutation displays parsed fields and requires confirmation.
- Current balances are derived from safe transactional writes.
- Duplicate retries do not duplicate stock.
- Low-stock items are visible and answerable by voice/text.
- Manual input works when microphone, browser, provider, or network fails.
- Tenant and role checks are tested.
- A mobile demo works end-to-end.
- Logs report request ID, provider, language, confidence, and latency without exposing secrets.
- Source code, migrations, setup instructions, demo data, and test cases are included.

## 18. Immediate Build Checklist

- [ ] Select one primary language and one STT provider.
- [ ] Create PostgreSQL/Supabase project.
- [ ] Implement `products`, `product_aliases`, `inventory_transactions`, and `stock_balances`.
- [ ] Add atomic commit function with idempotency.
- [ ] Build dashboard and confirmation UI.
- [ ] Implement MediaRecorder capture; the browser API supports recording a media stream for upload. [web:3]
- [ ] Add STT adapter and test audio format.
- [ ] Implement parser for five exact demo command patterns.
- [ ] Add product matching and clarification.
- [ ] Add low-stock SQL query.
- [ ] Add error, retry, and manual fallback states.
- [ ] Measure latency from microphone click to committed result.
- [ ] Test with at least 20 utterances per supported language.
- [ ] Deploy, test on Android, and record the demo.

## Final Engineering Principle

Build the first version as a reliable inventory ledger with a voice interface—not as a chatbot that happens to change stock. Speech and AI should help the owner express an action; the database, validation rules, permissions, and confirmation flow must decide whether that action is safe to commit.

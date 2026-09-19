# VoiceStock — Voice-Based Inventory Management for Small Businesses

A simple, voice-first inventory management web application tailored for local Indian retail and wholesale merchants (Kirana shops, general stores, Mandi traders). It allows shop owners to add, remove, track, and query their stock naturally by speaking in **Hindi (हिन्दी)**, **Telugu (తెలుగు)**, or **English**, including mixed colloquial speech (Hinglish / Telugish) and common Indian trade units (*bori, bag, carton, packet, quintal, kg, litre, dozen*).

Built with **React 19 + TypeScript + Vite + Tailwind CSS v4** (Frontend), **FastAPI + Motor** (Backend), and **MongoDB** (Stock Balance & Transaction Ledger).

---

## 🌟 Key Features

- **Voice-First Interaction:** Speak naturally without typing complex SKU numbers or navigation trees.
- **Multilingual Support:**
  - **Hindi (हिन्दी):** `"चावल 5 बोरी आया"`, `"आलू 10 किलो बेच दिया"`, `"चीनी कितना बचा है?"`
  - **Telugu (తెలుగు):** `"బియ్యం 5 బస్తాలు వచ్చాయి"`, `"నూనె 2 లీటర్లు అమ్మేసాను"`
  - **English / Mixed:** `"Add 5 bags of rice"`, `"Remove 2 cartons surf"`, `"What is running low?"`
- **Indian Trade Units & Conversions:**
  - Automatically converts wholesale units (*bori/bag, carton, box, dozen*) into base inventory metrics (*kg, grams, litres, pieces*).
  - Handles number words (*"पांच बोरी"*, *"five bags"*, *"పది"*).
- **Two-Step Voice Confirmation & Safety:**
  - Every voice command parses intent and returns a **visual preview card** for the shopkeeper to verify before committing.
  - One-tap editable quantities and units on the confirmation card before committing.
- **Atomic Stock Mutations & Idempotency:**
  - ACID inventory ledger updates in MongoDB preventing double-charging or duplicate entries on network retries.
  - Out-of-stock validation prevents negative inventory balances.
- **Smart Low-Stock Alerts & Queries:**
  - Instant voice queries (*"How much sugar is in stock?"* or *"What is running low?"*).
  - Automated threshold alerts flagged in red/amber on the dashboard.

---

## 🎙️ Dual Voice Architecture: Azure AI Speech & Web Speech API

VoiceStock supports two operating modes:

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 Browser Client (React)                 │
                  └────────────┬──────────────────────────────┬────────────┘
                               │                              │
                    Mode 1: Free Browser STT        Mode 2: Production Azure AI Speech
                               │                              │
                               ▼                              ▼
                 Web Speech API (Chrome/Edge)     MediaRecorder (Audio Blob)
                               │                              │
                               ▼                              ▼
                 POST /api/v1/voice/commands     POST /api/v1/voice/transcribe
                               │                              │
                               └──────────────┬───────────────┘
                                              │
                                              ▼
                                 FastAPI Multilingual NLP
                               (Regex + Phonetic Matcher)
                                              │
                                              ▼
                                 Atomic MongoDB Transaction
                                              │
                                              ▼
                             Spoken Answer via SpeechSynthesis
                             (or Azure Neural TTS /voice/speak)
```

### 1. Free Mode (Default — Zero Keys Required)
The app runs completely free out of the box using the browser's built-in **Web Speech API** for Speech-to-Text and **SpeechSynthesis** for Text-to-Speech. No external cloud account or API keys are required.

### 2. Azure AI Speech Mode (Enterprise Cloud STT & Neural TTS)
For high-accuracy noisy shop environments, VoiceStock natively integrates with **Azure Cognitive Services Speech**:

- **Speech-to-Text (STT):** Cloud audio recognition via Azure Speech REST API (`POST /api/v1/voice/transcribe`), decoding WebM / OGG / WAV audio across Indian language locales (`hi-IN`, `te-IN`, `en-IN`).
- **Neural Text-to-Speech (TTS):** Natural neural audio output via `POST /api/v1/voice/speak` using Microsoft Azure's Neural voice models:
  - **Hindi:** `hi-IN-SwaraNeural`
  - **Telugu:** `te-IN-ShrutiNeural`
  - **English (India):** `en-IN-NeerjaNeural`

#### Configuring Azure AI Speech:
1. In `backend/.env`, set:
   ```env
   SPEECH_PROVIDER=azure
   AZURE_SPEECH_KEY=your_azure_speech_key_here
   AZURE_SPEECH_REGION=uaenorth
   ```
2. In `frontend/.env`, set:
   ```env
   VITE_SPEECH_PROVIDER=azure
   ```
3. Restart both servers. Voice recordings will now be processed via Azure Neural STT & TTS.

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 19, TypeScript, Vite 8 | Ultra-fast UI with strict typing |
| **Styling** | Tailwind CSS v4, Lucide Icons | Responsive Kirana-tailored mobile-first UI |
| **State & Cache** | Zustand, TanStack React Query v5 | Client state & optimistic cache |
| **Localization** | i18next, LanguageDetector | Hindi, Telugu, and English UI locales |
| **Backend** | FastAPI (Python 3.12), Uvicorn | Async REST API with automatic Swagger docs |
| **NLP Engine** | Custom Multilingual Regex & Phonetic Parser | Fast, deterministic parsing (<15ms latency) |
| **Database** | MongoDB 8, Motor (Async driver) | Document store for products, balances & transactions |
| **Speech** | Web Speech API & Azure AI Speech | Dual-mode STT & Neural TTS |

---

## 📂 Project Structure

```
voice-inventory/
├── README.md                                    # Project documentation
├── docker-compose.yml                           # MongoDB container definition
├── start_servers.bat                            # One-click Windows starter
├── start_servers.ps1                            # PowerShell server starter
├── voice_inventory_requirements_blueprint.md    # Product requirements & specification
├── fastapi_react_mongodb_detailed_architecture.md # Comprehensive system architecture
│
├── backend/                                     # FastAPI Python Backend
│   ├── app/
│   │   ├── main.py                              # App entrypoint & CORS middleware
│   │   ├── config.py                            # Pydantic Settings & environment vars
│   │   ├── dependencies.py                      # Database & JWT auth dependencies
│   │   ├── api/                                 # REST Endpoints
│   │   │   ├── auth.py                          # Demo shop login & JWT issuing
│   │   │   ├── products.py                      # Product catalog CRUD
│   │   │   ├── inventory.py                     # Transactions, stock balances & ledger
│   │   │   ├── voice.py                         # Voice command pipeline & preview
│   │   │   ├── dashboard.py                     # Store summary & alert metrics
│   │   │   └── alerts.py                        # Low-stock notification triggers
│   │   ├── core/                                # Core logic & constants
│   │   │   ├── constants.py                     # Units, operations & number dictionaries
│   │   │   ├── i18n.py                          # Multilingual response templates
│   │   │   └── security.py                      # JWT encode/decode utilities
│   │   ├── db/                                  # Database layer
│   │   │   ├── mongodb.py                       # Motor async client & index manager
│   │   │   └── seed.py                          # 10 Kirana products with multilingual aliases
│   │   ├── repositories/                        # MongoDB Repository pattern layer
│   │   └── services/                            # Business logic services
│   │       ├── nlp_service.py                   # Multilingual deterministic NLP engine
│   │       ├── product_matcher.py               # Fuzzy & Unicode-safe product matcher
│   │       ├── inventory_service.py             # Atomic transaction commit logic
│   │       ├── unit_service.py                  # Unit conversions & normalization
│   │       ├── speech_service.py                # Azure & WebSpeech STT provider
│   │       └── tts_service.py                   # Azure Neural TTS synthesis
│   ├── tests/                                   # Pytest automated test suite (13 tests)
│   └── requirements.txt                         # Python dependencies
│
└── frontend/                                    # React 19 Frontend
    ├── src/
    │   ├── components/ui/                       # Button, Modal, Card, Input, Badge
    │   ├── features/
    │   │   ├── auth/LoginPage.tsx               # Demo login view
    │   │   ├── dashboard/DashboardPage.tsx       # Live dashboard summary & alerts
    │   │   ├── inventory/                       # Product catalog & transaction history
    │   │   └── voice/
    │   │       ├── VoiceButton.tsx              # Floating mic button & audio recording
    │   │       └── VoiceModal.tsx               # Voice verification & answer card
    │   ├── i18n/locales/                        # en.json, hi.json, te.json
    │   ├── stores/                              # Zustand authStore & voiceStore
    │   └── lib/api.ts                           # Axios API client with JWT interceptor
    └── package.json                             # NPM dependencies & scripts
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.12+**
- **Node.js 18+** & npm
- **MongoDB** (Local Windows service, Docker container, or MongoDB Atlas free tier)

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/MunnaKumar32990/Voice-Based-Inventory-Management-for-Small-Businesses.git
cd Voice-Based-Inventory-Management-for-Small-Businesses
```

---

### Step 2: Set Up & Run Backend
1. Open a terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment (`backend/.env`):
   ```env
   MONGODB_URI=mongodb://localhost:27017
   DB_NAME=voice_inventory
   JWT_SECRET=voicestock-dev-secret-key-change-in-production-2024
   ```
4. Start the FastAPI server:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *Interactive API documentation is live at: **[http://localhost:8000/docs](http://localhost:8000/docs)***

---

### Step 3: Set Up & Run Frontend
1. Open a second terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```
   *Web application will open at: **[http://localhost:5173](http://localhost:5173)***

---

### Step 4 (Windows): One-Click Start
On Windows, you can double-click [`start_servers.bat`](file:///c:/Users/ak612/OneDrive/Desktop/voice%20agent/start_servers.bat) in the project root to automatically launch both the backend and frontend in separate console windows.

---

## 🧪 Testing the Voice Commands

Log in using the **Start Demo** button as *Kumar General Store* (pre-seeded with 10 products: Rice, Sugar, Atta, Oil, Soap, Dal, Salt, Chai, Milk, Onion).

Tap the floating microphone button and try any of these commands:

| Language | Spoken Command | Detected Action | Result |
|---|---|---|---|
| **English** | *"Add 5 bags of rice"* | `STOCK_IN` | Converts 5 bags = 125 kg; asks confirmation; commits |
| **English** | *"Remove 2 cartons of soap"* | `STOCK_OUT` | Deducts 2 cartons; checks stock availability |
| **Hindi** | *"चावल 5 बोरी आया"* | `STOCK_IN` | Identifies Rice (`chawal`), 5 bags (`bori`); updates ledger |
| **Hinglish** | *"Sugar 10 kilo bech diya"* | `STOCK_OUT` | Identifies Sugar, 10 kg, deducts stock |
| **Telugu** | *"బియ్యం 5 బస్తాలు వచ్చాయి"* | `STOCK_IN` | Identifies Rice (`biyyam`), 5 bags |
| **Voice Query** | *"How much rice is available?"* | `STOCK_QUERY` | Answers immediately with current stock balance |
| **Voice Query** | *"What is running low?"* | `LOW_STOCK_QUERY`| Lists all products below reorder threshold |

---

## 🧩 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/demo-login` | Authenticates demo store and seeds initial catalog |
| `GET` | `/api/v1/dashboard/summary` | Retrieves stock totals, daily transactions & alerts |
| `GET` | `/api/v1/products/` | Lists all catalog items with real-time stock balance |
| `POST` | `/api/v1/products/` | Adds a new product with trade units & aliases |
| `POST` | `/api/v1/voice/commands` | Parses voice transcript, matches product, returns preview |
| `POST` | `/api/v1/voice/commands/{id}/commit` | Atomically executes and commits verified transaction |
| `POST` | `/api/v1/voice/commands/{id}/cancel` | Cancels a pending command preview |
| `POST` | `/api/v1/voice/transcribe` | Uploads audio blob for Azure STT processing |
| `POST` | `/api/v1/voice/speak` | Synthesizes neural audio response via Azure TTS |
| `GET` | `/api/v1/alerts/` | Lists open low-stock inventory alerts |
| `POST` | `/api/v1/inventory/transactions` | Fallback manual inventory adjustments |

---

## 🔒 Security & Reliability

- **JWT Authentication:** Every API request validates shop tenancy, preventing cross-tenant data access.
- **Idempotency Keys:** Voice transactions pass unique interaction IDs to guarantee that accidental double-taps do not create duplicate stock entries.
- **Fail-Safe Fallback:** If browser microphone permissions are blocked, a built-in text input modal allows typing the command with the exact same NLP intelligence.

---

## 📄 License
MIT License. Created for the Indian Kirana & Small Business Ecosystem.

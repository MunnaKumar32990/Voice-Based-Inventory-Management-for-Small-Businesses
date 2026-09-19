# Demo script — 5-command voice walkthrough (acceptance A1–A10)

1. Open the app, **Start Demo** as `Kumar General Store`. Dashboard shows seeded products.
2. Say **“Add five bags of rice”** → confirm → Rice balance increases (5 bags × 25 kg). [A1]
3. Say **“Remove two cartons of soap”** → confirm → Soap decreases by 2. [A2]
4. Say **“Remove 9999 kg rice”** → blocked with *Insufficient stock*, no negative balance. [A3]
5. Say **“How much rice is available?”** → answer shows current balance + unit. [A4]
6. Say **“What is low?”** → lists products at/below threshold with names. [A5]
7. Say **“Add 2 packets unicorn mix”** → *product not found* + suggestions. [A6]
8. Say **“Add rice”** → asked *“How many?”* (no silent write). [A7]
9. Tap Confirm twice / retry commit → single ledger entry (`already_processed`). [A8]
10. Stop the backend and retry → friendly error + **Manual Entry** fallback at `/manual`. [A9]
11. Switch language (EN/HI/TE) in navbar or Settings → UI + voice answers change, stock numbers unchanged. [A10]

Mixed-language example: “Rice five bags add karo” → STOCK_IN 5 bag rice.
Hindi example: “चावल 5 बोरी आया” → STOCK_IN 5 bag.

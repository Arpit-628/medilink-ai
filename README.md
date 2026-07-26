# MediLink AI — Hackathon MVP Guide

## What's already built for you
- `backend/database.py` — SQLite models + seed data (3 pharmacies, 7 medicines, inventory)
- `backend/main.py` — FastAPI backend with 4 working endpoints
- `frontend/index.html` — single-file demo UI, no build step

This runs **right now**, out of the box. Your job for the rest of the hackathon is to run it, understand it, extend it a little, and package it for submission.

---

## Step 1 — Run it (10 minutes)

```bash
cd backend
pip install -r requirements.txt
python database.py        # creates + seeds medilink.db (run once)
uvicorn main:app --reload  # starts server at http://127.0.0.1:8000
```

Open `frontend/index.html` directly in your browser (double-click it). It talks to the backend automatically.

Also open `http://127.0.0.1:8000/docs` — FastAPI gives you a free interactive API tester. Use this in your demo video, it looks impressive with zero extra work.

---

## Step 2 — Understand the 4 features (what to say in your pitch)

| Feature | Endpoint | The "AI" part |
|---|---|---|
| Smart Search | `/search` | Maps symptoms → medicines (rule-based NLP layer; swap for an LLM call if time allows) |
| Pharmacy Recommendation | `/recommend` | Weighted multi-factor scoring (distance 40%, price 30%, stock 20%, rating 10%) — **explainable AI**, judges can see exactly why a store was picked |
| Alternative Engine | `/alternatives` | Matches by active ingredient (salt), never guesses randomly |
| Emergency Mode | `/emergency` | Filters open + in-stock + within radius, sorted by real GPS distance (haversine formula) |

Emphasize **"explainable AI"** in your pitch — this is a strong answer to "why is this AI and not just a database filter."

## Step 3 — Extend it a little (only if time allows, ~2-4 hrs)

Pick **one**, not all:
- **LLM chatbot**: add a `/chatbot` POST endpoint that sends the user's question to an LLM API with a system prompt like *"You give general medicine information only, always end by recommending the user consult a doctor."* Keep it to ~15 lines.
- **Prescription OCR**: `pip install easyocr`, run it on an uploaded image, regex out capitalized words, feed them into `/search`. This is the single most impressive demo feature if you have time — do this over the chatbot if you must choose.

Don't attempt both. A working 4-feature MVP beats a half-broken 6-feature one.

## Step 4 — Polish for judging criteria

- **Technical Implementation (30%)**: make sure `uvicorn main:app --reload` runs cleanly from a fresh clone — judges may actually try it.
- **UX (15%)**: the provided HTML is plain but functional; if you have a designer on the team, restyle it — don't touch the logic.
- **Feasibility (15%)**: in your docs, explicitly note the real-world gap — pharmacies need an inventory dashboard (mention it as a fast-follow, don't build it now).
- **Pitch (15%)**: open with the problem (30–60 minutes wasted per emergency medicine search), then show the recommendation engine live — it's your best "wow" moment because the score breakdown is visible.

## Step 5 — Submission checklist

- [ ] GitHub repo with this code pushed, README included
- [ ] 2–3 min demo video: show search → recommendation → alternatives → emergency mode, in that order
- [ ] Docs: 1-page problem statement + architecture diagram + the "removed features / why" reasoning (shows maturity, judges like this)
- [ ] Mention data limitation honestly: inventory is simulated for the demo; production would need pharmacy-side data entry

---

## Architecture

```
Browser (index.html)
      │  fetch()
      ▼
FastAPI (main.py)
      │
      ▼
SQLAlchemy ── SQLite (medilink.db)
```

No cloud, no API keys, no build tools required — this is intentional so you can demo it offline if wifi fails at the venue.

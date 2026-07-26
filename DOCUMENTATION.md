# MediLink AI
### AI-Powered Medicine Discovery, Prescription Intelligence & Smart Pharmacy Recommendation

**Team submission — AI First Hackathon 2026 (Techible × I3C, IIT Jammu), Round 2 MVP**

---

## 1. Problem Statement

When a patient needs medicine urgently, the biggest obstacle isn't buying it — it's **finding it fast**. A typical journey looks like this:

```
Doctor prescribes medicine → Patient visits Pharmacy A → Out of stock
→ Visits Pharmacy B → Available, but overpriced → 30-60 minutes wasted
```

This delay is especially dangerous during emergencies (e.g., insulin, antibiotics) and is a genuine, everyday pain point rather than a hypothetical one.

## 2. Our Solution

MediLink AI acts as an **AI decision assistant** for medicine availability — not another e-commerce pharmacy. Given a medicine name or a plain-language symptom description, it finds nearby pharmacies with real-time-style stock, and uses an **explainable weighted scoring model** to recommend the best option, rather than just listing raw results.

## 3. Core Features (MVP)

| # | Feature | What it does | AI/Logic Element |
|---|---------|--------------|-------------------|
| 1 | Smart Medicine Search | Accepts medicine name *or* symptom description (e.g. "fever and headache") | Symptom-to-medicine mapping layer (NLP-lite; upgradeable to LLM) |
| 2 | Smart Pharmacy Recommendation | Ranks pharmacies stocking the medicine | Weighted multi-factor scoring: 40% distance, 30% price, 20% stock, 10% rating — fully explainable, not a black box |
| 3 | Medicine Alternative Engine | Suggests substitutes when a medicine is unavailable | Matches strictly by active ingredient (salt) + dosage, never a random suggestion |
| 4 | Emergency Mode | One-click filter for urgent needs | Filters pharmacies that are open now, in stock, and within a set radius, sorted by real GPS distance (haversine formula) |

**Deliberately excluded from this MVP:** voice search (no AI novelty beyond existing Speech APIs), delivery logistics, price prediction (needs historical data we don't have), and medicine reminders (no AI component). We chose depth over feature count within the time-boxed sprint.

## 4. System Architecture

```
        User (Browser)
              │
       HTML/JS Frontend
              │  REST calls (fetch)
              ▼
        FastAPI Backend
              │
      ┌───────┼────────┐
      ▼       ▼        ▼
  Search   Recommend  Alternatives /
  Engine    Engine     Emergency Filter
      │       │        │
      └───────┴────────┘
              │
        SQLAlchemy ORM
              │
          SQLite DB
   (Medicines, Pharmacies, Inventory)
```

## 5. Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy
- **Database:** SQLite (demo) — designed to migrate directly to PostgreSQL for production, schema unchanged
- **Frontend:** HTML/CSS/JavaScript (no framework/build step, for fast iteration during the hackathon)
- **AI Layer:** rule-based weighted recommendation scoring (explainable AI) + symptom-mapping search; architecture supports swapping in an LLM/embedding-based matcher without changing the API contract

## 6. Feasibility & Scalability

The core technical challenge for a production version is **real-time pharmacy inventory data**, not the AI logic itself. Our roadmap:

- **Now (MVP):** simulated inventory via a seeded database, to prove the recommendation and search logic works correctly.
- **Next:** a pharmacy-facing dashboard where store owners log in and update stock/price directly — this is the real unlock for production accuracy.
- **Later:** integrate with pharmacy POS/vendor systems for automatic stock sync, add prescription OCR to remove manual entry, and add an expiry-risk alert for pharmacies to reduce wastage.

The scoring engine, database schema, and API are already structure-ready for this — no rearchitecture is needed to add these, only new endpoints and a data source.

## 7. Impact

MediLink AI benefits **two sides** of the same problem:
- **Patients** save time and money during a stressful, time-sensitive moment.
- **Pharmacies** gain visibility to nearby demand and (in the extended roadmap) tools to reduce stock wastage.

---
*Team: [add your names] | Repo: [add your GitHub link] | Demo video: [add link]*

"""
MediLink AI — backend
Run with: uvicorn main:app --reload
Docs auto-generated at http://127.0.0.1:8000/docs (great for your demo video)
"""
def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        import easyocr   # <-- this one
        _ocr_reader = easyocr.Reader(["en"], gpu=False)
    return _ocr_reader

import math
from fastapi import FastAPI, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from database import SessionLocal, Medicine, Pharmacy, Inventory, init_db, seed

app = FastAPI(title="MediLink AI")

# OCR reader is created lazily (only on first prescription scan) because
# loading EasyOCR's model takes a few seconds — we don't want that to slow
# down normal server startup for every other feature.
_ocr_reader = None


def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        import easyocr
        _ocr_reader = easyocr.Reader(["en"], gpu=False)
    return _ocr_reader


# Allow the frontend (opened as a local file / different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
seed()


# ---------- helper ----------
def haversine_km(lat1, lon1, lat2, lon2):
    """Straight-line distance between two GPS points, in km."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# A tiny symptom -> medicine map. This is the "AI Smart Search" logic.
# For the hackathon this rule-based map is enough; swap in an LLM call later if you have time.
SYMPTOM_KEYWORDS = ["fever", "headache", "body pain", "cold", "allergy",
                     "sneezing", "acidity", "stomach pain", "infection", "throat pain"]


# ---------- internal logic (reused by both individual endpoints and /assistant) ----------
def _search_medicine(db, query: str):
    query_lower = query.lower()
    name_matches = db.query(Medicine).filter(Medicine.name.ilike(f"%{query}%")).all()
    if name_matches:
        return {"mode": "name_match", "results": [m.name for m in name_matches]}

    found_symptoms = [s for s in SYMPTOM_KEYWORDS if s in query_lower]
    if not found_symptoms:
        return {"mode": "no_match", "results": [], "note": "Try a medicine name or describe a symptom."}

    matches = []
    for m in db.query(Medicine).all():
        med_symptoms = m.symptoms.split(",")
        if any(s in med_symptoms for s in found_symptoms):
            matches.append(m.name)

    return {
        "mode": "symptom_match",
        "matched_symptoms": found_symptoms,
        "results": matches,
        "disclaimer": "Educational suggestions only. Please consult a doctor before taking any medicine.",
    }


def _recommend_pharmacies(db, medicine_name: str, user_lat: float, user_lng: float):
    medicine = db.query(Medicine).filter(Medicine.name.ilike(medicine_name)).first()
    if not medicine:
        return {"error": "Medicine not found"}

    rows = db.query(Inventory).filter(Inventory.medicine_id == medicine.id, Inventory.stock > 0).all()
    if not rows:
        return {"medicine": medicine.name, "results": [], "note": "Out of stock everywhere nearby."}

    scored = []
    max_price = max(r.price for r in rows)
    max_dist = max(haversine_km(user_lat, user_lng, r.pharmacy.latitude, r.pharmacy.longitude) for r in rows) or 1

    for r in rows:
        dist = haversine_km(user_lat, user_lng, r.pharmacy.latitude, r.pharmacy.longitude)
        dist_score = 1 - (dist / max_dist)
        price_score = 1 - (r.price / max_price)
        stock_score = min(r.stock / 20, 1)
        rating_score = r.pharmacy.rating / 5
        final_score = (0.4 * dist_score) + (0.3 * price_score) + (0.2 * stock_score) + (0.1 * rating_score)

        scored.append({
            "pharmacy": r.pharmacy.name,
            "distance_km": round(dist, 2),
            "price": r.price,
            "stock": r.stock,
            "rating": r.pharmacy.rating,
            "score": round(final_score, 3),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    best = scored[0]

    return {
        "medicine": medicine.name,
        "results": scored,
        "best_choice": {
            "pharmacy": best["pharmacy"],
            "reason": f"Best balance of distance ({best['distance_km']} km), price (\u20b9{best['price']}), "
                      f"and stock ({best['stock']} units).",
        },
    }


def _find_alternatives(db, medicine_name: str):
    medicine = db.query(Medicine).filter(Medicine.name.ilike(medicine_name)).first()
    if not medicine:
        return {"error": "Medicine not found"}

    alternatives = (
        db.query(Medicine)
        .filter(Medicine.salt == medicine.salt, Medicine.id != medicine.id)
        .all()
    )
    return {
        "medicine": medicine.name,
        "salt": medicine.salt,
        "alternatives": [{"name": a.name, "dosage": a.dosage} for a in alternatives],
        "note": "Only medicines with the same active ingredient and dosage are suggested.",
    }


def _emergency_search(db, medicine_name: str, user_lat: float, user_lng: float, radius_km: float = 3):
    medicine = db.query(Medicine).filter(Medicine.name.ilike(medicine_name)).first()
    if not medicine:
        return {"error": "Medicine not found"}

    rows = (
        db.query(Inventory)
        .filter(Inventory.medicine_id == medicine.id, Inventory.stock > 0)
        .join(Pharmacy)
        .filter(Pharmacy.open_now == True)
        .all()
    )

    results = []
    for r in rows:
        dist = haversine_km(user_lat, user_lng, r.pharmacy.latitude, r.pharmacy.longitude)
        if dist <= radius_km:
            results.append({
                "pharmacy": r.pharmacy.name,
                "distance_km": round(dist, 2),
                "stock": r.stock,
                "price": r.price,
            })
    results.sort(key=lambda x: x["distance_km"])
    return {"medicine": medicine.name, "open_now_within_radius": results}


# ---------- 1. Smart Medicine Search ----------
@app.get("/search")
def search_medicine(query: str = Query(..., description="Medicine name OR a symptom sentence")):
    db = SessionLocal()
    result = _search_medicine(db, query)
    db.close()
    return result


# ---------- 2. Smart Pharmacy Recommendation (explainable AI scoring) ----------
@app.get("/recommend")
def recommend_pharmacies(medicine_name: str, user_lat: float = 20.2961, user_lng: float = 85.8245):
    db = SessionLocal()
    result = _recommend_pharmacies(db, medicine_name, user_lat, user_lng)
    db.close()
    return result


# ---------- 3. Medicine Alternative Engine ----------
@app.get("/alternatives")
def find_alternatives(medicine_name: str):
    db = SessionLocal()
    result = _find_alternatives(db, medicine_name)
    db.close()
    return result


# ---------- 4. Emergency Mode ----------
@app.get("/emergency")
def emergency_search(medicine_name: str, user_lat: float = 20.2961, user_lng: float = 85.8245, radius_km: float = 3):
    db = SessionLocal()
    result = _emergency_search(db, medicine_name, user_lat, user_lng, radius_km)
    db.close()
    return result


# ---------- 5. Prescription Scanner (OCR) — stretch feature ----------
@app.post("/prescription/scan")
async def scan_prescription(file: UploadFile = File(...)):
    """
    Upload a prescription image. We OCR it, then match any recognized words
    against known medicine names in our database (fuzzy substring match).
    """
    contents = await file.read()
    temp_path = f"_temp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(contents)

    reader = get_ocr_reader()
    raw_results = reader.readtext(temp_path, detail=0)
    raw_text = " ".join(raw_results)

    import os
    os.remove(temp_path)

    db = SessionLocal()
    all_medicines = db.query(Medicine).all()
    matched = []
    for m in all_medicines:
        name_parts = m.name.lower().split()
        if any(part in raw_text.lower() for part in name_parts if len(part) > 3):
            matched.append(m.name)
    db.close()

    return {
        "ocr_raw_text": raw_text,
        "matched_medicines": sorted(set(matched)),
        "note": "Verify matches manually — OCR on handwritten prescriptions is imperfect. "
                "Use /search with a matched name to find nearby pharmacies.",
    }


# ---------- 6. Assistant (combined) — powers the "type once, get everything" frontend ----------
@app.get("/assistant")
def assistant(
    query: str = Query(..., description="Medicine name OR a symptom sentence"),
    user_lat: float = 20.2961,
    user_lng: float = 85.8245,
    emergency: bool = False,
):
    """
    One call that does what the frontend needs on every keystroke:
    search -> pick the top matched medicine -> recommend pharmacies (or emergency filter)
    -> find alternatives. Cuts 3 round trips down to 1, so the live-search UI feels instant.
    """
    db = SessionLocal()
    search_result = _search_medicine(db, query)

    matched = search_result.get("results", [])
    if not matched:
        db.close()
        return {"query": query, "search": search_result, "primary_medicine": None}

    primary = matched[0]

    if emergency:
        location_result = _emergency_search(db, primary, user_lat, user_lng)
    else:
        location_result = _recommend_pharmacies(db, primary, user_lat, user_lng)

    alt_result = _find_alternatives(db, primary)
    db.close()

    return {
        "query": query,
        "search": search_result,
        "primary_medicine": primary,
        "emergency_mode": emergency,
        "pharmacies": location_result,
        "alternatives": alt_result,
    }


@app.get("/")
def root():
    return {"message": "MediLink AI backend is running. Visit /docs for the interactive API."}

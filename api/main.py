from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import pandas as pd
from sqlalchemy import create_engine, text
from pymongo import MongoClient

load_dotenv()

app = FastAPI(title="Urban Data Explorer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_engine(os.getenv("POSTGRES_URL"))
mongo  = MongoClient(os.getenv("MONGO_URL"))["urban_explorer"]

# ── Test ──────────────────────────────────────────────────────────
@app.get("/", tags=["Status"])
def root():
    return {"status": "ok", "message": "Urban Data Explorer API"}

# ── Indicateur 1 : Accessibilité ─────────────────────────────────
@app.get("/ind1", tags=["Accessibilité à l'achat"])
def get_ind1():
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM ind1_accessibilite", conn)
    return df.to_dict(orient="records")

@app.get("/ind1/{arrondissement}", tags=["Accessibilité à l'achat"])
def get_ind1_arr(arrondissement: int):
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM ind1_accessibilite WHERE arrondissement = :arr"), conn, params={"arr": arrondissement})
    return df.to_dict(orient="records")[0] if not df.empty else {"error": "non trouvé"}

# ── Indicateur 2 : Pression immobilière ──────────────────────────
@app.get("/ind2", tags=["Vivabilité urbaine"])
def get_ind2():
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM ind2_vivabilite", conn)
    return df.to_dict(orient="records")

@app.get("/ind2/{arrondissement}", tags=["Vivabilité urbaine"])
def get_ind2_arr(arrondissement: int):
    with engine.connect() as conn:
        df = pd.read_sql(
            text("SELECT * FROM ind2_vivabilite WHERE arrondissement = :arr"),
            conn, params={"arr": arrondissement}
        )
    return df.to_dict(orient="records")[0] if not df.empty else {"error": "non trouvé"}

# ── Indicateur 3 : Attractivité ───────────────────────────────────
@app.get("/ind3", tags=["Score attractivité"])
def get_ind3():
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM ind3_attractivite", conn)
    return df.to_dict(orient="records")

@app.get("/ind3/{arrondissement}", tags=["Score attractivité"])
def get_ind3_arr(arrondissement: int):
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM ind3_attractivite WHERE arrondissement = :arr"), conn, params={"arr": arrondissement})
    return df.to_dict(orient="records")[0] if not df.empty else {"error": "non trouvé"}

# ── Indicateur 4 : Mixité sociale ────────────────────────────────
@app.get("/ind4", tags=["Mixité sociale"])
def get_ind4():
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM ind4_mixite", conn)
    return df.to_dict(orient="records")

@app.get("/ind4/{arrondissement}", tags=["Mixité sociale"])
def get_ind4_arr(arrondissement: int):
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM ind4_mixite WHERE arrondissement = :arr"), conn, params={"arr": arrondissement})
    return df.to_dict(orient="records")[0] if not df.empty else {"error": "non trouvé"}

# ── Transactions ──────────────────────────────────────────────────
@app.get("/transactions/{arrondissement}", tags=["Transactions DVF"])
def get_transactions(arrondissement: int):
    with engine.connect() as conn:
        df = pd.read_sql(
            text("SELECT * FROM transactions WHERE arrondissement = :arr LIMIT 100"),
            conn, params={"arr": arrondissement}
        )
    return df.to_dict(orient="records")

# ── MongoDB ───────────────────────────────────────────────────────
@app.get("/logements-sociaux", tags=["MongoDB"])
def get_logements():
    return list(mongo["logements_sociaux"].find({}, {"_id": 0}))

@app.get("/espaces-verts", tags=["MongoDB"])
def get_espaces():
    return list(mongo["espaces_verts"].find({}, {"_id": 0}))

@app.get("/stations", tags=["MongoDB"])
def get_stations():
    return list(mongo["stations_ratp"].find({}, {"_id": 0}))

@app.get("/contours", tags=["MongoDB"])
def get_contours():
    data = list(mongo["contours"].find({}, {"_id": 0}))
    return {"type": "FeatureCollection", "features": data}

@app.get("/timeline/{arrondissement}", tags=["Timeline"])
def get_timeline(arrondissement: int):
    with engine.connect() as conn:
        df = pd.read_sql(
            text("""
                SELECT annee,
                       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2) as prix_m2_median,
                       COUNT(*) as nb_transactions
                FROM transactions
                WHERE arrondissement = :arr
                GROUP BY annee
                ORDER BY annee
            """),
            conn, params={"arr": arrondissement}
        )
    return df.to_dict(orient="records")

@app.get("/timeline", tags=["Timeline"])
def get_timeline_paris():
    with engine.connect() as conn:
        df = pd.read_sql(
            text("""
                SELECT annee, arrondissement,
                       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY prix_m2) as prix_m2_median
                FROM transactions
                GROUP BY annee, arrondissement
                ORDER BY arrondissement, annee
            """),
            conn
        )
    return df.to_dict(orient="records")
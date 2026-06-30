from fastapi import FastAPI, Depends, HTTPException, Security, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
import pandas as pd
from sqlalchemy import create_engine, text
from pymongo import MongoClient

# --- Sécurité : limitation de débit (quotas) ---
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

load_dotenv()

# =====================================================================
#  SÉCURITÉ
# =====================================================================

# --- 1. Authentification par clé API (en-tête HTTP "X-API-Key") ---
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    """Toute requête doit présenter une clé API valide (front public OU admin)."""
    if api_key in (os.getenv("API_KEY"), os.getenv("ADMIN_API_KEY")):
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Clé API invalide ou manquante",
    )

def require_admin(api_key: str = Security(api_key_header)):
    """Niveau d'autorisation supérieur : réservé à la clé admin (routes sensibles)."""
    if api_key != os.getenv("ADMIN_API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Opération réservée à l'administrateur",
        )
    return api_key

# --- 2. Quotas / rate limiting : 60 requêtes/min et 1000/jour par adresse IP ---
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute", "1000/day"])

# =====================================================================
#  APPLICATION
# =====================================================================

# La dépendance globale get_api_key protège TOUTES les routes d'un coup.
app = FastAPI(
    title="Urban Data Explorer API",
    dependencies=[Depends(get_api_key)],
)

# Branchement du limiteur de débit
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS restreint : seules les origines déclarées (ton front) peuvent appeler l'API
ALLOWED_ORIGINS = os.getenv("FRONTEND_URL", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# =====================================================================
#  CONNEXIONS BASES DE DONNÉES
# =====================================================================
engine = create_engine(os.getenv("POSTGRES_URL"))
mongo  = MongoClient(os.getenv("MONGO_URL"))["urban_explorer"]

# =====================================================================
#  SCHEDULER : mise à jour automatique de ind1 (hebdomadaire)
# =====================================================================
def update_ind1():
    print(f"[{datetime.now()}] Mise à jour ind1 en cours...")
    try:
        transactions = pd.read_csv("data/silver/transactions_paris.csv")
        revenus      = pd.read_csv("data/silver/revenus_paris.csv")

        prix = transactions.groupby("arrondissement")["prix_m2"].agg(
            prix_m2_median="median",
            prix_m2_moyen="mean",
            nb_transactions="count"
        ).reset_index()

        df = prix.merge(revenus, on="arrondissement")
        df["accessibilite_achat"] = (df["prix_m2_median"] * 50) / df["revenu_median"]
        moyenne_paris = df["prix_m2_median"].median()
        df["vs_moyenne_paris"] = ((df["prix_m2_median"] - moyenne_paris) / moyenne_paris * 100).round(2)
        df["updated_at"] = datetime.now().isoformat()

        df.to_sql("ind1_accessibilite", engine, if_exists="replace", index=False)
        print(f"[{datetime.now()}] ind1 mis à jour — {len(df)} arrondissements")
    except Exception as e:
        print(f"[{datetime.now()}] Erreur update ind1 : {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(update_ind1, "interval", weeks=1)
scheduler.start()

# =====================================================================
#  ROUTES
# =====================================================================

# --- Statut ---
@app.get("/", tags=["Status"])
def root():
    return {"status": "ok", "message": "Urban Data Explorer API"}

# --- Indicateur 1 : Accessibilité ---
@app.get("/ind1", tags=["Accessibilité à l'achat"])
def get_ind1():
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM ind1_accessibilite", conn)
    return df.to_dict(orient="records")

@app.get("/ind1/status", tags=["Accessibilité à l'achat"])
def get_ind1_status():
    with engine.connect() as conn:
        df = pd.read_sql("SELECT MAX(updated_at) as last_update FROM ind1_accessibilite", conn)
    return {"last_update": df["last_update"][0]}

@app.get("/ind1/{arrondissement}", tags=["Accessibilité à l'achat"])
def get_ind1_arr(arrondissement: int):
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM ind1_accessibilite WHERE arrondissement = :arr"), conn, params={"arr": arrondissement})
    return df.to_dict(orient="records")[0] if not df.empty else {"error": "non trouvé"}

# --- Indicateur 2 : Vivabilité urbaine ---
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

# --- Indicateur 3 : Attractivité ---
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

# --- Indicateur 4 : Mixité sociale ---
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

# --- Transactions DVF ---
@app.get("/transactions/{arrondissement}", tags=["Transactions DVF"])
def get_transactions(arrondissement: int):
    with engine.connect() as conn:
        df = pd.read_sql(
            text("SELECT * FROM transactions WHERE arrondissement = :arr LIMIT 100"),
            conn, params={"arr": arrondissement}
        )
    return df.to_dict(orient="records")

# --- Filtres supplémentaires (PostgreSQL) ---
@app.get("/criminalite", tags=["Filtres"])
def get_criminalite():
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM criminalite", conn)
    return df.to_dict(orient="records")

@app.get("/revenus", tags=["Filtres"])
def get_revenus():
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM revenus", conn)
    return df.to_dict(orient="records")

# --- MongoDB ---
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

# --- Timeline ---
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

# =====================================================================
#  ROUTE ADMIN PROTÉGÉE (niveau d'autorisation supérieur)
# =====================================================================
@app.post("/admin/refresh-ind1", tags=["Admin"])
def admin_refresh_ind1(api_key: str = Depends(require_admin)):
    """Relance manuellement le calcul de ind1. Nécessite la clé ADMIN."""
    update_ind1()
    return {"status": "ok", "message": "ind1 recalculé manuellement"}
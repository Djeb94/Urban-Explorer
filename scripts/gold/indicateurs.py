from dotenv import load_dotenv
import os
import pandas as pd
from sqlalchemy import create_engine

load_dotenv()
engine = create_engine(os.getenv("POSTGRES_URL"))

# ── Chargement des silver ─────────────────────────────────────────
transactions = pd.read_csv("data/silver/transactions_paris.csv")
revenus      = pd.read_csv("data/silver/revenus_paris.csv")
criminalite  = pd.read_csv("data/silver/criminalite.csv")
logements    = pd.read_csv("data/silver/logements_sociaux.csv")
espaces      = pd.read_csv("data/silver/espaces_verts.csv")
stations     = pd.read_csv("data/silver/stations_par_arrondissement.csv")

# ── Indicateur 1 : Accessibilité à l'achat ───────────────────────
# (Prix moyen m² × 50) / Revenu médian
prix_moyen = transactions.groupby("arrondissement")["prix_m2"].median().reset_index()
prix_moyen.columns = ["arrondissement", "prix_m2_median"]

ind1 = prix_moyen.merge(revenus, on="arrondissement")
ind1["accessibilite_achat"] = (ind1["prix_m2_median"] * 50) / ind1["revenu_median"]

# ── Indicateur 2 : Pression immobilière ──────────────────────────
# Nb ventes / Nb logements sociaux
nb_ventes = transactions.groupby("arrondissement").size().reset_index(name="nb_ventes")
ind2 = nb_ventes.merge(logements, on="arrondissement")
ind2["pression_immo"] = ind2["nb_ventes"] / ind2["total_logements_sociaux"]

# ── Indicateur 3 : Score attractivité ────────────────────────────
# 0.3 × transports + 0.3 × sécurité + 0.4 × espaces verts
# Normaliser chaque composante entre 0 et 1
def normaliser(serie):
    return (serie - serie.min()) / (serie.max() - serie.min())

stations["score_transport"]  = normaliser(stations["nb_stations"])
criminalite["score_securite"] = 1 - normaliser(criminalite["total_delits"])  # inverse
espaces["score_vert"]        = normaliser(espaces["surface_totale_m2"])

ind3 = stations.merge(criminalite, on="arrondissement").merge(espaces, on="arrondissement")
ind3["score_attractivite"] = (
    0.3 * ind3["score_transport"] +
    0.3 * ind3["score_securite"] +
    0.4 * ind3["score_vert"]
)

# ── Indicateur 4 : Mixité sociale ────────────────────────────────
# Part logements sociaux vs prix du marché
total_logements_paris = logements["total_logements_sociaux"].sum()
ind4 = logements.copy()
ind4["part_logements_sociaux"] = ind4["total_logements_sociaux"] / total_logements_paris
ind4 = ind4.merge(prix_moyen, on="arrondissement")
ind4["mixite_sociale"] = ind4["part_logements_sociaux"] / (normaliser(ind4["prix_m2_median"]) + 0.01)

# ── Fusion Gold ───────────────────────────────────────────────────
gold = ind1[["arrondissement", "prix_m2_median", "revenu_median", "accessibilite_achat"]]
gold = gold.merge(ind2[["arrondissement", "nb_ventes", "pression_immo"]], on="arrondissement")
gold = gold.merge(ind3[["arrondissement", "score_attractivite"]], on="arrondissement")
gold = gold.merge(ind4[["arrondissement", "part_logements_sociaux", "mixite_sociale"]], on="arrondissement")

# ── Sauvegarde CSV gold ───────────────────────────────────────────
os.makedirs("data/gold", exist_ok=True)
gold.to_csv("data/gold/indicateurs.csv", index=False)
print("✓ Gold sauvegardé")
print(gold)

# ── Sauvegarde PostgreSQL gold ────────────────────────────────────
gold.to_sql("indicateurs_gold", engine, if_exists="replace", index=False)
print("✓ Gold inséré dans PostgreSQL")
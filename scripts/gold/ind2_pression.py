from dotenv import load_dotenv
import os, pandas as pd
from sqlalchemy import create_engine

load_dotenv()
engine = create_engine(os.getenv("POSTGRES_URL"))

transactions = pd.read_csv("data/silver/transactions_paris.csv")
logements    = pd.read_csv("data/silver/logements_sociaux.csv")

# Nb ventes et prix par arrondissement et par année
ventes = transactions.groupby(["arrondissement", "annee"]).agg(
    nb_ventes=("prix_m2", "count"),
    prix_m2_median=("prix_m2", "median")
).reset_index()

# Total ventes toutes années
total_ventes = transactions.groupby("arrondissement").size().reset_index(name="nb_ventes_total")

# Fusion logements sociaux
df = total_ventes.merge(logements, on="arrondissement")

# Pression = nb ventes / nb logements sociaux
df["pression_immo"] = (df["nb_ventes_total"] / df["total_logements_sociaux"]).round(4)

# Normalisation 0-1
df["pression_normalisee"] = (
    (df["pression_immo"] - df["pression_immo"].min()) /
    (df["pression_immo"].max() - df["pression_immo"].min())
).round(4)

# Sauvegarde
os.makedirs("data/gold", exist_ok=True)
df.to_csv("data/gold/ind2_pression.csv", index=False)
df.to_sql("ind2_pression", engine, if_exists="replace", index=False)
print("✓ Indicateur 2 sauvegardé")
print(df[["arrondissement", "nb_ventes_total", "total_logements_sociaux", "pression_immo", "pression_normalisee"]])
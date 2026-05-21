from dotenv import load_dotenv
import os, pandas as pd
from sqlalchemy import create_engine

load_dotenv()
engine = create_engine(os.getenv("POSTGRES_URL"))

transactions = pd.read_csv("data/silver/transactions_paris.csv")
logements    = pd.read_csv("data/silver/logements_sociaux.csv")
revenus      = pd.read_csv("data/silver/revenus_paris.csv")

def normaliser(serie):
    return (serie - serie.min()) / (serie.max() - serie.min())

# Prix médian par arrondissement
prix = transactions.groupby("arrondissement")["prix_m2"].median().reset_index()
prix.columns = ["arrondissement", "prix_m2_median"]

# Part des logements sociaux sur le total Paris
total = logements["total_logements_sociaux"].sum()
logements["part_logements_sociaux"] = logements["total_logements_sociaux"] / total

# Fusion
df = logements.merge(prix, on="arrondissement").merge(revenus, on="arrondissement")

# Ecart de revenus par rapport à la moyenne parisienne
moyenne_revenus = df["revenu_median"].mean()
df["ecart_revenus"] = ((df["revenu_median"] - moyenne_revenus) / moyenne_revenus * 100).round(2)

# Score mixité = part logements sociaux / prix normalisé
# Plus il y a de logements sociaux dans un arr cher = meilleure mixité
df["mixite_sociale"] = (
    df["part_logements_sociaux"] / (normaliser(df["prix_m2_median"]) + 0.01)
).round(4)

# Normalisation finale
df["mixite_normalisee"] = normaliser(df["mixite_sociale"]).round(4)
df["rang_mixite"] = df["mixite_sociale"].rank(ascending=False).astype(int)

# Sauvegarde
os.makedirs("data/gold", exist_ok=True)
df.to_csv("data/gold/ind4_mixite.csv", index=False)
df.to_sql("ind4_mixite", engine, if_exists="replace", index=False)
print("✓ Indicateur 4 sauvegardé")
print(df[["arrondissement", "part_logements_sociaux", "prix_m2_median", "ecart_revenus", "mixite_normalisee", "rang_mixite"]].sort_values("rang_mixite"))
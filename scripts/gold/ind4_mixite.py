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

# Part des logements sociaux
total = logements["total_logements_sociaux"].sum()
logements["part_logements_sociaux"] = logements["total_logements_sociaux"] / total

df = logements.merge(prix, on="arrondissement").merge(revenus, on="arrondissement")

#normalisées
df["social_norm"] = normaliser(df["part_logements_sociaux"])
df["prix_norm"]   = normaliser(df["prix_m2_median"]) 

# Contexte écart du revenu
moyenne_revenus = df["revenu_median"].mean()
df["ecart_revenus"] = ((df["revenu_median"] - moyenne_revenus) / moyenne_revenus * 100).round(2)

#valorise présence de social ET prix élevé
df["mixite_sociale"] = (0.6 * df["social_norm"] + 0.4 * df["prix_norm"]).round(4)

df["mixite_normalisee"] = normaliser(df["mixite_sociale"]).round(4)
df["rang_mixite"] = df["mixite_sociale"].rank(ascending=False).astype(int)

os.makedirs("data/gold", exist_ok=True)
df.to_csv("data/gold/ind4_mixite.csv", index=False)
df.to_sql("ind4_mixite", engine, if_exists="replace", index=False)
print("✓ Indicateur 4 (mixité, score additif) sauvegardé")
print(df[["arrondissement", "part_logements_sociaux", "prix_m2_median",
          "social_norm", "prix_norm", "mixite_normalisee", "rang_mixite"]]
      .sort_values("rang_mixite"))
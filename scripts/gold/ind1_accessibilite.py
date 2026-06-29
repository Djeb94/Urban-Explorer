from dotenv import load_dotenv
import os, pandas as pd
from sqlalchemy import create_engine

load_dotenv()
engine = create_engine(os.getenv("POSTGRES_URL"))

transactions = pd.read_csv("data/silver/transactions_paris.csv")
revenus      = pd.read_csv("data/silver/revenus_paris.csv")

#prix median m2/arr
prix = transactions.groupby("arrondissement")["prix_m2"].agg(
    prix_m2_median="median",
    prix_m2_moyen="mean",
    nb_transactions="count"
).reset_index()

#fusion avec revenus
df = prix.merge(revenus, on="arrondissement")

#nb années revenus pour acheter 50m2
df["accessibilite_achat"] = (df["prix_m2_median"] * 50) / df["revenu_median"]

#moyenne parisienne
moyenne_paris = df["prix_m2_median"].median()
df["vs_moyenne_paris"] = ((df["prix_m2_median"] - moyenne_paris) / moyenne_paris * 100).round(2)

#save
os.makedirs("data/gold", exist_ok=True)
df.to_csv("data/gold/ind1_accessibilite.csv", index=False)
df.to_sql("ind1_accessibilite", engine, if_exists="replace", index=False)
print("✓ Indicateur 1 sauvegardé")
print(df[["arrondissement", "prix_m2_median", "revenu_median", "accessibilite_achat", "vs_moyenne_paris"]])
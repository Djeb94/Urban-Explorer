from dotenv import load_dotenv
import os, pandas as pd
from sqlalchemy import create_engine

load_dotenv()
engine = create_engine(os.getenv("POSTGRES_URL"))

criminalite = pd.read_csv("data/silver/criminalite.csv")
espaces     = pd.read_csv("data/silver/espaces_verts.csv")
stations    = pd.read_csv("data/silver/stations_par_arrondissement.csv")

def normaliser(serie):
    return (serie - serie.min()) / (serie.max() - serie.min())

# Composantes normalisées
stations["score_transport"]   = normaliser(stations["nb_stations"])
criminalite["score_securite"] = 1 - normaliser(criminalite["total_delits"])
espaces["score_vert"]         = normaliser(espaces["surface_totale_m2"])

# Fusion
df = stations[["arrondissement", "nb_stations", "score_transport"]].merge(
     criminalite[["arrondissement", "total_delits", "score_securite"]], on="arrondissement").merge(
     espaces[["arrondissement", "nb_espaces_verts", "surface_totale_m2", "score_vert"]], on="arrondissement")

# Score final pondéré
df["score_attractivite"] = (
    0.3 * df["score_transport"] +
    0.3 * df["score_securite"] +
    0.4 * df["score_vert"]
).round(4)

# Rang
df["rang_attractivite"] = df["score_attractivite"].rank(ascending=False).astype(int)

# Sauvegarde
os.makedirs("data/gold", exist_ok=True)
df.to_csv("data/gold/ind3_attractivite.csv", index=False)
df.to_sql("ind3_attractivite", engine, if_exists="replace", index=False)
print("✓ Indicateur 3 sauvegardé")
print(df[["arrondissement", "score_transport", "score_securite", "score_vert", "score_attractivite", "rang_attractivite"]].sort_values("rang_attractivite"))
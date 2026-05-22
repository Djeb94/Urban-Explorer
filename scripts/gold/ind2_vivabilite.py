from dotenv import load_dotenv
import os, pandas as pd
from sqlalchemy import create_engine

load_dotenv()
engine = create_engine(os.getenv("POSTGRES_URL"))

def normaliser(serie):
    return (serie - serie.min()) / (serie.max() - serie.min())

df = pd.read_csv("data/silver/vivabilite.csv")

# Score vie sociale
df["score_social"] = normaliser(df["restaurant"] + df["bar"] + df["cafe"])

# Score culture
df["score_culture"] = normaliser(df["cinema"] + df["theatre"] + df["nb_musees_officiels"])

# Score commodités
df["score_commodites"] = normaliser(df["bakery"] + df["supermarket"])

# Score espaces verts
df["score_nature"] = normaliser(df["surface_totale_m2"])

# Score final
df["score_vivabilite"] = (
    0.35 * df["score_social"] +
    0.25 * df["score_culture"] +
    0.25 * df["score_commodites"] +
    0.15 * df["score_nature"]
).round(4)

df["rang_vivabilite"] = df["score_vivabilite"].rank(ascending=False).astype(int)

os.makedirs("data/gold", exist_ok=True)
df.to_csv("data/gold/ind2_vivabilite.csv", index=False)
df.to_sql("ind2_vivabilite", engine, if_exists="replace", index=False)
print("✓ Indicateur 2 sauvegardé")
print(df[["arrondissement", "score_social", "score_culture", "score_commodites", "score_nature", "score_vivabilite", "rang_vivabilite"]].sort_values("rang_vivabilite"))
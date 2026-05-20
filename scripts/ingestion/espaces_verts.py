import requests, os
import pandas as pd

URL = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/espaces_verts/exports/csv?lang=fr&timezone=Europe%2FParis&use_labels=true&delimiter=%3B"

print("Téléchargement espaces verts...")
r = requests.get(URL)
with open("data/bronze/espaces_verts_raw.csv", "wb") as f:
    f.write(r.content)

df = pd.read_csv("data/bronze/espaces_verts_raw.csv", sep=";")

# Code postal est un float genre 75011.0 → on convertit
df["cp"] = pd.to_numeric(df["Code postal"], errors="coerce")
df = df[df["cp"].between(75001, 75020)]
df["arrondissement"] = (df["cp"] % 100).astype(int)
df["surface"] = pd.to_numeric(df["Surface calculée"], errors="coerce").fillna(0)

# Agréger par arrondissement
result = df.groupby("arrondissement").agg(
    nb_espaces_verts=("Identifiant espace vert", "count"),
    surface_totale_m2=("surface", "sum")
).reset_index()

os.makedirs("data/silver", exist_ok=True)
result.to_csv("data/silver/espaces_verts.csv", index=False)
print(f"✓ Silver sauvegardé — {len(result)} arrondissements")
print(result)
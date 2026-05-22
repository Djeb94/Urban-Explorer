import requests, os
import pandas as pd

URL = "https://www.data.gouv.fr/api/1/datasets/r/d7933994-2c66-4131-a4da-cf7cd18040a4"
PATH = "../data/bronze/dvf_raw.csv.gz"

if not os.path.exists(PATH):
    os.makedirs("../data/bronze", exist_ok=True)
    r = requests.get(URL, stream=True)
    with open(PATH, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

reader = pd.read_csv(PATH, compression="gzip", low_memory=False, chunksize=100_000)
first = next(reader)
print("Valeurs code_departement :", first["code_departement"].dropna().unique()[:10])
print("Type :", first["code_departement"].dtype)
print("Valeurs :", first["code_departement"].dropna().unique()[:10])

#filtre 75
chunks = [first[first["code_departement"] == 75]]
for chunk in reader:
    chunks.append(chunk[chunk["code_departement"] == 75])
chunks = [c for c in chunks if not c.empty]
df_paris = pd.concat(chunks, ignore_index=True)

#choix colonnes
colonnes = [
    "id_mutation", "date_mutation", "nature_mutation",
    "valeur_fonciere", "code_postal", "nom_commune",
    "type_local", "surface_reelle_bati",
    "nombre_pieces_principales", "longitude", "latitude"
]
#nettoyage
df_paris = df_paris[colonnes]
df_paris = df_paris.dropna(subset=["valeur_fonciere", "surface_reelle_bati", "latitude", "longitude"])
df_paris = df_paris[df_paris["surface_reelle_bati"] > 0]

#prix au m2
df_paris["prix_m2"] = df_paris["valeur_fonciere"] / df_paris["surface_reelle_bati"]
df_paris = df_paris[(df_paris["prix_m2"] > 1000) & (df_paris["prix_m2"] < 50000)]

#arrondissement
df_paris["annee"] = pd.to_datetime(df_paris["date_mutation"]).dt.year
df_paris["arrondissement"] = (
    df_paris["code_postal"]
    .dropna()
    .astype(float).astype(int)
    .astype(str).str[-2:]
    .astype(int)
)
# Sauvegarde silver
os.makedirs("data/silver", exist_ok=True)
df_paris.to_csv("data/silver/transactions_paris.csv", index=False)
print(f"✓ Silver sauvegardé — {len(df_paris)} lignes")
print(df_paris.head(3))
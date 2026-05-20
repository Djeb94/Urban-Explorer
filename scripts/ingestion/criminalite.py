import requests, os
import pandas as pd

URL = "https://static.data.gouv.fr/resources/bases-statistiques-communale-departementale-et-regionale-de-la-delinquance-enregistree-par-la-police-et-la-gendarmerie-nationales/20260326-124144/donnee-data.gouv-2025-geographie2025-produit-le2026-02-03.csv.gz"
PATH_RAW = "data/bronze/criminalite_raw.csv.gz"

if not os.path.exists(PATH_RAW):
    print("Téléchargement...")
    os.makedirs("data/bronze", exist_ok=True)
    r = requests.get(URL, stream=True)
    with open(PATH_RAW, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024*1024):
            f.write(chunk)
    print("✓ Téléchargé")

# Lecture
df = pd.read_csv(PATH_RAW, compression="gzip", dtype=str, sep=";")

# Filtre Paris
paris = df[df["CODGEO_2025"].str.startswith("751", na=False)].copy()
print(f"Lignes Paris brut : {len(paris)}")
print(f"Valeurs est_diffuse : {paris['est_diffuse'].unique()}")

# Filtre diffusé
paris = paris[paris["est_diffuse"] == "diff"]
print(f"Lignes Paris diffusées : {len(paris)}")

# Nettoyage
paris["arrondissement"] = paris["CODGEO_2025"].str[-2:].astype(int)
paris["nombre"] = pd.to_numeric(paris["nombre"], errors="coerce")

# Agréger
result = paris.groupby("arrondissement")["nombre"].sum().reset_index()
result.columns = ["arrondissement", "total_delits"]

os.makedirs("data/silver", exist_ok=True)
result.to_csv("data/silver/criminalite.csv", index=False)
print(f"✓ Silver sauvegardé — {len(result)} arrondissements")
print(result)
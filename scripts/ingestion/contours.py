import requests, os
import json

URL = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/arrondissements/exports/geojson"
PATH = "data/silver/contours_arrondissements.geojson"

os.makedirs("data/silver", exist_ok=True)

print("Téléchargement des contours...")
r = requests.get(URL)
data = r.json()

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)

print(f" {len(data['features'])} arrondissements sauvegardés")

# Vérification rapide
for feature in data["features"][:3]:
    props = feature["properties"]
    print(f"  → {props}")
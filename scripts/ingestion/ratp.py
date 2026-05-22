import requests, os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import json

# Chemins des fichiers
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRONZE_PATH = os.path.join(BASE_DIR, "data", "bronze", "stations_idf.csv")
SILVER_PATH = os.path.join(BASE_DIR, "data", "silver", "stations_par_arrondissement.csv")
CONTOURS_PATH = os.path.join(BASE_DIR, "data", "silver", "contours_arrondissements.geojson")

# URL de l'API IDF Mobilités qui liste toutes les gares d'Île-de-France
URL = "https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/emplacement-des-gares-idf/exports/csv?delimiter=%3B&lang=fr&timezone=Europe%2FParis"

os.makedirs(os.path.dirname(BRONZE_PATH), exist_ok=True)
os.makedirs(os.path.dirname(SILVER_PATH), exist_ok=True)

# On télécharge le fichier une seule fois, si il existe déjà on skip
if not os.path.exists(BRONZE_PATH):
    print("Téléchargement stations IDF Mobilités...")
    r = requests.get(URL, timeout=60)
    print(f"Status : {r.status_code} — taille : {len(r.content)} octets")
    with open(BRONZE_PATH, "wb") as f:
        f.write(r.content)
    print("✓ Téléchargé")
else:
    print("Fichier bronze déjà présent")

# Lecture du fichier brut
df = pd.read_csv(BRONZE_PATH, sep=";", encoding="utf-8", low_memory=False)
print(f"Shape brut : {df.shape}")

# On extrait la latitude et longitude depuis la colonne geo_point_2d
# qui contient des valeurs comme "48.8566, 2.3522"
df["lat"] = df["geo_point_2d"].str.split(",").str[0].astype(float)
df["lon"] = df["geo_point_2d"].str.split(",").str[1].astype(float)

# On garde uniquement le Métro et le RER, pas les bus ni tramways
df_metro = df[df["mode"].isin(["METRO", "RER"])].copy()
print(f"Stations métro/RER : {len(df_metro)}")

# On charge les contours géographiques des arrondissements de Paris
# c'est le fichier GeoJSON qu'on avait récupéré depuis Paris Open Data
with open(CONTOURS_PATH, "r", encoding="utf-8") as f:
    contours = json.load(f)

# On convertit les contours en GeoDataFrame (format géographique)
# EPSG:4326 c'est le système de coordonnées GPS standard (latitude/longitude)
gdf_contours = gpd.GeoDataFrame.from_features(contours["features"])
gdf_contours = gdf_contours.set_crs("EPSG:4326")
gdf_contours["arrondissement"] = gdf_contours["c_ar"].astype(int)

# On convertit aussi les stations en GeoDataFrame
# Point(lon, lat) crée un point GPS pour chaque station
gdf_stations = gpd.GeoDataFrame(
    df_metro,
    geometry=[Point(row.lon, row.lat) for _, row in df_metro.iterrows()],
    crs="EPSG:4326"
)

# Jointure spatiale : pour chaque station, on cherche dans quel arrondissement elle se trouve
# "within" veut dire "le point est à l'intérieur du polygone"
gdf_joined = gpd.sjoin(
    gdf_stations,
    gdf_contours[["arrondissement", "geometry"]],
    how="inner",
    predicate="within"
)

# On compte le nombre de stations uniques par arrondissement
# nunique() évite de compter deux fois la même station
stations_par_arr = (
    gdf_joined.groupby("arrondissement")["nom_zdc"]
    .nunique()
    .reset_index()
    .rename(columns={"nom_zdc": "nb_stations"})
    .sort_values("arrondissement")
    .reset_index(drop=True)
)

print("\n✓ Stations par arrondissement :")
print(stations_par_arr.to_string())

# Sauvegarde en Silver
stations_par_arr.to_csv(SILVER_PATH, index=False)
print(f"\n✓ Silver sauvegardé — {len(stations_par_arr)} arrondissements")
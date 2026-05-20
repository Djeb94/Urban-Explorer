import requests, os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRONZE_PATH = os.path.join(BASE_DIR, "data", "bronze", "stations_idf.csv")
SILVER_PATH = os.path.join(BASE_DIR, "data", "silver", "stations_par_arrondissement.csv")
CONTOURS_PATH = os.path.join(BASE_DIR, "data", "silver", "contours_arrondissements.geojson")

URL = "https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/emplacement-des-gares-idf/exports/csv?delimiter=%3B&lang=fr&timezone=Europe%2FParis"

os.makedirs(os.path.dirname(BRONZE_PATH), exist_ok=True)
os.makedirs(os.path.dirname(SILVER_PATH), exist_ok=True)

#Téléchargement
if not os.path.exists(BRONZE_PATH):
    print("Téléchargement stations IDF Mobilités...")
    r = requests.get(URL, timeout=60)
    print(f"Status : {r.status_code} — taille : {len(r.content)} octets")
    with open(BRONZE_PATH, "wb") as f:
        f.write(r.content)
    print("✓ Téléchargé")
else:
    print("Fichier bronze déjà présent")


df = pd.read_csv(BRONZE_PATH, sep=";", encoding="utf-8", low_memory=False)
print(f"Shape brut : {df.shape}")

df["lat"] = df["geo_point_2d"].str.split(",").str[0].astype(float)
df["lon"] = df["geo_point_2d"].str.split(",").str[1].astype(float)

df_metro = df[df["mode"].isin(["METRO", "RER"])].copy()
print(f"Stations métro/RER : {len(df_metro)}")

with open(CONTOURS_PATH, "r", encoding="utf-8") as f:
    contours = json.load(f)

gdf_contours = gpd.GeoDataFrame.from_features(contours["features"])
gdf_contours = gdf_contours.set_crs("EPSG:4326")
gdf_contours["arrondissement"] = gdf_contours["c_ar"].astype(int)

gdf_stations = gpd.GeoDataFrame(
    df_metro,
    geometry=[Point(row.lon, row.lat) for _, row in df_metro.iterrows()],
    crs="EPSG:4326"
)

gdf_joined = gpd.sjoin(
    gdf_stations,
    gdf_contours[["arrondissement", "geometry"]],
    how="inner",
    predicate="within"
)

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

stations_par_arr.to_csv(SILVER_PATH, index=False)
print(f"\n✓ Silver sauvegardé — {len(stations_par_arr)} arrondissements")
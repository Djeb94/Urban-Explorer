import requests, os
import pandas as pd
import geopandas as gpd
import json

os.makedirs("data/bronze", exist_ok=True)
os.makedirs("data/silver", exist_ok=True)

# ── 1. POI OSM ────────────────────────────────────────────────────
print("Chargement POI OSM (restaurants, bars, cafés, commerces...)")
gdf_pois = gpd.read_file("data/bronze/osm/gis_osm_pois_free_1.shp")
categories = ["restaurant", "bar", "cafe", "bakery", "supermarket", "cinema", "theatre"]
gdf_pois = gdf_pois[gdf_pois["fclass"].isin(categories)]
print(f"✓ {len(gdf_pois)} POI filtrés")

# ── 2. Contours arrondissements ───────────────────────────────────
with open("data/silver/contours_arrondissements.geojson", "r") as f:
    contours = json.load(f)
gdf_contours = gpd.GeoDataFrame.from_features(contours["features"]).set_crs("EPSG:4326")
gdf_contours["arrondissement"] = gdf_contours["c_ar"].astype(int)
gdf_pois = gdf_pois.to_crs("EPSG:4326")

# ── 3. Jointure spatiale POI → arrondissement ─────────────────────
print("Jointure spatiale...")
gdf_joined = gpd.sjoin(gdf_pois, gdf_contours[["arrondissement", "geometry"]], how="inner", predicate="within")
poi_par_arr = gdf_joined.groupby(["arrondissement", "fclass"]).size().unstack(fill_value=0).reset_index()
print(f"✓ POI par arrondissement calculés")

# ── 4. Musées officiels (Ministère de la Culture) ─────────────────
print("Téléchargement musées officiels...")
URL_MUSEES = "https://data.culture.gouv.fr/api/explore/v2.1/catalog/datasets/liste-et-localisation-des-musees-de-france/exports/csv?delimiter=%3B"
if not os.path.exists("data/bronze/musees.csv"):
    r = requests.get(URL_MUSEES, timeout=60)
    with open("data/bronze/musees.csv", "wb") as f:
        f.write(r.content)
    print("✓ Téléchargé")
else:
    print("✓ Fichier déjà présent")
df_musees = pd.read_csv("data/bronze/musees.csv", sep=";")
df_musees = df_musees[df_musees["departement"] == "Paris"].copy()
df_musees["cp"] = pd.to_numeric(df_musees["code_postal"], errors="coerce").astype("Int64")
df_musees["arrondissement"] = df_musees["cp"] % 100
df_musees = df_musees[df_musees["arrondissement"].between(1, 20)]
musees_par_arr = df_musees.groupby("arrondissement").size().reset_index(name="nb_musees_officiels")
print(f"✓ {len(df_musees)} musées officiels à Paris")

# ── 5. Espaces verts (Paris Open Data) ───────────────────────────
print("Chargement espaces verts...")
df_espaces = pd.read_csv("data/silver/espaces_verts.csv")
print(f"✓ {len(df_espaces)} arrondissements")

# ── 6. Fusion tout ────────────────────────────────────────────────
all_arr = pd.DataFrame({"arrondissement": range(1, 21)})
result = all_arr.merge(poi_par_arr, on="arrondissement", how="left")
result = result.merge(musees_par_arr, on="arrondissement", how="left")
result = result.merge(df_espaces[["arrondissement", "surface_totale_m2"]], on="arrondissement", how="left")
result = result.fillna(0)

result.to_csv("data/silver/vivabilite.csv", index=False)
print(f"\n✓ Silver vivabilité sauvegardé — {len(result)} arrondissements")
print(result)
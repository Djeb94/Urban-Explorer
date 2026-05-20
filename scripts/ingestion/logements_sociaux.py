import requests, os
import pandas as pd

URL = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/logements-sociaux-finances-a-paris/exports/csv?lang=fr&timezone=Europe%2FParis&use_labels=true&delimiter=%3B"
PATH_OUT = "data/silver/logements_sociaux.csv"

print("Téléchargement logements sociaux Paris...")
r = requests.get(URL)
r.encoding = "utf-8"

with open("data/bronze/logements_sociaux_raw.csv", "wb") as f:
    f.write(r.content)

df = pd.read_csv("data/bronze/logements_sociaux_raw.csv", sep=";")
print(f"Colonnes : {df.columns.tolist()}")
print(f"Lignes : {len(df)}")
print(df.head(3))

# Nettoyage
df = df[["Arrondissement", "Année du financement - agrément", "Nombre total de logements financés"]]
df.columns = ["arrondissement", "annee", "nb_logements"]

# Nettoyer l'arrondissement (garder juste le numéro)
df["arrondissement"] = pd.to_numeric(df["arrondissement"], errors="coerce")
df["annee"] = pd.to_numeric(df["annee"], errors="coerce")
df["nb_logements"] = pd.to_numeric(df["nb_logements"], errors="coerce")
df = df.dropna()
df["arrondissement"] = df["arrondissement"].astype(int)
df["annee"] = df["annee"].astype(int)

# Agréger par arrondissement
total_par_arr = df.groupby("arrondissement")["nb_logements"].sum().reset_index()
total_par_arr.columns = ["arrondissement", "total_logements_sociaux"]

os.makedirs("data/silver", exist_ok=True)
total_par_arr.to_csv(PATH_OUT, index=False)
print(f"✓ Silver sauvegardé — {len(total_par_arr)} arrondissements")
print(total_par_arr)
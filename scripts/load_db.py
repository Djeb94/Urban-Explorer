from dotenv import load_dotenv
import os
import pandas as pd
from sqlalchemy import create_engine
from pymongo import MongoClient
import json

load_dotenv()

#Connexions
engine = create_engine(os.getenv("POSTGRES_URL"))
client = MongoClient(os.getenv("MONGO_URL"))
db = client["urban_explorer"]

#PostgreSQL

pd.read_csv("data/silver/transactions_paris.csv").to_sql(
    "transactions", engine, if_exists="replace", index=False)
print("transactions")

pd.read_csv("data/silver/revenus_paris.csv").to_sql(
    "revenus", engine, if_exists="replace", index=False)
print("revenus")

pd.read_csv("data/silver/criminalite.csv").to_sql(
    "criminalite", engine, if_exists="replace", index=False)
print("criminalite")



#MongoDB
print("\nChargement MongoDB...")

#logements sociaux
df = pd.read_csv("data/silver/logements_sociaux.csv")
db["logements_sociaux"].drop()
db["logements_sociaux"].insert_many(df.to_dict("records"))
print("logements_sociaux")

#espaces verts
df = pd.read_csv("data/silver/espaces_verts.csv")
db["espaces_verts"].drop()
db["espaces_verts"].insert_many(df.to_dict("records"))
print("espaces_verts")

#stations RATP
df = pd.read_csv("data/silver/stations_par_arrondissement.csv")
db["stations_ratp"].drop()
db["stations_ratp"].insert_many(df.to_dict("records"))
print("stations_ratp")

#contours GeoJSON
with open("data/silver/contours_arrondissements.geojson", "r") as f:
    contours = json.load(f)
db["contours"].drop()
db["contours"].insert_many(contours["features"])
print("contours")

print("\n Tout est chargé !")
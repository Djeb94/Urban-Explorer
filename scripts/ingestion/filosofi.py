import pandas as pd
import os

PATH_IN  = "data/bronze/BASE_TD_FILO_IRIS_2021_DISP.csv"
PATH_OUT = "data/silver/revenus_paris.csv"

df = pd.read_csv(PATH_IN, sep=";", decimal=",", dtype={"IRIS": str})

df = df[df["IRIS"].str.startswith("75")]

#revenu médian
df = df[["IRIS", "DISP_MED21"]]

# Remplacer ns/nd par NaN
df["DISP_MED21"] = pd.to_numeric(df["DISP_MED21"], errors="coerce")

# code cleaning
df["arrondissement"] = df["IRIS"].str[3:5].astype(int)

# Agréger par arrondissement
result = df.groupby("arrondissement")["DISP_MED21"].mean().reset_index()
result.columns = ["arrondissement", "revenu_median"]
result = result.dropna()

os.makedirs("data/silver", exist_ok=True)
result.to_csv(PATH_OUT, index=False)
print(f" {len(result)} arrondissements sauvegardés")
print(result)
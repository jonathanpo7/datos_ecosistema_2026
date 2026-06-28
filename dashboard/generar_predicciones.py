# -*- coding: utf-8 -*-
"""Genera dashboard/predicciones_2024.csv a partir del modelo persistido
(entrenamiento_csv/model_xgb.json) y df_forecast_raw.csv.

Reconstruye las ventanas de 2024 (misma logica que dataset.ipynb), predice
2024-1 con lags reales y 2024-2 de forma RECURSIVA (lag1 = prediccion de 2024-1).
No reentrena: solo carga el modelo ya entrenado.
"""
import os
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENTR = os.path.join(ROOT, "entrenamiento_csv")
COLS_CAT = ["CARACTER", "ORIGEN", "DEPARTAMENTO", "MUNICIPIO"]


def main():
    # 1) Cargar modelo entrenado y las categorias de entrenamiento (para alinear).
    model = XGBRegressor(enable_categorical=True)
    model.load_model(os.path.join(ENTR, "model_xgb.json"))
    x_train = pd.read_csv(os.path.join(ENTR, "X_train.csv"))
    cat_categories = {c: x_train[c].astype("category").cat.categories for c in COLS_CAT}

    # 2) Reconstruir el dataset con IES (misma ventana deslizante que dataset.ipynb).
    df = (pd.read_csv(os.path.join(ROOT, "df_forecast_raw.csv"))
          .sort_values(["IES", "periodo"]).reset_index(drop=True))
    filas = []
    for ies, g in df.groupby("IES"):
        tasas = g["tasa"].values
        periodos = g["periodo"].values
        for i in range(4, len(tasas)):
            filas.append({"IES": ies, "lag4": tasas[i-4], "lag3": tasas[i-3],
                          "lag2": tasas[i-2], "lag1": tasas[i-1],
                          "target": tasas[i], "periodo_target": periodos[i]})
    ds = pd.DataFrame(filas)
    meta = df.groupby("IES")[COLS_CAT].first().reset_index()
    ds = ds.merge(meta, on="IES", how="left")
    ds[["lag4", "lag3", "lag2", "lag1", "target"]] = np.clip(
        ds[["lag4", "lag3", "lag2", "lag1", "target"]], 0, 100)
    ds["semestre"] = ds["periodo_target"].str.split("-").str[1].astype(int)
    for c in COLS_CAT:
        ds[c] = ds[c].astype("category").cat.set_categories(cat_categories[c])

    feat = ["lag4", "lag3", "lag2", "lag1", "semestre"] + COLS_CAT
    t1 = ds[ds["periodo_target"] == "2024-1"].copy()
    t2 = ds[ds["periodo_target"] == "2024-2"].copy()

    # 3) Predicciones: 2024-1 directa; 2024-2 recursiva (lag1 = pred 2024-1).
    t1["pred_2024_1"] = np.clip(model.predict(t1[feat]), 0, 100)
    pred1_map = dict(zip(t1["IES"], t1["pred_2024_1"]))
    t2["lag1"] = t2["IES"].map(pred1_map).astype(float)
    t2["pred_2024_2"] = np.clip(model.predict(t2[feat]), 0, 100)

    # 4) Construir la tabla de salida por IES.
    # Nota: en df_forecast_raw.csv los acentos de CARACTER son correctos (ó=U+00F3,
    # é=U+00E9); el "?" que se ve en algunas consolas Windows es solo un artefacto de
    # render (cp1252), no mojibake real en el dato.
    out = t1[["IES", "DEPARTAMENTO", "MUNICIPIO", "CARACTER", "ORIGEN"]].copy()
    out["tasa_2023_2"] = t1["lag1"].values          # ultima tasa observada (real)
    out["pred_2024_1"] = t1["pred_2024_1"].values
    out["real_2024_1"] = t1["target"].values
    out["pred_2024_2"] = out["IES"].map(dict(zip(t2["IES"], t2["pred_2024_2"])))
    out["real_2024_2"] = out["IES"].map(dict(zip(t2["IES"], t2["target"])))
    out["tendencia"] = (out["pred_2024_1"] - out["tasa_2023_2"]).round(2)
    out["nivel_riesgo"] = pd.cut(out["pred_2024_1"], bins=[-1, 10, 20, 101],
                                 labels=["Bajo", "Medio", "Alto"])
    out["en_aumento"] = out["tendencia"] > 0
    for c in ["tasa_2023_2", "pred_2024_1", "real_2024_1", "pred_2024_2", "real_2024_2"]:
        out[c] = out[c].round(2)

    out = out.sort_values("pred_2024_1", ascending=False).reset_index(drop=True)
    dest = os.path.join(HERE, "predicciones_2024.csv")
    out.to_csv(dest, index=False, encoding="utf-8")

    # 5) Sanity check: el error vs real_2024_1 debe rondar el del notebook (~11 RMSE).
    rmse = float(np.sqrt(((out["pred_2024_1"] - out["real_2024_1"]) ** 2).mean()))
    print(f"OK -> {dest}")
    print(f"IES: {len(out)} | en riesgo (Alto): {(out['nivel_riesgo']=='Alto').sum()} "
          f"| RMSE pred_2024_1 vs real: {rmse:.2f} (esperado ~11.2)")


if __name__ == "__main__":
    main()

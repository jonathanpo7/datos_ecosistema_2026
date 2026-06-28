# Dashboard — Alerta temprana de deserción por IES

Dashboard interactivo (Streamlit) que visualiza las predicciones de tasa de deserción
2024 (t+1 y t+2) por Institución de Educación Superior, para apoyar la **priorización
de intervenciones** por parte de secretarías de educación.

## Cómo ejecutar

```bash
# 1) Instalar dependencias (incluye streamlit y plotly)
pip install -r requirements.txt

# 2) Generar las predicciones desde el modelo entrenado (crea predicciones_2024.csv)
python dashboard/generar_predicciones.py

# 3) Lanzar el dashboard
streamlit run dashboard/app.py
```

Se abre en `http://localhost:8501`.

## Qué muestra

- **KPIs:** nº de IES, IES en riesgo alto (tasa ≥ 20%), IES con tendencia al alza, tasa promedio predicha.
- **🚨 Ranking de riesgo:** tabla priorizada por tasa predicha 2024-1 + gráfico Top-20.
- **🗺️ Por departamento:** tasa promedio predicha y nº de IES en riesgo por departamento.
- **🏫 Detalle por IES:** serie histórica real + pronóstico 2024-1/2024-2, con comparación contra el valor real observado.

**Filtros** (barra lateral): departamento, carácter institucional, nivel de riesgo, tendencia al alza.

## Archivos

| Archivo | Rol |
|---------|-----|
| `generar_predicciones.py` | Carga `entrenamiento_csv/model_xgb.json` + `df_forecast_raw.csv`, reconstruye las ventanas 2024, predice (2024-2 recursivo) y exporta `predicciones_2024.csv`. No reentrena. |
| `app.py` | App Streamlit que lee `predicciones_2024.csv` (y `df_forecast_raw.csv` para la serie histórica). |
| `predicciones_2024.csv` | Predicciones por IES (regenerable con el script). |

## Uso responsable

El modelo es muy confiable para universidades (MAE ≈ 1.7 pp) y menos confiable para
instituciones técnicas profesionales (MAE ≈ 21 pp). Las predicciones **priorizan**; no
sustituyen el juicio de la secretaría de educación. Métricas honestas: RMSE 2024-1 ≈ 11.2,
ranking Spearman 0.87 (selección por validación, test medido una sola vez).

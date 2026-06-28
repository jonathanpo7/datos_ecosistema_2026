---
name: datos-ecosistema-2026
description: Use when working on the datos_ecosistema_2026 repo / "Datos al Ecosistema 2026" contest — a SNIES/MEN dropout-rate forecasting model (XGBoost + Optuna). Loads project context, pipeline, branch/PR rules, the audit findings (data leakage C1/C2, missing baseline) and current state so you don't re-derive them.
---

# datos-ecosistema-2026 — Contexto del proyecto

## Qué es
Modelo de ML que **predice la tasa de deserción por IES** en Colombia para el año siguiente (semestres `t+1` y `t+2`), con series históricas del **SNIES** (MEN). Proyecto del concurso **"Datos al Ecosistema 2026" / "IA para Colombia"** (MinTIC, datos.gov.co; final presencial ~agosto 2026; eje *educación*). Lo hizo un compañero (Jhonatan / "Jonathan Piedrahita"); el objetivo es dejarlo **competitivo para ganar**.

- **Target:** `tasa = (DESERTORES / MATRICULADOS) × 100`, acotada a `[0,100]`.
- **Universo:** 277/343 IES aptas (series ≥20 períodos sin huecos).
- **Métrica del README:** RMSE 9.48 / MAE 4.23 ⚠️ **afectada por data leakage** (ver hallazgos).

## Pipeline (orden de ejecución)
```
EDA_preprocesamiento.ipynb   → df_forecast_raw.csv   (limpieza + cobertura)
dataset.ipynb                → entrenamiento_csv/*.csv (ventana deslizante 4 lags → splits)
entrenamiento_csv/model.ipynb → XGBoost + Optuna + evaluación
```
**Split temporal:** train ≤2023-1 · val 2023-2 · test 2024-1/2024-2.

## Estado actual (jun 2026)
**Auditoría completa + correcciones implementadas** en el **PR #1** (rama `feat/correcciones-auditoria-2026`), aún **sin mergear a `main`**. 📄 Empezar por [`ESTADO_DEL_PROYECTO.md`](../../../ESTADO_DEL_PROYECTO.md); auditoría en [`reports/`](../../../reports/); bitácora de cambios en `reports/IMPLEMENTACION.md`.

## Hallazgos clave y su estado
| ID | Sev | Qué | Estado |
|----|-----|-----|--------|
| **C1** | 🔴 | Optuna minimizaba RMSE de **TEST** (leakage de selección) | ✅ Resuelto (objective→val) |
| **C2** | 🔴 | Sin forecast recursivo t+1→t+2 (leakage temporal) | ✅ Resuelto (recursivo + por horizonte) |
| **ML-2** | 🟠 | Sin baseline de persistencia | ✅ Resuelto |
| **A3 / R1** | 🟠 | No persistía modelo; Optuna sin semilla | ✅ Resuelto |
| **R2 / S02 / ML-1 / WEB-6/7/9** | 🟡/🟠 | requirements/LICENSE/Pillow; ranking/SHAP/conformal/dashboard | ✅ Resuelto |
| **DQ-TARGET** | 🟠 | Tasa no acotada (138 700%) | ⏳ Pendiente (cascada EDA) |
| **A2** | 🟡 | `SettingWithCopyWarning` | ⏳ Pendiente |
| **H1** | 🟠 | CSV de 99 MB en historial git | ⏳ Pendiente (destructivo — requiere acuerdo) |

**Métrica honesta (tras corregir):** RMSE test 10.14 (antes 9.48 con leakage); por horizonte t+1 11.16 / t+2 10.49; **ranking Spearman 0.872**; backtesting modelo 7.52 vs persistencia 8.33.

**Correcciones a hipótesis previas:** A1 era **código muerto, NO duplicaba categorías** (falso positivo). `.gitignore` SÍ existe. CARACTER en `df_forecast_raw.csv` tiene acentos correctos (el `?` en consola Windows es solo render).

**Lo que está bien (no romper):** README; split temporal correcto en concepto; `set_categories`; sin PII de personas naturales; diagnóstico de cobertura riguroso.

## Reglas de ramas / PRs
- Trabajo actual en el **PR #1** (rama `feat/correcciones-auditoria-2026`); **no mergeado a `main`**.
- **Convención:** `fix/...` (leakage, bugs), `feat/...` (baseline, SHAP, dashboard, features), `chore/...` (requirements, licencia, persistencia, higiene).
- **No `git push` a `main` ni force-push sin acuerdo del equipo.** No reescribir el historial (CSV de 99 MB) sin OK explícito. No versionar datos pesados nuevos (DVC / enlace al SNIES).
- Reproducibilidad: semillas fijadas (seed=42); `requirements.txt` pineado.

## Para ganar (estado)
✅ **Hechos:** corregir leakage, baseline de persistencia, métricas de priorización (Precision@K, Spearman), error por segmento, SHAP, conformal, backtesting, dashboard Streamlit. ⏳ **Pendiente:** saneamiento de la tasa (DQ-TARGET), feature engineering (tendencia/momentum/volatilidad), mapa coroplético, narrativa de impacto cuantificada, presentación/pitch. Detalle en `ESTADO_DEL_PROYECTO.md §6` y `reports/04_ideas_ganar.md`.

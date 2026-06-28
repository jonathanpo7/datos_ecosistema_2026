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
**En auditoría — 100% lectura.** No modificar código del proyecto sin aprobar el plan de PRs.
Informes completos en [`reports/`](../../reports/) (empezar por `00_INFORME_MAESTRO.md`).

## Hallazgos clave (verificados contra el código)
| ID | Sev | Qué | Dónde |
|----|-----|-----|-------|
| **C1** | 🔴 | Optuna minimiza el RMSE de **TEST**, no de val (leakage de selección); README L78/L89 lo niega = falso | `model.ipynb` celda 9 |
| **C2** | 🔴 | No hay forecast recursivo t+1→t+2; 2024-2 usa la tasa **real** de 2024-1 como lag1 | `dataset.ipynb` + `model.ipynb` |
| **ML-2** | 🟠 | Sin baseline de persistencia; el modelo (9.5) apenas supera a `lag1` (TEST 10.07, VAL 8.18) | `model.ipynb` |
| **A3 / R1** | 🟠 | No persiste modelo/`best_params`; Optuna sin semilla → no reproducible | `model.ipynb` celdas 9/10 |
| **DQ-TARGET** | 🟠 | Tasa no acotada en origen (llega a 138 700% por denominador=1) | `EDA` celda 12 |
| **H1** | 🟠 | CSV de 99 MB versionado y en historial git; sin `LICENSE`; sin `requirements.txt` | repo |

**Correcciones a hipótesis previas:** A1 (`dic`/`.replace()` comentado) es **código muerto, NO duplica categorías** (falso positivo). `.gitignore` SÍ existe (no cubre datos). README dice 9.48/4.23 pero el notebook hoy da 9.51/4.16.

**Lo que está bien (no romper):** README; split temporal correcto en concepto; `early_stopping` sobre val; `set_categories` alinea val/test; sin PII de personas naturales; diagnóstico de cobertura riguroso.

## Reglas de ramas / PRs
- Rama base de la auditoría: `chore/auditoria-inicial`.
- **Convención:** `fix/...` (leakage, bugs), `feat/...` (baseline, SHAP, features, dashboard, conformal), `chore/...` (requirements, .gitignore de datos, licencia, persistencia, higiene).
- **Orden must-fix (nombres canónicos del informe maestro):** `fix/optuna-objective-validacion` → `feat/forecast-recursivo-t1-t2` → `feat/baseline-persistencia` → `chore/persistir-modelo-y-semillas` → `chore/requirements-y-licencia`. Detalle completo (objetivo, archivos, criterio de aceptación) en `reports/00_INFORME_MAESTRO.md §3`.
- **No `git push` ni subir a GitHub sin autorización explícita del usuario.** No versionar datos pesados nuevos (usar DVC / enlace al SNIES).

## Para ganar (resumen de `reports/04_ideas_ganar.md`)
Quick wins: (1) baseline de persistencia + corregir leakage; (2) SHAP + error por segmento; (3) dashboard + narrativa de impacto con cifras. Luego: métricas de priorización (Precision@K), feature engineering (tendencia/momentum/volatilidad), intervalos conformal, backtesting rolling-origin.

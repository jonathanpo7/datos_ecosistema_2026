# 🛠️ Bitácora de Implementación — Correcciones del proyecto

> Registro de ingeniería **exhaustivo** de la fase de implementación (post-auditoría).
> Cada PR documenta: objetivo, archivos, cambios exactos (celda·línea), evidencia antes/después, comando de verificación, resultado y commit.
> **Política git:** commits locales documentados. **NO se hace `git push` sin autorización explícita del usuario.**

---

## Contexto y estrategia

- **Base:** rama `chore/auditoria-inicial` (contiene la auditoría: `reports/`, `CLAUDE.md`, skill). Commit `38eb77a`.
- **Topología de ramas:** una rama por PR, partiendo de la rama de auditoría (apiladas) para conservar el contexto de `reports/` y esta bitácora. Nombres canónicos según `00_INFORME_MAESTRO.md §3`.
- **Entorno de verificación:** Python 3.13.8 · xgboost 3.3.0 · optuna 4.9.0 · scikit-learn 1.8.0 · pandas 2.3.2 · numpy 2.3.3.
- **Alcance de ejecución:** `entrenamiento_csv/model.ipynb` se ejecuta de forma aislada (lee los `X_*/y_*.csv` ya generados; no requiere el CSV de 104 MB ni reejecutar el EDA).

### Estado del modelo ANTES de las correcciones (línea base con leakage)
| Medición | RMSE | MAE | Fuente |
|----------|------|-----|--------|
| Baseline XGBoost (celda `ffff5d67`, sobre **TEST**) | 9.70 | 4.17 | output versionado |
| Modelo final Optuna (celda `057d742d`, sobre **TEST**, clip) | 9.51 | 4.16 | output versionado |
| README (titular) | 9.48 | 4.23 | `README.md` L93-94 |
| Persistencia naive (`lag1`) sobre TEST | 10.07 | 4.42 | reproducido en auditoría |
| Persistencia naive sobre VAL | 8.18 | 3.15 | reproducido en auditoría |

> El número titular es de **test seleccionado mirando el test** (C1). Estas correcciones lo reemplazan por un número honesto.

---

## PR-1 · `fix/optuna-objective-validacion` — Eliminar el leakage de selección (C1, C1b, C1c)

**Objetivo:** que Optuna optimice sobre **validación** y que el **test** se toque una sola vez. Hacer reproducible la búsqueda.

**Hallazgos atacados:** C1 (Optuna minimiza RMSE de test), C1b (baseline mide sobre test), C1c (modelo final hereda params contaminados), R1 (Optuna sin semilla — parcial: solo el sampler).

**Cambios (`entrenamiento_csv/model.ipynb`):**

1. **Celda `7e313e16` (`objective` + Optuna)** — *causa raíz del leakage*:
   - ANTES: `y_pred = modelo.predict(x_test)` → `return np.sqrt(mean_squared_error(y_test, y_pred))`.
   - DESPUÉS: evalúa sobre `x_val`/`y_val`; `create_study(..., sampler=TPESampler(seed=42))` para reproducibilidad.

2. **Celda `ffff5d67` (evaluación del baseline)**:
   - ANTES: `predict(x_test)` y métrica sobre `y_test` ("Semestre 1 — RMSE 9.70").
   - DESPUÉS: evalúa el baseline sobre **validación** (para comparar contra el modelo seleccionado por val). El test se reserva.

3. **Celda `057d742d` (modelo final)**: se mantiene como la **única** medición sobre test (protocolo correcto: fijar HP por val → medir test una vez). Se documenta el número honesto resultante.

4. **`README.md`**: actualizar la tabla de resultados con el número honesto y dejar el texto (L78/L89) consistente con el código (Optuna ahora SÍ optimiza sobre validación).

**Verificación (ejecución real del notebook corregido):**
```
cd entrenamiento_csv
python -m jupyter nbconvert --to notebook --execute --inplace model.ipynb --ExecutePreprocessor.timeout=600
```
Entorno: xgboost 3.3.0 · optuna 4.9.0 · sklearn 1.8.0. Ejecución EXIT=0; outputs versionados actualizados.

**Resultados — número HONESTO (selección por validación, test medido una sola vez):**

| Medición | RMSE | MAE | Comentario |
|----------|------|-----|------------|
| Baseline XGBoost sobre **validación** | 5.22 | 2.75 | antes se medía sobre test (9.70) |
| Optuna `best_value` (**validación**) | 4.36 | — | antes minimizaba RMSE de test (9.51) |
| Modelo final — **validación** | 4.36 | 2.81 | métrica de selección |
| **Modelo final — TEST (honesto, 1 sola vez)** | **10.14** | **4.31** | antes 9.48–9.51 (con leakage) |
| Persistencia naive (`lag1`) — TEST | 10.07 | 4.42 | referencia trivial |

**🚨 Hallazgo empírico (confirma IMP-1 / ML-2):** corregido el leakage, el RMSE de test sube de 9.48 a **10.14** y el modelo **ya no supera al baseline de persistencia (10.07)** en RMSE (gana levemente en MAE: 4.31 vs 4.42). La predicción de la auditoría se cumple: *la métrica honesta es peor y el modelo apenas iguala lo trivial*.

**Observación metodológica (alimenta ML-7):** enorme brecha validación→test (val 4.36 vs test 10.14). El semestre de validación (2023-2) no es representativo de 2024 → motiva backtesting rolling-origin (PR-8) y reformular el valor hacia ranking/priorización (PR-8 métricas) en vez de error promedio.

**README:** tabla de resultados actualizada a 10.14 / 4.31 con nota de transparencia explicando la corrección. El texto L78/L89 ahora coincide con el código (Optuna optimiza sobre validación; test no usado en optimización).

**Commit:** `fix(model): Optuna optimiza sobre validacion, no sobre test (elimina data leakage C1)` (`f9a29c9`)

---

## PR-2 · `feat/forecast-recursivo-t1-t2` — Evaluación recursiva honesta (C2, D1)

**Objetivo:** implementar el encadenamiento t+1→t+2 que promete el README y reportar métricas por horizonte; eliminar el import muerto `MultiOutputRegressor`.

**Hallazgos atacados:** C2 (no había forecast recursivo; 2024-2 usaba la tasa real de 2024-1), D1 (`MultiOutputRegressor` importado y nunca usado).

**Cambios (`entrenamiento_csv/model.ipynb`):**
1. Celda `eaa35542` (imports): eliminado `from sklearn.multioutput import MultiOutputRegressor` (código muerto).
2. Nuevas celdas (markdown `73527519` + código `a6f0c004`) tras el modelo final: reconstruyen el dataset con `IES` desde `../df_forecast_raw.csv` (réplica exacta de la ventana deslizante de `dataset.ipynb`), y evalúan:
   - **h=1 (2024-1):** predicción directa con lags reales (≤ 2023-2).
   - **h=2 (2024-2) recursivo:** `lag1` = predicción de 2024-1 (mapeada por IES), no el valor real.
   - **h=2 con `lag1` real:** protocolo anterior, para cuantificar el leakage.
   - Persistencia por horizonte como referencia.
   - `assert len(t1)+len(t2)==len(x_test)` para validar la reconstrucción (pasó: 265+264=529).

**Verificación (ejecución real, EXIT=0):**

| Horizonte | Modelo RMSE / MAE | Persistencia RMSE / MAE |
|-----------|-------------------|--------------------------|
| t+1 (2024-1) | **11.16 / 4.74** | 11.48 / 4.97 |
| t+2 (2024-2, recursivo honesto) | **10.49 / 4.72** | 11.19 / 4.72 |
| t+2 (2024-2, con lag1 REAL — leakage anterior) | 8.99 / 3.89 | — |

**Conclusiones:**
- **C2 cuantificado:** el lag real de 2024-1 inflaba t+2 de RMSE 10.49 (honesto) a 8.99 (≈1.5 RMSE de optimismo indebido).
- **Buena noticia:** medido de forma justa por horizonte, **el modelo SÍ supera a la persistencia en ambos** (~0.3 RMSE en t+1, ~0.7 en t+2). El "modelo no aporta" del PR-1 era artefacto del agregado con leakage temporal; la evaluación honesta por horizonte es más favorable.

**README:** añadida subsección "Evaluación honesta por horizonte (forecast recursivo)" con la tabla. La afirmación del README sobre enfoque recursivo (L76) ahora SÍ está implementada.

**Commit:** `feat(model): evaluacion recursiva honesta t+1->t+2 por horizonte (corrige C2); elimina import muerto (D1)` (`57f3641`)

---

## PR-3 · `feat/baseline-persistencia` — Baselines triviales (ML-2)

**Objetivo:** demostrar de forma explícita si el modelo aporta sobre lo trivial, con baselines evaluados en el mismo protocolo y splits.

**Cambios (`entrenamiento_csv/model.ipynb`):** nueva celda markdown `5dfd2bd8` + código `2effbf59` que calcula y tabula **persistencia** (`ŷ = lag1`) y **media** (`ŷ = media(y_train)`) junto al modelo, en validación y test, y la mejora del modelo sobre persistencia.

**Verificación (ejecución real, EXIT=0):**

| Modelo / Baseline | VAL RMSE / MAE | TEST RMSE / MAE |
|-------------------|----------------|------------------|
| XGBoost (Optuna sobre val) | **4.36 / 2.81** | 10.14 / 4.31 |
| Persistencia (`lag1`) | 8.18 / 3.15 | 10.07 / 4.42 |
| Media (`y_train`) | 7.38 / 5.74 | 13.51 / 7.59 |

Mejora del modelo sobre persistencia (TEST agregado): **−0.07 RMSE / +0.10 MAE** (empate técnico).

**Lectura honesta:** en validación el modelo arrasa (4.36 vs 8.18), en test agregado empata con persistencia, y por horizonte (PR-2) la supera. Coincide exactamente con los números reproducidos en la auditoría (01_codigo_ml.md, ML-2). La enorme brecha val→test refuerza ML-7 (falta backtesting multi-ventana).

**README:** subsección "Comparación contra baselines (mismo protocolo y splits)".

**Commit:** `feat(model): baselines de persistencia y media con tabla comparativa (ML-2)`

---

## PR-4 · `chore/persistir-modelo-y-semillas` — Reproducibilidad y trazabilidad (A3, R1)

**Objetivo:** que la corrida sea reproducible bit-a-bit y que el modelo/params/métricas queden persistidos.

**Cambios (`entrenamiento_csv/model.ipynb`):**
1. Celda imports (`eaa35542`): `import random`; `np.random.seed(42)`; `random.seed(42)` (semillas globales, complementan `TPESampler(seed=42)`).
2. Nueva celda (`21b2ae90`): `modelo_final.save_model('model_xgb.json')`; `json.dump(study.best_params, 'best_params.json')`; y `metrics.json` con el cuadro honesto completo (val, test agregado, por horizonte, baselines).

**Artefactos generados (en `entrenamiento_csv/`):**
- `model_xgb.json` (~1.27 MB) — modelo XGBoost serializado.
- `best_params.json` (246 B) — hiperparámetros ganadores.
- `metrics.json` (753 B) — todas las métricas honestas.

**Verificación de reproducibilidad (R1):** el `best_value` de Optuna es **4.3578**, idéntico al de la corrida de PR-1 → la búsqueda es reproducible. EXIT=0.

**Commit:** `chore(model): semillas globales + persistencia de modelo/params/metricas (A3, R1)`

> Nota: `model_xgb.json` (1.27 MB) es estable (semillas fijas) y se versiona junto al número reportado, como recomienda A3. Si el equipo prefiere, puede moverse a un release/LFS (se deja fuera del `.gitignore` de datos en PR-5).

---

## Pendiente (no bloqueante para presentar)

- PR-5 `chore/requirements-y-licencia` (R2, S02-2/3/4): `requirements.txt` pineado (incl. `pillow>=12.2.0`), `LICENSE`, nota de licencia de datos SNIES.
- Mejoras (PR-6+): saneamiento de tasa, `.copy()` en splits, métricas de ranking/Precision@K, SHAP, dashboard, conformal — detalladas en `00_INFORME_MAESTRO.md §3`.

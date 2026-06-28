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

**Commit:** `fix(model): Optuna optimiza sobre validacion, no sobre test (elimina data leakage C1)`

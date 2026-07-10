# CLAUDE.md — datos_ecosistema_2026

> Guía para Claude Code (y para el equipo) al trabajar en este repositorio.
> Proyecto del concurso **"Datos al Ecosistema 2026"**.
> Estado: **auditoría completa + correcciones implementadas** (PR #1). 📄 **Empieza por [`ESTADO_DEL_PROYECTO.md`](ESTADO_DEL_PROYECTO.md)** — documento maestro de estado (qué se hizo, qué falta, qué sigue). Detalle de la auditoría en `reports/`; bitácora de cambios en `reports/IMPLEMENTACION.md`.

## Qué es este proyecto

Modelo de Machine Learning que **predice la tasa de deserción estudiantil por IES** (Institución de Educación Superior) en Colombia para el **año siguiente** (semestres `t+1` y `t+2`), a partir de series históricas del **SNIES** (Sistema Nacional de Información de la Educación Superior — Ministerio de Educación Nacional).

**Objetivo de impacto:** pasar de una gestión *reactiva* a *activa* de la deserción, dando a las secretarías de educación ~1 año de antelación para priorizar intervenciones.

- **Variable objetivo:** `tasa = (DESERTORES / MATRICULADOS) × 100`, acotada a `[0, 100]`.
- **Universo:** 343 IES en el SNIES → **277 IES aptas** con series consecutivas de ≥ 20 períodos (10 años) sin huecos.
- **Modelo:** XGBoost Regressor + optimización con Optuna.
- **Métricas reportadas en README:** RMSE 9.48 / MAE 4.23 (⚠️ ver hallazgos C1/C2 abajo: están afectadas por *data leakage*).

## Pipeline (orden de ejecución)

```
EDA_preprocesamiento.ipynb   # Limpieza + diagnóstico de cobertura → df_forecast_raw.csv
        │
        ▼
dataset.ipynb                # Ventana deslizante de 4 lags → splits en entrenamiento_csv/
        │
        ▼
entrenamiento_csv/model.ipynb  # XGBoost + Optuna + evaluación
```

**Split temporal:** train ≤ 2023-1 · validación = 2023-2 · test = 2024.

## Estructura del repositorio

```
├── EDA_preprocesamiento.ipynb        # EDA + limpieza
├── dataset.ipynb                     # Construcción del dataset (sliding window)
├── df_forecast_raw.csv               # Dataset consolidado de las 277 IES aptas
├── entrenamiento_csv/
│   ├── model.ipynb                   # Entrenamiento, Optuna y evaluación
│   ├── X_train.csv / y_train.csv     # Split train (≤2023-1)
│   ├── X_val.csv   / y_val.csv       # Split validación (2023-2)
│   └── X_test.csv  / y_test.csv      # Split test (2024)
├── graficas/                         # Notebooks de insights (género, estrato, icetex, programa)
│   └── RESUMEN_INSIGHTS.md
├── MEN_MATRICULA_ESTADISTICA_ES_*.csv  # Fuente SNIES (~99 MB, versionado)
├── MEN_INSTITUCIONES_*.csv             # Catálogo de IES (NIT/dirección — registro público)
├── *.csv                             # CSVs intermedios (dept/muni, sexo, icetex, etc.)
├── cargar_csv.py                     # Utilidad de carga
├── README.md                         # Documentación (excelente, pero ver C1/C2)
└── reports/                          # ← Informes de auditoría (generados por Claude)
```

## Cómo reproducir

```bash
pip install -r requirements.txt
```

1. Ejecutar `EDA_preprocesamiento.ipynb` (genera `df_forecast_raw.csv`).
2. Ejecutar `dataset.ipynb` (genera los CSV de `entrenamiento_csv/`).
3. Ejecutar `entrenamiento_csv/model.ipynb` (entrena y evalúa).

> Los datos fuente `MEN_*.csv` provienen del portal del SNIES — MEN Colombia.

## Estado actual y hallazgos clave

**Auditoría completa + correcciones implementadas** (PR #1). Estado por hallazgo en [`ESTADO_DEL_PROYECTO.md §5`](ESTADO_DEL_PROYECTO.md). Lo esencial:

| ID | Sev | Hallazgo | Estado |
|----|-----|----------|--------|
| **C1** | 🔴 Crítica | Optuna optimizaba sobre el test (leakage de selección) | ✅ Resuelto (objective→val) |
| **C2** | 🔴 Crítica | Sin forecast recursivo t+1→t+2 (leakage temporal) | ✅ Resuelto (recursivo + métricas por horizonte) |
| **ML-2** | 🟠 Alta | Sin baseline de persistencia | ✅ Resuelto |
| **A3 / R1** | 🟠 Alta | No persistía modelo; Optuna sin semilla | ✅ Resuelto |
| **R2 / S02** | 🟡/🟠 | Sin requirements/LICENSE; Pillow vulnerable | ✅ Resuelto |
| **ML-1/WEB-6/7/9** | 🟠 Alta | Sin ranking, SHAP, conformal, dashboard | ✅ Resuelto |
| **DQ-TARGET** | 🟠 Alta | Tasa no acotada en origen (138 700%) | ⏳ Pendiente (cascada EDA) |
| **A2** | 🟡 Media | `SettingWithCopyWarning` (slices sin `.copy()`) | ⏳ Pendiente |
| **H1** | 🟠 Alta | CSV de 99 MB en historial git | ⏳ Pendiente (destructivo — requiere acuerdo) |
| **A1** | INFO | dic/.replace comentado | ✅ Reclasificado: era código muerto, NO duplicaba categorías |

**Lo que está bien** (no romper): README; manejo de NaN reales con `min_count=1`; split temporal correcto en concepto; diagnóstico de cobertura riguroso; `enable_categorical` + `set_categories`.

## Skill del proyecto (carga de contexto automática)

Este repo incluye una skill propia en [`.claude/skills/datos-ecosistema-2026/`](.claude/skills/datos-ecosistema-2026/SKILL.md) que captura contexto, pipeline, reglas de ramas, hallazgos y estado actual. En futuras sesiones, invócala (`/datos-ecosistema-2026` o vía la herramienta Skill) para cargar todo el contexto sin re-derivarlo. Se actualiza a medida que avanza el proyecto.

## Reglas de trabajo

- **Estado:** correcciones implementadas en el **PR #1** (rama `feat/correcciones-auditoria-2026`); aún **no mergeado a `main`** (espera revisión del equipo).
- **Ramas (convención):** `fix/...` (leakage/bugs), `feat/...` (baseline, SHAP, dashboard, features), `chore/...` (requirements, licencia, persistencia, higiene).
- **No `git push` a `main` ni force-push** sin autorización del equipo. Trabajar siempre por PR. No reescribir el historial (CSV de 99 MB) sin acuerdo explícito.
- **No versionar datos pesados** nuevos: preferir DVC / enlace a la fuente SNIES.
- **Reproducibilidad:** semillas fijadas (seed=42); `requirements.txt` pineado.

---
*Mantenido por Claude Code. Documento de estado vivo: [`ESTADO_DEL_PROYECTO.md`](ESTADO_DEL_PROYECTO.md). Auditoría: `reports/`. Bitácora de cambios: `reports/IMPLEMENTACION.md`.*

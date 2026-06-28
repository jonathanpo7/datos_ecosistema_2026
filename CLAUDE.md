# CLAUDE.md — datos_ecosistema_2026

> Guía para Claude Code (y para el equipo) al trabajar en este repositorio.
> Proyecto del concurso **"Datos al Ecosistema 2026"**.
> Estado: **en auditoría** (ver `reports/`). Este archivo es la base de contexto; se enriquece con la skill del proyecto (`.claude/skills/`).

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
# No hay requirements.txt (pendiente — ver auditoría). Dependencias declaradas en README:
pip install pandas numpy xgboost scikit-learn optuna matplotlib seaborn jupyter
```

1. Ejecutar `EDA_preprocesamiento.ipynb` (genera `df_forecast_raw.csv`).
2. Ejecutar `dataset.ipynb` (genera los CSV de `entrenamiento_csv/`).
3. Ejecutar `entrenamiento_csv/model.ipynb` (entrena y evalúa).

> Los datos fuente `MEN_*.csv` provienen del portal del SNIES — MEN Colombia.

## Estado actual y hallazgos clave (resumen — detalle en `reports/`)

| ID | Sev | Hallazgo |
|----|-----|----------|
| **C1** | 🔴 Crítica | `model.ipynb` (celda 9): la función `objective` de Optuna evalúa sobre `x_test/y_test` → **los hiperparámetros se eligen mirando el test** (data leakage). El README afirma lo contrario. |
| **C2** | 🔴 Crítica | La evaluación no implementa el forecast recursivo t+1→t+2 que describe el README; usa la tasa real del semestre intermedio → leakage temporal. |
| **A1** | 🟠 Alta | En el EDA, el diccionario `dic` de normalización de departamentos está definido pero su `.replace()` está **comentado** → categorías duplicadas. |
| **A2** | 🟠 Alta | `SettingWithCopyWarning` en `dataset.ipynb` (slices sin `.copy()`). |
| **A3** | 🟠 Alta | No se persiste el modelo ni los `best_params` (sin `.pkl`/`.json`). |

**Lo que está bien** (no romper): README; manejo de NaN reales con `min_count=1`; split temporal correcto en concepto; diagnóstico de cobertura riguroso; `enable_categorical` + `set_categories`.

## Skill del proyecto (carga de contexto automática)

Este repo incluye una skill propia en [`.claude/skills/datos-ecosistema-2026/`](.claude/skills/datos-ecosistema-2026/SKILL.md) que captura contexto, pipeline, reglas de ramas, hallazgos y estado actual. En futuras sesiones, invócala (`/datos-ecosistema-2026` o vía la herramienta Skill) para cargar todo el contexto sin re-derivarlo. Se actualiza a medida que avanza el proyecto.

## Reglas de trabajo

- **Misión actual = auditoría 100% lectura.** No modificar el código del proyecto sin aprobación explícita del plan de PRs (ver `reports/00_INFORME_MAESTRO.md`).
- **Ramas (convención):** `fix/...` (correcciones de leakage/bugs), `feat/...` (baseline, SHAP, features, dashboard), `chore/...` (requirements, .gitignore de datos, licencia, persistencia).
- **No versionar datos pesados** nuevos: el CSV de ~99 MB ya infla el repo; preferir DVC / enlaces a la fuente SNIES en cambios futuros.
- **No exponer credenciales**: ninguna debería existir aquí (es data pública), pero validar antes de cada commit.

---
*Generado por Claude Code durante la auditoría del proyecto. Ver `reports/00_INFORME_MAESTRO.md` para el informe consolidado.*

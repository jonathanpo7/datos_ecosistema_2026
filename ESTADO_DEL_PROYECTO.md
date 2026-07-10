# 🧭 ESTADO DEL PROYECTO — Forecast de deserción IES · "Datos al Ecosistema 2026"

> **Documento maestro de contexto.** Punto de entrada único para entender qué es el proyecto,
> **qué hicimos**, **qué falta** y **qué sigue**. Vivo: se actualiza con cada avance.
> Última actualización: **2026-06-28**.

---

## 0. TL;DR (60 segundos)

- **Qué:** modelo que predice la **tasa de deserción por IES** en Colombia para el año siguiente (semestres t+1 y t+2), con datos del SNIES/MEN. Concurso **MinTIC "Datos al Ecosistema 2026"**, eje educación, final ~agosto 2026.
- **Estado:** se hizo una **auditoría técnica completa** + se **corrigieron 2 fugas de datos** que invalidaban la métrica, se añadieron baselines, métricas de priorización, interpretabilidad, validación robusta y un **dashboard interactivo**. Todo está en el **PR #1** listo para revisar/mergear.
- **Resultado honesto:** quitar el leakage subió el RMSE (9.48 → 10.14), **pero** el modelo gana a la persistencia por horizonte y en backtesting, y **ordena muy bien** las IES (Spearman 0.872) → su valor real es la **priorización**.
- **Dónde:** rama `feat/correcciones-auditoria-2026` → **PR #1**: https://github.com/jonathanpo7/datos_ecosistema_2026/pull/1

---

## 1. Qué es el proyecto

Modelo de Machine Learning que **anticipa la tasa de deserción** de cada Institución de Educación Superior (IES) para el año siguiente, a partir de su historial de ≥10 años de datos del **SNIES** (Sistema Nacional de Información de la Educación Superior — Ministerio de Educación).

**Objetivo de impacto (política pública):** pasar de una gestión *reactiva* a *activa* de la deserción — dar a las secretarías de educación ~1 año de antelación para **priorizar intervenciones** en las IES en riesgo.

- **Variable objetivo:** `tasa = (DESERTORES / MATRICULADOS) × 100`, acotada a `[0, 100]`.
- **Universo:** 277 / 343 IES aptas (series ≥ 20 períodos consecutivos sin huecos).
- **Concurso:** "Datos al Ecosistema 2026 / IA para Colombia" (MinTIC, datos.gov.co). Criterios: **impacto, escalabilidad y uso estratégico/responsable del dato**. Final presencial primera semana de agosto 2026 (GovCamps).

## 2. Arquitectura / pipeline

```text
MEN_*.csv (SNIES, 104 MB)
   │  EDA_preprocesamiento.ipynb   (limpieza, cobertura, consolidación)
   ▼
df_forecast_raw.csv  (277 IES aptas)
   │  dataset.ipynb                (ventana deslizante de 4 lags → splits)
   ▼
entrenamiento_csv/X_*.csv, y_*.csv
   │  entrenamiento_csv/model.ipynb (XGBoost + Optuna + evaluación honesta)
   ▼
model_xgb.json + metrics.json  ──►  dashboard/ (Streamlit)
```
**Split temporal:** train ≤ 2023-1 · validación = 2023-2 · test = 2024 (2024-1 y 2024-2).

---

## 3. ✅ LO QUE HICIMOS

### 3.1 Auditoría (solo lectura) — `reports/`
Auditoría multi-agente con verificación adversarial. 7 informes:

| Informe | Contenido |
|---------|-----------|
| `00_INFORME_MAESTRO.md` | Consolidado + tabla priorizada + plan de PRs |
| `01_codigo_ml.md` | Leakage C1/C2, baselines reproducidos, validez métrica |
| `02_seguridad.md` | Secretos, pip-audit, PII (sin PII de personas naturales) |
| `03_investigacion_web.md` | Concurso MinTIC + estado del arte + gaps |
| `04_ideas_ganar.md` | Diferenciadores priorizados por impacto/esfuerzo |
| `05_debate.md` | Debate Abogado/Fiscal/Juez + veredicto de competitividad |
| `06_mlops_reproducibilidad.md` | Reproducibilidad, persistencia, higiene de repo |
| `IMPLEMENTACION.md` | **Bitácora de ingeniería** de todas las correcciones (antes/después) |

### 3.2 Correcciones implementadas (código)

| # | Qué se hizo | Hallazgo | Verificado |
|---|-------------|----------|-----------|
| 1 | **Optuna optimiza sobre validación**, no sobre test (elimina data leakage de selección) | C1 | ✅ ejecutado |
| 2 | **Forecast recursivo t+1→t+2** + métricas por horizonte (corrige leakage temporal) | C2 | ✅ |
| 3 | **Baselines** de persistencia y media (demostrar aporte sobre lo trivial) | ML-2 | ✅ |
| 4 | **Semillas globales** + persistencia de `model_xgb.json`/`best_params.json`/`metrics.json` | A3, R1 | ✅ reproducible |
| 5 | **`requirements.txt`** pineado (con `pillow>=12.2.0`) + **`LICENSE`** MIT | R2, S02-2/3/4 | ✅ |
| 6 | **Métricas de ranking/priorización** (Spearman, Precision@K) + **error por segmento** | ML-1, ML-5 | ✅ |
| 7 | **SHAP** (interpretabilidad) | WEB-6 | ✅ |
| 8 | **Intervalos conformal** (incertidumbre) | WEB-7 | ✅ |
| 9 | **Backtesting rolling-origin** (robustez multi-ventana) | ML-7 | ✅ |
| 10 | Eliminado código muerto (`MultiOutputRegressor`) | D1 | ✅ |

### 3.3 Dashboard — `dashboard/`
App **Streamlit + Plotly** de alerta temprana (verificada con `AppTest`, 0 excepciones):
- KPIs (IES analizadas, en riesgo alto, con tendencia al alza, tasa promedio).
- 🚨 Ranking de IES en riesgo (Top-20 + tabla filtrable).
- 🗺️ Agregado por departamento.
- 🏫 Detalle por IES (serie histórica real + pronóstico).
- Filtros: departamento, carácter, nivel de riesgo, tendencia.

### 3.4 Documentación
`CLAUDE.md`, skill `.claude/skills/datos-ecosistema-2026/`, este `ESTADO_DEL_PROYECTO.md`, y un README actualizado con las métricas honestas.

---

## 4. 📊 Métricas honestas (la historia real)

| Vista | Resultado | Lectura |
|-------|-----------|---------|
| Test agregado **antes** (con leakage) | RMSE 9.48 / MAE 4.23 | optimista, irreproducible |
| Test agregado **honesto** | RMSE 10.14 / MAE 4.31 | sube al quitar el leakage |
| **Por horizonte** | t+1: 11.16 (vs persist. 11.48) · t+2: 10.49 (vs 11.19) | el modelo **gana** en ambos |
| **Baselines** (test) | persistencia 10.07 · media 13.51 | persistencia es rival fuerte |
| **Ranking** | **Spearman 0.872** · Precision@50 0.74 | el modelo **ordena muy bien** |
| Riesgo (≥p75) | Precision 0.94 / Recall 0.43 | si marca riesgo, acierta 94% |
| Error por segmento | Universidad MAE 1.66 · Técnica prof. 21.58 | confiable en univ., no en técnicas |
| **Backtesting** (4 cortes) | modelo **7.52 ± 1.60** vs persist. 8.33 ± 1.94 | gana en 3 de 4 → robusto |
| Conformal 90% | banda ±5.2 pp · cobertura 81% en 2024 | algo sobreconfiado en 2024 |

**Conclusión para el jurado:** un modelo **honesto** que igual aporta valor en lo que importa (priorizar) y comunica su incertidumbre, vale más que un 9.48 inflado que se desmonta en 10 minutos.

---

## 5. 🗺️ Estado de cada hallazgo de la auditoría

| ID | Hallazgo | Severidad | Estado |
|----|----------|-----------|--------|
| C1 | Optuna optimiza sobre test | 🔴 Crítica | ✅ **Resuelto** |
| C2 | Sin forecast recursivo | 🔴 Crítica | ✅ **Resuelto** |
| ML-1 | No medía ranking/priorización | 🟠 Alta | ✅ **Resuelto** |
| ML-2 | Sin baseline | 🟠 Alta | ✅ **Resuelto** |
| A3 | No persistía el modelo | 🟠 Alta | ✅ **Resuelto** |
| R1 | Optuna sin semilla | 🟠 Alta | ✅ **Resuelto** |
| R2 | Sin requirements.txt | 🟡 Media | ✅ **Resuelto** |
| S02-2 | Sin LICENSE | 🟠 Alta | ✅ **Resuelto** |
| S02-4 | Pillow vulnerable | 🟡 Media | ✅ **Resuelto** (pin) |
| ML-7 | Validación de un solo semestre | 🟡 Media | ✅ **Resuelto** (backtesting) |
| WEB-6/7 | Sin SHAP / sin intervalos | 🟠 Alta | ✅ **Resuelto** |
| WEB-9 | Sin dashboard/visual | 🟠 Alta | ✅ **Resuelto** |
| D1 | Código muerto | 🟡 Media | ✅ **Resuelto** |
| **DQ-TARGET** | Tasa 138 700% en origen | 🟠 Alta | ⏳ **Pendiente** (PR-6, cascada) |
| **A2** | SettingWithCopyWarning | 🟡 Media | ⏳ **Pendiente** (PR-7) |
| **H1** | CSV 99 MB en historial | 🟠 Alta | ⏳ **Pendiente** (destructivo) |
| A1 | dic/.replace comentado | INFO | ✅ Reclasificado (no era bug) |

---

## 6. ⏳ LO QUE FALTA / QUÉ SIGUE

### 6.1 Técnico — pendiente (necesita decisión del equipo)
| Tarea | Qué implica | Riesgo |
|-------|-------------|--------|
| **Saneamiento de la tasa** (DQ-TARGET) | Re-ejecutar el EDA (CSV 104 MB) y regenerar todo el pipeline | Medio — cambia muchos archivos y los resultados ya verificados |
| **`.copy()` en splits** (A2) | Re-ejecutar `dataset.ipynb` | Bajo, pero puede regenerar los CSV de entrenamiento (drift) |
| **🚨 Sacar el CSV de 99 MB del historial git** (H1) | Reescribir historial + `git push --force` | **Alto / destructivo** — afecta a todos los clones del equipo. **Requiere acuerdo explícito.** |

### 6.2 Mejoras opcionales (suben el techo)
- **Feature engineering**: tendencia (`lag1-lag4`), momentum (`lag1-lag2`), volatilidad, dummy COVID 2020.
- **Mapa coroplético** por departamento en el dashboard (hoy es barra).
- **Ensemble** XGBoost + baseline estadístico (StatsForecast: AutoETS/Theta) — estilo M5.
- **Narrativa de impacto cuantificada**: # IES priorizables, # estudiantes cubiertos.

### 6.3 Entregables del concurso (no técnicos)
- [ ] **Presentación / pitch** del proyecto (Mar lo mencionó en el grupo) — ≤90 s + slides.
- [ ] Conseguir la **rúbrica oficial 2026** (Términos de Referencia) para optimizar la entrega (WEB-2).
- [ ] Confirmar requisitos del equipo (en 2025 se pedía "al menos una mujer" — Mar cumple).
- [ ] Decidir formato del entregable final (notebook + dashboard + informe).

---

## 7. ▶️ Cómo correr todo

```bash
# 1) Entorno (reproducible)
pip install -r requirements.txt

# 2) Pipeline (en orden)
#    Ejecutar EDA_preprocesamiento.ipynb  -> df_forecast_raw.csv
#    Ejecutar dataset.ipynb               -> entrenamiento_csv/*.csv
#    Ejecutar entrenamiento_csv/model.ipynb -> entrena, evalúa, persiste model_xgb.json

# 3) Dashboard
python dashboard/generar_predicciones.py   # genera predicciones_2024.csv desde el modelo
streamlit run dashboard/app.py             # abre en http://localhost:8501
```

## 8. 📂 Estructura del repo (clave)

```text
├── EDA_preprocesamiento.ipynb     # Paso 1: limpieza + cobertura
├── dataset.ipynb                  # Paso 2: ventana deslizante → splits
├── entrenamiento_csv/
│   ├── model.ipynb                # Paso 3: XGBoost + Optuna + evaluación honesta
│   ├── model_xgb.json             # Modelo persistido (A3)
│   ├── best_params.json, metrics.json
│   └── X_*.csv, y_*.csv           # Splits
├── dashboard/                     # App Streamlit + generador de predicciones
├── reports/                       # Auditoría (00..06) + IMPLEMENTACION.md
├── ESTADO_DEL_PROYECTO.md         # ← este documento
├── CLAUDE.md                      # Contexto para Claude Code + skill
├── requirements.txt, LICENSE
└── README.md                      # Doc del proyecto (métricas honestas)
```

## 9. 🔗 Enlaces

- **PR #1 (todo el trabajo):** https://github.com/jonathanpo7/datos_ecosistema_2026/pull/1
- **Rama:** `feat/correcciones-auditoria-2026`
- **Repo:** https://github.com/jonathanpo7/datos_ecosistema_2026

## 10. 🧠 Decisiones clave (por qué)

- **Subir el RMSE fue lo correcto:** 9.48 era falso (leakage). 10.14 es el desempeño real. La honestidad metodológica es una ventaja ante el jurado, no una debilidad.
- **El valor del modelo se reposicionó hacia la priorización** (Spearman 0.872), porque en error promedio agregado empata con la persistencia, pero en *ordenar* IES y por horizonte/backtesting sí aporta.
- **No se tocó `main` ni se reescribió el historial:** todo va por PR para que el equipo revise; lo destructivo (CSV de 99 MB) espera acuerdo.

# 00 — INFORME MAESTRO DE AUDITORÍA
## Datos al Ecosistema 2026 — Forecast de deserción por IES (SNIES/MEN)

**Proyecto:** Modelo XGBoost + Optuna que predice la tasa de deserción por Institución de Educación Superior (IES) en Colombia para el año siguiente (semestres `t+1` y `t+2`), con series del SNIES (MEN).
**Repositorio:** `datos_ecosistema_2026` · remoto público `github.com/jonathanpo7/datos_ecosistema_2026` (rama `main`) · auditoría en rama `chore/auditoria-inicial`.
**Pipeline:** `EDA_preprocesamiento.ipynb` → `dataset.ipynb` → `entrenamiento_csv/model.ipynb`. Split temporal: train ≤ 2023-1 · val = 2023-2 · test = 2024.
**Métrica titular (README):** RMSE 9.48 / MAE 4.23.
**Rol de este documento:** Consolidación de los 6 informes de auditoría (ML, Seguridad, Web, Ideas, Debate, MLOps).
**Alcance:** 100% lectura. No se ejecutaron notebooks ni se modificó el repo. No se leyó completo el CSV de 104 MB.
**Fecha:** 2026-06-28.

> **Nota de procedencia.** La carpeta `EX/` con extractos de código (`code_*.txt`, `data_profile.txt`) mencionada en el encargo **no existe en este checkout**. Todas las citas archivo-celda-línea se construyeron y validaron leyendo directamente los notebooks reales (`model.ipynb`, `dataset.ipynb`, `EDA_preprocesamiento.ipynb`) sin ejecutarlos, más `git ls-files`/`git log` y lectura de los CSV de split ya generados. La numeración de celdas es 0-based (markdown + código); la celda "objective + Optuna" es la celda 9, consistente con C1 en README/CLAUDE.md.

---

## 1. Resumen ejecutivo

El proyecto tiene una **narrativa de política pública excelente** (README de primer nivel) y un **esqueleto técnico conceptualmente sólido**: split temporal correcto en concepto, manejo defensivo de NaN (`min_count=1`), alineación de categorías train→val/test (`set_categories`), diagnóstico de cobertura riguroso (≥ 20 períodos sin huecos) y `early_stopping` correctamente sobre validación. **Pero la métrica titular 9.48 / 4.23 no es honesta** y, tal como está, **un jurado técnico la descarta**.

Tres problemas invalidan las métricas actuales:

1. **C1 — Optuna optimiza sobre el TEST (data leakage).** En `model.ipynb · celda 9`, `objective()` retorna `RMSE(y_test, predict(x_test))`; con `direction='minimize'` y 100 trials, los hiperparámetros se eligen mirando el test. El README (L78, L89) afirma lo contrario. El 9.48/4.23 es métrica de test contaminada por *winner's curse*.
2. **C2 — No existe forecast recursivo t+1→t+2.** El test de 2024-2 usa la tasa **real** de 2024-1 como `lag1` (verificado: 264/264 casos). El encadenamiento recursivo que promete el README (L76) no se implementa, regalando el semestre intermedio y subestimando el error de t+2 — justo el horizonte de planeación de política pública.
3. **ML-2 / QW-1 — Sin baseline naive, el aporte es marginal.** Reproducido sobre los splits reales: la **persistencia** (`y = lag1`) da TEST RMSE 10.07 / MAE 4.42 y, en validación, 8.18 (mejor que el test publicado del modelo). El modelo con fuga apenas mejora ~0.6 RMSE sobre algo trivial sin entrenar.

**Veredicto de competitividad:** proyecto con **alto techo pero no presentable en su estado actual**. La corrección de C1 son ~2 líneas y blinda toda la credibilidad; añadir baseline y evaluación recursiva honesta + reformular como priorización/ranking (Precision@K) lo convierte en un candidato fuerte. Higiene de repo (CSV de 99 MB en historial, sin LICENSE, sin requirements) y reproducibilidad (Optuna sin semilla, modelo no persistido) son must-fix de bajo costo. **Sin PII de personas naturales** (solo agregados públicos del SNIES); sin secretos en el árbol ni en el historial.

---

## 2. Tabla única de hallazgos (priorizada por severidad)

> IDs deduplicados: varios hallazgos llegaron por más de un agente (p. ej. `R1`, `R2`, `A2`, `A3`, `H1`, leakage, baseline, clip). Se consolidan en una fila canónica con la fuente combinada. **Reclasificaciones:** `A1` (departamentos) se confirma como **código muerto, no bug**; `NUEVO-ML-1` (clip pre-split) se **descarta como leakage**. Orden: CRÍTICA → ALTA → MEDIA → BAJA → INFO → BIEN.

| ID | Sev | Categoría | Hallazgo | Ubicación | Fix | Fuente |
|----|-----|-----------|----------|-----------|-----|--------|
| **C1 / QW-2** | 🔴 CRÍTICA | Data leakage / selección | Optuna selecciona hiperparámetros minimizando RMSE de **TEST**, no de validación. README L78/L89 dicen lo contrario (falso). | `model.ipynb · celda 9` (`objective`: `predict(x_test)`, `return RMSE(y_test,…)`; `create_study(minimize)`, `n_trials=100`) | En `objective()` usar `x_val/y_val`; elegir `best_params` por val; tocar test una sola vez al final; `TPESampler(seed=42)`; corregir README L78/L89 | 01-ML, 04-Ideas |
| **C2** | 🔴 CRÍTICA | Leakage temporal / horizonte | No hay forecast recursivo t+1→t+2: 2024-2 usa la tasa **real** de 2024-1 como `lag1` (264/264). One-step evalúa 529 filas a la vez. | `dataset.ipynb · celda ventana` (id e7bb2962, L432-436) y `celda split` (id 83a85286, L999); `model.ipynb` celdas 7/9/10 | Evaluación recursiva: predecir 2024-1; construir 2024-2 con `lag1` = predicción; reportar RMSE/MAE separados por h=1 y h=2 vs persistencia equivalente | 01-ML, 06-MLOps |
| **IMP-1** | 🟠 ALTA | Impacto / cuantificación | La métrica honesta será **peor** que 9.48/4.23 por efectos acumulativos (C1 winner's curse + C2 recursivo + test condicionado a cobertura). Mayor deterioro en t+2. | Síntesis de C1, C1b/C1c, C2, NUEVO-ML-4 | Re-medir bajo protocolo honesto y reportar tabla RMSE/MAE de val, test t+1 y test t+2; corregir README L76/78/89 | 01-ML |
| **ML-1 / DIF-RANK** | 🟠 ALTA | Validez métrica / caso de uso | RMSE/MAE de regresión **no miden** la tarea real (priorizar/rankear IES en riesgo). Sin Precision@K/Recall@K, Spearman/Kendall. La rama "clasificación por comportamiento" del README nunca se implementa. | `model.ipynb` celdas 7 y 10; `README.md` L16-23, 41-45 | Definir umbral de riesgo; reportar precision/recall/F1, Precision@K y Recall@K (K=20,50), Spearman/Kendall sobre **validación**; mantener RMSE/MAE como secundarias | 01-ML, 04-Ideas |
| **ML-2 / QW-1** | 🟠 ALTA | Validez métrica / baseline | Sin baseline de persistencia. Reproducido: persistencia TEST 10.07/4.42, VAL 8.18/3.15; media TEST 13.47/7.93. El modelo (con fuga) da 9.48-9.51. Mejora real ~0.6 RMSE. | `model.ipynb · celda 5` (el "baseline" es un XGBoost de 500 árboles) y `celda 7`; `README.md` L82-97 | Añadir baseline persistencia (`y_pred = X['lag1']`) y de media con mismo protocolo/splits; reportar en README; afirmar valor solo si bate persistencia en val/backtesting | 01-ML, 04-Ideas |
| **C1c** | 🟠 ALTA | Data leakage / evaluación | El modelo final reentrena con `best_params` contaminados (C1) y vuelve a medir en test. Inconsistencia de clip vs baseline. | `model.ipynb · celda 10` (id 057d742d, L1355-1371: `best_params=study.best_params`, `clip(predict(x_test),0,100)`) | Unificar clip; reportar métrica final una sola vez tras fijar HP por val; persistir `best_params` y modelo | 01-ML |
| **DQ-TARGET / DIF-DQ** | 🟠 ALTA | Construcción del target | La tasa no está acotada en origen: llega a **138700%** por denominador=1 (artefactos SNIES). 153 filas >100% en `df_forecast_raw.csv`. Clip aplicado tarde. | `EDA_preprocesamiento.ipynb · celda 12` (L767-768, `np.where(MAT>0, DES/MAT*100, nan)`); `df_forecast_raw.csv`; clip tardío `dataset.ipynb · celda 15` (L806) | Sanear en el EDA antes de exportar: NaN/descartar filas con `MATRICULADOS < umbral` (5-10) o `tasa>100`; recalcular cobertura; documentar/winsorizar | 01-ML, 04-Ideas |
| **A3** | 🟠 ALTA | Reproducibilidad / MLOps | No se persiste el modelo ni `best_params` (sin `.pkl/.json/.ubj/.joblib`). `git ls-files` no lista artefactos. | `model.ipynb · celda 9` (solo `print` best_params) y `celda 10` (modelo no serializado) | `modelo_final.save_model(...)`; `json.dump(study.best_params,…)`; versionar artefacto + params junto al número reportado; `predict.py` que cargue el modelo | 01-ML, 06-MLOps |
| **R1** | 🟠 ALTA | Reproducibilidad | Optuna sin sampler con semilla; `np.random.seed` no fijado → `best_params`/métrica no reproducibles. XGB sí fija `random_state=42`. README 9.48/4.23 vs notebook 9.51/4.16. | `model.ipynb · celda 9` (L1332, `create_study(direction='minimize')` sin `sampler=`) | `np.random.seed(42)`; `random.seed(42)`; `sampler=TPESampler(seed=42)`; documentar versión de Optuna | 01-ML, 06-MLOps |
| **R2 / S02-3** | 🟠 ALTA | Reproducibilidad / dependencias | Sin `requirements.txt`/lock; versiones no pineadas (única referencia: README L125, sin versiones). Cadena de suministro no auditable (xgboost/optuna ni instalados al auditar). | raíz del repo; `README.md` L125 | `pip freeze` → `requirements.txt` pineado (incl. jupyter); lockfile (uv/poetry); documentar versión de Python; re-`pip-audit` sobre venv aislado | 06-MLOps, 02-Seg |
| **A2** | 🟠 ALTA | Bug pandas / fragilidad | `SettingWithCopyWarning`: los 3 splits se crean por slicing booleano sin `.copy()` y luego se les asignan columnas. Funciona "por suerte". | `dataset.ipynb · celda split` (L997-999) y disparadores celda 21 (L1134-1136) / celda 23 (L1214-1216) | Crear splits con `.copy()`: `train = dataset[mask].copy()` (idem val, test) | 01-ML, 06-MLOps |
| **H1 / S02-1** | 🟠 ALTA | Higiene repo / exposición | CSV de **99 MB** versionado y en el historial (commit 077d606); `.gitignore` no lo cubre. Al borde del límite de 100 MB de GitHub, en remoto público. | `MEN_MATRICULA_ESTADISTICA_ES_20260519.csv` (104.054.678 bytes, ~390.904 filas) | `git rm --cached` + patrón en `.gitignore`; limpiar historial (`git filter-repo`/BFG, coordinar force-push); externalizar con DVC/enlace SNIES | 06-MLOps, 02-Seg |
| **S02-2 / H4** | 🟠 ALTA | Legal | Ausencia de `LICENSE` → código bajo "todos los derechos reservados" por defecto; contradice un concurso de datos abiertos y puede contravenir las bases. | raíz del repo | Añadir `LICENSE` (MIT/Apache-2.0) para el código; declarar por separado licencia/términos de los datos SNIES; revisar bases del concurso | 02-Seg, 06-MLOps |
| **QW-3** | 🟠 ALTA | Estrategia ML / producto | Solo MAE/RMSE global; el target tiene cola pesada (media 14.57, mediana 10.85, std 13.47, max 100). El error global esconde heterogeneidad. | `df_forecast_raw.csv`; `model.ipynb · celda 11` (solo importancia global) | `groupby` del error absoluto por DEPARTAMENTO, CARACTER y cuartiles de MATRICULADOS; mapa de confiabilidad + narrativa por segmento | 04-Ideas |
| **C1b** | 🟡 MEDIA | Data leakage / evaluación | El baseline también reporta su métrica sobre TEST (`y_pred_test`); el clip a val está comentado. Comparación baseline-vs-final es test-contra-test. | `model.ipynb · celda 7` (id ffff5d67, L1160-1164) | Evaluar el baseline sobre `x_val/y_val`; reservar el test para una única medición final | 01-ML |
| **DQ-CLIP-ORDEN / ML-9 / CL1** | 🟡 MEDIA | Construcción de features / consistencia | Clip `[0,100]` aplicado a lags/target **después** de construir las ventanas y **inconsistente** (baseline sin clip, modelo final con clip). El mismo dato vale 138700% en `df_forecast_raw.csv` y 100% en X_train. | `dataset.ipynb · celda ventana` (lags sin clip) y `celda 15` (L806); `model.ipynb` celda 7 (clip comentado) vs celda 10 (clip aplicado) | Mover el saneamiento al EDA antes de exportar; aplicar clip idéntico (o ninguno) en todas las celdas de evaluación, incl. baseline naive; documentar el post-proceso una vez | 01-ML, 04-Ideas |
| **DQ-COBERTURA-SESGO** | 🟡 MEDIA | Sesgo de selección | El filtro de cobertura (≥20 períodos) es correcto pero introduce sesgo de supervivencia: 343→277 aptas (descarta 46 por hueco interno, 20 por serie corta). El modelo solo ve IES grandes/antiguas/estables. | `EDA_preprocesamiento.ipynb · celda 13` (UMBRAL=20) y `celda 15` (filtro 'apta') | Documentar cobertura 277/343 y perfilar excluidas; considerar imputar huecos de 1 período, bajar UMBRAL; métricas estratificadas por tamaño/carácter | 01-ML |
| **DQ-MOJIBAKE** | 🟡 MEDIA | Encoding / mojibake | Mojibake del SNIES ("Instituci?n", "Sin informaci?n") contamina CARACTER/ORIGEN/SEXO, que SÍ son features del modelo (DEPARTAMENTO/MUNICIPIO se salvan por `limpieza_total`). | `Ies_dept_muni_sex_car_orig.csv` → `df_forecast_raw.csv` → features categóricas de `dataset.ipynb` | Releer CSV con encoding correcto (latin-1/utf-8) o mapear CARACTER/SEXO a forma legible; aplicar `limpieza_total` también a CARACTER/ORIGEN/SEXO | 01-ML, 04-Ideas |
| **ML-5** | 🟡 MEDIA | Interpretación de métricas | "RMSE/MAE cercano a 2 es saludable" es engañoso: 2.24 señala cola pesada/outliers, no buena salud (para errores ~normales el ratio ~1.25). | `README.md` L83, 95-97; `dataset.ipynb` describe | Reemplazar la heurística por análisis de residuales: histograma, error por cuartil de tasa, métricas robustas (MdAE, P90 del error absoluto) | 01-ML |
| **ML-6** | 🟡 MEDIA | Comunicación de métricas | "Margen 28-40% relativo" es aritméticamente consistente pero engañoso: divide error en puntos por nivel agregado, denominador elegido a mano, MAE contaminado. | `README.md` L97 | Error relativo POR IES (distribución/percentiles) o por estrato de tasa; recalcular tras corregir C1/C2 | 01-ML |
| **ML-7** | 🟡 MEDIA | Protocolo de validación | Validación de un solo semestre (val=2023-2, n=265) y un solo año de test → alta varianza. Persistencia: VAL 8.18 vs TEST 10.07. | `dataset.ipynb · celda split`; `model.ipynb · celda 9`; `README.md` L77 | Backtesting rolling-origin/expanding-window: validar 2022-1, 2022-2, … agregando RMSE/MAE (media+desv) vs persistencia; reservar 2024 como holdout final | 01-ML |
| **H2 / S02-5** | 🟡 MEDIA | Higiene repo | `.gitignore` (plantilla Python estándar, 219 líneas) presente pero **no** ignora `*.csv`/datos → datos versionados pese a tener `.gitignore`. | `.gitignore` | Añadir bloque de datos: `MEN_*.csv`, `df_forecast_raw.csv`, `entrenamiento_csv/*.csv`, `*.parquet`, artefactos de modelo, `CLAUDE.md` | 06-MLOps, 02-Seg |
| **H3** | 🟡 MEDIA | Higiene repo | Notebooks con outputs versionados; ruta de usuario filtrada (`C:/Users/Jonathan Piedrahita/…` en outputs de `dataset.ipynb`). | `dataset.ipynb`, `EDA_…ipynb`, `model.ipynb` | `nbconvert --clear-output --inplace` y/o `nbstripout` como filtro git/pre-commit; export HTML/PDF aparte para gráficas | 06-MLOps |
| **S02-4** | 🟡 MEDIA | Dependencias vulnerables | `pillow` 11.3.0 (transitiva de matplotlib) con 6 CVEs. Resto del stack ML sin vulnerabilidades. Impacto real bajo (no procesa imágenes no confiables). | Entorno Python (pillow 11.3.0) | Fijar `pillow>=12.2.0` en `requirements.txt` | 02-Seg |
| **D1** | 🟡 MEDIA | Código muerto | `MultiOutputRegressor` importado y nunca usado (vestigio de la idea multi-salida t+1/t+2 que nunca se implementó → se conecta con C2). | `model.ipynb · celda 1` | Eliminar el import; si se quiere t+1→t+2 real, implementar encadenamiento recursivo (C2) | 06-MLOps |
| **R3** | 🔵 INFO/MEDIA | Reproducibilidad | Orden de ejecución frágil entre notebooks (sin orquestador); `model.ipynb` lee CSVs versionados que pueden estar desactualizados respecto al EDA/dataset. | repo (3 notebooks encadenados por CSVs en disco) | `Makefile`/`run_pipeline.py` que ejecute los 3 pasos con checksums/timestamps; CI ligero sobre muestra | 06-MLOps |
| **NUEVO-ML-4** | 🔵 BAJA | Sesgo de selección | La cobertura ≥20 evaluada incluyendo 2024 condiciona el test a IES con reporte completo en el año objetivo (sesgo, no leakage de valor). No cuantificable sin reejecutar EDA. | `EDA_…ipynb` celdas 13/15 → `df_forecast_raw.csv` | Definir elegibilidad solo con info hasta el corte (≥20 hasta 2023-2) y evaluar sobre todas las elegibles, o documentar la condición | 01-ML |
| **D2** | 🔵 BAJA | Código muerto | `periodo_num` calculado y no usado; el orden temporal depende de `sort_values` sobre strings 'YYYY-S' (frágil). | `dataset.ipynb · celda 5` | Eliminar `periodo_num` o usarlo: `sort_values(['IES','periodo_num'])` | 06-MLOps |
| **D3** | 🔵 BAJA | Código muerto | `cargar_csv.py` script huérfano (6 líneas, `print(df.head())`), fuera del pipeline. | `cargar_csv.py` (raíz) | Eliminar o mover a `scratch/` excluida | 06-MLOps |
| **H5** | 🔵 BAJA | Higiene repo | CSVs intermedios huérfanos versionados (`programa.csv`, `valle_.csv`, `icetex.csv`, etc.) no documentados en el pipeline. | raíz del repo | Mover insumos a `data/raw/` y derivados a `data/processed/` ignoradas; documentar qué genera cada uno | 06-MLOps |
| **S02-6** | 🔵 BAJA | Privacidad | NIT/Dirección/Teléfono de **instituciones** (personas jurídicas, registro público SNIES) en `MEN_INSTITUCIONES`. No PII de personas naturales; el modelo no usa estas columnas. | `MEN_INSTITUCIONES_EDUCACIÓN_SUPERIOR_20260520.csv` | Opcional: omitir columnas de contacto del repo público (no necesarias para el pipeline) | 02-Seg |
| **S02-8** | 🔵 BAJA | Higiene / exposición | `CLAUDE.md` no rastreado en el working tree (riesgo de commit accidental). | `CLAUDE.md` (untracked) | No commitearlo; añadir a `.gitignore`; revisar contenido antes de cualquier `git add` | 02-Seg |
| **CA1** | ⚪ INFO | Modelado / cardinalidad | MUNICIPIO (67 cats) actúa como proxy de identidad de IES (metadata por `groupby('IES').first()`). No es bug (0 unseen en val/test) pero el desempeño está condicionado a IES ya vistas (no zero-shot). | `model.ipynb · celda 4`; `dataset.ipynb · celda 9` | Documentar que solo predice IES con historial; revisar importancia de MUNICIPIO; regularizar/agrupar municipios raros; un split por IES revelaría la generalización real | 01-ML |
| **DQ-NAN-INERTE** | ⚪ INFO | Manejo de faltantes | El manejo de NaN (`min_count=1` + `np.where`) es correcto pero **inerte**: 0 NaN en la práctica (el filtro de cobertura ya elimina huecos). | `EDA_…ipynb` celdas 11-12 | Mantener (correcto y barato); opcional `assert`/`print` de cuántos NaN se preservaron; no sobre-vender en README | 01-ML |
| **A1** | ⚪ INFO | Normalización (reclasificado) | El `dic` de departamentos + `.replace()` **comentado** es código muerto, **NO** genera duplicados (salida real ya limpia; claves del dic no coinciden). Falso positivo descartado. | `EDA_…ipynb · celda 5` (L290 dic, L291 replace comentado) | Eliminar el bloque (código muerto) o reconstruir el `dic` con claves correctas y aplicarlo; hoy innecesario | 01-ML |
| **NUEVO-ML-1** | ⚪ INFO | Preprocesamiento (descartado) | El clip global `[0,100]` antes del split **NO** es leakage (límites constantes, no parámetros estimados). Falso positivo descartado. | `dataset.ipynb · celda 15` (L806) | Mantener el clip pero aplicarlo de forma consistente (ver DQ-CLIP-ORDEN) | 01-ML |
| **S02-7** | ⚪ INFO | Secretos | detect-secrets: 8 falsos positivos (PNG base64 embebidos en notebooks, cabecera `iVBORw0KGgo`). 8/8 falsos. | notebooks varios | Generar `.secrets.baseline` excluyendo CSVs; `nbstripout` antes de commitear | 02-Seg |
| **S02-10** | ⚪ INFO | Secretos / historial | Historial git (5 commits) sin secretos reales (solo falsos positivos léxicos). Limitación: `gitleaks`/`trufflehog` no instalados. | `.git` | Si se requiere garantía formal, instalar gitleaks/trufflehog; integrar detect-secrets como pre-commit | 02-Seg |
| **INT-1** | 🟢 BIEN | Validación temporal | Split temporal sin solapamiento de filas (IES,período) entre train/val/test (intersección = 0). No tocar. | `dataset.ipynb · celda split` | Ninguno; solo añadir evaluación recursiva (C2) y mover selección de HP a val (C1) | 01-ML |
| **NUEVO-ML-2 / B1** | 🟢 BIEN | Preprocesamiento / encoding | Sin scaler/encoder global; alineación de categorías train→val/test correcta (`set_categories`, 0 unseen). No hay fuga por preprocesamiento. | `dataset.ipynb`; `model.ipynb · celda 4` | Ninguno; opcional mover `set_categories(train)` a `dataset.ipynb` por coherencia | 01-ML |
| **NUEVO-ML-3** | 🟢 BIEN | Definición de target/features | El target no se deriva de las features: lags y target son la misma serie desplazada. Sin fuga clásica de feature que codifica el target. | `dataset.ipynb · celda ventana` | Ninguno | 01-ML |
| **DQ-DEDUP** | 🟢 BIEN | Consolidación / duplicados | Consolidación por IES+período correcta: 0 duplicados; metadata `.first()` segura (cada IES con un único DEPTO/MUNI/CARACTER/ORIGEN). | `EDA_…ipynb · celda 12`; `dataset.ipynb · celda metadata` | Nada; opcional asserts de unicidad y merge 1:1 | 01-ML |
| **ML-10** | 🟢 BIEN | Buenas prácticas | Split temporal correcto en concepto y `early_stopping` sobre validación. El problema no es el split sino la selección de HP (C1). | `dataset.ipynb · celda split`; `model.ipynb` celdas 5 y 9 | No tocar la lógica del split ni `eval_set`; corregir solo C1 y C2 | 01-ML |
| **B2** | 🟢 BIEN | Higiene repo | `.gitignore` plantilla Python estándar presente (cubre entornos/caches). Única carencia: patrones de datos (H2). | `.gitignore` | Complementar con patrones de datos; mantener la base | 06-MLOps |
| **S02-9** | 🟢 BIEN | Privacidad | Sin PII de personas naturales (minimización de datos): granularidad mínima = conteos agregados; artefactos usan código SNIES + categóricos geográficos. | CSVs de matrícula y entrenamiento | Mantener el diseño | 02-Seg |

---

## 3. Plan de acción — ramas/PRs sugeridos (sin ejecutar)

> Convención: `fix/…` correcciones de leakage/bugs · `feat/…` baselines, métricas, features · `chore/…` higiene/reproducibilidad. **Toda corrección de código va sobre rama, nunca sobre `main`.** Orden recomendado: primero lo que invalida la métrica (PR-1, PR-2, PR-3), luego lo que la hace defendible (PR-4, PR-5), luego higiene/reproducibilidad (PR-6 a PR-9). Las mejoras de diferenciación (PR-10, PR-11) son opcionales pero suben el techo competitivo.

### MUST-FIX antes de presentar al concurso

**PR-1 · `fix/optuna-objective-validacion` — Eliminar el leakage de selección (C1, C1b, C1c, QW-2)**
- **Objetivo:** que Optuna optimice sobre validación y el test se toque una sola vez.
- **Archivos:** `entrenamiento_csv/model.ipynb` (celdas 5, 7, 9, 10); `README.md` (L78, L89).
- **Cambios:** en `objective()` reemplazar `x_test/y_test` por `x_val/y_val`; seleccionar `best_params` por val; reentrenar y medir test **una vez**; evaluar también el baseline sobre val; corregir el texto del README.
- **Aceptación:** ninguna celda de tuning referencia `x_test/y_test`; el README describe el protocolo real; se reporta RMSE de val (selección) y RMSE de test (una vez).
- **Orden:** 1 (bloqueante; ~2 líneas, máximo impacto).

**PR-2 · `feat/forecast-recursivo-t1-t2` — Evaluación recursiva honesta (C2, D1)**
- **Objetivo:** implementar el encadenamiento t+1→t+2 que promete el README y reportar por horizonte.
- **Archivos:** `entrenamiento_csv/model.ipynb`; opcionalmente `dataset.ipynb` (construcción de la fila 2024-2 con `lag1`=predicción); `README.md` (L76).
- **Cambios:** predecir 2024-1 con lags reales; construir 2024-2 con `lag1` = predicción de 2024-1 (desplazar lag2..lag4); reportar RMSE/MAE separados h=1 y h=2 vs persistencia equivalente; eliminar el import muerto `MultiOutputRegressor`.
- **Aceptación:** tabla con métricas h=1 y h=2; el test de 2024-2 ya no usa la tasa real de 2024-1.
- **Orden:** 2.

**PR-3 · `feat/baseline-persistencia` — Baselines naive (ML-2, QW-1, ML-9)**
- **Objetivo:** demostrar que el modelo aporta sobre lo trivial.
- **Archivos:** `entrenamiento_csv/model.ipynb`; `README.md` (tabla de resultados).
- **Cambios:** baseline de persistencia (`y_pred = X['lag1']`) y de media, con mismo protocolo/splits y mismo post-proceso (clip idéntico o ninguno); tabla comparativa modelo vs persistencia vs media en val y test.
- **Aceptación:** README muestra la tabla; la afirmación de valor solo se sostiene si el modelo bate la persistencia en validación.
- **Orden:** 3.

**PR-4 · `chore/persistir-modelo-y-semillas` — Reproducibilidad mínima (A3, R1)**
- **Objetivo:** que el número publicado sea reproducible y auditable.
- **Archivos:** `entrenamiento_csv/model.ipynb`; nuevos `model_xgb.json`, `best_params.json`, `metrics.json`.
- **Cambios:** `np.random.seed(42)` + `random.seed(42)` + `TPESampler(seed=42)`; `save_model` + `json.dump(best_params/metrics)`.
- **Aceptación:** dos corridas dan el mismo `best_value`; artefactos presentes.
- **Orden:** 4 (tras PR-1 para que la semilla aplique al objective correcto).

**PR-5 · `chore/requirements-y-licencia` — Dependencias y legal (R2, S02-3, S02-4, S02-2/H4)**
- **Objetivo:** entorno reproducible y código legalmente reutilizable (requisito típico de concurso).
- **Archivos:** nuevo `requirements.txt` (pineado, incl. jupyter, `pillow>=12.2.0`), `LICENSE` (MIT/Apache-2.0), nota de licencia de datos SNIES en `README.md`.
- **Aceptación:** `pip install -r requirements.txt` reconstruye el entorno; existe `LICENSE`; bases del concurso revisadas.
- **Orden:** 5.

### Mejoras (suben el techo, no bloqueantes para presentar)

**PR-6 · `fix/data-quality-target-y-encoding` — Saneamiento en el EDA (DQ-TARGET, DQ-CLIP-ORDEN, DQ-MOJIBAKE, DIF-DQ)**
- **Archivos:** `EDA_preprocesamiento.ipynb`, `dataset.ipynb`, `df_forecast_raw.csv` (regenerado).
- **Cambios:** filtrar/NaN tasas absurdas por umbral de `MATRICULADOS` antes de exportar; clip unificado en un único punto; reparar encoding de CARACTER/ORIGEN/SEXO.
- **Aceptación:** `df_forecast_raw.csv` sin tasas >100%; categorías legibles; clip consistente EDA↔dataset↔model.

**PR-7 · `fix/dataframe-copy-warnings` — Robustez pandas (A2)**
- **Archivos:** `dataset.ipynb` (celda split). **Cambios:** `.copy()` en los 3 splits. **Aceptación:** sin `SettingWithCopyWarning`.

**PR-8 · `feat/metricas-ranking-y-error-por-segmento` — Adecuación al caso de uso (ML-1, DIF-RANK, QW-3, ML-5, ML-6)**
- **Archivos:** `entrenamiento_csv/model.ipynb`; `README.md`.
- **Cambios:** Precision@K/Recall@K, Spearman/Kendall sobre val; error absoluto por DEPARTAMENTO/CARACTER/cuartil de MATRICULADOS; reemplazar la heurística RMSE/MAE≈2 y el "28-40% relativo" por análisis de residuales/error por IES.
- **Aceptación:** README con narrativa "dónde confiar" y métricas de ranking.

**PR-9 · `chore/higiene-repo-y-historial` — Limpieza de repo (H1/S02-1, H2/S02-5, H3, H5, D2, D3, S02-8)**
- **Archivos:** `.gitignore`, notebooks (clear-output), eliminación de `cargar_csv.py`/`periodo_num`, reorganización `data/`.
- **Cambios:** `git rm --cached` del CSV 99 MB; `.gitignore` con patrones de datos y `CLAUDE.md`; `nbstripout`; **reescritura de historial (`git filter-repo`/BFG) coordinada con el equipo y force-push**.
- **Aceptación:** `git ls-files` sin CSVs pesados; clone ligero; outputs limpios.
- **Nota:** la reescritura de historial es destructiva — coordinar con el dueño del remoto (`jonathanpo7`).

**PR-10 · `feat/backtesting-rolling` — Validación robusta (ML-7, NUEVO-ML-4, DQ-COBERTURA-SESGO)**
- **Archivos:** `model.ipynb`, `dataset.ipynb`, `README.md`. **Cambios:** rolling-origin sobre varios semestres; documentar cobertura 277/343 y sesgo de supervivencia; métricas estratificadas.

**PR-11 · `chore/orquestador-pipeline` — Encadenamiento reproducible (R3)**
- **Archivos:** nuevo `run_pipeline.py`/`Makefile`. **Cambios:** ejecutar EDA→dataset→model en orden con checksums.

---

## 4. Índice de los informes detallados

| # | Archivo | Rol | Contenido |
|---|---------|-----|-----------|
| 00 | `reports/00_INFORME_MAESTRO.md` | **Líder de auditoría** | Este documento: consolidación, tabla única, plan de PRs |
| 01 | `reports/01_codigo_ml.md` | Código y Machine Learning | Leakage (C1/C2), baselines reproducidos, data quality del target, métricas, hallazgos BIEN |
| 02 | `reports/02_seguridad.md` | Seguridad y privacidad | Secretos (falsos positivos), PII (solo institucional), dependencias (pillow), higiene de exposición |
| 03 | `reports/03_investigacion_web.md` | Investigación web | Existencia/reglas del concurso (criterios: impacto, escalabilidad, uso estratégico del dato), estado del arte, gap analysis |
| 04 | `reports/04_ideas_ganar.md` | Estrategia / ML product | Quick wins (baseline, leakage, error por segmento), diferenciadores (ranking/Precision@K) |
| 05 | `reports/05_debate.md` | Debate adversarial / Council | Posturas a favor/en contra de "puede ganar"; veredicto del juez y must-fix |
| 06 | `reports/06_mlops_reproducibilidad.md` | MLOps / reproducibilidad | Semillas, persistencia, requirements, .gitignore, historial git, orquestación |

---

## 5. Cierre

El proyecto **no es presentable hoy** porque su número estrella está contaminado, pero está **a pocos PRs de ser competitivo**: los tres must-fix de credibilidad (PR-1 leakage, PR-2 recursivo, PR-3 baseline) son de bajo a medio esfuerzo y de impacto crítico. Lo que está bien hecho (split temporal, NaN, `set_categories`, cobertura, README) es base sólida que **no debe romperse** al corregir. Recomendación: ejecutar PR-1 a PR-5 antes de cualquier entrega, y PR-6 a PR-11 para maximizar la puntuación en impacto, escalabilidad y uso responsable del dato.

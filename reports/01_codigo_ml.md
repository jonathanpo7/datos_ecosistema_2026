# Informe de Auditoría — Código y Machine Learning
## Modelo de predicción de tasa de deserción por IES — "Datos al Ecosistema 2026"

**Alcance:** Pipeline `EDA_preprocesamiento.ipynb` → `dataset.ipynb` → `entrenamiento_csv/model.ipynb` (XGBoost + Optuna). Split temporal: train ≤ 2023-1, val = 2023-2, test = 2024-1/2024-2. README reporta RMSE 9.48 / MAE 4.23.

**Método:** Auditoría de solo lectura sobre los notebooks reales del repositorio (la carpeta `EX/` con extractos no existe en este checkout; se verificó directamente sobre los `.ipynb`, sin ejecutarlos). Las métricas de baseline se reprodujeron de forma independiente leyendo los CSV de split ya generados (`entrenamiento_csv/*.csv`), sin reentrenar ni ejecutar los notebooks.

---

## Veredicto ejecutivo

El esqueleto del proyecto es sólido (split temporal correcto en concepto, manejo defensivo de NaN, alineación de categorías, diagnóstico de cobertura riguroso, README excelente). **Pero la métrica titular 9.48 / 4.23 NO es honesta** por dos fugas confirmadas que se refuerzan entre sí:

1. **Fuga de selección de modelo (C1):** Optuna optimiza los hiperparámetros **minimizando el RMSE del propio conjunto de TEST**, no de validación. Los 100 ensayos se evalúan contra el test y se elige el mejor. El README (líneas 78 y 89) afirma lo contrario, y es falso respecto al código.
2. **Fuga temporal de horizonte (C2):** No existe el forecast recursivo t+1→t+2 que promete el README (línea 76). El semestre 2024-2 se evalúa usando la tasa **REAL** de 2024-1 como `lag1`, regalando el valor intermedio que en producción no se conocería.

Además, **el modelo apenas supera a un baseline trivial de persistencia** (`y = lag1`): en test mejora ~0.6 RMSE (y eso ya inflado por la fuga); en validación la persistencia (RMSE 8.18) es **mejor** que la métrica de test publicada. Tras corregir las fugas, es plausible que el modelo no aporte valor frente a no hacer nada.

**Impacto para política pública:** Las secretarías de educación tomarían decisiones de priorización creyendo un margen de error de ~4.23 pp homogéneo, cuando el margen honesto es mayor, está concentrado en las IES de tasa alta (las "en riesgo", justo las que más importan) y se degrada en el horizonte t+2 (el semestre de planeación real).

---

## Tabla resumen de hallazgos

| ID | Severidad | Categoría | Título | Ubicación | Estado |
|----|-----------|-----------|--------|-----------|--------|
| C1 / ML-3 | **CRÍTICA** | Data leakage (selección) | Optuna minimiza RMSE de TEST, no de validación | model.ipynb celda 9 (id 7e313e16) L28-32 | Confirmado |
| C2 / ML-4 | **CRÍTICA** | Leakage temporal | No hay forecast recursivo; 2024-2 usa lag real de 2024-1 | dataset.ipynb e7bb2962 / 83a85286; model.ipynb | Confirmado |
| ML-1 | ALTA | Validez métrica | RMSE/MAE no miden la tarea real (ranking/priorización) | model.ipynb celdas 7/10; README L16-23 | Confirmado |
| ML-2 | ALTA | Baseline | Sin baseline naive de persistencia; aporte marginal | model.ipynb celda 5/7; README L82-97 | Confirmado |
| C1c | ALTA | Leakage / evaluación | Modelo final reentrena con best_params contaminados | model.ipynb celda 10 (id 057d742d) L16-18 | Confirmado |
| DQ-TARGET | ALTA | Variable objetivo | tasa no acotada en origen: llega a 138 700% (denominador=1) | EDA celda 12 L11-15; df_forecast_raw.csv | Confirmado (parcial en alcance) |
| A3 | ALTA | Reproducibilidad / MLOps | No se persiste modelo ni best_params (sin .pkl/.json) | model.ipynb celdas 9/10 | Confirmado |
| R1 / ML-8 | ALTA | Reproducibilidad | Optuna sin sampler con semilla → best_params no reproducibles | model.ipynb celda 9 L31 | Confirmado |
| H1 | ALTA | Higiene del repo | CSV de 99 MB versionado y en historial git | repo raíz; commit 077d606 | Confirmado |
| C1b | MEDIA | Leakage / evaluación | Baseline también mide sobre TEST | model.ipynb celda 7 (id ffff5d67) | Confirmado |
| DQ-CLIP-ORDEN | MEDIA | Consistencia | Clip [0,100] post-ventana e inconsistente con el EDA | dataset.ipynb celda 7 vs celda 15 | Confirmado |
| DQ-COBERTURA | MEDIA | Sesgo de selección | Filtro ≥20 periodos descarta 66/343 IES (sesgo de supervivencia) | EDA celda 13/15 | Confirmado |
| DQ-MOJIBAKE | MEDIA | Encoding | Mojibake "Instituci?n" en CARACTER (feature del modelo) | Ies_dept_muni_sex_car_orig.csv; df_forecast_raw.csv | Confirmado |
| ML-5 | MEDIA | Interpretación métrica | Regla "RMSE/MAE≈2 es saludable" es engañosa | README L83, 95-97 | Confirmado |
| ML-6 | MEDIA | Comunicación | "28-40% relativo" engañoso metodológicamente | README L97 | Confirmado (media) |
| ML-7 | MEDIA | Protocolo de validación | Validación de un solo semestre → alta varianza | dataset.ipynb 83a85286; model.ipynb celda 9 | Confirmado |
| R2 | MEDIA | Reproducibilidad | Sin requirements.txt (deps sin versiones) | repo; README L125 | Confirmado |
| A2 | MEDIA | Calidad de código | SettingWithCopyWarning (slices sin .copy()) | dataset.ipynb celdas 21/23 | Confirmado |
| NUEVO-ML-4 | BAJA | Sesgo de selección | Cobertura ≥20 evaluada incluyendo 2024 → test condicionado | EDA → df_forecast_raw.csv | Confirmado (media confianza) |
| ML-9 | BAJA | Consistencia | Clip inconsistente baseline (sin) vs final (con) | model.ipynb celda 7 L5 vs celda 10 L16 | Confirmado |
| A1 | INFO | Calidad de datos | dic + .replace() comentado: código muerto, NO genera duplicados | EDA celda 5 L290-291 | Refutado como bug; reclasificado |
| NUEVO-ML-1 | INFO | Falso positivo | Clip [0,100] global no es leakage (límite constante) | dataset.ipynb celda 15 | Descartado correctamente |
| DQ-NAN | INFO | Faltantes | NaN-handling correcto pero inerte (0 NaN en la práctica) | EDA celdas 11/12 | Confirmado |
| IMP-1 | ALTA | Cuantificación de impacto | Métrica honesta será peor que 9.48/4.23 (síntesis) | Síntesis C1/C2/ML-4 | Confirmado (direccional) |
| INT-1 | **BIEN** | Validación temporal | Split sin solapamiento de filas entre train/val/test | dataset.ipynb 83a85286 | Confirmado |
| NUEVO-ML-2 | **BIEN** | Preprocesamiento | Sin scaler/encoder global; alineación de categorías correcta | model.ipynb 1ff1a797 | Confirmado |
| NUEVO-ML-3 | **BIEN** | Definición de target | Lags = serie desplazada; sin target leakage intra-fila | dataset.ipynb e7bb2962 | Confirmado |
| DQ-DEDUP | **BIEN** | Consolidación | 0 duplicados (IES,periodo); metadata .first() segura | EDA celda 12; dataset celda 9 | Confirmado |
| ML-10 | **BIEN** | Buenas prácticas | Split temporal y early_stopping sobre val correctos | dataset 83a85286; model 5/9 | Confirmado |

---

## Confirmación explícita de los hallazgos pre-marcados (C1, C2, A1, A2, A3)

- **C1 — CONFIRMADO (CRÍTICA).** En `model.ipynb` celda 9 (id `7e313e16`), `objective()` entrena con `eval_set=[(x_val,y_val)]` (solo controla early stopping = número de árboles), pero retorna `np.sqrt(mean_squared_error(y_test, y_pred))` con `y_pred = modelo.predict(x_test)` (L1329-1330). `study = optuna.create_study(direction='minimize')` + `study.optimize(objective, n_trials=100)` (L1332-1333). Los 8 hiperparámetros (max_depth, learning_rate, subsample, colsample_bytree, gamma, reg_lambda, reg_alpha) se eligen mirando el test. README L78/L89 afirman lo opuesto: **falso, verificado verbatim**.

- **C2 — CONFIRMADO (CRÍTICA).** `dataset.ipynb` celda ventana (id `e7bb2962`) construye `lag1=tasas[i-1]…lag4=tasas[i-4]`, `target=tasas[i]` (L432-436) con tasas REALES. Split (id `83a85286`) define `test = dataset[periodo_target.isin(['2024-1','2024-2'])]` (L999). `model.ipynb` predice las 529 filas de una sola vez (one-step). No existe encadenamiento recursivo (grep recurs/encaden/chain = 0). Reproducción: para las 264 IES con 2024-2, `lag1` == tasa real de 2024-1 en 264/264 casos. README L76 (forecast recursivo) **no existe en el código**.

- **A1 — REFUTADO COMO BUG, RECLASIFICADO A INFO (código muerto).** `EDA_preprocesamiento.ipynb` celda 5 L290 define `dic={'archipielago de sa':…, 'san andres y provi':…, 'narinio':'narino', 'la guajira':'guajira'}` y L291 el `.replace()` está COMENTADO (además referencia `matriculados`, variable inexistente; el DataFrame se llama `df`). Pero la salida real (L318-333) muestra DEPARTAMENTO ya limpio sin duplicados: `narino` 26, `la guajira` 8, `archipielago de san andres y providencia` 4. **No hay categorías duplicadas.** Las claves del dic ni siquiera coinciden con la salida del normalizador. Es deuda técnica (código muerto que aparenta hacer algo), no un defecto de datos.

- **A2 — CONFIRMADO (MEDIA).** `dataset.ipynb`: los tres splits se crean por slicing booleano sin `.copy()` (L997-999) y luego se les asigna (`train[col] = … .astype('category')`, L1134-1136; `train['semestre'] = …`, L1214-1216), disparando `SettingWithCopyWarning` (stderr versionado en las celdas 21 y 23). En esta corrida las escrituras surtieron efecto (fragilidad "funciona por suerte"), no corrompió el artefacto, pero es un patrón frágil.

- **A3 — CONFIRMADO (ALTA).** `study.best_params` solo se imprime (celda 9, L1336); `modelo_final` se entrena y evalúa pero **nunca se serializa** (celda 10). Grep de `save_model|joblib|pickle|json.dump` en todos los `.ipynb` = sin coincidencias; `git ls-files` no lista ningún `.pkl/.joblib/.ubj/.json`. Sin artefacto y sin semilla en Optuna (R1), el número publicado no es auditable ni reproducible.

---

## Hallazgos CRÍTICOS (detalle)

### C1 / ML-3 — Optuna selecciona hiperparámetros minimizando el RMSE de TEST
**Ubicación:** `entrenamiento_csv/model.ipynb`, celda 9 (id `7e313e16`), L1325-1333.
**Descripción:** El `objective()` ajusta con early stopping sobre validación pero retorna el RMSE de test. Con `direction='minimize'` y 100 trials, `study.best_value` (output real: "Mejor RMSE: 9.5071") es el mínimo de 100 evaluaciones ruidosas sobre el holdout → *winner's curse*.
**Por qué importa (política pública):** El 9.48/4.23 publicado es optimista por construcción: el test dejó de ser una estimación insesgada del desempeño futuro. El jurado y las secretarías creerían un desempeño que el modelo no tendrá sobre IES no vistas.
**Fix:** En `objective()` cambiar `predict(x_test)`/`mean_squared_error(y_test, …)` por `x_val`/`y_val`. Seleccionar `best_params` por validación, reentrenar y tocar el test **una sola vez** al final. Documentar dos números (RMSE val para selección, RMSE test reportado una vez). Corregir README L78 y L89.

### C2 / ML-4 — No existe forecast recursivo; 2024-2 usa el lag REAL de 2024-1
**Ubicación:** `dataset.ipynb` celda ventana (id `e7bb2962`) y split (id `83a85286`); evaluación one-step en `model.ipynb` celdas 7/9/10.
**Descripción:** La ventana deslizante asigna lags reales; el test mezcla 2024-1 (265 filas) y 2024-2 (264 filas) como filas independientes y se predicen todas a la vez. Para 2024-2, `lag1` es la tasa observada de 2024-1, no la predicha. El encadenamiento del README L76 no se implementa.
**Por qué importa (política pública):** El producto promete pronóstico a 1 año emitido en un único momento de corte. Al predecir 2024-2 desde 2023-2, la tasa de 2024-1 aún no se conoce; habría que usar la predicción (error acumulado). La evaluación actual elimina la parte más difícil del horizonte y subestima el error de t+2, justo el semestre de planeación de política. Evidencia: la persistencia para 2024-2 con su lag real ya da RMSE 8.42 (más "fácil" que 2024-1, RMSE 11.48), confirmando el regalo del valor intermedio.
**Fix:** Implementar evaluación recursiva: (1) predecir 2024-1 con lags reales hasta 2023-2; (2) construir 2024-2 con `lag1 = predicción de 2024-1` (desplazando lag2..lag4); (3) reportar RMSE/MAE separados por horizonte h=1 y h=2, comparados contra la persistencia equivalente.

---

## Hallazgos ALTOS (detalle)

### ML-1 — RMSE/MAE no miden la tarea real (priorización/ranking)
**Ubicación:** `model.ipynb` celdas 7/10; README L16-23, 41-45.
El propósito declarado es clasificar/priorizar IES en riesgo, pero solo se reporta RMSE/MAE global. No hay precision/recall sobre "IES en riesgo", ni Precision@K/Recall@K/NDCG, ni Spearman/Kendall. La rama "Clasificación por comportamiento" del README nunca se implementa. **Por qué importa:** para priorizar importa el ORDEN, no el error promedio; con cola pesada (target medio 14.57, std 13.48, max recortado a 100, p99≈89.75) el RMSE está dominado por pocas IES extremas. **Fix:** definir umbral de riesgo y reportar precision/recall/F1, Precision@K (K=20,50) y correlación de ranking sobre **validación**.

### ML-2 — Sin baseline de persistencia; el aporte del modelo es marginal
**Ubicación:** `model.ipynb` celda 5/7 (el "baseline" es un XGBoost de 500 árboles, no trivial); README L82-97.
Reproducción independiente sobre los splits reales: **persistencia (`y=lag1`)** → TEST RMSE 10.07 / MAE 4.42, VAL RMSE 8.18 / MAE 3.15; **media** → TEST RMSE 13.47 / MAE 7.93. El modelo (con fuga) reporta TEST 9.48-9.51. **Por qué importa:** el modelo solo mejora ~0.6 RMSE sobre algo trivial sin entrenar, y eso con la fuga inflándolo; en validación la persistencia es mejor que el test publicado. Las tasas de deserción son altamente persistentes; sin batir la persistencia en backtesting, no puede sostenerse que el modelo aporte frente a no hacer nada. **Fix:** añadir persistencia y media con el mismo protocolo/splits y reportarlas junto al modelo.

### C1c — Modelo final reentrena con best_params contaminados y mide en test
**Ubicación:** `model.ipynb` celda 10 (id `057d742d`) L1355-1371.
`best_params = study.best_params` (heredado de C1) → `modelo_final` → `y_pred_test = np.clip(modelo_final.predict(x_test),0,100)` → "Test RMSE 9.51 / MAE 4.16". Hereda el sesgo de C1 más el clip aplicado solo aquí (no en el baseline), por lo que la mejora aparente baseline→final mezcla tuning y post-proceso. **Fix:** unificar clip, reportar la métrica final una vez tras fijar hiperparámetros por validación.

### DQ-TARGET-NO-ACOTADO — La tasa no está acotada en origen (llega a 138 700%)
**Ubicación:** `EDA_preprocesamiento.ipynb` celda 12 L767-768; `df_forecast_raw.csv`; clip tardío en `dataset.ipynb` celda 15 L806.
`tasa = np.where(MATRICULADOS>0, DESERTORES/MATRICULADOS*100, np.nan)`: el `np.where` evita división por cero pero NO acota a 100. En `df_forecast_raw.csv`: min 0, mediana 9.6, **max 138 700**, 153 filas con tasa>100 (ej. IES 1202 2021-2: 1387/1 → 138 700). **Por qué importa:** (1) `df_forecast_raw.csv` (consumido por dashboard/EDA y por las barras de CARACTER en EDA celda 20) muestra valores absurdos; la media de tasa por "Universidad" pasa de 32.08% (sin clip) a 9.35% (con clip). (2) El clip convierte un error de medición (denominador=1) en un 100% "plausible" que el modelo aprende como real. **Matiz verificado:** la `tasa_nacional` (EDA celda 18, SUM/SUM) es robusta y NO se distorsiona; el barplot por departamento usa DESERTORES, no tasa. **Fix:** sanear en el EDA antes de exportar (marcar NaN/descartar filas con MATRICULADOS<umbral o tasa>100, o winsorizar), recalcular cobertura sobre la serie saneada y luego construir ventanas.

### A3 — No se persiste el modelo ni los best_params
**Ubicación:** `model.ipynb` celdas 9/10. Ver confirmación arriba. **Fix:** `modelo_final.save_model(...)` / `joblib.dump`, y `json.dump(study.best_params, ...)` para trazabilidad y auditoría del número publicado.

### R1 / ML-8 — Optuna sin sampler con semilla
**Ubicación:** `model.ipynb` celda 9 L1332: `optuna.create_study(direction='minimize')` sin `sampler=`. El XGBoost fija `random_state=42`, pero el TPESampler por defecto es estocástico y no se fija `np.random.seed`. Los 100 trials y los `best_params` no son reproducibles entre corridas (de hecho el README reporta 9.48/4.23 y el notebook actual da 9.51/4.16 → corrida no sembrada). **Fix:** `sampler=optuna.samplers.TPESampler(seed=42)` y `np.random.seed(42)`.

### H1 — CSV de 99 MB versionado y en el historial git
**Ubicación:** `MEN_MATRICULA_ESTADISTICA_ES_20260519.csv` (104 054 678 bytes / 99.23 MB, 390 904 líneas). `git ls-files` lo lista; introducido en commit `077d606` ("Carga de los archivos primer commit"); `.gitignore` (existe, plantilla Python) NO lo ignora (`git check-ignore` sin match). El dato es público del SNIES (README L59/L133), descargable, no requiere versionarse; no hay PII de personas naturales. **Por qué importa:** el blob persiste en el historial; todo clone lo arrastra. Es higiene/peso, no seguridad. **Fix:** `git rm --cached`, añadir patrón a `.gitignore`, y limpiar historial con `git filter-repo`/BFG o externalizar con DVC.

---

## Hallazgos MEDIOS (detalle)

- **C1b (MEDIA):** El baseline (celda 7, id `ffff5d67`) imprime sus métricas sobre x_test/y_test (`y_pred_test = modelo_baseline.predict(x_test)`, "Semestre 1 RMSE 9.70 / MAE 4.17"); el único clip a validación está comentado (L1162). La comparación baseline-vs-final es test-contra-test (multiple testing sobre el holdout). **Fix:** evaluar el baseline sobre validación.

- **DQ-CLIP-ORDEN (MEDIA):** El clip a [0,100] se aplica en `dataset.ipynb` celda 15 (L806) sobre la matriz de lags ya armada, después de construir ventanas desde `grupo['tasa'].values` sin clip (celda 7); el EDA nunca clipa. Resultado: el mismo dato vale 138 700% en `df_forecast_raw.csv` y 100% en X_train; no se distingue un 100% legítimo de uno clipado. **Fix:** sanear la tasa en el EDA antes de exportar y formar ventanas.

- **DQ-COBERTURA-SESGO (MEDIA):** El filtro ≥20 periodos consecutivos sin huecos (EDA celda 13, UMBRAL=20) retiene 277/343 IES (descarta 46 por hueco_interno, 20 por serie corta). Es metodológicamente correcto para lags contiguos, pero introduce sesgo de supervivencia: el modelo solo ve IES grandes, antiguas y estables; las 66 excluidas (nuevas, pequeñas, intermitentes) son las de mayor interés de política. El RMSE/MAE aplica solo a la subpoblación "sobreviviente". **Fix:** documentar cobertura 277/343, perfilar las excluidas, considerar imputación de huecos cortos y reportar métricas estratificadas.

- **DQ-MOJIBAKE (MEDIA):** Doble decodificación (utf-8 leído como latin-1) produce "Instituci?n universitaria", "Instituci?n t?cnica profesional", "Sin informaci?n" en CARACTER/SEXO de `Ies_dept_muni_sex_car_orig.csv`, que se propaga a `df_forecast_raw.csv` y a las features categóricas del modelo (CARACTER). DEPARTAMENTO/MUNICIPIO se salvan porque pasan por `limpieza_total` (NFD + descarte no-ASCII); CARACTER/ORIGEN/SEXO no. XGBoost lo trata como categoría estable, pero rompe gráficas, dashboard del concurso y joins futuros. **Fix:** releer con encoding correcto o mapear explícitamente a forma legible.

- **ML-5 (MEDIA):** README L83 afirma "RMSE/MAE≈2 es saludable; >3 problemático". Es engañoso: para errores ~normales el ratio tiende a ~1.25; un 2.24 indica cola pesada/outliers (target std≈13.5, valores recortados a 100), no buena salud. Probablemente el modelo falla feo en las IES de tasa alta (las "en riesgo"). **Fix:** reemplazar por histograma de residuales, error por estrato de tasa y métricas robustas (MdAE, p90 del error).

- **ML-6 (MEDIA, confianza media):** README L97 ("MAE 4.23 → 28-40% relativo") es aritméticamente consistente pero engañoso: divide un error en puntos por el nivel agregado (no por-IES), usa un denominador (10-15%) menor que la media real (14.57), y se construye sobre un MAE contaminado. En una IES con 5% de tasa, 4.23 pp es ~85% relativo. **Fix:** reportar error relativo por IES con distribución/percentiles, o error por estrato; recalcular tras corregir C1/C2.

- **ML-7 (MEDIA):** Validación de un solo semestre (2023-2, 265 filas) y un solo año de test. La varianza entre cortes es grande (persistencia: VAL 8.18 vs TEST 10.07). Conclusiones frágiles ("modelo vs persistencia") dependen del semestre. **Fix:** backtesting rolling-origin / expanding-window, agregando RMSE/MAE (media y desviación) sobre varios orígenes; reservar 2024 como holdout único.

- **R2 (MEDIA):** No hay `requirements.txt`/`pyproject.toml`/`environment.yml`. Única declaración: README L125 `pip install pandas numpy xgboost scikit-learn optuna matplotlib seaborn` (sin versiones). `enable_categorical`, `early_stopping_rounds` en el constructor y `min_count` dependen de versiones recientes de XGBoost/pandas. **Fix:** congelar `requirements.txt` con versiones exactas.

- **A2 (MEDIA):** Ver confirmación arriba. **Fix:** crear los splits con `.copy()`.

---

## Hallazgos BAJOS / INFO

- **NUEVO-ML-4 (BAJA, confianza media):** La elegibilidad por cobertura ≥20 se evalúa sobre toda la historia incluido 2024, así que una IES entra al test 2024 solo si tiene reporte completo en 2024 → sesgo de selección que infla la calidad aparente del test. **Fix:** definir elegibilidad solo con info hasta el corte (≤2023-2), o documentar explícitamente que el test está condicionado a cobertura 2024.

- **ML-9 (BAJA):** Clip inconsistente: baseline sin clip (celda 7 L1162 comentado), final con clip (celda 10 L1370). La mejora aparente puede deberse al clip. **Fix:** mismo post-proceso para todas las predicciones, incluido el baseline naive.

- **DQ-NAN (INFO):** `min_count=1` + `np.where` es correcto pero inerte: `agg_base` y `df_forecast_raw.csv` quedan con 0 NaN (ningún grupo totalmente NaN, ningún MATRICULADOS=0). Buena ingeniería defensiva que no se activa; no sobre-venderla en el README. **Fix opcional:** un assert que confirme cuántos NaN se preservaron (hoy 0).

- **A1 (INFO):** Código muerto (dic + replace comentado) que no genera duplicados; ver confirmación. **Fix:** eliminar el bloque o reconstruir el dic con claves que coincidan con la salida del normalizador y aplicarlo de verdad.

- **NUEVO-ML-1 (INFO):** El clip global [0,100] antes del split NO es leakage estadístico (límites constantes, no parámetros estimados). Falso positivo correctamente descartado. El problema real asociado es la inconsistencia de aplicación (DQ-CLIP-ORDEN, ML-9).

---

## Lo que está bien hecho (balance)

- **INT-1 (BIEN):** Split temporal sin solapamiento de filas (IES, periodo) entre train/val/test; intersección de claves = 0 en los tres pares. La clase de fuga por filas duplicadas/futuras cruzando particiones está descartada. El único problema temporal real es el del semestre intermedio (C2).
- **NUEVO-ML-2 (BIEN):** Sin StandardScaler/MinMaxScaler/target encoding/imputación por media global. Las categorías se alinean fijando las de train sobre val/test (`cat.set_categories(x_train[col].cat.categories)`, model.ipynb id `1ff1a797`), buena práctica que evita fuga inversa. XGBoost con `enable_categorical` no requiere escalado.
- **NUEVO-ML-3 (BIEN):** Los lags son la serie estrictamente desplazada (i-1..i-4); las categóricas son atributos estáticos de la IES por `groupby.first`. No hay feature que codifique el target del mismo periodo: sin target leakage intra-fila.
- **DQ-DEDUP-CONSOLIDACION (BIEN):** Consolidación por (IES, periodo) con 0 duplicados; las 190 filas SEXO="Sin información" se suman correctamente al total; cada IES tiene un único DEPARTAMENTO/MUNICIPIO/CARACTER/ORIGEN, por lo que `.first()` es seguro.
- **ML-10 (BIEN):** Diseño conceptual del split temporalmente correcto (entrena en pasado, valida el semestre siguiente, testea el año posterior, sin barajado) y `early_stopping` usa correctamente `(x_val, y_val)`. La base para una evaluación honesta está puesta; solo hay que redirigir la métrica de selección de Optuna de test a val y añadir el encadenamiento recursivo y los baselines.
- **README excelente** y **diagnóstico de cobertura riguroso** (verifica el rango [primer, último] contra el conjunto esperado de periodos) — la lógica de detección de huecos es correcta; el reparo es de validez externa (sesgo), no de implementación.

---

## Plan de remediación priorizado

1. **(C1/ML-3)** Mover la métrica de `objective()` a validación; tocar el test una sola vez. Corregir README L78/L89.
2. **(C2/ML-4)** Implementar evaluación recursiva real y reportar RMSE/MAE separados por horizonte t+1 y t+2.
3. **(ML-2)** Añadir baselines de persistencia y media con el mismo protocolo; condición de "aporta valor" = batir persistencia en backtesting.
4. **(ML-1)** Añadir métricas de ranking/clasificación alineadas a la priorización (Precision@K, recall sobre IES en riesgo) sobre validación.
5. **(DQ-TARGET/DQ-CLIP)** Sanear la tasa en el EDA antes de exportar `df_forecast_raw.csv`; un único criterio de acotamiento, documentado.
6. **(R1/A3/R2)** Sembrar Optuna (`TPESampler(seed=42)`), persistir `best_params` y modelo, congelar `requirements.txt`.
7. **(H1)** Sacar el CSV de 99 MB del repo e historial.
8. **(ML-7)** Backtesting rolling-origin; **(ML-5/ML-6)** sustituir las heurísticas de interpretación por análisis de residuales por estrato.

*Nota de honestidad: las magnitudes del impacto (cuánto subirá el RMSE honesto) no se midieron porque requeriría reentrenar (prohibido). La dirección está sustentada en código y en los baselines reproducidos: la métrica honesta será peor que 9.48/4.23, con el mayor deterioro en t+2.*

# Informe 06 — MLOps, Reproducibilidad e Higiene de Repositorio

**Proyecto:** Datos al Ecosistema 2026 — Forecast de deserción por IES (SNIES/MEN)
**Rol:** Ingeniería MLOps / reproducibilidad / higiene de repo
**Alcance:** 100% lectura. No se ejecutó ningún notebook ni se modificó el repo.
**Fecha:** 2026-06-28

> Nota de procedencia: los archivos `EX/code_*.txt` y `EX/data_profile.txt` mencionados en el encargo **no existen en disco** (no hay carpeta `EX/` en el repo ni en el árbol del proyecto). Por tanto, todas las citas archivo-celda-línea de este informe se construyeron leyendo directamente los notebooks `entrenamiento_csv/model.ipynb`, `dataset.ipynb` y `EDA_preprocesamiento.ipynb` (sin ejecutarlos) y validando la estructura con `git ls-files` / `git log`. La numeración de celdas es 0-based contando celdas markdown + código, consistente con el encargo (la celda "objective+Optuna" es la 9 y coincide con la referencia C1 del README/CLAUDE.md).

---

## Resumen ejecutivo

El proyecto es metodológicamente ambicioso y bien documentado, pero **no es reproducible de forma determinista ni desplegable** en su estado actual. Los problemas de leakage (C1/C2) ya están cubiertos por los informes de modelado; aquí me concentro en los siete ejes de MLOps encargados y confirmo todos los hallazgos previos añadiendo evidencia y precisión:

- **Reproducibilidad parcial (R1, ALTA):** `XGBRegressor` fija `random_state=42`, pero `optuna.create_study()` se crea **sin sampler con semilla** y **nunca se llama a `np.random.seed`** en `model.ipynb`. El sampler por defecto (`TPESampler`) es estocástico → cada corrida de las 100 trials explora hiperparámetros distintos y produce `best_params` distintos. El 9.48/4.23 del README no es reproducible bit-a-bit.
- **Sin gestión de dependencias (R2, ALTA):** no hay `requirements.txt`, `pyproject.toml`, `environment.yml` ni lockfile. Las versiones de pandas/numpy/xgboost/optuna/sklearn no están pineadas. El comportamiento de `enable_categorical`, `early_stopping_rounds` y `pivot_table(min_count=...)` depende de la versión de XGBoost/pandas.
- **Sin persistencia del modelo (A3, ALTA):** no se serializa el modelo (`.json`/`.ubj`/`.pkl`) ni los `best_params`. Cada inferencia exige re-ejecutar Optuna (100 trials). No hay forma de servir ni auditar el modelo entregado.
- **A2 confirmado (ALTA):** `SettingWithCopyWarning` reproducido en los **outputs versionados** de `dataset.ipynb`, en dos celdas (astype category y asignación de `semestre`), por slices sin `.copy()`.
- **Higiene de repo (H1–H4):** CSV de 99.23 MB **versionado y presente en el historial** (commit `077d606`); `.gitignore` presente pero **no cubre datos**; **sin LICENSE**; notebooks con **outputs versionados** (incl. una ruta de usuario `C:\Users\Jonathan Piedrahita\...` filtrada en los tracebacks); CSVs intermedios huérfanos versionados.
- **Código muerto:** `MultiOutputRegressor` importado y nunca usado; `cargar_csv.py` es un script de 4 líneas que lee un CSV ni siquiera parte del pipeline documentado; `periodo_num` se calcula y no se usa aguas abajo.
- **Clip inconsistente:** baseline (celda 7) reporta **sin** clip; modelo final (celda 10) reporta **con** `np.clip(...,0,100)` → las métricas baseline vs final **no son estrictamente comparables**.

**Veredicto MLOps:** el repositorio está en estado de *notebook de exploración*, no de *artefacto reproducible*. Con un `requirements.txt`, fijación de semillas, persistencia del modelo y limpieza del historial de datos se puede llevar a un estándar de entrega de concurso en pocas horas.

---

## Tabla de hallazgos

| ID | Severidad | Categoría | Título | Ubicación |
|----|-----------|-----------|--------|-----------|
| R1 | ALTA | Reproducibilidad | Optuna sin sampler con semilla; `np.random.seed` no fijado | model.ipynb · celda 9 |
| R2 | ALTA | Dependencias | Sin `requirements.txt`/lockfile; versiones no pineadas | raíz del repo |
| A3 | ALTA | Persistencia | No se guarda modelo ni `best_params` | model.ipynb · celdas 9–10 |
| A2 | ALTA | Bug pandas | `SettingWithCopyWarning` (slices sin `.copy()`) | dataset.ipynb · celdas 21 y 23 |
| H1 | ALTA | Higiene repo | CSV de 99 MB versionado y en historial git | raíz · `MEN_MATRICULA_ESTADISTICA_ES_20260519.csv` |
| H2 | MEDIA | Higiene repo | `.gitignore` no cubre datos (CSV/artefactos) | `.gitignore` |
| H3 | MEDIA | Higiene repo | Notebooks con outputs versionados; ruta de usuario filtrada | dataset.ipynb (outputs) |
| H4 | MEDIA | Legal | Ausencia de LICENSE | raíz del repo |
| D1 | MEDIA | Código muerto | `MultiOutputRegressor` importado y no usado | model.ipynb · celda 1 |
| D2 | BAJA | Código muerto | `periodo_num` calculado y no usado aguas abajo | dataset.ipynb · celda 5 |
| D3 | BAJA | Código muerto | `cargar_csv.py` script huérfano fuera del pipeline | `cargar_csv.py` |
| CL1 | MEDIA | Métricas | Clip inconsistente baseline (sin) vs final (con) | model.ipynb · celdas 7 y 10 |
| CA1 | INFO | Modelado/cardinalidad | MUNICIPIO (67) actúa como proxy de identidad de IES | model.ipynb · celda 4 / dataset features |
| H5 | BAJA | Higiene repo | CSVs intermedios huérfanos versionados | raíz (varios `*.csv`) |
| R3 | INFO | Reproducibilidad | Orden de ejecución frágil entre notebooks (sin script orquestador) | repo |
| B1 | BIEN | Reproducibilidad | `set_categories` alinea categorías val/test con train | model.ipynb · celda 4 |
| B2 | BIEN | Higiene repo | `.gitignore` plantilla Python estándar presente | `.gitignore` |

---

## Detalle por hallazgo

### R1 — Optuna sin sampler con semilla; `np.random.seed` no fijado (ALTA)
**Ubicación:** `entrenamiento_csv/model.ipynb` — celda 9, línea `study = optuna.create_study(direction='minimize')` y `study.optimize(objective, n_trials=100)`.

**Evidencia:** En toda `model.ipynb` la única semilla fijada es `random_state=42` dentro de `XGBRegressor` (celdas 5, 9, 10). `optuna.create_study(direction='minimize')` se invoca **sin** `sampler=optuna.samplers.TPESampler(seed=...)`. No existe ninguna llamada a `np.random.seed(...)` en este notebook (sí aparece en `EDA_preprocesamiento.ipynb` celda `d65ab600`, pero solo para elegir una IES aleatoria de un gráfico, no para el modelado).

**Por qué importa:** El `TPESampler` por defecto de Optuna es estocástico. Sin semilla, dos ejecuciones de las 100 trials exploran trayectorias distintas → `study.best_params` y `study.best_value` cambian entre corridas. El modelo final (celda 10) se construye con esos `best_params`, por lo que **el 9.48/9.51 RMSE y el 4.16/4.23 MAE no son reproducibles bit-a-bit**. Para un concurso esto significa que un jurado que re-ejecute no obtendrá las cifras del README.

**Fix:**
```python
import numpy as np, random
np.random.seed(42); random.seed(42)
sampler = optuna.samplers.TPESampler(seed=42)
study = optuna.create_study(direction='minimize', sampler=sampler)
```
Y documentar versión exacta de Optuna (el comportamiento de TPE con seed cambió entre versiones).

---

### R2 — Sin `requirements.txt`/lockfile; versiones no pineadas (ALTA)
**Ubicación:** raíz del repo. Verificado: `requirements.txt`, `pyproject.toml`, `environment.yml`, `Pipfile`, `poetry.lock`, `uv.lock`, `setup.py` → **todos AUSENTES**. La única referencia de dependencias es el README línea 125: `pip install pandas numpy xgboost scikit-learn optuna matplotlib seaborn` (sin versiones).

**Por qué importa:** El pipeline depende de comportamientos sensibles a versión: `XGBRegressor(enable_categorical=True)` (API de categóricas nativas estabilizada en XGBoost ≥1.6/2.x), `early_stopping_rounds` como parámetro del constructor (vs. `callbacks` en otras versiones), `pivot_table(aggfunc=lambda x: x.sum(min_count=1))`, y el `FutureWarning` de `groupby().apply` sobre columnas de agrupación (visible en EDA celda `dd1b977f`) que en pandas futuro **cambiará de resultado**. Sin pin, la reproducción puede romperse o cambiar silenciosamente las métricas.

**Fix:** Generar `requirements.txt` con versiones pineadas (`pip freeze` del entorno que produjo el README) y, idealmente, un lockfile (`uv.lock`/`poetry.lock`). Mínimo recomendado:
```
pandas==<v>
numpy==<v>
xgboost==<v>
scikit-learn==<v>
optuna==<v>
matplotlib==<v>
seaborn==<v>
jupyter==<v>
```

---

### A3 — No se persiste el modelo ni los `best_params` (ALTA)
**Ubicación:** `entrenamiento_csv/model.ipynb` — celda 9 (`study.best_params` solo se imprime) y celda 10 (`modelo_final` se entrena y se evalúa, pero **no se guarda**). No existe ningún `.pkl`/`.json`/`.ubj`/`.joblib` en el repo (`git ls-files` no lista artefactos de modelo).

**Por qué importa:** El modelo "entregado" del concurso no existe como artefacto: para usarlo hay que re-ejecutar las 100 trials de Optuna (minutos/decenas de minutos) y, por R1, se obtendrá un modelo distinto. No hay forma de servir el modelo, auditarlo, ni garantizar que la inferencia futura use exactamente los pesos reportados. Tampoco se persisten los `best_params`, así que ni siquiera se puede re-instanciar el mismo hiperparámetro-set de forma fiable.

**Fix:**
```python
import json
modelo_final.save_model('model_xgb.json')          # formato nativo, portable
with open('best_params.json','w') as f:
    json.dump(best_params, f, indent=2)
# y registrar metricas:
json.dump({'rmse': float(rmse), 'mae': float(mae)}, open('metrics.json','w'))
```
Versionar `best_params.json`/`metrics.json` (texto, ligero) y **excluir** el `.json` del modelo si es pesado o gestionarlo con un registry. Idealmente añadir un `predict.py` que cargue `model_xgb.json` y produzca el forecast.

---

### A2 — `SettingWithCopyWarning` (slices sin `.copy()`) (ALTA)
**Ubicación:** `dataset.ipynb` — celda 21 (loop `train[col]=...astype('category')`, líneas 4–6) y celda 23 (`train['semestre']=...`, `val['semestre']=...`, `test['semestre']=...`, líneas 1–3). Causa raíz: celda 19, donde `train`, `val`, `test` se crean por slicing booleano **sin `.copy()`** (`train = dataset[dataset['periodo_target'] <= '2023-1']`, etc.).

**Evidencia:** Los outputs versionados del notebook muestran el `SettingWithCopyWarning` repetido (traceback `...ipykernel_32644\434128757.py:4/5/6` y `...481311707.py:1/2/3`).

**Por qué importa:** Asignar sobre una vista (no copia) es comportamiento indefinido en pandas: puede no propagar la escritura o emitir el warning y, en versiones futuras de pandas (Copy-on-Write activado por defecto), **cambiar de semántica**. Aquí "funciona por suerte", pero es frágil y ensucia los outputs entregados.

**Fix:** Materializar copias al hacer el split:
```python
train = dataset[dataset['periodo_target'] <= '2023-1'].copy()
val   = dataset[dataset['periodo_target'] == '2023-2'].copy()
test  = dataset[dataset['periodo_target'].isin(['2024-1','2024-2'])].copy()
```
Tras esto, las asignaciones de categóricas y `semestre` dejan de advertir.

---

### H1 — CSV de 99 MB versionado y en el historial git (ALTA)
**Ubicación:** raíz — `MEN_MATRICULA_ESTADISTICA_ES_20260519.csv` (99.23 MB, ~390.904 filas). Confirmado con `git ls-files` (aparece) y `git log -- <archivo>` (introducido en commit `077d606 "Carga de los archivos primer commit"`).

**Por qué importa:** El archivo está **dentro del historial**, no solo en el working tree. El `pack` actual es de 8.87 MB porque git comprime bien el CSV, pero el blob vive en el historial permanentemente: cualquier `git clone` lo arrastra y crece con cada re-commit del dato. Para un repo de concurso esto infla el clone y dificulta la portabilidad. Es un dato público del SNIES descargable de la fuente, no necesita versionarse.

**Por qué importa (matiz):** No es un problema de seguridad (es dato agregado público, sin PII de personas naturales según el perfil), sino de **higiene y peso del repo**.

**Fix:** Sacar el CSV del control de versiones y documentar su descarga:
1. `git rm --cached MEN_MATRICULA_ESTADISTICA_ES_20260519.csv`
2. Añadir el patrón a `.gitignore` (ver H2).
3. Para limpiar el historial: `git filter-repo`/BFG (operación destructiva, requiere coordinación de equipo). Alternativa moderna: DVC o un enlace a la fuente SNIES en el README.

---

### H2 — `.gitignore` presente pero no cubre datos (MEDIA)
**Ubicación:** `.gitignore` (219 líneas, plantilla Python estándar de GitHub). Ignora `__pycache__`, `.venv`, `.ipynb_checkpoints`, etc., pero **no ignora `*.csv` ni los `MEN_*.csv`**. Por eso H1/H5 ocurren pese a haber `.gitignore`.

**Por qué importa:** La plantilla da falsa sensación de cobertura. Los datos pesados y los artefactos intermedios entran al repo igualmente.

**Fix:** Añadir un bloque de datos:
```gitignore
# Datos fuente y artefactos (no versionar; obtener de la fuente SNIES)
MEN_*.csv
df_forecast_raw.csv
entrenamiento_csv/*.csv
*.parquet
# Artefactos de modelo grandes
model_xgb.json
```
(Conservar versionados solo `best_params.json`/`metrics.json` por ser ligeros y auditables.)

---

### H3 — Notebooks con outputs versionados; ruta de usuario filtrada (MEDIA)
**Ubicación:** `dataset.ipynb` y `EDA_preprocesamiento.ipynb` (y `model.ipynb`) con celdas ejecutadas (`execution_count` no nulo; en `model.ipynb` 10 celdas ejecutadas en el blob de HEAD). Los outputs de `dataset.ipynb` contienen rutas absolutas de un equipo de desarrollo: `C:\Users\Jonathan Piedrahita\AppData\Local\Temp\ipykernel_32644\...`.

**Por qué importa:** (1) Los outputs versionados generan diffs ruidosos y conflictos; (2) filtran información del entorno del autor (nombre de usuario, rutas), que es fuga menor de metadatos; (3) los outputs contienen los warnings y tracebacks (A2), perpetuando la impresión de un pipeline con errores.

**Fix:** Limpiar outputs antes de commitear (`jupyter nbconvert --clear-output --inplace *.ipynb`) y/o instalar `nbstripout` como filtro de git, o `pre-commit` con el hook `nbstripout`. Conservar como evidencia de resultados un export estático separado (HTML/PDF) si se desea mostrar gráficas.

---

### H4 — Ausencia de LICENSE (MEDIA)
**Ubicación:** raíz. Verificado: `LICENSE`, `LICENSE.md` → AUSENTES.

**Por qué importa:** Sin licencia, el código es "todos los derechos reservados" por defecto; el jurado/terceros no tienen derecho legal a usar, reproducir o derivar el trabajo, lo que contradice el espíritu de un concurso de datos abiertos.

**Fix:** Añadir `LICENSE` (MIT/Apache-2.0 para código; los datos SNIES siguen su propia licencia de origen, citar la fuente).

---

### D1 — `MultiOutputRegressor` importado y no usado (MEDIA)
**Ubicación:** `entrenamiento_csv/model.ipynb` — celda 1: `from sklearn.multioutput import MultiOutputRegressor`. No se referencia en ninguna celda posterior.

**Por qué importa:** Es un vestigio de la idea original (modelo multi-salida t+1/t+2 del README) que nunca se implementó. Su presencia **engaña al lector**: sugiere multi-output cuando el modelo es estrictamente un-paso (target único, ver `dataset.ipynb` celda 7 que construye un solo `target`). Esto se conecta con el hallazgo C2 (no hay forecast recursivo encadenado). Es código muerto que ancla una expectativa falsa.

**Fix:** Eliminar el import. Si se quiere realmente t+1→t+2, implementar el encadenamiento recursivo (predicción de t+1 alimentada como `lag1` para predecir t+2) en lugar de importar `MultiOutputRegressor`.

---

### D2 — `periodo_num` calculado y no usado (BAJA)
**Ubicación:** `dataset.ipynb` — celda 5: `df['periodo_num'] = (año*2 + semestre - 1)`. No se usa en la ventana deslizante (celda 7 itera por orden de filas, no por `periodo_num`) ni en el split (celda 19 usa `periodo_target` como string).

**Por qué importa:** Cómputo muerto. Además, el orden temporal correcto depende de que `sort_values(['IES','periodo'])` (celda 5) ordene strings `'YYYY-S'` lexicográficamente bien — lo cual funciona para 1998–2024 pero es frágil; `periodo_num` existía justamente para ese fin pero se abandonó.

**Fix:** Eliminar `periodo_num`, o usarlo de verdad para ordenar (`sort_values(['IES','periodo_num'])`) y hacer el orden temporal robusto.

---

### D3 — `cargar_csv.py` script huérfano (BAJA)
**Ubicación:** `cargar_csv.py` (raíz). Contenido: 6 líneas que leen `Ies_dept_muni_sex_car_orig.csv` y hacen `print(df.head())`. No es invocado por ningún notebook del pipeline y el CSV que lee es un insumo del EDA, no del flujo principal.

**Por qué importa:** Ruido. Sugiere un punto de entrada que no existe.

**Fix:** Eliminar o mover a una carpeta `scratch/`/`notebooks_exploratorios/` excluida.

---

### CL1 — Clip inconsistente baseline vs modelo final (MEDIA)
**Ubicación:** `entrenamiento_csv/model.ipynb` — celda 7 (baseline): `y_pred_test = modelo_baseline.predict(x_test)` con la línea `# y_pred_val = np.clip(y_pred_val,0,100)` **comentada** → métricas **sin** clip (RMSE 9.70 / MAE 4.17). Celda 10 (final): `y_pred_test = np.clip(modelo_final.predict(x_test), 0, 100)` → métricas **con** clip (RMSE 9.51 / MAE 4.16).

**Por qué importa:** La comparación "baseline 9.70 vs final 9.51" mezcla dos transformaciones distintas del output. Parte de la mejora aparente puede deberse al clip, no al tuning. Para una comparación honesta, ambas deben usar el mismo post-procesamiento. (Nota: el target ya está clipeado a [0,100] en `dataset.ipynb` celda 15, así que clipear la predicción es defendible — pero debe aplicarse **consistentemente** a baseline y final.)

**Fix:** Aplicar `np.clip(pred, 0, 100)` (o no aplicarlo) en **ambas** celdas, y reportar la comparación con la misma convención. Documentar en el README que la predicción se acota a [0,100] por coherencia con el dominio de la tasa.

---

### CA1 — Cardinalidad: MUNICIPIO actúa como proxy de identidad de IES (INFO)
**Ubicación:** `model.ipynb` celda 4 / `dataset.ipynb` features (`cols_cat = ['CARACTER','ORIGEN','DEPARTAMENTO','MUNICIPIO']`). Cardinalidades medidas sobre los CSV de entrenamiento:

| Columna | nunique (train) | nunique (val) | nunique (test) | Cats no vistas en train |
|---------|-----------------|---------------|----------------|--------------------------|
| CARACTER | 4 | 4 | 4 | 0 |
| ORIGEN | 2 | 2 | 2 | 0 |
| DEPARTAMENTO | 28 | 27 | 27 | 0 (val y test) |
| MUNICIPIO | 67 | 62 | 62 | 0 (val y test) |

**Por qué importa (riesgo controlado, no explosión):** Con `enable_categorical=True`, XGBoost maneja MUNICIPIO (67 niveles) sin one-hot, así que **no hay explosión dimensional**. Y como **no hay categorías nuevas en val/test** (0 unseen), `set_categories` (B1) alinea correctamente. El riesgo real es de otra naturaleza: la metadata categórica se asigna por IES con `groupby('IES').first()` (`dataset.ipynb` celda 9), de modo que **cada IES colapsa a un único MUNICIPIO/DEPARTAMENTO/CARACTER/ORIGEN fijo**. MUNICIPIO (67 valores, algunos con una sola IES) funciona entonces como un **proxy parcial de identidad institucional**: el modelo puede memorizar el nivel de deserción de IES concretas vía su municipio, inflando el desempeño en train sin capacidad de generalización a IES nuevas. Esto no es un bug, pero conviene reportarlo: el desempeño está condicionado a predecir IES ya vistas.

**Fix / mitigación:** (1) Documentar explícitamente que el modelo predice solo IES con historial (no es zero-shot a IES nuevas). (2) Evaluar la importancia de MUNICIPIO (la celda 11 ya grafica feature importance — revisar si MUNICIPIO domina). (3) Considerar regularización (`reg_lambda`/`reg_alpha` ya están en el search space) o agrupar municipios de baja frecuencia. (4) Para robustez futura, un split por IES (no solo temporal) revelaría la generalización real fuera de muestra.

---

### H5 — CSVs intermedios huérfanos versionados (BAJA)
**Ubicación:** raíz — `programa.csv`, `sex_programa.csv`, `valle_.csv`, `icetex.csv`, `codIES_dept_muni.csv`, `IES_dept_muni_gene.csv`, `cara_dept_muni.csv`, `sex_ing_nopersonas.csv`, `Ies_dept_muni_sex_car_orig.csv`, `df_forecast_raw.csv`. Todos en `git ls-files`. Varios no aparecen en el pipeline documentado (README/CLAUDE.md describen solo `MEN_*`, `df_forecast_raw.csv` y `entrenamiento_csv/*`).

**Por qué importa:** Artefactos intermedios versionados que no se regeneran de forma documentada. Inflan el repo y confunden sobre cuáles son insumos vs. derivados. `df_forecast_raw.csv` (1.17 MB) **sí** es salida documentada del EDA, así que es regenerable y no necesita versionarse.

**Fix:** Mover insumos a una carpeta `data/raw/` ignorada y derivados a `data/processed/` ignorada; documentar en el README qué genera cada uno. Versionar solo el código que los produce.

---

### R3 — Orden de ejecución frágil entre notebooks (INFO)
**Ubicación:** repo (3 notebooks encadenados por archivos CSV en disco). El README (líneas 128–131) y CLAUDE.md describen el orden EDA → dataset → model, pero **no hay script orquestador**: cada notebook escribe CSVs que el siguiente lee por ruta relativa. `dataset.ipynb` lee `df_forecast_raw.csv` (producido por EDA) y escribe en `entrenamiento_csv/`; `model.ipynb` lee desde ahí.

**Por qué importa:** El acoplamiento por archivos en disco es frágil: si alguien ejecuta `model.ipynb` con CSVs viejos (los que ya están versionados, H1/H5), obtendrá resultados sobre datos desactualizados sin darse cuenta. No hay verificación de que los CSV de `entrenamiento_csv/` correspondan a la última corrida del EDA/dataset.

**Fix:** Un `Makefile` o `run_pipeline.py` que ejecute los tres pasos en orden (`jupyter nbconvert --execute` o, mejor, extraer la lógica a `.py`), con checksums/timestamps de los insumos. CI ligero que ejecute el pipeline en datos de muestra.

---

### B1 — `set_categories` alinea categorías val/test con train (BIEN)
**Ubicación:** `model.ipynb` — celda 4: `x_val[col] = x_val[col].astype('category').cat.set_categories(x_train[col].cat.categories)` (idem `x_test`). Correcto: garantiza que los códigos categóricos de val/test mapeen al mismo espacio que train. Reconocido como buena práctica; no tocar. (El bloque alternativo comentado arriba **sí** tenía un bug de cruce de variables `x_test=x_val[col]...`, pero está comentado y la versión activa es la correcta.)

### B2 — `.gitignore` plantilla Python estándar presente (BIEN)
**Ubicación:** `.gitignore` (219 líneas). Cubre correctamente entornos, caches y artefactos de Python. La carencia es solo de patrones de datos (H2), no de la base.

---

## Recomendaciones MLOps (plan accionable)

**Prioridad 1 — Reproducibilidad determinista (rama `chore/reproducibility`)**
1. Fijar semillas: `np.random.seed(42)`, `random.seed(42)`, y `TPESampler(seed=42)` en `create_study` (R1).
2. Generar `requirements.txt` pineado con `pip freeze` del entorno del README; añadir `python_version` (R2).
3. Añadir `pyproject.toml` mínimo + lockfile (`uv`/`poetry`) para reproducción exacta.

**Prioridad 2 — Persistencia y servibilidad (rama `chore/model-persistence`)**
4. `modelo_final.save_model('model_xgb.json')` + `best_params.json` + `metrics.json` (A3).
5. Script `predict.py` que cargue el modelo y produzca el forecast (desacoplar inferencia del entrenamiento).
6. Implementar el forecast recursivo t+1→t+2 real si se mantiene la promesa del README (conecta con C2/D1).

**Prioridad 3 — Higiene de repo (rama `chore/repo-hygiene`)**
7. `.gitignore` de datos (`MEN_*.csv`, derivados) + `git rm --cached` de los CSV pesados; documentar descarga SNIES en README (H1/H2/H5).
8. Limpiar outputs de notebooks (`nbstripout`/`nbconvert --clear-output`) — elimina rutas de usuario filtradas y warnings (H3).
9. Añadir `LICENSE` (H4).
10. Eliminar código muerto: `MultiOutputRegressor`, `periodo_num`, `cargar_csv.py` (D1/D2/D3).

**Prioridad 4 — Correcciones de comparabilidad (rama `fix/metrics-consistency`)**
11. Clip consistente baseline/final (CL1); documentar la convención.
12. Materializar copias en el split de `dataset.ipynb` (`.copy()`) para eliminar `SettingWithCopyWarning` (A2).

**Prioridad 5 — CI ligero (rama `chore/ci`)**
13. GitHub Actions: job que (a) instala `requirements.txt`, (b) corre `ruff`/`flake8` y `nbstripout --check`, (c) ejecuta el pipeline sobre una muestra pequeña y verifica que `metrics.json` se genere. Sin reentrenar Optuna completo en CI (usar `n_trials` reducido o cargar el modelo persistido).
14. `pre-commit` con hooks: `nbstripout`, `ruff`, y un check de tamaño de archivo (`check-added-large-files`) que **bloquee** commits de CSV >1 MB (previene la recurrencia de H1).

**Riesgo residual reconocido:** Aun corrigiendo todo lo anterior, las métricas reportadas (9.48/4.23) seguirán siendo de **test con leakage** hasta que se corrija C1 (Optuna optimizando sobre test) y C2 (forecast recursivo). MLOps no resuelve el leakage; solo lo hace reproducible. La corrección de C1/C2 es prerrequisito para que cualquier persistencia (A3) guarde un modelo cuyas métricas sean creíbles.

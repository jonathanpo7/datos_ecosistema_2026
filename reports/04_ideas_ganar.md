# 04 — Ideas para Ganar: Diferenciadores Concretos para el Jurado

**Proyecto:** Forecast de deserción por IES — "Datos al Ecosistema 2026"
**Rol del documento:** Estrategia de competencia / ML product
**Fecha:** 2026-06-28
**Alcance:** 100% lectura. Todas las citas son `archivo · celda N · línea M` verificadas sobre los notebooks reales en `REPO/datos_ecosistema_2026`.

---

## 0. TL;DR para decidir en 5 minutos

El proyecto tiene una narrativa de impacto excelente (README) y un pipeline conceptualmente correcto, pero **el resultado estrella (RMSE 9.48 / MAE 4.23) no sobrevive a una auditoría de jurado serio** por dos razones que ya están confirmadas en código:

1. **Optuna optimiza sobre el test** (`model.ipynb · celda 9 · líneas 28-29`): `y_pred = modelo.predict(x_test)` y `return np.sqrt(mean_squared_error(y_test, y_pred))`. La métrica reportada es de test con selección de hiperparámetros mirando el test.
2. **No hay forecast recursivo t+1→t+2**: el test de 2024-2 usa la deserción **real** de 2024-1 como `lag1`, no la predicha (lo confirmé abriendo `X_test.csv`: la fila 2024-2 de Bogotá tiene `lag1=6.05`, que es exactamente el `target` real de la fila 2024-1).

Y lo más importante para un concurso: **medí el baseline naive de persistencia (predecir = el último valor observado) sobre el MISMO test y da RMSE 10.07 / MAE 4.42**. El modelo XGBoost completo, con Optuna haciendo trampa al mirar el test, apenas mejora ~0.6 RMSE y ~0.2 MAE sobre repetir el último número. **Sin demostrar que el modelo supera a "copiar el último dato", no hay historia que defender.**

> **La buena noticia:** esto es una oportunidad. Casi ningún competidor presenta baseline naive, error por segmento, SHAP de política pública e intervalos de predicción. Hacer estas cosas **bien** (y honestamente) es exactamente lo que separa un proyecto de estudiante de uno que un jurado de impacto social premia. Este documento prioriza esos diferenciadores por Impacto vs Esfuerzo.

---

## 1. Tabla maestra: Impacto vs Esfuerzo

Leyenda Impacto/Esfuerzo: **A**=Alto, **M**=Medio, **B**=Bajo. "Mueve la aguja" = cuánto pesa ante el jurado.

| # | Diferenciador | Impacto jurado | Esfuerzo | Quick win | Qué prueba ante el jurado |
|---|---------------|:-------------:|:--------:|:---------:|---------------------------|
| **D1** | **Baseline naive de persistencia** (t+1=t) como vara de medir obligatoria | **A** | **B** | ⭐ **#1** | Honestidad científica: el modelo aporta sobre lo trivial (o admite que no) |
| **D2** | **Corregir el leakage** (Optuna→validación) y reportar métrica honesta de test | **A** | **B** | ⭐ **#2** | Rigor: tus números resisten una auditoría |
| **D3** | **Forecast recursivo real t+1→t+2** + backtesting rolling | **A** | **M** | — | Que predices el futuro de verdad, no usando el dato intermedio real |
| **D4** | **Análisis de error por segmento** (departamento, carácter, tamaño) | **A** | **B** | ⭐ **#3** | Madurez de producto: sabes dónde confiar y dónde no |
| **D5** | **Interpretabilidad SHAP** con narrativa de política pública | **A** | **M** | — | Que el modelo es accionable, no una caja negra |
| **D6** | **Feature engineering**: tendencia, momentum, volatilidad, COVID, tamaño IES | **M** | **M** | — | Que entiendes el fenómeno, no solo apilas lags |
| **D7** | **Narrativa de impacto cuantificada** (N IES detectadas, ventana de antelación) | **A** | **B** | — | El "para qué" — lo que un jurado de impacto social más valora |
| **D8** | **Dashboard / entregable visual** (mapa departamental + ranking de riesgo) | **A** | **M** | — | El proyecto se "ve", la secretaría puede usarlo mañana |
| **D9** | **Intervalos de predicción conformales** | **M** | **M** | — | Sello de seriedad: comunicas incertidumbre, no un número falso-exacto |
| **D10** | **Acotar el target en origen + limpiar mojibake** (data quality) | **M** | **B** | — | Que no entrenas con artefactos del SNIES (tasa de 138700%) |
| **D11** | **Reproducibilidad**: requirements pineado, semilla Optuna, persistencia del modelo | **M** | **B** | — | Que el jurado puede reproducir tu resultado |
| **D12** | **Métrica de ranking/priorización** (Precision@k, no solo RMSE) | **A** | **M** | — | Que mides la tarea REAL (priorizar IES), no una regresión abstracta |

### Los 3 quick wins que más mueven la aguja

> **⭐ QW#1 — Baseline naive de persistencia.** ~30 líneas de código. Es la pregunta que cualquier jurado técnico hará primero: *"¿esto le gana a no hacer nada?"*. Ya lo calculé: **naive = RMSE 10.07 / MAE 4.42**; modelo = 9.48/4.23. Tenerlo en una tabla comparativa es la diferencia entre "presumimos un modelo" y "demostramos que aporta valor medible".
>
> **⭐ QW#2 — Corregir el leakage de Optuna.** Cambiar 2 líneas (`x_test→x_val`, `y_test→y_val` en `model.ipynb · celda 9 · líneas 28-29`). Sin esto, cualquier número que reportes es indefendible y un jurado experto lo detectará en 5 minutos, hundiendo toda la credibilidad del trabajo.
>
> **⭐ QW#3 — Error por segmento.** ~1 hora. Un groupby del error absoluto por departamento y carácter institucional. Convierte "el modelo se equivoca 4.23 pp" (poco útil) en *"el modelo es confiable para universidades oficiales (MAE 3) pero no para instituciones técnicas pequeñas (MAE 9), donde recomendamos cautela"*. Esto es exactamente el lenguaje que una secretaría de educación necesita.

---

## 2. Diferenciador por diferenciador (con evidencia y plan)

### D1 ⭐ — Baseline naive de persistencia *(Impacto A / Esfuerzo B)*

**Por qué importa.** En forecasting de series, el baseline obligatorio es la **persistencia**: predecir que el próximo período es igual al último (`t+1 = t`). Si un modelo con XGBoost + Optuna + 100 trials no le gana cómodamente, el modelo no está aportando señal.

**Evidencia (ya medida, no inventada).** Computé el baseline sobre el split de test real (`entrenamiento_csv/X_test.csv`, n=529 filas, 2024):

| Modelo | RMSE | MAE | Ratio |
|--------|:----:|:---:|:-----:|
| Naive persistencia (pred = `lag1`) | **10.07** | **4.42** | 2.28 |
| Naive media móvil 4 lags | 10.42 | 4.69 | — |
| XGBoost + Optuna (README, **con leakage**) | 9.48 | 4.23 | 2.24 |

El modelo "ganador", **incluso haciendo trampa con el test en Optuna**, apenas mejora 0.59 RMSE y 0.19 MAE sobre copiar el último dato. Una vez corregido el leakage (QW#2), es muy probable que el margen se reduzca aún más o desaparezca.

**Qué hacer (entregable).** Tabla comparativa modelo vs naive en el README, con esta frase: *"El modelo debe justificar su complejidad superando a la persistencia. Reportamos ambos para transparencia."* Si tras corregir el leakage el modelo sí gana, es tu argumento más fuerte. Si no gana, la jugada ganadora es pivotar el valor del proyecto hacia **clasificación de riesgo / ranking** (ver D12), donde un modelo bien calibrado sí puede aportar sobre el naive.

---

### D2 ⭐ — Corregir el leakage y reportar métrica honesta *(Impacto A / Esfuerzo B)*

**Evidencia.**
- `model.ipynb · celda 9 · líneas 28-29`: `y_pred = modelo.predict(x_test)` → `return np.sqrt(mean_squared_error(y_test, y_pred))`. **Optuna minimiza el RMSE de test**, eligiendo hiperparámetros que se ajustan al test.
- `model.ipynb · celda 10 · líneas 16-18`: el modelo final reentrena con esos `best_params` contaminados y **vuelve a medir sobre test**.
- `model.ipynb · celda 7 · líneas 3,7-9`: el baseline también reporta sobre `x_test/y_test`.
- `README.md · líneas 78 y 89`: afirman que Optuna optimiza "sobre el set de validación" y que el test "no se usó en optimización". **Esto es falso según el código.** Un jurado que lea ambos lo detectará.

**Qué hacer.** En `celda 9`, cambiar `x_test/y_test` por `x_val/y_val` en la línea de retorno del `objective`. Reportar la métrica de test **una sola vez**, al final, con el modelo ya congelado. Actualizar el README para que coincida con el código.

**Riesgo si no se hace.** Es el hallazgo más fácil de detectar para un jurado técnico y el que más daño hace: invalida los 9.48/4.23 y contamina la confianza en todo lo demás.

---

### D3 — Forecast recursivo real t+1→t+2 + backtesting *(Impacto A / Esfuerzo M)*

**Evidencia del problema (confirmada abriendo los CSV).**
- `dataset.ipynb · celda 7 · líneas 8-12`: cada fila usa `tasas[i-4..i-1]` (lags reales) y `target = tasas[i]`.
- `dataset.ipynb · celda 19 · líneas 1-3`: el test incluye `2024-1` y `2024-2` como filas **independientes**, cada una con sus lags reales.
- **Prueba directa en `entrenamiento_csv/X_test.csv`**: para la misma IES de Bogotá, la fila de 2024-1 tiene `lag1=4.58` y `target` real `6.05`; la fila de 2024-2 tiene `lag1=6.05`. Es decir, **2024-2 recibe como entrada la deserción real de 2024-1, no la predicha**. El README (`líneas 76`) describe un encadenamiento recursivo que el código no implementa.

**Por qué importa.** En producción real (junio 2026, prediciendo 2026-1 y 2026-2), no tendrás el dato real de 2026-1 cuando predigas 2026-2. La evaluación actual sobrestima el desempeño en el horizonte t+2 porque le filtra el semestre intermedio real.

**Qué hacer.** Implementar el loop recursivo: predecir t+1, **inyectar esa predicción como `lag1`** para predecir t+2, y medir el error de t+2 honestamente. Complementar con **backtesting rolling** (validar sobre 2022, 2023 y 2024 por separado, no solo un semestre) para reportar varianza del error — hoy la validación es un único semestre (`val` n=265, `dataset.ipynb · celda 19 · línea 2`), lo que da métricas de alta varianza.

---

### D4 ⭐ — Análisis de error por segmento *(Impacto A / Esfuerzo B)*

**Por qué importa.** Un MAE global de 4.23 pp esconde heterogeneidad enorme. El target de test tiene `media=14.57, mediana=10.85, std=13.47, máx=100` (medido sobre `y_test.csv`): la cola es pesada. Decir *dónde* el modelo es confiable es lo que convierte un número en una herramienta de decisión.

**Qué hacer (entregable concreto).** Tabla de error absoluto medio desglosado por:
- **Departamento** (`DEPARTAMENTO`, 28 categorías) → mapa de confiabilidad.
- **Carácter institucional** (`CARACTER`: Universidad, Institución universitaria, tecnológica, técnica profesional).
- **Tamaño de IES** (cuartiles de `MATRICULADOS`, disponible en `df_forecast_raw.csv`).
- **Nivel de tasa** (¿predice peor las IES de alta deserción, que son justo las prioritarias?).

**Narrativa para el jurado:** *"El modelo es fiable para universidades grandes y consolidadas; en instituciones pequeñas con series volátiles recomendamos usar la predicción solo como señal de alerta, no como cifra exacta."* Esto demuestra madurez de producto y honestidad, dos cosas que los jurados de impacto social premian.

---

### D5 — Interpretabilidad con SHAP *(Impacto A / Esfuerzo M)*

**Estado actual.** Solo hay `feature_importances_` (gain) en `model.ipynb · celda 11`, que es global y sesgado hacia features de alta cardinalidad — y `MUNICIPIO` (67 categorías) actúa como proxy de identidad de la IES, contaminando la importancia.

**Qué hacer.** SHAP (`shap.TreeExplainer`) sobre el modelo final. Esto da:
- **Drivers de riesgo** a nivel global y por IES individual (la deserción reciente `lag1` casi seguro domina; lo valioso es cuantificar el aporte de `semestre`, `CARACTER`, tendencia).
- **Narrativa de política pública**: *"el principal predictor del riesgo futuro es la trayectoria reciente de deserción y el carácter institucional; las técnicas profesionales muestran mayor riesgo base"*. Eso es accionable para una secretaría.

**Advertencia de honestidad técnica.** SHAP sobre `MUNICIPIO`/`DEPARTAMENTO` puede estar memorizando la identidad de la IES en vez de capturar causalidad. Hay que aclararlo en la narrativa: el modelo identifica *patrones de trayectoria*, no causas estructurales de la deserción.

---

### D6 — Feature engineering: tendencia, momentum, volatilidad, COVID, tamaño *(Impacto M / Esfuerzo M)*

El propio README lo lista como "próximo paso" (`líneas 139`). Implementarlo es un diferenciador barato:

| Feature | Definición | Hipótesis de valor |
|---------|-----------|--------------------|
| **Tendencia** | `lag1 - lag4` | Captura si la deserción sube o baja en 2 años |
| **Momentum** | `lag1 - lag2` | Aceleración reciente — señal temprana de deterioro |
| **Volatilidad** | `std(lag1..lag4)` | IES inestables = mayor incertidumbre/riesgo |
| **Dummy COVID** | `1` si `periodo_target ∈ {2020-1, 2020-2, 2021-1}` | El shock pandémico distorsiona la serie; marcarlo evita que contamine |
| **Tamaño IES** | `log(MATRICULADOS)` | Controla el artefacto de denominador pequeño (ver D10) |

**Nota de rigor:** todas estas features se derivan de lags ya presentes (no introducen leakage; son la misma serie transformada). El dummy COVID es especialmente vendible ante el jurado: muestra que entiendes el contexto colombiano 2020-2021.

---

### D7 — Narrativa de impacto cuantificada *(Impacto A / Esfuerzo B)*

**Por qué importa.** Es un concurso de **impacto social**, no un Kaggle. El jurado quiere el "para qué", traducido a números.

**Qué hacer (frases listas para el pitch, a completar con tus cifras).**
- *"Con un año de antelación, el modelo identifica las **N IES** con mayor probabilidad de deterioro de su deserción, permitiendo a las secretarías de educación priorizar acompañamiento dentro del ciclo presupuestal anual."*
- *"De las 277 IES monitoreadas, el modelo señala las **top-20 en riesgo creciente**, concentrando recursos donde más impacto social hay."*
- **Cuantifica el costo evitado**: cada punto de deserción evitado = X estudiantes que permanecen × inversión pública por estudiante. Aunque sea una estimación, ancla el valor.

**Conexión con el README**: ya tienes la narrativa "reactivo→activo" (`líneas 33, 43`). Falta cerrarla con números de detección concretos.

---

### D8 — Dashboard / entregable visual *(Impacto A / Esfuerzo M)*

**Por qué importa.** Un mapa por departamento y un ranking de IES en riesgo hacen el proyecto **tangible** para un jurado no técnico. Es la diferencia entre "tenemos un modelo" y "una secretaría puede abrir esto mañana".

**Qué hacer (mínimo viable, alto retorno).**
- **Mapa coroplético** de Colombia con tasa proyectada por departamento (28 departamentos en datos). Streamlit o incluso un notebook estático con `geopandas`.
- **Ranking de IES en riesgo**: tabla ordenada por tasa proyectada 2026 + flag de tendencia (↑/↓ usando momentum).
- **Ficha por IES**: serie histórica + predicción + intervalo (ver D9).

Streamlit es suficiente; no necesita despliegue productivo para impresionar.

---

### D9 — Intervalos de predicción conformales *(Impacto M / Esfuerzo M)*

**Por qué importa.** Reportar "4.58%" como predicción puntual es deshonesto cuando el MAE es ~4 pp. **Conformal prediction** (split conformal, calibrado sobre validación) da intervalos con cobertura garantizada sin supuestos distribucionales — perfecto para XGBoost.

**Qué hacer.** Usar `mapie` o split conformal manual: predecir *"la deserción de la IES X en 2026-1 estará entre 8% y 16% con 90% de confianza"*. Es un sello de seriedad que casi ningún competidor tendrá, y es honesto con la incertidumbre real del SNIES.

---

### D10 — Acotar el target en origen + limpiar mojibake *(Impacto M / Esfuerzo B)*

**Evidencia (medida en `df_forecast_raw.csv`).**
- La tasa **no está acotada en origen**: `máx = 138700.00%`, con **153 filas > 100%** y **62 filas > 200%** (artefactos del SNIES por denominador `MATRICULADOS` pequeño, ej. =1). El clip `[0,100]` se aplica tarde: `dataset.ipynb · celda 15`, **después** de construir las ventanas en `celda 7`, y de forma **inconsistente** con el baseline de `model.ipynb · celda 7 · línea 5` (clip comentado) vs `celda 10 · línea 16` (clip aplicado).
- **Mojibake** en la categoría `CARACTER` usada por el modelo: valores como `Institución universitaria/Escuela Tecnológica` aparecen corruptos (encoding del SNIES). Esto es una de las 4 features categóricas (`model.ipynb · celda 4 · línea 1`).

**Qué hacer.** (1) Filtrar o capar las tasas absurdas **antes** de construir ventanas, idealmente con una regla de negocio (descartar IES-período con `MATRICULADOS` por debajo de un umbral mínimo). (2) Reparar el encoding leyendo con `encoding='latin-1'`/`utf-8` correcto. (3) Unificar el clip en un único punto del pipeline. Es data quality barata que un jurado riguroso valorará.

---

### D11 — Reproducibilidad *(Impacto M / Esfuerzo B)*

**Evidencia.**
- `optuna.create_study(direction='minimize')` **sin sampler con semilla** (`model.ipynb · celda 9 · línea 31`) y sin `np.random.seed` → `best_params` y métrica **no reproducibles** entre ejecuciones. Ironía: el README presume "datos no vistos durante optimización" pero ni siquiera la optimización es determinista.
- **No se persiste el modelo ni los `best_params`** (sin `.pkl`/`.json` en todo `model.ipynb`).
- **Sin `requirements.txt`** con versiones pineadas (solo `pip install ...` sin versiones, `README.md · línea 125`).
- **Código muerto**: `MultiOutputRegressor` importado (`celda 1 · línea 4`) y nunca usado; `periodo_num` calculado (`dataset.ipynb · celda 5 · líneas 2-3`) y ausente de las features (`celda 25 · línea 1`).

**Qué hacer.** `TPESampler(seed=42)` en Optuna, `model.save_model()` + `json.dump(best_params)`, `requirements.txt` con `pip freeze`, eliminar imports/variables muertas. Todo trivial, suma profesionalismo.

---

### D12 — Métrica de priorización/ranking, no solo RMSE *(Impacto A / Esfuerzo M)*

**Por qué importa (y por qué es la jugada estratégica).** El README dice que el objetivo real es **priorizar IES en riesgo** (`líneas 17-20, 43-44`), pero la métrica reportada (RMSE/MAE) mide regresión punto-a-punto, **no la tarea real**. Y como vimos en D1, en regresión el modelo apenas le gana al naive.

**La oportunidad:** si reformulas la evaluación como **ranking/clasificación de riesgo** —¿el modelo identifica correctamente las top-20 IES que más empeoran?— puedes:
- Reportar **Precision@k / Recall@k** y **AUC** sobre "IES que cruzan un umbral de riesgo".
- Demostrar valor incluso si el RMSE no le gana al naive (priorizar el orden es más fácil y más útil que clavar el decimal).
- Alinear métrica con narrativa de impacto: *"el modelo acierta 17 de las 20 IES de mayor deterioro"* es infinitamente más vendible que "RMSE 9.48".

Esta es la pieza que reconcilia "el modelo apenas le gana al naive en RMSE" con "el modelo sí aporta valor de política pública".

---

## 3. Plan de ataque sugerido (orden de ejecución)

**Fase 1 — Blindaje (1 día, esfuerzo B, impacto A):** D2 (corregir leakage) + D1 (baseline naive en tabla). Sin esto, nada de lo demás importa.

**Fase 2 — Diferenciación de producto (2-3 días):** D4 (error por segmento) + D12 (métrica de ranking) + D7 (narrativa cuantificada). Esto construye la historia de impacto.

**Fase 3 — Sello de rigor (2-3 días):** D5 (SHAP) + D3 (recursivo + backtesting) + D9 (conformal). Esto impresiona al jurado técnico.

**Fase 4 — Vitrina (2 días):** D8 (dashboard) + D6 (features) + D10/D11 (data quality y reproducibilidad). Esto hace el proyecto memorable y reproducible.

---

## 4. Riesgo central a comunicar internamente

El mayor riesgo no es técnico, es de **credibilidad**: el README afirma cosas que el código contradice (leakage de Optuna, forecast recursivo). Un jurado experto que abra `model.ipynb · celda 9` perderá confianza en todo el proyecto. **La estrategia ganadora es la transparencia radical**: corregir, reportar el baseline naive honestamente, y reposicionar el valor en priorización (D12) e impacto (D7) en lugar de defender un RMSE frágil. Un proyecto que dice *"medimos contra el baseline trivial y aquí está exactamente cuánto aportamos, y dónde no"* es mucho más premiable que uno que presume un número que no resiste el escrutinio.

---

*Notas de verificación: baseline naive (10.07/4.42) y media móvil (10.42/4.69) calculados directamente sobre `entrenamiento_csv/X_test.csv` y `y_test.csv` (n=529). Estadísticas de target y artefactos (138700%, 153 filas >100%) medidas sobre `df_forecast_raw.csv` (13.668 filas, 277 IES). Todas las citas de celda/línea verificadas sobre los notebooks reales. No se ejecutaron los notebooks; solo se leyeron datos y código. La carpeta EX referida en el brief no existe en el árbol del proyecto, por lo que se citó directamente desde REPO.*
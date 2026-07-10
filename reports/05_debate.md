# 05 — Debate del Consejo: ¿Puede ganar este proyecto?

**Proyecto:** Forecast de deserción por IES (SNIES/MEN) — Concurso "Datos al Ecosistema 2026: IA para Colombia"
**Formato:** Debate adversarial (Abogado Defensor vs. Fiscal) + Veredicto del Juez
**Fecha:** 2026-06-28
**Alcance:** 100% lectura. Citas `archivo · celda N · línea M` verificadas sobre los notebooks reales y los informes hermanos (`reports/01`, `02`, `03`, `06`). No se ejecutó ningún notebook.

> **Nota de procedencia.** La carpeta `EX/` con extractos `code_*.txt` y `data_profile.txt` **no existe en este checkout** (confirmado por los informes 01 y 06). Todas las citas se construyeron leyendo directamente los `.ipynb` y los CSV de split ya generados. La evidencia central (C1) la verifiqué verbatim en `entrenamiento_csv/model.ipynb · celda 9 (id 7e313e16) · líneas 28-29 y 31`.

---

## Acta de apertura

Tres voces, una pregunta: **¿este proyecto compite por ganar "Datos al Ecosistema 2026" en su estado actual, o lo descalifica el primer jurado con perfil de ciencia de datos que abra el notebook?**

El concurso —confirmado oficial (MinTIC/datos.gov.co), 349 equipos, final presencial primera semana de agosto en GovCamps 2026 (`reports/03 §1.1-1.2`)— premia **impacto + uso responsable del dato + solidez metodológica + comunicación**, no solo la métrica (`reports/03 §1.4`). Eso enmarca todo lo que sigue: la métrica titular RMSE 9.48 / MAE 4.23 es una fracción de la nota, pero la **credibilidad metodológica** es un multiplicador de toda la propuesta.

---

## Ronda 1 — Alegatos de apertura

### ABOGADO DEFENSOR

> "Señorías, lo que tienen delante no es un notebook de Kaggle más. Es una **propuesta de política pública bien construida** que resuelve un problema nacional real con datos abiertos del Estado. Y el concurso premia exactamente eso.

> **Primero, el framing.** El README (líneas 29-47) articula el cambio de paradigma *reactivo → activo*: dar a las secretarías de educación ~1 año de anticipación para priorizar intervenciones, alineado con los ciclos de presupuesto y gobierno. Esto no es relleno: el informe web confirma que el jurado valora 'resolver problemas reales de impacto nacional, sectorial o territorial' (`reports/03 §1.4`). El README es, según la propia auditoría técnica, **'excelente'** (`reports/01`, sección 'Lo que está bien', línea 161) — y eso lo dice el fiscal de la casa, no yo.

> **Segundo, el diseño de modelo es el correcto para el problema.** Un **único XGBoost global** entrenado sobre las 277 IES con `enable_categorical` por IES/departamento/municipio: esto es *cross-learning*, exactamente la arquitectura que **ganó la M5 de Walmart** (ensemble de LightGBM globales). El informe web lo dice sin ambigüedad: 'Nuestro enfoque ya es un modelo global... conceptualmente correcto y alineado con M5. Bien' (`reports/03 §3.1`). Es nuestra mayor fortaleza técnica.

> **Tercero, el rigor de datos es real donde importa.** El diagnóstico de cobertura es riguroso: verifica el rango [primer, último] período contra el conjunto esperado y detecta huecos internos (≥20 períodos consecutivos), reteniendo 277/343 IES (`reports/01`, DQ-COBERTURA). El manejo de NaN con `min_count=1` es ingeniería defensiva correcta. La alineación de categorías train→val/test con `cat.set_categories` (`model.ipynb · celda 4`, id `1ff1a797`) evita fuga inversa — la auditoría lo marca **BIEN** (B1, NUEVO-ML-2). Y el split temporal es **conceptualmente correcto**: entrena en pasado, valida el semestre siguiente, testea el año posterior, sin barajado (INT-1, ML-10, ambos **BIEN**). No hay solapamiento de filas (IES, período) entre particiones: intersección = 0.

> **Cuarto, honestidad documental.** El README reconoce explícitamente los artefactos del SNIES y por qué se descarta el horizonte a 2 años (línea 47). Eso es madurez, no debilidad.

> En un concurso que pesa impacto + comunicación + uso del dato tanto como la métrica, **este equipo ya tiene construido el 60% de lo difícil de enseñar: la narrativa y el esqueleto correcto.** Lo que falta son correcciones acotadas, no una reescritura."

### FISCAL

> "Señorías, admiro el discurso del defensor. Pero un jurado técnico no puntúa el README: **abre `model.ipynb` y lee la función objetivo.** Y cuando lo haga, encontrará esto, verbatim, en `entrenamiento_csv/model.ipynb · celda 9 (id 7e313e16) · líneas 28-29`:

> ```python
> y_pred = modelo.predict(x_test)
> return np.sqrt(mean_squared_error(y_test, y_pred))
> ```

> Y dos líneas abajo (línea 31): `study = optuna.create_study(direction='minimize')`, optimizado 100 veces (línea 32). **Optuna está eligiendo los hiperparámetros minimizando el RMSE del conjunto de TEST.** El `eval_set=[(x_val, y_val)]` (línea 24) solo controla el early stopping; la *selección* del mejor trial mira el test. Esto es **C1, leakage de selección de modelo, CRÍTICO y confirmado** (`reports/01`, C1).

> Y aquí está el agravante reputacional: el README **afirma lo contrario**. Línea 78: 'Optuna con 100 ensayos buscando los mejores hiperparámetros sobre el set de validación'. Línea 89: 'datos no vistos durante entrenamiento ni optimización'. **Las dos afirmaciones son falsas respecto al código.** No es solo un bug; es una afirmación de la propuesta que el código desmiente. Un evaluador de ciencia de datos que lo detecte no piensa 'error honesto': piensa 'no puedo confiar en ninguna métrica de este equipo'. El informe web lo llama 'riesgo reputacional crítico' que 'destruye la credibilidad de solidez metodológica' (`reports/03 §1.4`).

> **Segundo cargo: C2, leakage temporal, también CRÍTICO.** El README (línea 76) promete un 'enfoque recursivo... para obtener la predicción del segundo semestre se encadena la salida del primero como entrada'. **Eso no existe en el código.** `dataset.ipynb` (celda ventana, id `e7bb2962`) construye los lags con tasas REALES; el split (id `83a85286`) mete 2024-1 y 2024-2 como filas independientes y `model.ipynb` las predice todas de una vez (one-step). Para 2024-2, `lag1` es la deserción **real** de 2024-1 — verificado: en las 264 IES con fila 2024-2, `lag1` == tasa real de 2024-1 en 264/264 casos (`reports/01`, C2). En producción, al pronosticar desde 2023-2, la tasa de 2024-1 **no se conoce**. El modelo está leyendo el futuro intermedio.

> **Tercer cargo, y el que mata el caso del defensor: el modelo no aporta valor demostrable.** La auditoría reprodujo de forma independiente el **baseline naive de persistencia** (`y = lag1`, repetir la última tasa) sobre los MISMOS splits (`reports/01`, ML-2):
> - Persistencia en TEST: **RMSE 10.07 / MAE 4.42**
> - Modelo XGBoost (¡con el leakage inflándolo!): RMSE 9.48-9.51 / MAE 4.16-4.23
> - Persistencia en VALIDACIÓN: **RMSE 8.18 / MAE 3.15** — *mejor* que la métrica de test publicada.

> El modelo, haciendo trampa al mirar el test, mejora ~0.6 RMSE sobre **no hacer nada y repetir el último número**. El informe web es lapidario: en las competencias M, 'solo ~7.5% de los equipos logró batir el benchmark de suavizamiento exponencial'; sin baseline naive 'no podemos demostrar que el XGBoost aporta valor sobre repetir la última tasa' (`reports/03 §4.1, G1`). **Y este proyecto no reporta ningún baseline.**

> **Cargos menores que cierran el caso:** Optuna sin sampler con semilla (`create_study` sin `TPESampler(seed=...)`, línea 31) → las cifras del README no son reproducibles bit-a-bit; de hecho el notebook actual da 9.51/4.16 y el README dice 9.48/4.23, prueba de corrida no sembrada (R1, `reports/06`). No hay `requirements.txt` (R2). No se persiste el modelo ni los `best_params` — el 'modelo entregado' no existe como artefacto (A3). Validación de **un solo semestre** (2023-2, 265 filas), sin backtesting (ML-7).

> Señorías: la métrica titular es **de test, con doble leakage, no reproducible, y apenas supera a una línea de código trivial.** Un jurado técnico no la descarta por dura: la descarta porque **es falsa**."

---

## Ronda 2 — Réplicas

### DEFENSOR (réplica)

> "El fiscal tiene razón en los hechos. No los discuto: C1 y C2 están en el código. Pero discuto la **sentencia**.

> **Punto 1 — el daño es reparable y barato.** C1 se arregla cambiando dos referencias: `x_test/y_test` → `x_val/y_val` en la línea 28-29 de la celda 9. El propio informe lo dice: 'redirigir la métrica de selección de Optuna de test a val' (`reports/01`, ML-10). El esqueleto temporal ya es correcto (INT-1, ML-10 **BIEN**); no hay que rediseñar nada, solo redirigir la métrica y tocar el test una vez. C2 se arregla implementando el encadenamiento recursivo que el README *ya describe* — la intención está, falta el código.

> **Punto 2 — el baseline no es una condena, es un regalo.** El fiscal dice que el modelo apenas bate la persistencia. De acuerdo. Pero eso significa que **el equipo ya tiene medido su baseline** (lo midió la auditoría, es trivial de incorporar) y puede convertirlo en un argumento de honestidad: 'comparamos contra persistencia y reportamos la diferencia real'. Eso es exactamente lo que premian los jurados de datathon LatAm: rigor honesto sobre métricas infladas.

> **Punto 3 — el concurso no es Kaggle.** No hay leaderboard privado automático. La nota es impacto + uso del dato + comunicación + metodología (`reports/03 §1.4`). Tenemos ventaja estructural en tres de cuatro ejes. Si cerramos el eje metodológico (C1/C2/baseline), pasamos de 'descalificable' a 'competitivo con diferenciadores' (SHAP, intervalos conformales, dashboard — `reports/03 §5`, G3/G4/G8).

> El proyecto no está roto. Está **a unas horas de ingeniería de ser defendible.**"

### FISCAL (contrarréplica)

> "Tres precisiones, señorías.

> **Una: 'reparable' no es 'reparado'.** El defensor pide que se juzgue el proyecto que *podría* existir tras los fixes, no el que está en el repo. Pero el jurado evalúa lo que se entrega. Hoy, lo que se entrega afirma en el README (líneas 78, 89) algo que el código contradice. Si el equipo presenta esto sin corregir, el README pasa de activo a **prueba de cargo**: documenta una metodología que el notebook no implementa.

> **Dos: corregir C1/C2 probablemente *empeora* la métrica titular.** El informe lo dice: 'la métrica honesta será peor que 9.48/4.23, con el mayor deterioro en t+2' (`reports/01`, IMP-1). Cuando Optuna optimice sobre validación y el forecast sea recursivo real, el RMSE honesto subirá y el margen sobre la persistencia (~0.6) se estrechará o desaparecerá. **El defensor está pidiendo arreglar el código para que el modelo se vea peor.** Es lo correcto éticamente, pero destruye el argumento de 'tenemos un gran resultado'.

> **Tres: el sesgo de supervivencia sigue ahí aunque arreglen el leakage.** El filtro ≥20 períodos descarta 66/343 IES — las nuevas, pequeñas, intermitentes, que son **justo las de mayor interés de política pública** (`reports/01`, DQ-COBERTURA). El modelo solo ve IES grandes, antiguas y estables. Y la metadata categórica colapsa cada IES a un municipio fijo vía `groupby.first` (`dataset.ipynb · celda 9`), de modo que MUNICIPIO (67 niveles) actúa como **proxy de identidad institucional** (CA1, `reports/06`): el modelo memoriza el nivel de cada IES vía su municipio, sin generalizar a IES nuevas. El producto promete priorizar IES en riesgo, pero no puede puntuar a las que no tienen 10 años de historia.

> Mantengo el cargo: en su estado actual, **es descalificable ante un jurado técnico.** Concedo que es *recuperable*. No es lo mismo."

---

## Ronda 3 — El punto que ambos conceden

Hay un terreno donde defensor y fiscal coinciden, y conviene fijarlo para el veredicto:

| Tema | Consenso de ambas partes |
|---|---|
| Diseño del modelo global | Correcto y alineado con M5 (`reports/03 §3.1`). No tocar. |
| Split temporal (concepto) | Correcto, sin solapamiento de filas (INT-1, ML-10). No tocar. |
| README / narrativa | Excelente como comunicación; **pasivo si no se corrigen las afirmaciones falsas** (líneas 78, 89, 76). |
| C1 (Optuna sobre test) | Real, CRÍTICO, y **barato de arreglar** (2 líneas). |
| C2 (sin recursivo real) | Real, CRÍTICO, requiere implementar el encadenamiento. |
| Baseline | Inexistente hoy; el modelo apenas lo supera. **Debe reportarse.** |
| Efecto neto de los fixes | La métrica honesta **bajará**; el valor del proyecto pasa a depender de impacto + diferenciadores, no del número. |

---

## VEREDICTO DEL JUEZ

He escuchado a ambas partes. Mi síntesis es la siguiente, y es honesta con las dos.

**El defensor tiene razón sobre el potencial; el fiscal tiene razón sobre el presente.** Este es un proyecto con un **esqueleto correcto y una narrativa de política pública genuinamente fuerte**, herido por **dos leakages críticos confirmados en código (C1, C2)** que (a) invalidan la métrica titular, (b) contradicen afirmaciones explícitas del README, y (c) ocultan que el modelo apenas supera a repetir el último número. En un concurso que pesa metodología junto a impacto y comunicación, **presentarlo sin corregir es un riesgo de descalificación reputacional**: el primer jurado con perfil de datos que lea la celda 9 dejará de creer todo lo demás.

Pero el daño es **reparable en horas, no en semanas**, y al repararlo el proyecto no pierde su mayor activo (la narrativa y el diseño global). El veredicto, por tanto, no es "descártenlo": es **"no lo presenten hasta cerrar el bloque must-fix, y entonces apóyense en los diferenciadores, no en la métrica."**

### Sentencia priorizada

#### MUST-FIX (sin esto, no se presenta — bloquea credibilidad metodológica)

1. **Corregir C1 (Optuna → validación).** En `model.ipynb · celda 9 · líneas 28-29`, cambiar `predict(x_test)` / `mean_squared_error(y_test, …)` por `x_val` / `y_val`. Seleccionar `best_params` por validación; tocar el test **una sola vez** al final. Esfuerzo: minutos.
2. **Corregir el README (líneas 76, 78, 89).** Hacer que describa lo que el código *realmente* hace. Mientras C1/C2 no se arreglen, estas líneas son afirmaciones falsas; tras arreglarlos, deben reflejar el protocolo honesto. Esfuerzo: minutos.
3. **Reportar el baseline de persistencia** (y la media) con el mismo protocolo y splits (`reports/01`, ML-2; `reports/03`, G1). Condición de "el modelo aporta valor" = batir la persistencia. Esfuerzo: bajo.
4. **Implementar el forecast recursivo t+1→t+2 real (C2)** o, si no da tiempo, **declarar honestamente** que la evaluación es one-step (t+1) y retirar la promesa recursiva del README. Reportar RMSE/MAE separados por horizonte. Esfuerzo: medio (recursivo) / bajo (declarar).
5. **Sembrar Optuna** (`TPESampler(seed=42)` + `np.random.seed(42)`) y **persistir** `model_xgb.json` + `best_params.json` + `metrics.json` (`reports/06`, R1/A3). Sin esto, las cifras no son auditables ni reproducibles por el jurado. Esfuerzo: bajo.

#### DESEABLE (sube la nota; son los diferenciadores que recomienda el estado del arte)

6. **SHAP / explicabilidad** — estándar en la literatura de deserción; permite decir *por qué* una IES está en riesgo (`reports/03`, G3). Alto retorno para "uso del dato" e "impacto".
7. **Intervalos de predicción** (conformal: MAPIE / EnbPI) — convierte "será 14.2%" en "14.2% [10.1–18.3] al 90%"; diferenciador fuerte para decisiones de política pública con riesgo cuantificado (`reports/03`, G4).
8. **Métricas de ranking/priorización** (Precision@K, recall sobre "IES en riesgo") sobre validación — porque la tarea real es **ordenar**, no minimizar el error promedio, y con cola pesada el RMSE está dominado por pocas IES extremas (`reports/01`, ML-1).
9. **Cifras de impacto + dashboard + pitch ≤90s** — el README narra bien pero no cuantifica (# IES priorizables, # estudiantes cubiertos) (`reports/03`, G8).
10. **`requirements.txt` pineado** y limpieza de outputs de notebooks (R2, H3).

#### OPCIONAL (higiene y robustez; no mueve la nota del jurado a corto plazo)

11. Backtesting rolling-origin multi-ventana con media±σ del error (ML-7; M5-style).
12. Sacar el CSV de 99 MB del repo e historial (H1) — higiene, no seguridad (no hay PII de personas naturales, `reports/02`).
13. Saneamiento de la tasa en el EDA (clip/winsorize consistente antes de exportar; hoy llega a 138 700% por denominador=1) y mojibake de CARACTER (`reports/01`, DQ-TARGET, DQ-MOJIBAKE).
14. `.copy()` en los splits (A2), `LICENSE` (H4), eliminar código muerto (`MultiOutputRegressor`, `periodo_num`, `cargar_csv.py`).
15. Documentar el sesgo de supervivencia (66/343 IES excluidas) y que el modelo predice solo IES con historial, no IES nuevas (DQ-COBERTURA, CA1).

### Veredicto de competitividad

| Escenario | Competitividad (0-10) | Justificación |
|---|---|---|
| **Estado actual** (sin fixes) | **3.5 / 10** | Narrativa y diseño global fuertes (eje impacto/comunicación), pero la métrica titular es de test con doble leakage, contradice el README y apenas bate la persistencia. Un jurado técnico lo penaliza fuerte en "solidez metodológica" y puede contaminar la percepción del resto. No descalificado automáticamente (no hay leaderboard privado), pero **frágil ante el primer evaluador de datos**. |
| **Tras MUST-FIX** (1-5) | **6.0 / 10** | Metodología honesta y auditable. La métrica probablemente *baja* (IMP-1), pero la propuesta se vuelve **creíble** y el storytelling deja de ser un riesgo. Competitivo en el grupo medio-alto; aún sin diferenciadores técnicos visibles frente a otros equipos. |
| **Tras MUST-FIX + DESEABLE** (1-10) | **7.5–8.0 / 10** | Modelo global honesto + baseline + explicabilidad (SHAP) + intervalos conformales + métricas de priorización + dashboard/pitch con cifras. Esto **sí** diferencia: combina el eje que ya domina (política pública) con solidez metodológica y diferenciadores que el propio estado del arte recomienda (`reports/03 §5`). Candidato real a finalista. |

### Cierre del Juez

El número (9.48/4.23) **no es el activo de este proyecto; es su pasivo escondido.** El activo es la pregunta correcta (anticipar deserción por IES para priorizar política pública) atacada con la arquitectura correcta (modelo global). La tarea del equipo no es defender la métrica —debe dejar que baje a su valor honesto— sino **construir credibilidad alrededor del problema**: corregir el leakage, mostrar el baseline sin miedo, y apilar los diferenciadores (explicabilidad, intervalos, priorización, dashboard) que convierten un buen forecast en una **herramienta de decisión defendible ante un jurado**.

Sentencia: **recuperable y competitivo, condicionado a ejecutar el bloque MUST-FIX antes de presentar.** No antes.

*Honestidad metodológica: las magnitudes exactas del deterioro de la métrica tras corregir C1/C2 no se midieron (requeriría reentrenar, prohibido por alcance). La dirección está sustentada en código (C1/C2 verificados) y en los baselines reproducidos por `reports/01`. Los pesos exactos de la rúbrica del concurso no se confirmaron oficialmente (`reports/03`, nota de honestidad); las puntuaciones 0-10 son juicio del consejo sobre criterios oficiales confirmados (impacto, uso del dato, metodología, comunicación), no un cálculo sobre pesos publicados.*
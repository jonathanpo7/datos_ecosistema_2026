# 03 — Investigación Web: Estado del arte y contexto competitivo

**Proyecto:** Forecast de deserción por IES (SNIES/MEN) — Concurso "Datos al Ecosistema 2026: IA para Colombia"
**Rol:** Investigador externo (web)
**Fecha:** 2026-06-28
**Alcance:** Verificar la existencia y reglas del concurso; mapear el estado del arte en predicción/forecasting de deserción en Colombia; extraer técnicas de equipos ganadores en competencias de datos; recoger el consenso de la comunidad sobre forecasting de series cortas con XGBoost vs. alternativas; y cerrar con un gap analysis accionable.

> **Nota de honestidad metodológica.** El concurso SÍ existe y está confirmado en fuentes oficiales (MinTIC / datos.gov.co). Sin embargo, **no logré recuperar el documento oficial de "Términos de Referencia" con la rúbrica de puntuación exacta y sus pesos** (la página "story" de datos.gov.co es JS-renderizada y no expone el texto; el PDF de la presentación 2025 devolvió HTTP 502 de forma persistente). Por tanto, los criterios de evaluación que reporto provienen de (a) notas de prensa oficiales de MinTIC y (b) la estructura de la edición 2025, complementados con (c) rúbricas típicas de datathons LatAm. **Donde no hay pesos oficiales, lo digo explícitamente y marco la inferencia.**

---

## 1. El concurso "Datos al Ecosistema 2026: IA para Colombia"

### 1.1 Existencia y organización (confirmado)

- **Existe y es real.** Organizado por el **Ministerio TIC (MinTIC)** a través del portal **Datos Abiertos Colombia (datos.gov.co)**, como parte del Programa de Fortalecimiento de Capacidades Públicas Digitales. La edición 2026 lleva el subtítulo **"Inteligencia Artificial para Colombia"**.
- **Escala 2026:** **1.096 participantes** organizados en **349 equipos** multidisciplinarios. Los proyectos finalistas se presentarán en una **gran final presencial prevista para la primera semana de agosto**, dentro de **GovCamps 2026**.
- **Recursos:** los equipos pueden usar **más de 8.000 conjuntos de datos abiertos** del portal estatal (el SNIES/MEN es uno de ellos — encaja perfecto con nuestro proyecto).

### 1.2 Calendario (confirmado para 2026 / inferido del ciclo)

- **Inscripciones 2026:** abiertas **10–30 de abril de 2026** (cerradas a la fecha de este informe). *Implicación: la ventana de postulación ya cerró; el valor de este análisis es maximizar el desempeño en la fase de desarrollo/jurado, no la inscripción.*
- **Fase actual:** desarrollo con acompañamiento técnico.
- **Final:** primera semana de agosto 2026 (GovCamps).

### 1.3 Áreas temáticas (confirmado)

Salud, **seguridad, movilidad, educación y medio ambiente**. Nuestro proyecto cae de lleno en **educación** (deserción en educación superior) con cruce hacia **política pública territorial**.

### 1.4 Criterios de evaluación

**Confirmado por fuentes oficiales (fase final / jurado experto):** el jurado evalúa **impacto, escalabilidad y uso estratégico/responsable de los datos**, con énfasis en el **uso responsable, ético y creativo de los datos** y en **resolver problemas reales de impacto nacional, sectorial o territorial**.

**Requisito de equipo confirmado (edición 2025, muy probablemente vigente):** equipos de **2 a 4 personas, al menos una mujer**, con perfil especializado en analítica, ingeniería o ciencia de datos. *Verificar en los TdR 2026 que este requisito siga vigente — no pude confirmarlo para 2026.*

**Estructura típica de fases (basada en 2025):** (1) inscripción y postulación al reto; (2) ciclo de formación/talleres (metodologías ágiles, consumo de datos vía API del portal); (3) presentación ante jurado nacional y selección de finalistas.

**No pude confirmar oficialmente:** los **pesos porcentuales** por criterio, el **formato exacto de entregable** (¿repo + video + pitch + resumen ejecutivo?), ni los **premios** (las notas de MinTIC hablan de acompañamiento/escalamiento, no de premio monetario explícito).

**Rúbrica típica de datathons LatAm (referencia para llenar el vacío — INFERIDO, no oficial):** combinando las bases públicas de CEIC Datathon LatAm 2025 y Desafío Latam-NODO, los ejes recurrentes son:
1. **Pertinencia / relevancia** del problema (responde a un problema real con impacto local).
2. **Solidez metodológica** (calidad del análisis y de los modelos).
3. **Innovación / originalidad**.
4. **Impacto potencial** (alcance real, personas beneficiadas, cifras).
5. **Comunicación / pitch** (claridad, storytelling, demo, video, resumen ejecutivo).
6. **Ética, sostenibilidad y escalabilidad**.

> **Lectura para el proyecto:** en este formato, **la métrica del modelo (RMSE 9.48 / MAE 4.23) es solo una fracción** de la nota. "Impacto", "uso responsable del dato", "escalabilidad" y "comunicación" pesan tanto o más. El README actual ya está alineado con esto (narrativa reactivo→activo, política pública), pero **el leakage C1/C2 detectado por la auditoría es un riesgo reputacional crítico ante un jurado experto**: un evaluador con perfil de ciencia de datos puede detectar que "el test se usó en la optimización", lo que destruye la credibilidad de "solidez metodológica".

---

## 2. Estado del arte: predicción/forecasting de deserción en educación superior (Colombia y SNIES)

### 2.1 Contexto institucional colombiano

- **SPADIES** (Sistema para la Prevención de la Deserción en Educación Superior, MEN) es la herramienta oficial que pondera factores y riesgos de deserción a partir de datos reportados por las IES. El MEN clasifica las causas en cuatro dimensiones: **individuales, académicas, socioeconómicas e institucionales**. Es la referencia de política pública a la que nuestro proyecto debería citar/anclar.
- Existe un **modelo de Monte Carlo** (Razón Crítica, U. Tadeo) para proyectar la tendencia de deserción nacional como insumo de política pública (estimaba ~11.65% promedio 2022-1 a 2024-1, σ≈2.82%). **Esto valida nuestro supuesto del README de que la tasa nacional ronda 10–15%** y es un buen benchmark de "orden de magnitud" para contextualizar nuestro MAE de 4.23 pp.

### 2.2 Lo que hace la literatura técnica (modelos, features, métricas)

El patrón dominante en la literatura (Colombia, Ecuador, Finlandia, revisiones sistemáticas) es **clasificación a nivel de estudiante** (¿este alumno deserta sí/no?), **no forecasting de la tasa agregada por institución** como hace nuestro proyecto. Esto es importante: **nuestro enfoque (serie temporal de la tasa por IES) es relativamente original** frente al grueso de la literatura, lo cual es a la vez una oportunidad de diferenciación y una señal de que hay menos benchmarks directos.

Hallazgos cuantitativos representativos:

| Referencia | Enfoque | Modelo ganador | Métrica reportada | Features clave |
|---|---|---|---|---|
| Sistema inteligente deserción universitaria Colombia (RG 2025) | Clasificación, 104.147 registros de 1 universidad CO | **LightGBM** (sobre 7 algoritmos, +SMOTE) | F1 ponderado **0.8125** | 27 features de ingeniería; reclasificación del target |
| MDPI Appl. Sci. 2025 — *Early Warning desde el día 1* | Clasificación con datos pre-matrícula | **XGBoost** | (modelo de alerta temprana) | datos pre-inscripción |
| Caso universidad ecuatoriana (IEEE 2024) | ML + Deep Learning | comparativo | — | activity LMS, créditos, cursos reprobados |
| Estudio XGBoost vs RF | Clasificación | **XGBoost** (mejor sensibilidad) | AUC-ROC **0.69**, F1 **0.69**, sensibilidad 88% | académicas + socioeconómicas, **SHAP** |
| Balanced Random Forest (varios) | Clasificación desbalanceada | **BRF** | **AUC 0.94**, recall >0.8 clase positiva | — |
| Review MDPI Computers 2025 | Revisión ML/DL para dropout | — | — | features académicas, engagement, demográficas |

**Observaciones aplicables a nuestro proyecto:**
- **LightGBM y XGBoost dominan** la familia tabular en este dominio → nuestra elección de XGBoost es defendible y mainstream.
- **SHAP es prácticamente estándar** para explicar factores de riesgo. **Nuestro proyecto NO usa SHAP ni ninguna explicabilidad** → gap claro y barato de cerrar (alto valor para el criterio "uso del dato" e "impacto/política pública": permite decir *por qué* una IES está en riesgo).
- La literatura trabaja con **decenas de features** (27 en el estudio colombiano); nuestro modelo usa esencialmente **4 lags + semestre + carácter/origen/dpto/municipio**. El README ya lista feature engineering (tendencia, momentum, volatilidad) como "próximos pasos" — **ejecutarlo nos acerca al estado del arte**.
- El desbalanceo/artefactos del target es un tema recurrente (SMOTE, reclasificación del target). En nuestro caso el análogo es el **clipping a [0,100] y los artefactos del SNIES**, que el README ya reconoce con honestidad (bien).

---

## 3. Técnicas de los equipos GANADORES en competencias de datos

### 3.1 Forecasting (M4, M5) — lo que ganó

- **M5 (Walmart, demanda jerárquica): el 1er lugar usó un ensemble de modelos LightGBM "globales"** entrenados por agrupaciones (store, store-category, store-department) — **220 modelos**, cada serie pronosticada promediando ~6 modelos, con variantes recursiva y no recursiva. **Cross-learning**: un solo modelo aprende de muchas series relacionadas. **Validación robusta**: usaron las últimas 4 ventanas de 28 días midiendo **media Y desviación estándar del error** para elegir una solución precisa *y estable*.
- **M4: de los 17 métodos más precisos, 12 eran combinaciones (mayoritariamente estadísticas).** El ganador fue un **híbrido** (LSTM + suavizamiento exponencial). **Los métodos de ML "puros" rindieron pobremente**; ningún método domina en todas las series → **ensembles/combinaciones estadística+ML son lo más robusto**.

**Implicaciones directas:**
- Nuestro enfoque ya es **un modelo global** (un XGBoost para las 277 IES con `enable_categorical` por IES/dpto) — **conceptualmente correcto y alineado con M5**. Bien.
- **Falta lo que hizo ganar M5/M4:** (a) **ensemble/combinación** (al menos XGBoost + un baseline estadístico); (b) **validación que mide estabilidad** (no solo el RMSE de un split, sino media±σ sobre varias ventanas / backtesting); (c) **comparar contra baselines fuertes** (ver §4).

### 3.2 Kaggle / tabular — playbook de Grandmasters

- **Feature engineering = groupby aggregations** (con target encoding hecho *solo sobre train tras el split*, vía nested/expanding CV para no filtrar).
- **CV temporal = "time K-fold"**: entrenar solo con pasado, predecir futuro; recalcular features *después* del split temporal; usar `groupby().expanding()` para agregaciones sin fuga.
- **Anti-leakage es el tema #1**: "usar el futuro para predecir el pasado" en agregaciones/validación es el error que más penaliza y produce *shake-up* (caída brutal en el leaderboard privado). Nunca incluir datos externos ni duplicados en el set de validación; calcular medias/encodings solo desde train.

> **Conexión crítica con la auditoría:** el hallazgo **C1 (Optuna minimiza RMSE de TEST)** y **C2 (no hay forecast recursivo encadenado; 2024-2 usaría el lag real de 2024-1)** son *exactamente* las dos formas de leakage que la comunidad Kaggle identifica como las que matan una solución en el leaderboard privado. Un jurado técnico que reproduzca el notebook lo verá. **Corregirlos no es opcional para competir con seriedad.**

### 3.3 Datathons LatAm — qué premian los jurados (storytelling/impacto)

- **Siempre incluir cifras de impacto**: reducción de tiempos, # de personas beneficiadas, proyecciones claras. Los jurados quieren entender el alcance real.
- **Pitch de ~90 segundos** claro y persuasivo: problema → innovación → impacto esperado.
- Bonus por **componente social fuerte y enfoque de género/inclusión**, y por **liderazgo de mujeres** en el equipo (consistente con el requisito "al menos una mujer").
- Entregables típicos: **demo/pitch + video técnico + resumen ejecutivo + documentación**.

> Nuestro README ya tiene excelente storytelling de política pública (reactivo→activo, secretarías de educación, benchmark de buenas prácticas). **Falta traducirlo a cifras de impacto concretas** (p. ej. "permite priorizar las N IES de mayor riesgo con un año de anticipación, cubriendo X estudiantes") y a un **pitch/demo/dashboard**.

---

## 4. Comunidad: forecasting de SERIES CORTAS con XGBoost vs. alternativas

Este es el punto técnico más sensible del proyecto, porque tenemos **pocas observaciones por serie** (~20 períodos/IES = 10 años semestrales) y el modelo es gradient boosting con lags.

### 4.1 Lo que recomienda el consenso

1. **Baselines estadísticos primero, siempre.** En las competencias M, **el Naïve2 (random walk estacional) superó a la mitad de los métodos de ML**, y **solo ~7.5% de los equipos lograron batir el benchmark de suavizamiento exponencial**. Petropoulos et al. (2022) recomienda **ARIMA, ETS, Theta y Naive** como benchmarks obligatorios para cualquier método nuevo. **Nuestro proyecto NO reporta ningún baseline naive/seasonal-naive/ETS** → no podemos demostrar que el XGBoost aporta valor sobre "repetir la última tasa". Este es probablemente **el gap técnico más importante y barato de cerrar.**

2. **"Mind the naive forecast"** (Applied Intelligence, 2025): en series de **baja predictibilidad**, los modelos de ML frecuentemente **no superan al naive**, y evaluar sin compararse rigurosamente contra el naive lleva a conclusiones falsamente optimistas. Recomienda el seasonal-naive como vara de medir obligatoria. *(Citado desde el resumen del buscador; no pude acceder al texto completo por paywall — verificar antes de citar como autoridad fuerte.)*

3. **Modelos globales / cross-learning** son el camino correcto cuando hay **muchas series cortas** (M5, Nixtla). Un solo modelo que aprende de las 277 IES comparte fuerza estadística que ninguna serie individual tiene. **Nuestro diseño ya hace esto** — es nuestra mayor fortaleza técnica y hay que **explicitarla y defenderla** (cita M5).

4. **Gradient boosting con lags funciona** para forecasting (transformar la serie en problema supervisado con ventana deslizante + lags + rolling), pero **requiere ingeniería de features temporal manual** (lags, medias móviles, tendencia, estacionalidad codificada). Nuestro `dataset.ipynb` ya hace la ventana de 4 lags; falta **rolling/tendencia/momentum/volatilidad** (que el README promete).

5. **Cuantificación de incertidumbre con conformal prediction.** Para series y para XGBoost, la comunidad recomienda **MAPIE** (split conformal) y, para series temporales, **EnbPI / ACI** (no requieren intercambiabilidad, manejan no-estacionariedad). Convierte una predicción puntual en un **intervalo con cobertura garantizada**. *Enorme valor para política pública*: en lugar de "la tasa será 14.2%", decir "será 14.2% [10.1–18.3] con 90% de cobertura" → permite al jurado y a la secretaría de educación tomar decisiones con riesgo cuantificado. **Nuestro proyecto no entrega intervalos** → gap de alto impacto y diferenciador.

6. **Para horizontes multi-paso (t+1, t+2):** la estrategia recursiva (encadenar la predicción del paso 1 como input del paso 2) es válida y es lo que el README *dice* hacer — pero el hallazgo **C2 confirma que el notebook no lo implementa** (solo evalúa 1 paso y usaría el lag real intermedio). La comunidad advierte que la estrategia recursiva **acumula error**; alternativas son **direct multi-step** (un modelo por horizonte) o **multi-output**. *Nota:* `MultiOutputRegressor` está **importado pero sin usar** en el notebook (código muerto detectado por la auditoría) — justamente la herramienta que serviría para el enfoque directo/multi-output. Hay que decidir una estrategia y implementarla de verdad.

### 4.2 Alternativas concretas que la comunidad pondría sobre la mesa

- **Statistical baselines:** `StatsForecast` de Nixtla (AutoARIMA, AutoETS, Theta, SeasonalNaive) — rápido, ideal como benchmark obligatorio.
- **Modelos globales ML:** LightGBM/XGBoost global (lo nuestro), o `MLForecast` (Nixtla) que estandariza lags+rolling+global model.
- **Foundation models de series (2024–2025):** Chronos, TimesFM, etc. — probablemente *overkill* y arriesgado para 20 puntos/serie y para explicabilidad de política pública, pero útil mencionarlos como "estado del arte explorado y descartado por X".
- **Conformal prediction:** MAPIE (regresión), EnbPI/ACI (series).

---

## 5. Cierre: "Qué hace el estado del arte / la competencia" vs. "Qué nos falta" (gap analysis accionable)

| # | Qué hace el estado del arte / competencias ganadoras | Qué tiene nuestro proyecto hoy | Gap → Acción accionable | Prioridad |
|---|---|---|---|---|
| G1 | **Comparar SIEMPRE contra baselines estadísticos** (Naive, SeasonalNaive, ETS, Theta). Solo ~7.5% bate el benchmark de ETS en M. | Sin ningún baseline; solo XGBoost vs. nada. | Añadir SeasonalNaive + ETS/Theta (StatsForecast) y reportar MAE/RMSE comparativo. **Si XGBoost no bate al naive, hay que saberlo.** | **CRÍTICA** |
| G2 | **Sin leakage**: optimización en validación, test intocado; CV temporal; recursivo real. | **C1**: Optuna minimiza RMSE de *test*. **C2**: no hay recursivo encadenado real; el README miente sobre ambos. | Cambiar la función objetivo de Optuna a `(x_val,y_val)`; implementar el forecast recursivo t+1→t+2 usando la **predicción** como lag; re-reportar métricas honestas; corregir el README. | **CRÍTICA** |
| G3 | **Explicabilidad (SHAP)** es estándar en deserción; los jurados premian "por qué". | Sin explicabilidad. | Añadir SHAP / importancia de features; traducir a factores accionables por IES. | ALTA |
| G4 | **Intervalos de predicción** (conformal: MAPIE/EnbPI) para decisiones con riesgo cuantificado. | Predicción puntual sola. | Envolver el modelo con conformal prediction y entregar bandas [low, high] al 80/90%. Diferenciador fuerte para política pública. | ALTA |
| G5 | **Ensemble/combinación** estadística+ML (M4/M5). | Modelo único. | Combinar XGBoost con un baseline estadístico (promedio o stacking simple). | MEDIA |
| G6 | **Validación robusta**: backtesting multi-ventana, media±σ del error (M5). | Un solo split temporal; un solo semestre de validación. | Backtesting rolling-origin (varias ventanas), reportar media y σ del error. | MEDIA |
| G7 | **Feature engineering temporal** rica (tendencia, momentum, rolling, volatilidad). | 4 lags + categóricas; el resto está como "próximos pasos". | Implementar `lag1-lag4` (tendencia), `lag1-lag2` (momentum), rolling mean/std (volatilidad) que el README ya promete. | MEDIA |
| G8 | **Storytelling con cifras de impacto + demo/pitch/dashboard** (datathons LatAm). | Excelente README narrativo, sin cifras de impacto ni dashboard. | Cuantificar impacto (# IES priorizables, # estudiantes cubiertos), construir dashboard por IES/dpto, preparar pitch ≤90s. | ALTA |
| G9 | **Anclaje a política pública oficial** (SPADIES, dimensiones MEN, modelo Monte Carlo nacional). | Menciona MEN/SNIES; no cita SPADIES ni el marco de 4 dimensiones. | Citar SPADIES y las 4 dimensiones del MEN; contrastar el ~11.65% nacional (Monte Carlo) como sanity check del orden de magnitud. | MEDIA |
| G10 | **Reproducibilidad/artefactos** (semillas, persistencia, requirements). | Sin persistencia de modelo/params, Optuna sin sampler con semilla, sin requirements.txt. | Fijar `sampler=TPESampler(seed=42)` + `np.random.seed`, persistir `.pkl`/`best_params.json`, añadir `requirements.txt`. | MEDIA |

**Síntesis ejecutiva:** El concurso premia **impacto + uso responsable del dato + solidez metodológica + comunicación**, no solo la métrica. Nuestro mayor activo es un **diseño correcto de modelo global** (alineado con M5) y un **storytelling de política pública sólido**. Nuestros mayores riesgos son los **dos leakages confirmados (C1, C2)** —que un jurado técnico detectaría y que invalidan la "solidez metodológica" y contradicen el README— y la **ausencia de baselines estadísticos**, sin los cuales no podemos demostrar que el modelo aporta valor. Cerrar G1+G2 es no negociable; G3+G4+G8 son los diferenciadores de mayor retorno frente a un jurado.

---

## Fuentes (URLs)

**Concurso (oficial Colombia):**
- https://www.datos.gov.co/stories/s/Concurso-Datos-al-Ecosistema-2026-IA-para-Colombia/ddau-8cy9/
- https://www.mintic.gov.co/portal/inicio/Sala-de-prensa/Noticias/433740:Participe-en-Datos-al-Ecosistema-2026-Inteligencia-Artificial-para-Colombia
- https://www.mintic.gov.co/portal/inicio/Sala-de-prensa/Noticias/437417:Ultimos-dias-para-activar-soluciones-de-impacto-social-con-Datos-al-Ecosistema-2026
- https://www.mintic.gov.co/portal/inicio/Sala-de-prensa/Noticias/437759:Mas-de-1-000-participantes-de-todo-el-pais-avanzan-en-el-reto-de-convertir-datos-publicos-en-soluciones-reales
- https://www.mintic.gov.co/portal/inicio/Sala-de-prensa/Noticias/418985:Avanza-con-exito-el-Concurso-Datos-al-Ecosistema-2025-148-equipos-seguiran-desarrollando-soluciones-basadas-en-datos-abiertos
- https://www.datos.gov.co/stories/s/Concurso-Datos-al-Ecosistema-2025/jy2q-75un/

**Deserción en educación superior (Colombia / SNIES / SPADIES):**
- https://www.mineducacion.gov.co/sistemasinfo/spadies/
- https://www.mineducacion.gov.co/sistemasdeinformacion/1735/articles-254702_libro_desercion.pdf
- https://revistas.utadeo.edu.co/index.php/razoncritica/article/view/modelo-monte-carlo-prediccion-desercion
- https://www.javeriana.edu.co/recursosdb/5581483/8102914/INFORME-74-DESERCIO%CC%81N-EDU-SUPERIOR2023.pdf

**Predicción de deserción con ML (papers/benchmarks):**
- https://www.researchgate.net/publication/396712462_Desarrollo_de_un_sistema_inteligente_para_predecir_la_desercion_universitaria_en_Colombia_mediante_tecnicas_de_machine_learning
- https://www.mdpi.com/2076-3417/15/16/9202 (XGBoost early-warning desde el día 1)
- https://www.mdpi.com/2073-431X/15/3/164 (review ML/DL dropout)
- https://ieeexplore.ieee.org/document/10590352/ (caso Ecuador ML+DL)
- https://www.researchgate.net/publication/389688261_Student_Dropout_Prediction_Using_Random_Forest_and_XGBoost_Method
- https://www.sciencedirect.com/science/article/pii/S0160791X24000228 (Finlandia)

**Competencias de forecasting (M4/M5) y técnicas ganadoras:**
- https://www.sciencedirect.com/science/article/pii/S0169207021001874 (M5 results/findings)
- https://statmodeling.stat.columbia.edu/wp-content/uploads/2021/10/M5_accuracy_competition.pdf
- https://www.sciencedirect.com/science/article/abs/pii/S0169207018300785 (M4 results)
- https://arxiv.org/pdf/2211.08661 (SETAR-Tree, global TS forecasting)

**Kaggle / datathons (técnicas y rúbricas):**
- https://developer.nvidia.com/blog/the-kaggle-grandmasters-playbook-7-battle-tested-modeling-techniques-for-tabular-data/
- https://developer.nvidia.com/blog/grandmaster-pro-tip-winning-first-place-in-kaggle-competition-with-feature-engineering-using-nvidia-cudf-pandas/
- https://info.ceicdata.com/hackatonlatam (criterios CEIC Datathon LatAm 2025)
- https://desafiolatam.com/bases-hackathon/ (criterios Desafío Latam-NODO)
- https://p4s.co/news/como-ganar-una-hackathon-segun-expertos-de-la-region/

**Series cortas: XGBoost, baselines, conformal:**
- https://machinelearningmastery.com/xgboost-for-time-series-forecasting/
- https://www.kaggle.com/code/robikscube/tutorial-time-series-forecasting-with-xgboost
- https://www.nixtla.io/blog/statsforecast-automatic-model-selection
- https://nixtlaverse.nixtla.io/statsforecast/docs/tutorials/statisticalneuralmethods.html
- https://link.springer.com/article/10.1007/s10489-025-06268-w ("Mind the naive forecast"; resumen vía buscador, texto completo con paywall)
- https://mapie.readthedocs.io/en/latest/ (conformal prediction, MAPIE)
- https://arxiv.org/pdf/2010.09107 (conformal prediction for time series)
- https://towardsdatascience.com/time-series-forecasting-with-conformal-prediction-intervals-scikit-learn-is-all-you-need-4b68143a027a/

---
*Limitaciones: no se accedió a los Términos de Referencia oficiales con la rúbrica de pesos exactos del concurso (página JS-renderizada + PDF con HTTP 502). Los pesos por criterio y el formato de entregable/premio NO están confirmados oficialmente y se marcaron como inferidos. La cita "Mind the naive forecast" proviene del resumen del buscador, no del texto completo.*
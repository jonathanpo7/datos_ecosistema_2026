# Forecast de Deserción en Instituciones de Educación Superior — Colombia

Modelo de machine learning que predice la tasa de deserción estudiantil por IES para el **semestre siguiente**, usando series históricas del SNIES.

> 🧭 **¿Eres del equipo? Empieza por [`ESTADO_DEL_PROYECTO.md`](ESTADO_DEL_PROYECTO.md)** — qué se hizo, qué falta y qué sigue. Las correcciones y el dashboard están en el [PR #1](https://github.com/jonathanpo7/datos_ecosistema_2026/pull/1).

---

## Flujo del proyecto

```mermaid
flowchart TD
    A[SNIES — Datos MEN] --> B[Preprocesamiento\n277 IES con series\ncompletas ≥ 10 años]
    B --> C[Dataset Sliding Window\nHistorial 4 períodos → target]
    C --> D[Modelo XGBoost\nForecast 1 semestre ahead]

    D --> E[Ranking de IES\npor tasa predicha]

    E --> F[IES en riesgo\nTasa alta o en aumento]
    E --> G[IES referente\nTasa baja o en descenso]

    F --> H[Priorización de\nintervención\nSecretarías de Educación]
    G --> I[Identificar buenas\nprácticas institucionales\nBenchmark replicable]

    H --> J[Política pública\nbasada en evidencia\nPlanificación activa]
    I --> J
```

---

## Contexto y problema

La deserción estudiantil en la educación superior colombiana es uno de los principales retos del sistema educativo. Según los datos del Ministerio de Educación Nacional, una proporción significativa de los estudiantes que ingresan a una IES no logra graduarse, con impactos directos en la movilidad social, el retorno a la inversión pública en educación y la sostenibilidad de las instituciones.

Históricamente, las entidades de gobierno han respondido a este fenómeno de forma **reactiva**: se detecta el problema cuando ya ocurrió. Este proyecto busca cambiar ese paradigma.

---

## Contexto de política pública

Las secretarías de educación y el Ministerio de Educación Nacional operan dentro de ciclos de gobierno con ventanas de planificación anuales. Para que una secretaría pueda diseñar e implementar una intervención efectiva en una IES —ya sea acompañamiento, asignación de recursos o alertas tempranas— necesita anticipar el comportamiento con al menos un año de antelación.

Un modelo que prediga la tasa de deserción para el próximo semestre permite:

- **Pasar de reactivo a activo**: identificar qué IES están en riesgo antes de que el problema escale
- **Priorizar intervenciones**: enfocar recursos en las instituciones con mayor probabilidad de deterioro
- **Planificar dentro del ciclo de gobierno**: la predicción a un semestre se alinea con los ciclos de presupuesto y política educativa

El horizonte definido es **un semestre adelante** (`t+1`). Si se requiere proyección al segundo semestre, el modelo puede encadenarse de forma recursiva — pero esa extensión acumula la incertidumbre del primer semestre y debe comunicarse con transparencia, no con la misma confianza que `t+1`.

---

## Objetivo

Predecir la **tasa de deserción por IES** para el semestre `t+1` (el siguiente período), a partir de su historial de al menos 10 años de datos consecutivos, y construir un ranking de riesgo que permita priorizar intervenciones.

---

## Datos

- **Fuente**: Sistema Nacional de Información de la Educación Superior (SNIES) — Ministerio de Educación Nacional
- **Cobertura**: 343 IES con datos históricos en el sistema
- **IES aptas para forecast**: 277 instituciones seleccionadas con series consecutivas de **mínimo 20 períodos (10 años)** sin huecos internos
- **Variable objetivo**: tasa de deserción = `(DESERTORES / MATRICULADOS) × 100`, acotada a [0, 100] para corregir artefactos de reporte del SNIES donde DESERTORES puede provenir de cohortes distintas a MATRICULADOS
- **Calidad de datos en origen:** los datos crudos del SNIES contienen tasas anómalas (hasta 138 700%) por denominadores muy pequeños o inconsistencias de cohorte. Estos artefactos son un problema de la **fuente**, no de la manipulación. El clip [0, 100] se aplica en `dataset.ipynb` sobre el dataset completo **antes del split**, por lo que train, val y test están todos protegidos. El archivo `df_forecast_raw.csv` conserva los valores originales para trazabilidad.

---

## Metodología

El pipeline se divide en tres etapas:

### 1. Preprocesamiento (`dataset.ipynb`)
- Consolidación de registros por IES y período, sumando sexos con preservación de valores faltantes reales
- Diagnóstico de cobertura para identificar las 277 IES con series completas
- Construcción del dataset de entrenamiento mediante **ventana deslizante**: cada fila representa una posición en la serie histórica con 4 períodos anteriores como entrada y el siguiente período como objetivo

### 2. Entrenamiento (`entrenamiento_csv/model.ipynb`)
- **Modelo**: XGBoost Regressor — predice un semestre adelante (`t+1`) a partir de los 4 períodos anteriores
- **Split temporal**: Train ≤ 2023-1 | Validación = 2023-2 | Test = 2024
- **Optimización**: Optuna con 100 ensayos buscando los mejores hiperparámetros sobre el set de validación
- **Features**: últimos 4 períodos de tasa (`lag1`–`lag4`), semestre, carácter institucional, origen, departamento y municipio

### 3. Evaluación
- **MAE**: error promedio en puntos porcentuales — el número más interpretable para comunicar a tomadores de decisión
- **RMSE**: penaliza errores grandes — útil para detectar IES donde el modelo falla mucho (cola pesada)
- **Ranking (Spearman)**: mide qué tan bien el modelo ordena las IES por nivel de riesgo, que es el uso real en política pública

---

## Resultados

Evaluación sobre el set de test (año 2024, datos **no vistos durante entrenamiento ni optimización**). Los hiperparámetros se seleccionan con Optuna **sobre el set de validación** (2023-2) y el test se mide **una sola vez** con el modelo ya congelado:

| Métrica | Valor (test 2024) |
|---------|-------------------|
| RMSE    | 10.14 |
| MAE     | 4.31  |
| Ratio RMSE/MAE | 2.35 |

> **Nota de transparencia (corrección de metodología).** Una versión previa reportaba RMSE 9.48 / MAE 4.23, pero esa cifra se obtuvo con Optuna optimizando los hiperparámetros sobre el propio conjunto de **test** (*data leakage* de selección). Corregido el protocolo (selección por validación, test medido una sola vez con `TPESampler(seed=42)` para reproducibilidad), el número honesto es **RMSE 10.14 / MAE 4.31**. Es ligeramente peor, pero es el desempeño real esperable sobre IES no vistas.

**Interpretación para el negocio**: en promedio, el modelo se equivoca **4.31 puntos porcentuales** al predecir la tasa de deserción de una IES. Como referencia, un baseline trivial de **persistencia** (predecir que la tasa se mantiene igual a la del último semestre) obtiene RMSE 10.07 / MAE 4.42 sobre el mismo test agregado. Para una comparación justa conviene mirar el desempeño **por horizonte** (abajo).

### Evaluación honesta por horizonte (forecast recursivo)

El producto promete un pronóstico a un año emitido en un único corte (fin de 2023-2). Bajo ese uso, al predecir 2024-2 **no se conoce** la tasa real de 2024-1: se usa la *predicción* de 2024-1 como `lag1` (encadenamiento recursivo). Reportar la métrica por horizonte y compararla contra la persistencia equivalente es lo metodológicamente correcto:

| Horizonte | Modelo (RMSE / MAE) | Persistencia (RMSE / MAE) |
|-----------|---------------------|---------------------------|
| **t+1** (2024-1) | **11.16 / 4.74** | 11.48 / 4.97 |
| **t+2** (2024-2, recursivo) | **10.49 / 4.72** | 11.19 / 4.72 |
| t+2 (2024-2, con `lag1` real — *protocolo anterior, optimista*) | 8.99 / 3.89 | — |

Dos conclusiones: (1) **el modelo supera a la persistencia en ambos horizontes** cuando se le mide de forma justa (≈0.3 RMSE en t+1, ≈0.7 en t+2); (2) usar la tasa **real** de 2024-1 (en vez de la predicha) hacía que t+2 pareciera mucho mejor de lo que honestamente es (RMSE 8.99 vs 10.49) — ese era el *leakage temporal* ahora corregido con la evaluación recursiva.

### Comparación contra baselines (mismo protocolo y splits)

| Modelo / Baseline | VAL (RMSE / MAE) | TEST agregado (RMSE / MAE) |
|-------------------|------------------|----------------------------|
| **XGBoost** (Optuna sobre validación) | **4.36 / 2.81** | 10.14 / 4.31 |
| Persistencia (`lag1`) | 8.18 / 3.15 | 10.07 / 4.42 |
| Media (`y_train`) | 7.38 / 5.74 | 13.51 / 7.59 |

En **validación** el modelo supera ampliamente a la persistencia; en el **test agregado** prácticamente empata (las tasas de deserción son muy persistentes, así que "repetir el último valor" es un rival fuerte). La ventaja real del modelo se ve sobre todo (a) en la evaluación **por horizonte** (tabla anterior, donde gana en t+1 y t+2) y (b) en la **priorización/ranking** de IES en riesgo (abajo). La gran brecha validación→test confirma la necesidad de **backtesting multi-ventana** (un solo semestre de validación no es representativo).

### Priorización y error por segmento

El caso de uso real es **priorizar IES en riesgo**, no solo minimizar el error promedio. Evaluado sobre 2024-1:

- **Ranking (Spearman predicho vs real): 0.872** — el modelo ordena bien las IES por nivel de deserción. Una secretaría puede tomar la lista ordenada por tasa predicha y priorizar intervenciones de arriba hacia abajo con alta confianza en el orden.
- **Precision@50 = 0.74** — de las 50 IES que el modelo señala como de mayor deserción, 37 realmente lo son.

**Dónde confiar (MAE por tipo de IES, 2024-1):**

| Carácter institucional | MAE | n |
|------------------------|-----|---|
| Universidad | **1.66** | 118 |
| Inst. universitaria / Escuela Tecnológica | 4.75 | 104 |
| Institución tecnológica | 7.12 | 25 |
| Institución técnica profesional | **21.58** | 18 |

El modelo es **muy confiable para universidades** (error ≈ 1.7 pp) y **poco confiable para instituciones técnicas profesionales** (error ≈ 21 pp): para esas IES las predicciones deben tomarse con cautela. Esta transparencia por segmento es clave para un uso responsable en política pública.

### Interpretabilidad, incertidumbre y robustez

- **Drivers (SHAP / TreeSHAP):** la última tasa observada (`lag1`) domina la predicción (media |SHAP| ≈ 3.05 pp), seguida de los lags previos, el municipio y el carácter institucional; el origen apenas aporta. El riesgo se explica sobre todo por la **trayectoria reciente** de la propia IES.
- **Incertidumbre (conformal split, 90%):** banda de ±5.2 pp; cobertura empírica del **81%** en 2024 (objetivo 90%) → el modelo es algo **sobreconfiado** en 2024 (un año más difícil que la validación), un dato honesto que conviene comunicar al usuario.
- **Backtesting rolling-origin (cortes 2022-1 … 2023-2):** modelo RMSE **7.52 ± 1.60** vs persistencia **8.33 ± 1.94** → en promedio el modelo **sí supera** a la persistencia (gana en 3 de 4 cortes), con varianza entre semestres. La evaluación multi-ventana da una lectura más robusta y favorable que el único corte 2024.

---

## Estructura del proyecto

```
├── dataset.ipynb                  # Preprocesamiento y construcción del dataset
├── EDA_preprocesamiento.ipynb     # Análisis exploratorio de datos
├── df_forecast_raw.csv            # Dataset consolidado de las 277 IES aptas
├── entrenamiento_csv/
│   ├── model.ipynb                # Entrenamiento, optimización y evaluación
│   ├── X_train.csv                # Features de entrenamiento
│   ├── X_val.csv                  # Features de validación
│   ├── X_test.csv                 # Features de test
│   ├── y_train.csv                # Targets de entrenamiento
│   ├── y_val.csv                  # Targets de validación
│   └── y_test.csv                 # Targets de test
└── MEN_*.csv                      # Datos fuente del SNIES
```

---

## Cómo reproducir

### Requisitos

```bash
# Dependencias con versiones fijadas (reproducibilidad):
pip install -r requirements.txt
```

### Orden de ejecución

1. **`dataset.ipynb`** — Ejecutar todas las celdas en orden. Genera `df_forecast_raw.csv` y los archivos CSV en `entrenamiento_csv/`
2. **`entrenamiento_csv/model.ipynb`** — Ejecutar todas las celdas en orden. Carga los CSV, entrena el modelo y evalúa en test

> Los datos fuente (`MEN_*.csv`) deben estar en la raíz del proyecto. Se obtienen directamente del portal del SNIES — Ministerio de Educación Nacional de Colombia.

---

## Próximos pasos

- Feature engineering: tendencia (`lag1 - lag4`), momentum (`lag1 - lag2`), volatilidad de la serie
- Incorporación de variables externas: tasas de desempleo regional, indicadores socioeconómicos ICETEX
- Mejorar cobertura de instituciones técnicas y tecnológicas (datos SNIES más consistentes en ese segmento)
- Mapa coroplético por departamento en el dashboard

---

## Licencia

- **Código:** licencia [MIT](LICENSE).
- **Datos:** los archivos `MEN_*.csv` y derivados provienen del **SNIES** (Ministerio de Educación Nacional de Colombia), datos abiertos de carácter público; su uso se rige por los términos del portal de datos abiertos del MEN, no por la licencia MIT del código. Revisar las bases del concurso "Datos al Ecosistema 2026" para los términos de la entrega.

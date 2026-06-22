# Resumen de insights — Análisis socioeconómico complementario al modelo de deserción

Este documento resume los hallazgos de los 3 notebooks exploratorios en `graficas/`, pensados para complementar el modelo de forecast (`entrenamiento_csv/model.ipynb`) con contexto socioeconómico que el modelo **no tiene como feature** a nivel de IES. El objetivo es que esta información se pueda llevar al tablero/app como narrativa de apoyo, no como input directo del modelo.

---

## Metodología común a los 3 análisis

Todos los CSV de origen (`sex_ing_nopersonas.csv`, `sex_programa.csv`, `icetex.csv`) vienen en formato ancho del SNIES/MEN (una columna por período `1998-1`...`2024-2`, con una fila `TIPO` = `DESERTORES` y otra `TIPO` = `MATRICULADOS`). El procesamiento en cada notebook sigue el mismo patrón:

1. Carga y exploración de categorías (incluyendo conteo de valores "Sin información").
2. Conversión de ancho a largo (`melt`).
3. Pivot para obtener `DESERTORES` y `MATRICULADOS` por combinación de categorías + período.
4. **Cálculo de `tasa = (DESERTORES / MATRICULADOS) × 100`, acotada a [0, 100]** — mismo criterio de corrección de artefactos que se usa en el dataset del modelo (`dataset.ipynb`).
5. Gráficas usando siempre `tasa` (nunca conteos absolutos), para que las comparaciones entre categorías sean justas y no estén sesgadas por el tamaño de cada grupo.

**Nota de calidad de dato:** en todos los datasets, la categoría "Sin información" tiene un peso relevante (no se eliminó, se dejó marcada como categoría visible) — es en sí misma un hallazgo: una parte importante de los registros de deserción no tiene contexto socioeconómico/financiero reportado, lo cual condiciona qué tan generalizables son las demás conclusiones.

---

## 1. Género, estrato e ingreso familiar (`genero_estrato.ipynb`)

**Fuente:** `sex_ing_nopersonas.csv` — sexo, ingreso familiar, número de personas en el hogar, estrato.

- **Estrato e ingreso NO muestran una relación clara con la tasa de deserción.** Los estratos 1 a 6 rondan todos entre 13-17% de tasa, sin tendencia descendente al subir de estrato.
- **Contraintuitivo:** las categorías de mayor ingreso ("15 o más salarios mínimos", "entre 13 y 15") muestran tasas iguales o **ligeramente más altas** (~18-20%) que "menos de un salario mínimo" (~15-16%).
- **Sexo:** Hombres con tasa promedio levemente mayor que mujeres (~14.6% vs ~13%).
- **Conclusión para el tablero:** estrato/ingreso reportado por el estudiante, por sí solos, no son buenos predictores de deserción — no conviene presentarlos como causa principal sin matizar.

## 2. Sexo, núcleo académico y nivel de formación (`sex_programa.ipynb`)

**Fuente:** `sex_programa.csv` — sexo, núcleo (área de conocimiento, 57 categorías), nivel de formación.

- **El nivel de formación sí marca una diferencia fuerte:** `FORMACION TECNICA PROFESIONAL` (~27%) y `TECNOLOGICA` (~15-19%) tienen tasas notablemente más altas que `UNIVERSITARIA` (~10%).
- **Sexo:** Hombres ~17.8% vs Mujeres ~15.8% — mismo patrón que en el dataset anterior.
- **Núcleos con mayor deserción:** Ingeniería Administrativa, Física, Ingeniería Agroindustrial, Ingeniería Industrial (~20-27%).
- **Núcleos con menor deserción:** Formación militar/policial, Antropología, Áreas de la salud en general (Medicina, Enfermería, Nutrición) (~7-15%) — aunque hay que revisar tamaño de muestra antes de generalizar en los núcleos más pequeños.
- **Conclusión para el tablero:** el nivel de formación (técnica/tecnológica vs. universitaria) es un mejor candidato de segmentación que el estrato socioeconómico.

## 3. Financiación ICETEX (`icetex.ipynb`)

**Fuente:** `icetex.csv` — créditos académicos (`ACADE`), créditos financieros/subsistencia (`FINAN`), créditos de continuidad (`CI_RECI`).

- **Hallazgo más fuerte de los 3 análisis:** a más créditos académicos o financieros recibidos, **menor** tasa de deserción.
  - Sin ningún crédito: tasa promedio ~14.3%.
  - Con algún crédito ICETEX: tasa promedio ~6%.
  - Por categoría: de "Ninguno" (~8-9.6%) a "Más de 7" créditos (~4.1-4.5%) hay una caída sostenida y consistente.
- **`CI_RECI` (créditos de continuidad) muestra la relación inversa** (más créditos → más deserción, de 4.2% a 8.1%). La definición exacta de esta variable no está documentada en el repo (no hay diccionario de datos SNIES/ICETEX) — probablemente mide renovaciones otorgadas después de alguna interrupción, lo cual explicaría que correlacione con más riesgo en vez de menos. **Importante: no presentar este hallazgo sin esa aclaración**, porque a simple vista parece contradecir el de ACADE/FINAN.
- **Conclusión para el tablero:** el acceso a financiación ICETEX (créditos académicos/de subsistencia) es la variable con relación más clara y consistente con la deserción de las 3 fuentes exploradas — más fuerte que estrato, ingreso o género.

---

## Qué llevar al tablero (propuesta de prioridad)

1. **Gráfico ICETEX "con vs. sin crédito"** — el hallazgo más contundente y fácil de comunicar a una secretaría de educación (financiación reduce deserción a más de la mitad).
2. **Tasa por nivel de formación** (técnica/tecnológica vs. universitaria) — segunda variable más explicativa.
3. **Nota de transparencia de datos** — % de registros sin estrato/ingreso/sexo reportado, para que el tablero no sobrevenda conclusiones sobre datos incompletos.
4. Estrato, ingreso familiar y núcleo académico como gráficos secundarios/exploratorios, dejando claro que la relación es débil o no concluyente en el caso de estrato/ingreso.

## Pendiente / próximos pasos

- Confirmar con el equipo o la fuente SNIES/ICETEX la definición exacta de `CI_RECI`.
- Validar tamaño de muestra de los núcleos académicos con tasas extremas antes de destacarlos en el tablero.
- Evaluar si alguna de estas variables (en particular `ACADE`/`FINAN`) podría agregarse a nivel IES como feature del modelo de forecast (actualmente el modelo no tiene visibilidad de financiación estudiantil).

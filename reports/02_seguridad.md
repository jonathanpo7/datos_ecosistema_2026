# Informe 02 — Auditoría de Seguridad y Privacidad de Datos

**Proyecto:** Datos al Ecosistema 2026 — Forecast de deserción por IES (SNIES/MEN)
**Repositorio auditado:** `C:\Users\FERNANDO VEGA\Desktop\concurso-datos-ecosistema-2026\datos_ecosistema_2026` (REPO)
**Remoto:** `https://github.com/jonathanpo7/datos_ecosistema_2026.git` (rama `main` → `origin/main`)
**Alcance:** SOLO LECTURA. Auditoría limitada estrictamente a REPO. No se ejecutaron notebooks. No se leyó completo el CSV de 104 MB.
**Fecha:** 2026-06-28
**Auditor:** Seguridad y privacidad de datos

---

## Resumen ejecutivo

| Área | Resultado |
|---|---|
| Secretos/credenciales en árbol de trabajo | **No se encontraron secretos reales.** Los 8 hallazgos de detect-secrets son falsos positivos (imágenes PNG base64 embebidas en notebooks). |
| Secretos en historial git | **No se encontraron.** Historial pequeño (5 commits) revisado con `git log -p --all`. Sin `.env` jamás commiteado, sin ficheros borrados. |
| Dependencias vulnerables (stack del proyecto) | El stack ML directo (pandas, numpy, scikit-learn, matplotlib, seaborn) **sin vulnerabilidades**. Riesgo en `pillow` 11.3.0 (transitiva de matplotlib, 6 CVEs). Falta de `requirements.txt` impide auditar versiones reproducibles. |
| PII de personas naturales | **NO existe.** Todo es agregado institucional público del SNIES (conteos por IES/programa/período/género). |
| PII institucional | `MEN_INSTITUCIONES_*.csv` contiene NIT, dirección y teléfono **de instituciones** = registro público. Riesgo bajo. |
| Higiene/exposición | **CRÍTICO de higiene:** CSV de 99 MB (~390.903 filas) **committeado a git y publicado en GitHub público**. Sin `LICENSE`. `.gitignore` no protege datos. |

**Conclusión de privacidad:** El proyecto **no expone datos personales de estudiantes ni de personas naturales**. El principal problema no es de confidencialidad sino de **higiene de repositorio y cadena de suministro**: datos masivos versionados en un repo público, ausencia de `LICENSE` (problema legal para un concurso) y ausencia de `requirements.txt` (reproducibilidad + auditoría de dependencias).

---

## 1) Secretos y credenciales

### 1.1 Escaneo del árbol de trabajo — `detect-secrets scan --exclude-files ".*\.csv$"`

Ejecutado con **detect-secrets 1.5.0** dentro de REPO. Resultado: 8 hallazgos, **todos de tipo `Base64 High Entropy String`**, ubicados exclusivamente dentro de notebooks:

| Archivo | Líneas |
|---|---|
| `EDA_preprocesamiento.ipynb` | 1273, 1313, 1350, 1402 |
| `entrenamiento_csv/model.ipynb` | 1399 |
| `graficas/genero_estrato.ipynb` | 912 |
| `graficas/icetex.ipynb` | 807 (y siguientes) |
| `graficas/sex_programa.ipynb` | (1) |

**Verificación manual:** cada línea reportada es del patrón `"image/png": "iVBORw0KGgoAAAANSUhEUg..."`. La firma `iVBORw0KGgo` es el encabezado base64 de la cabecera PNG (`\x89PNG\r\n`). Son **salidas de gráficos matplotlib embebidas** en los notebooks, no credenciales.

**Veredicto: 8/8 FALSOS POSITIVOS. No hay secretos en el árbol de trabajo.**

### 1.2 Escaneo del historial git

Cobertura: historial completo (5 commits: `1d6f252`, `485de0d`, `3943262`, `077d606`, `1dd81b0`). Comando: `git log -p --all` filtrado con regex de patrones de secretos (api key, secret, password, token, `AKIA…`, `BEGIN (RSA|OPENSSH|PRIVATE) KEY`, `sk-…`, `ghp_…`, `xox[baprs]-`, bearer, client_secret, `.env`).

- Las coincidencias devueltas fueron **falsos positivos léxicos**: la palabra "SECRETARIADO" (nombre de programas, p. ej. *TECNICA PROFESIONAL EN SECRETARIADO EJECUTIVO*) y "secretaría de educación" en el README. **No** hay API keys, tokens, contraseñas, claves AWS ni claves privadas.
- **Ningún archivo `.env` fue committeado** en ningún momento.
- **No hay archivos borrados del historial** (`--diff-filter=A` lista solo ficheros que siguen presentes); no existe riesgo de un secreto "oculto" en una versión previa eliminada.

**Cobertura honesta:** gitleaks y trufflehog **NO están instalados** (verificado). El barrido se realizó con `git log -p` + regex y con detect-secrets sobre el working tree. Esto cubre patrones conocidos y entropía base64/hex, pero es **menos exhaustivo** que un escáner dedicado con detección de verificación en vivo. Dado el tamaño del historial (5 commits, repo de datos sin código de integración), la confianza en "sin secretos" es **alta**.

---

## 2) Dependencias vulnerables (`pip-audit`)

Ejecutado **pip-audit 2.10.1**. Importante: como **no hay `requirements.txt` ni entorno virtual del proyecto**, pip-audit auditó el **entorno Python global** del sistema, que mezcla dependencias de muchos proyectos ajenos (aiohttp, flask, gradio, langchain, torch, paramiko, yt-dlp, etc.). Resultado global: 99 vulnerabilidades en 28 paquetes — la **gran mayoría irrelevante** a este proyecto.

**Filtrado a las librerías declaradas en el README** (`pandas, numpy, xgboost, scikit-learn, optuna, matplotlib, seaborn, jupyter`):

| Librería declarada | Versión instalada | Vulnerabilidades (pip-audit) |
|---|---|---|
| pandas | 2.3.2 | Ninguna |
| numpy | 2.3.3 | Ninguna |
| scikit-learn | 1.8.0 | Ninguna |
| matplotlib | 3.10.8 | Ninguna |
| seaborn | 0.13.2 | Ninguna |
| xgboost | **no instalada** en este entorno | No auditable |
| optuna | **no instalada** en este entorno | No auditable |
| jupyter / notebook | **no instalada** en este entorno | No auditable |

**Única vulnerabilidad relevante al proyecto:** `pillow` 11.3.0 — dependencia **transitiva de matplotlib** (confirmado: `Required-by: ... matplotlib ...`). 6 CVEs: CVE-2026-25990, CVE-2026-40192, CVE-2026-42309, CVE-2026-42310, CVE-2026-42311, PYSEC-2026-165. Fix: actualizar a Pillow ≥ 12.2.0. Severidad para este proyecto: **media-baja** (Pillow solo se usa para renderizar/guardar gráficos; no procesa imágenes de origen no confiable).

**Riesgo de cadena de suministro:** la ausencia de `requirements.txt`/lock es un hallazgo en sí mismo. Implica que (a) no se puede reproducir el entorno que produjo RMSE 9.48/MAE 4.23, y (b) **no se pueden auditar** las versiones reales de xgboost/optuna/jupyter usadas, que sí han tenido CVEs históricos. La instrucción del README (`pip install pandas numpy xgboost scikit-learn optuna matplotlib seaborn`) instala **lo último disponible**, no versiones fijadas → builds no determinísticos.

---

## 3) PII / datos sensibles en los CSV

Inspección de cabeceras (sin leer el CSV de 104 MB completo: solo `sed -n '1p'` para la cabecera + `wc -l` en streaming).

### Conclusión principal: ¿hay PII de personas naturales? **NO.**

- **`MEN_MATRICULA_ESTADISTICA_ES_20260519.csv`** (104.054.678 bytes, 390.903 filas + cabecera): la granularidad mínima es `Id Género` + `Total Matriculados` (conteos). Dimensiones: institución, programa, nivel, metodología, área, departamento/municipio, año, semestre, género agregado. **No hay cédula, documento, nombre, correo ni identificador de estudiante.** Es estadística agregada del SNIES.
- **`df_forecast_raw.csv`**, **`entrenamiento_csv/X_*.csv`, `y_*.csv`**: usan el **código SNIES de la IES** (p. ej. `1101`), no nombres, más categóricos (departamento, municipio, carácter, origen) y la tasa/conteos. Sin PII.
- Resto de CSVs derivados (icetex, programa, sex_*, valle_, etc.): agregados; ninguno tiene columnas de identificación personal.

### Matiz — PII **institucional** (no de personas)

`MEN_INSTITUCIONES_EDUCACIÓN_SUPERIOR_20260520.csv` sí contiene, **por institución**:
- `Número Identificación Tributaria - NIT` (p. ej. `892.300.285-6`)
- `Dirección Domicilio`, `Teléfono Domicilio`

Estos son datos de **personas jurídicas** y forman parte del **registro público del SNIES/MEN**. **No constituyen PII de personas naturales** y su riesgo es **bajo**. Se documenta para transparencia, evitando falsa alarma. (Nota: el artefacto de encoding "Sin Informaci?n" descrito en el contexto **no se confirmó** en la cabecera/muestra de este archivo específico; sí es típico del SNIES en otros campos.)

**Recomendación de privacidad:** ninguna acción obligatoria por PII personal. Si se quiere minimizar exposición de contacto institucional, podría omitirse NIT/Dirección/Teléfono del repo público (no son necesarios para el modelo: el pipeline usa solo el código IES y categóricos geográficos).

---

## 4) Higiene y exposición

### 4.1 CSV pesado versionado y publicado (hallazgo de mayor severidad de higiene)

- `MEN_MATRICULA_ESTADISTICA_ES_20260519.csv` = **99 MB** (blob git de 103.663.774 bytes) está **trackeado por git, committeado al historial y NO ignorado** (`git check-ignore` → no ignorado; `git ls-files` → trackeado). El repo apunta a un **GitHub público** (`jonathanpo7/datos_ecosistema_2026`).
- Consecuencia: el dataset masivo (y todo `.git`) se sirve públicamente; clonar el repo descarga ~107 MB de working tree + historial. Supera el umbral recomendado de GitHub (avisos >50 MB, límite duro 100 MB por archivo — este archivo está **al borde del límite de 100 MB**). Riesgo de rechazo de push futuro y de repo inmanejable.
- El archivo ya está en historial, por lo que un simple `.gitignore` **no lo elimina** del pasado: requiere reescritura de historial (`git filter-repo` o BFG) + force-push, coordinado con el equipo, **antes** de que el concurso lo evalúe.

### 4.2 `.gitignore`

- **Existe** (plantilla estándar Python, 4.846 bytes). Ignora `.env` y `.envrc` (línea 151-152) — bien para credenciales.
- **NO ignora `*.csv` ni los datos** → los datos quedan versionados igual. Recomendado añadir patrones de datos (`*.csv`, `data/`, `*.pkl`) y mantener los fuente fuera del repo o vía Git LFS / enlace al portal SNIES.

### 4.3 Ausencia de `LICENSE`

- **No existe `LICENSE`** (verificado: ausentes LICENSE/.md/.txt). Para un **concurso**, la falta de licencia tiene implicaciones legales: sin licencia explícita, el código está bajo copyright por defecto ("todos los derechos reservados"), lo que **impide su reutilización/redistribución** y puede contravenir las bases del concurso (que suelen exigir licencia abierta para el código entregado). Añadir `LICENSE` (p. ej. MIT/Apache-2.0 para el código) y documentar la licencia de uso de los datos del MEN.

### 4.4 Licencia/uso de datos del MEN

- Los `MEN_*.csv` provienen del SNIES (datos abiertos del Ministerio de Educación Nacional). Conviene **citar la fuente y los términos de uso** de datos abiertos del MEN en el README/LICENSE de datos. El README ya cita la fuente; falta declarar explícitamente la licencia/términos de los datos redistribuidos en el repo.

### 4.5 PDF "Idea proyecto Estudiantil.pdf"

- 1.800.320 bytes, 4 páginas, **basado en imágenes** (sin texto extraíble en las páginas inspeccionadas). Metadatos: `Author` vacío, `Producer = "Microsoft: Print To PDF"`, `Title = "overview_desercion_estudiantil.md"`. **No se detectó información sensible del equipo** (sin nombres de autor, correos ni teléfonos en metadatos ni texto extraíble). Riesgo informativo: bajo. Recomendación: confirmar visualmente que el contenido renderizado no incluya datos de contacto del equipo antes de publicar.

### 4.6 `cargar_csv.py`

- Script trivial de 6 líneas: solo `pd.read_csv(...)` y `print`. Sin credenciales, sin rutas absolutas sensibles, sin conexiones de red.

### 4.7 Archivo no rastreado en el árbol de trabajo

- `git status` reporta un `CLAUDE.md` **no rastreado** en la raíz del working tree. No forma parte del repo (no committeado). **Recomendación:** no committearlo y añadirlo a `.gitignore`; verificar que no contenga información que no deba publicarse antes de cualquier `git add`. (No se inspecciona su contenido por estar fuera del alcance de esta auditoría.)

---

## Tabla de severidad y remediación

| ID | Hallazgo | Severidad | Remediación |
|---|---|---|---|
| S02-1 | CSV de 99 MB committeado y publicado en GitHub público | **ALTA** | Reescribir historial (`git filter-repo`/BFG) para purgar el blob; servir el dato vía Git LFS o enlace al portal SNIES; añadir `*.csv` a `.gitignore`. Coordinar force-push con el equipo. |
| S02-2 | Ausencia de `LICENSE` | **ALTA** | Añadir `LICENSE` para el código (MIT/Apache-2.0) y declarar la licencia de uso de datos del MEN. Verificar las bases del concurso. |
| S02-3 | Ausencia de `requirements.txt`/lock (riesgo de cadena de suministro y reproducibilidad) | **MEDIA** | Crear `requirements.txt` con versiones fijadas (incluyendo xgboost, optuna, jupyter) y re-ejecutar pip-audit sobre ese set en un venv aislado. |
| S02-4 | `pillow` 11.3.0 vulnerable (transitiva de matplotlib) | **MEDIA** | Fijar `pillow>=12.2.0` en requirements; bajo impacto real (solo render de gráficos). |
| S02-5 | `.gitignore` no protege datos | **MEDIA** | Añadir `*.csv`, `data/`, `*.pkl`, `CLAUDE.md`. |
| S02-6 | PII institucional (NIT/Dirección/Teléfono) en `MEN_INSTITUCIONES` | **BAJA** | Registro público; opcionalmente omitir columnas de contacto no usadas por el modelo. |
| S02-7 | 8 falsos positivos de detect-secrets (PNG base64) | **INFO** | Generar `.secrets.baseline` con `detect-secrets scan > .secrets.baseline` para silenciar ruido en CI. |
| S02-8 | Archivo `CLAUDE.md` no rastreado en working tree | **INFO/BAJA** | No committear; añadir a `.gitignore`; revisar contenido antes de cualquier `git add`. |
| S02-9 | Sin PII de personas naturales | **BIEN** | Mantener: el pipeline trabaja solo con agregados y código IES. Buena práctica de minimización de datos. |

---

## Nota de limitaciones

1. **Herramientas no instaladas:** `gitleaks` y `trufflehog` **NO** están disponibles en el sistema (verificado). El barrido de secretos se hizo con `detect-secrets` (working tree) + `git log -p` con regex (historial). Cobertura buena para patrones conocidos y entropía, pero menos exhaustiva que escáneres dedicados con verificación en vivo.
2. **EX/data_profile.txt y EX/code_*.txt no existían** en el sistema en el momento de la auditoría (carpeta `EX` ausente). Por ello las cabeceras de CSV se inspeccionaron **directamente** sobre REPO (solo cabecera + `wc -l` en streaming; **nunca** se cargó el CSV de 104 MB completo en memoria).
3. **pip-audit auditó el entorno global**, no un venv del proyecto (porque no hay `requirements.txt`). Por eso aparecen 99 vulnerabilidades mayormente ajenas; el informe filtró a las 8 librerías declaradas. xgboost/optuna/jupyter **no estaban instaladas** en este entorno → no auditables aquí.
4. **PDF basado en imágenes:** no fue posible extraer texto (sin OCR); el juicio "sin info sensible del equipo" se basa en metadatos + texto extraíble vacío, no en lectura visual del render.
5. Auditoría **estrictamente confinada a REPO**; no se inspeccionaron ni citaron rutas fuera de esa carpeta.
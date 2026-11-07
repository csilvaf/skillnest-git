# 🛠️ Asistente Integral de Servicio Técnico (Consolas y PC) — Gate 1 a Unidad U2.4

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Provider](https://img.shields.io/badge/provider-Google%20AI%20Studio-orange.svg)](https://aistudio.google.com/)
[![Model](https://img.shields.io/badge/model-gemini--3.5--flash--lite-green.svg)](https://ai.google.dev/)
[![Framework](https://img.shields.io/badge/orchestration-LangChain-blueviolet.svg)](https://www.langchain.com/)
[![Status](https://img.shields.io/badge/evaluation-Gate%201%20%26%20U2.4%20Ready-brightgreen.svg)]()

Miniaplicación de línea de comandos (CLI) y sistema de orquestación con IA desarrollado en Python para la automatización del **triaje técnico, clasificación de fallas, procedimientos de soporte, estimación de presupuestos y atención conversacional con agentes autónomos** en un servicio técnico integral de tecnología (consolas PlayStation 5, Nintendo Switch, notebooks y computadores de escritorio).

El sistema cubre todas las áreas operativas del taller:
- **Microelectrónica y Hardware:** Diagnóstico de placas madre, fuentes de poder, líneas de voltaje y reemplazo de componentes SMD/BGA.
- **Software y Sistemas Operativos:** Formateos, instalación limpia de Windows/Linux, respaldo de datos, eliminación de malware y resolución de pantallazos azules (BSOD).
- **Armado de PC, Upgrades y Mantenimiento:** Validación de compatibilidad de piezas (CPU, placas B550/X670, RAM, GPU), actualización de BIOS, cambios de hardware y mantenimiento térmico preventivo.
- **Orquestación, Enrutamiento y Agentes (Módulo 2):** Flujos multipaso, bifurcación inteligente de intenciones (preguntas, quejas y sugerencias), resiliencia con fallbacks y agentes ReAct con herramientas tipadas en Pydantic y memoria conversacional por sesión.

Consume la API de **Google Gemini** aplicando separación de responsabilidades, validación defensiva estricta en cada capa, telemetría de consumo de tokens, backoff exponencial con jitter, evaluación con métrica F1 y orquestación mediante **LangChain**.

> **Contexto académico:** Proyecto evolutivo que abarca desde la entrega **U1.6: Gate 1 - Habilitación técnica** hasta la **Unidad U2.4: Agentes, herramientas externas y memoria** de la *Especialización en Desarrollo con IA Generativa (Accenture / Skillnest)*.

---

## 🎯 Problema de Negocio y Alcance

En la recepción y laboratorio de un servicio técnico integral, los tiempos de atención y diagnóstico suelen verse afectados por:
1. Errores de clasificación inicial en el mesón al recibir requerimientos diversos (confundir fallas de sistema operativo o drivers con fallas físicas de hardware, o mezclar consultas técnicas con reclamos de garantía).
2. Demora en la validación de compatibilidad en armado de equipos, upgrades de componentes (ej. procesadores Ryzen serie 5000/7000 en distintas revisiones de BIOS) o procedimientos de formateo y respaldo.
3. Tiempo invertido en determinar las líneas de alimentación y componentes críticos a medir con multímetro u osciloscopio en etapas de microelectrónica (ej. circuitos integrados de carga M92T36/BQ24193 en Nintendo Switch o secuencias de encendido en PS5).
4. Consultas repetitivas de clientes sobre el estado e historial de sus órdenes de trabajo (`PS5-202`, `PC-100`) o el cálculo rápido de presupuestos combinando mano de obra y repuestos.

Esta solución estandariza y automatiza el análisis técnico y la atención al cliente, devolviendo desde diagnósticos en JSON estructurado hasta respuestas conversacionales con memoria de sesión y ejecución autónoma de herramientas de negocio.

---

## 🏗️ Arquitectura del Software y Flujo de Datos

### Fase 1: Cliente HTTP Puro, Telemetría y Salida JSON (Módulo 1 y U2.1)

El diseño modular inicial desacopla estrictamente la orquestación, el transporte HTTP y el procesamiento de datos (`src/consumir_gemini.py` y `cliente.py`), integrando telemetría, reintentos con backoff exponencial y programación defensiva:

    [ 👤 Usuario / main.py ]                   [( 📁 Archivo .env )]
              │                                         │
              │ pregunta: str, response_schema: dict     │ GEMINI_API_KEY
              ▼                                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. armar_peticion(...)                                       │
│    • isinstance(pregunta, str) -> ValueError                 │
│    • Validación de espacios en blanco -> ValueError          │
│    • os.getenv("GEMINI_API_KEY") -> ValueError si falta      │
│    • Separa 'systemInstruction' de 'contents'                │
│    • Inyecta 'generationConfig' (JSON schema) si aplica      │
└──────────────────────────────┬───────────────────────────────┘
                               │ url: str + body: dict
                               ▼
┌──────────────────────────────────────────────────────────────┐       ┌────────────────────────────┐
│ 2. enviar_peticion(...) + con_reintento(...)                 │       │ ☁️ Google Gemini API       │
│    • requests.post(url, json=body) ──────POST HTTP (JSON)───►│       │    (gemini-3.5-flash-lite) │
│    • Backoff exponencial + jitter (HTTP 429 / Timeout)       │       │ • Inferencia y detokenizado│
│    • respuesta.json()              ◄──HTTP 200 OK (JSON)─────│       │ • Desglose usageMetadata   │
│    • except ConnectionError -> RuntimeError                  │       └────────────────────────────┘
│    • except JSONDecodeError -> RuntimeError                  │
└──────────────┬───────────────────────────────┬───────────────┘
               │                               │
               │ rama 'candidates'             │ rama 'usageMetadata'
               ▼                               ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐
│ 3. extraer_texto(...)        │ │ 4. Telemetría de Consumo     │
│    • candidates[0]...["text"]│ │    • promptTokenCount       │
│    • except (KeyError,       │ │    • candidatesTokenCount   │
│      IndexError)             │ │    • totalTokenCount        │
│      -> RuntimeError         │ └─────────────┬───────────────┘
└──────────────┬───────────────┘               │
               │ texto / JSON crudo            │
               ▼                               │
┌──────────────────────────────┐               │
│ 5. parsear_respuesta_json(...)│              │
│    • Sanitizado de Markdown  │               │
│    • json.loads(limpio)      │               │
│    • except JSONDecodeError  │               │
│      -> ValueError           │               │
└──────────────┬───────────────┘               │
               │ dict estructurado             │
               └───────────────┬───────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ 🏁 Salida a Terminal / Consola                               │
│ Retorno tipado + Desglose de tokens y costos acumulados      │
└──────────────────────────────────────────────────────────────┘

El diagrama de arquitectura exportado en alta resolución se encuentra versionado en `docs/diagrama_arquitectura.png`.

---

## 🧠 Evolución Módulo 2: Métricas, Orquestación con LangChain y Agentes

Durante el Módulo 2, el proyecto evolucionó incorporando cuatro subsistemas clave probados con `pytest` y mocks:

### 1. Pipeline de Texto y Evaluación Cualitativa/Cuantitativa (Unidad U2.2 — Bloques 15 a 17)
- **Normalización y Tokenización (`pipeline_texto.py`):** Limpieza de texto mediante expresiones regulares (conversión a minúsculas, eliminación de puntuación y colapso de espacios) y tokenización segura con validación de tipos (`TypeError`).
- **Métricas Formales (`calcular_precision_cobertura_f1`):** Cálculo matemático de Precisión, Cobertura (Recall) y F1-Score utilizando intersección de multiconjuntos (`collections.Counter`) para respetar repeticiones de palabras y prevenir divisiones por cero.
- **Auditoría Cualitativa y Límites (`revision_manual.py` y `docs/limites_metrica.md`):** Evaluación humana sobre una muestra de 10 casos del taller bajo una rúbrica de 3 criterios (*corrección factual*, *completitud* y *contradicción*), documentando los modos de falla de la métrica léxica (falsos negativos por sinónimos y falsos positivos ante omisión de negaciones críticas).

### 2. Cadenas Secuenciales de Tres Pasos (Unidad U2.3 — Bloque 18)
- **Orquestación Lineal (`cadena_tres_pasos.py`):** Uso de `PromptTemplate`, `ChatGoogleGenerativeAI`, `StrOutputParser` y el operador pipe (`|`) para transformar un reporte técnico crudo en tres etapas conectadas por funciones intermedias (`lambda`):
  1. *Paso 1 (Extracción):* Aísla los 3 puntos técnicos clave del síntoma reportado.
  2. *Paso 2 (Simplificación):* Traduce los puntos técnicos a una explicación clara y empática para el dueño del equipo.
  3. *Paso 3 (Formato):* Estructura la salida en una lista de viñetas Markdown para la orden de trabajo interna.

### 3. Enrutamiento Condicional y Resiliencia por Paso (Unidad U2.3 — Bloques 19 y 20)
- **Bifurcación Inteligente (`enrutamiento.py`):** Clasificación automática de la intención del mensaje del cliente (normalizada con `.strip().lower()`) y derivación dinámica mediante `RunnablePassthrough.assign` y `RunnableBranch` hacia tres rutas especializadas:
  - `cadena_queja`: Respuesta empática y activación inmediata de protocolo de revisión por garantía.
  - `cadena_sugerencia`: Agradecimiento y registro para evaluación de mejora continua.
  - `cadena_pregunta` *(ruta por defecto)*: Respuesta técnica directa y precisa sobre hardware/consolas.
- **Manejo de Errores Multicapa (`test_orquestacion.py`):**
  - *Nivel de Ruta:* Protección con `.with_fallbacks([respuesta_generica])` en la ruta de quejas para entregar una respuesta de respaldo si el modelo falla.
  - *Nivel de Flujo Completo:* Función `procesar_mensaje_seguro()` con bloque `try/except` general y registro en `logging.error()` para garantizar que ningún fallo en la clasificación o en la red detenga la aplicación.

### 4. Agentes Autónomos ReAct, Herramientas Pydantic y Memoria (Unidad U2.4 — Bloques 21 y 22)
- **Agente con Herramientas (`agente.py`):** Implementación de un agente autónomo mediante `create_tool_calling_agent` y `AgentExecutor` (`langchain_classic`), capaz de decidir en tiempo de ejecución si debe invocar una o varias herramientas o responder directamente, exponiendo su traza de razonamiento en `intermediate_steps`.
- **Herramientas Personalizadas con Esquemas Estrictos (`args_schema`):**
  - `consultar_estado_reparacion_detallado`: Validada con `ArgumentosEstadoReparacion(BaseModel)` de Pydantic. Consulta el estado actual de una orden (`PS5-202`, `PC-100`) y, opcionalmente, despliega su bitácora histórica de hitos (`incluir_historial: bool`).
  - `calcular_presupuesto_trabajo`: Validada con `ArgumentosPresupuesto(BaseModel)`. Calcula el presupuesto total sumando horas de mano de obra técnica ($15.000 CLP/hora) y costo de repuestos.
- **Memoria Conversacional Aislada por Sesión:** Integración de `RunnableWithMessageHistory` e `InMemoryChatMessageHistory` junto con un paso de normalización (`AIMessage`) para recordar el contexto entre turnos de un mismo cliente (`session_id`) manteniendo aislamiento estricto entre sesiones de distintos usuarios.

---

## ⚡ Selección de Modelo y Trade-Offs de Ingeniería

De acuerdo con el análisis formal documentado en `docs/decision-arquitectura.md`, se evaluaron los candidatos de la familia Gemini considerando costo por cada 1.000 tokens, latencia de red y calidad de respuesta para el taller:

| Criterio Evaluado | Gemini 3.5 Flash-Lite (Operativo en Código) | Gemini 2.5 / 3.1 Pro (Referencia Analítica) |
| :--- | :--- | :--- |
| **Costo entrada (por 1.000 tokens)** | **0.000075 USD** ($0.075 / 1M) | 0.00125 USD ($1.25 / 1M) |
| **Costo salida (por 1.000 tokens)** | **0.000300 USD** ($0.300 / 1M) | 0.00500 USD ($5.00 / 1M) |
| **Latencia promedio observada** | **~1.82 segundos** | ~4.35 segundos |
| **Idoneidad para el caso** | **Excelente para triaje rápido, encadenamiento en LangChain, tool calling en agentes y JSON estricto.** | Alta profundidad analítica para esquemáticos complejos, pero más lento para cadenas multipaso y agentes. |
| **Estabilidad operativa** | Alta disponibilidad en Free Tier sin saturación (`503`) ni agotamiento prematuro de cuota (`429`). | Restricciones estrictas de RPM en cuentas sin facturación vinculada. |

---

## 🔒 Protocolo de Seguridad y Gestión de Secretos

Para dar cumplimiento estricto a las directrices de seguridad del programa y al **criterio no compensable de credenciales protegidas**:
1. **Zero Hardcoded Secrets:** Ninguna credencial sensible, URL interna o token viaja incrustado en el código fuente. Se recuperan en tiempo de ejecución vía `python-dotenv`.
2. **Control en `.gitignore`:** El archivo `.gitignore` excluye deliberadamente cualquier variación de archivos de entorno (`.env`, `*.env`) y carpetas de entorno virtual (`.venv/`), manteniendo una excepción explícita para versionar la plantilla pública (`!.env.example`).
3. **Auditoría de Historial Git:** El repositorio cuenta con verificación de historial limpio demostrable mediante:

    git log --all --oneline -- .env

   *(Resultado esperado: vacío, confirmando que la clave nunca fue commiteada en el historial).*

---

## 📁 Estructura del Repositorio

    skillnest-git/
    ├── docs/
    │   ├── decision-arquitectura.md          # Justificación técnica de costos, latencias y modelo (Bloque 9)
    │   ├── diagrama_arquitectura.png         # Diagrama de flujo, excepciones y bifurcación de datos (Bloque 8)
    │   ├── evidencia_peticion_autenticada.md # Evidencia de prueba de red HTTP 200 OK (Bloque 4)
    │   └── limites_metrica.md                # Documentación de límites de la métrica F1 (Bloque 17)
    ├── prompts/
    │   ├── banco.py                          # Banco de prompts (recepción, laboratorio/armado, presupuestos)
    │   ├── test_consistencia.py              # Validador empírico de consistencia (3 corridas por prompt)
    │   └── registro_resultados.json          # Registro JSON con tasa de éxito 3/3 en adherencia de formato
    ├── src/
    │   └── consumir_gemini.py                # Módulo base desacoplado de consumo HTTP y parseo JSON
    ├── .env.example                          # Plantilla de referencia pública de variables de entorno
    ├── .gitignore                            # Exclusión de credenciales privadas, cache y venv
    ├── main.py                               # Punto de entrada principal del Gate 1 con demostración defensiva
    ├── cliente.py                            # Cliente modular con backoff exponencial, jitter y registro de costos (U2.1)
    ├── pipeline_texto.py                     # Limpieza, tokenización y cálculo de Precisión, Cobertura y F1 (U2.2)
    ├── resultados_metricas.json              # Persistencia de métricas cuantitativas evaluadas (Bloque 16)
    ├── revision_manual.py                    # Script de evaluación cualitativa con rúbrica de 3 criterios (Bloque 17)
    ├── revision_manual.json                  # Muestra de 10 casos revisados manualmente (Bloque 17)
    ├── cadena_tres_pasos.py                  # Chain secuencial de 3 etapas con LangChain (Bloque 18)
    ├── enrutamiento.py                       # Bifurcación con RunnableBranch, fallbacks y try/except global (Bloques 19 y 20)
    ├── agente.py                             # Agente ReAct con herramientas Pydantic (args_schema) y memoria por sesión (Bloques 21 y 22)
    ├── test_cliente.py                       # Suite de pruebas unitarias del cliente y reintentos (Bloque 14)
    ├── test_pipeline_texto.py                # Suite de pruebas unitarias de limpieza y tokenización (Bloque 15)
    ├── test_cadena_tres_pasos.py             # Pruebas con mocks para la chain de 3 pasos (Bloque 18)
    ├── test_enrutamiento.py                  # Pruebas de las rutas condicionales, default y normalización (Bloque 19)
    ├── test_orquestacion.py                  # Pruebas de resiliencia, fallbacks y captura de excepciones (Bloque 20)
    ├── README.md                             # Guía técnica de reproducción autónoma y arquitectura
    └── requirements.txt                      # Especificación congelada de dependencias del proyecto

---

## 🚀 Guía de Reproducción y Verificación Autónoma

Esta sección permite a un evaluador o desarrollador externo clonar, configurar y ejecutar todos los módulos del proyecto desde cero sin intervención asistida:

### 1. Clonar el repositorio

    git clone https://github.com/csilvaf/skillnest-git.git
    cd skillnest-git

### 2. Crear y activar el entorno virtual
- **Windows (Git Bash):**

      python -m venv .venv
      source .venv/Scripts/activate

- **Windows (PowerShell):**

      python -m venv .venv
      .\.venv\Scripts\Activate.ps1

- **macOS / Linux:**

      python3 -m venv .venv
      source .venv/bin/activate

### 3. Instalar dependencias fijadas
Instala las versiones exactas registradas en el archivo de requerimientos (`requests`, `python-dotenv`, `pytest`, `langchain`, `langchain-core`, `langchain-google-genai`, `langchain-classic`, `pydantic`):

    pip install -r requirements.txt

Para verificar que no existen inconsistencias entre librerías:

    pip check

### 4. Configurar variables de entorno
Copia la plantilla `.env.example` para generar tu archivo `.env` local:
- **Git Bash / Linux / macOS:**

      cp .env.example .env

- **Windows (PowerShell):**

      Copy-Item .env.example .env

Abre `.env` en tu editor e introduce tu clave de API válida de Google AI Studio:

    GEMINI_API_KEY=AIzaSy...tu_clave_real...

### 5. Ejecución de los módulos del sistema

#### A. Demostración del Asistente Técnico Base (Gate 1)

    python main.py

- **Caso 1:** Clasificación y diagnóstico inicial en recepción devuelto en JSON validado.
- **Caso 2:** Procedimiento técnico de taller paso a paso en JSON.
- **Caso 3:** Validación defensiva ante una entrada errónea no textual (`[1, 2]`), demostrando la captura limpia de `ValueError` sin arrojar `Traceback`.

#### B. Validación Empírica del Banco de Prompts (Consistencia)

    python prompts/test_consistencia.py

*(Exporta resultados en `prompts/registro_resultados.json` confirmando `3/3` respuestas válidas por prompt).*

#### C. Evaluación de Métricas F1 y Revisión Cualitativa (Unidad U2.2)

    python pipeline_texto.py
    python revision_manual.py

*(Genera `resultados_metricas.json` con precisión, cobertura y F1, y `revision_manual.json` con la auditoría cualitativa de 10 casos).*

#### D. Orquestación con LangChain: Chain de 3 Pasos y Enrutamiento Seguro (Unidad U2.3)

    python cadena_tres_pasos.py
    python enrutamiento.py

*(Ejecuta la cadena de extracción-diagnóstico-formato y prueba el enrutador condicional con protección de fallbacks ante preguntas, quejas y sugerencias).*

#### E. Agente Autónomo con Herramientas Pydantic y Memoria de Sesión (Unidad U2.4)

    python agente.py

*(Demuestra la invocación autónoma de herramientas estructuradas con `args_schema`, la continuidad conversacional entre turnos de un mismo `session_id` y el aislamiento estricto de memoria frente a un segundo cliente).*

#### F. Ejecución de la Suite Completa de Pruebas Automatizadas (`pytest`)
Para correr todas las pruebas unitarias del repositorio (usando `MagicMock` sin consumir cuota de la API real):

    pytest -v

*(Verifica de punta a punta `test_cliente.py`, `test_pipeline_texto.py`, `test_cadena_tres_pasos.py`, `test_enrutamiento.py` y `test_orquestacion.py`).*

---

## 📋 Registro del Ensayo de Instalación Limpia

- **Fecha:** 2026-10-22
- **Ambiente de prueba:** Directorio aislado temporal fuera del árbol de desarrollo, terminal Git Bash en Windows.
- **Encontrado:** En la primera verificación se revisó que todas las librerías utilizadas (`requests`, `python-dotenv`) estuvieran debidamente congeladas en `requirements.txt` y que `.gitignore` permitiera explícitamente `.env.example` mediante la regla `!.env.example`.
- **Corregido:** Se actualizaron las dependencias con `pip freeze > requirements.txt`, se ajustó `.gitignore` y se validó la carga automática desde `main.py` y `src/consumir_gemini.py`.
- **Resultado tras la corrección:** Clonación remota ejecutada sin anomalías, entorno `.venv` inicializado e instalado al 100% (`pip check` sin conflictos), archivo `.env` configurado a partir de `.env.example` y ejecución de `python main.py` y `python prompts/test_consistencia.py` completada sin intervención manual ni excepciones no controladas.

---

## 📈 Registro del Ensayo de Rate Limit

- **Fecha:** 2026-10-29
- **Peticiones enviadas:** 15
- **Peticiones donde apareció el error 429:** en la petición 0 (inicio del lote tras pruebas previas) y en la petición 7
- **Esperas observadas:** 2.0s y 2.1s (backoff exponencial con jitter del 10%, funcionando según lo diseñado)
- **Costo total del ensayo:** $0.00156
- **Resultado:** todas las 15 peticiones terminaron con éxito tras reintentar automáticamente, registrando costos únicamente en las operaciones completadas.
# 🛠️ Asistente Integral de Servicio Técnico (Consolas y PC) — Gate 1

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Provider](https://img.shields.io/badge/provider-Google%20AI%20Studio-orange.svg)](https://aistudio.google.com/)
[![Model](https://img.shields.io/badge/model-gemini--3.5--flash--lite-green.svg)](https://ai.google.dev/)
[![Status](https://img.shields.io/badge/evaluation-Gate%201%20Ready-brightgreen.svg)]()

Miniaplicación de línea de comandos (CLI) desarrollada en Python para la automatización del **triaje técnico, clasificación de fallas, procedimientos de soporte y estimación de presupuestos** en un servicio técnico integral de tecnología (consolas PlayStation 5, Nintendo Switch, notebooks y computadores de escritorio).

El sistema cubre todas las áreas operativas del taller:
- **Microelectrónica y Hardware:** Diagnóstico de placas madre, fuentes de poder, líneas de voltaje y reemplazo de componentes SMD/BGA.
- **Software y Sistemas Operativos:** Formateos, instalación limpia de Windows/Linux, respaldo de datos, eliminación de malware y resolución de pantallazos azules (BSOD).
- **Armado de PC, Upgrades y Mantenimiento:** Validación de compatibilidad de piezas (CPU, placas B550/X670, RAM, GPU), actualización de BIOS, cambios de hardware y mantenimiento térmico preventivo.

Consume la API de **Google Gemini** aplicando separación de responsabilidades, validación defensiva estricta en cada capa, telemetría de consumo de tokens y forzado de salida estructurada en **JSON tipado** mediante `responseSchema`.

> **Contexto académico:** Entrega oficial de la actividad **U1.6: Gate 1 - Habilitación técnica** de la *Especialización en Desarrollo con IA Generativa (Accenture / Skillnest)*.

---

## 🎯 Problema de Negocio y Alcance

En la recepción y laboratorio de un servicio técnico integral, los tiempos de atención y diagnóstico suelen verse afectados por:
1. Errores de clasificación inicial en el mesón al recibir requerimientos diversos (confundir fallas de sistema operativo o drivers con fallas físicas de hardware).
2. Demora en la validación de compatibilidad en armado de equipos, upgrades de componentes (ej. procesadores Ryzen serie 5000/7000 en distintas revisiones de BIOS) o procedimientos de formateo y respaldo.
3. Tiempo invertido en determinar las líneas de alimentación y componentes críticos a medir con multímetro u osciloscopio en etapas de microelectrónica (ej. circuitos integrados de carga M92T36/BQ24193 en Nintendo Switch o secuencias de encendido en PS5).

Esta miniaplicación estandariza y automatiza el análisis inicial de requerimientos, devolviendo diagnósticos, procedimientos paso a paso y presupuestos preliminares fiables en formato JSON estructurado, listos para integrarse con sistemas de órdenes de trabajo.

---

## 🏗️ Arquitectura del Software y Flujo de Datos

El diseño modular del proyecto desacopla estrictamente la orquestación, el transporte HTTP y el procesamiento de datos (`src/consumir_gemini.py`), integrando telemetría y programación defensiva:

```text
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
   │ 2. enviar_peticion(...)                                      │       │ ☁️ Google Gemini API       │
   │    • requests.post(url, json=body) ──────POST HTTP (JSON)───►│       │    (gemini-3.5-flash-lite) │
   │    • respuesta.json()              ◄──HTTP 200 OK (JSON)─────│       │ • Inferencia y detokenizado│
   │    • except ConnectionError -> RuntimeError                  │       │ • Desglose usageMetadata   │
   │    • except JSONDecodeError -> RuntimeError                  │       └────────────────────────────┘
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
   │ Retorno tipado + Desglose de tokens procesados               │
   └──────────────────────────────────────────────────────────────┘
```

El diagrama de arquitectura exportado en alta resolución se encuentra versionado en `docs/diagrama_arquitectura.png`.

---

## ⚡ Selección de Modelo y Trade-Offs de Ingeniería

De acuerdo con el análisis formal documentado en `docs/decision-arquitectura.md`, se evaluaron los candidatos de la familia Gemini considerando costo por cada 1.000 tokens, latencia de red y calidad de respuesta para el taller:

| Criterio Evaluado | Gemini 3.5 Flash-Lite (Operativo en Código) | Gemini 2.5 / 3.1 Pro (Referencia Analítica) |
| :--- | :--- | :--- |
| **Costo entrada (por 1.000 tokens)** | **0.000075 USD** ($0.075 / 1M) | 0.00125 USD ($1.25 / 1M) |
| **Costo salida (por 1.000 tokens)** | **0.000300 USD** ($0.300 / 1M) | 0.00500 USD ($5.00 / 1M) |
| **Latencia promedio observada** | **~1.82 segundos** | ~4.35 segundos |
| **Idoneidad para el caso** | **Excelente para triaje rápido en recepción, procedimientos de software/armado y generación de JSON estricto.** | Alta profundidad analítica para esquemáticos complejos, pero más lento para atención rápida en mesón. |
| **Estabilidad operativa** | Alta disponibilidad en Free Tier sin agotar cuotas (evita error `429`). | Restricciones estrictas de RPM en cuentas sin facturación vinculada. |

---

## 🔒 Protocolo de Seguridad y Gestión de Secretos

Para dar cumplimiento estricto a las directrices de seguridad del programa y al **criterio no compensable de credenciales protegidas**:
1. **Zero Hardcoded Secrets:** Ninguna credencial sensible, URL interna o token viaja incrustado en el código fuente. Se recuperan en tiempo de ejecución vía `python-dotenv`.
2. **Control en `.gitignore`:** El archivo `.gitignore` excluye deliberadamente cualquier variación de archivos de entorno (`.env`, `*.env`) y carpetas de entorno virtual (`.venv/`), manteniendo una excepción explícita para versionar la plantilla pública (`!.env.example`).
3. **Auditoría de Historial Git:** El repositorio cuenta con verificación de historial limpio demostrable mediante:
   ```bash
   git log --all --oneline -- .env
   ```
   *(Resultado esperado: vacío, confirmando que la clave nunca fue commiteada en el historial).*

---

## 📁 Estructura del Repositorio

```text
skillnest-git/
├── docs/
│   ├── decision-arquitectura.md          # Justificación técnica de costos, latencias y modelo
│   ├── diagrama_arquitectura.png         # Diagrama de flujo, excepciones y bifurcación de datos
│   └── evidencia_peticion_autenticada.md # Evidencia de prueba de red HTTP 200 OK
├── prompts/
│   ├── banco.py                          # Banco de prompts (recepción, laboratorio/armado, presupuestos)
│   ├── test_consistencia.py              # Validador empírico de consistencia (3 corridas por prompt)
│   └── registro_resultados.json          # Registro JSON con tasa de éxito 3/3 en adherencia de formato
├── src/
│   └── consumir_gemini.py                # Módulo central desacoplado con manejo robusto de excepciones
├── .env.example                          # Plantilla de referencia pública de variables de entorno
├── .gitignore                            # Exclusión de credenciales privadas, cache y venv
├── main.py                               # Punto de entrada principal con demostración de casos y blindaje
├── README.md                             # Guía técnica de reproducción autónoma y arquitectura
└── requirements.txt                      # Especificación inmutable de dependencias del proyecto
```

---

## 🚀 Guía de Reproducción y Verificación Autónoma

Esta sección permite a un evaluador o desarrollador externo clonar, configurar y ejecutar el proyecto desde cero sin intervención asistida:

### 1. Clonar el repositorio
```bash
git clone [https://github.com/csilvaf/skillnest-git.git](https://github.com/csilvaf/skillnest-git.git)
cd skillnest-git
```

### 2. Crear y activar el entorno virtual
- **Windows (Git Bash):**
  ```bash
  python -m venv .venv
  source .venv/Scripts/activate
  ```
- **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
- **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Instalar dependencias fijadas
Instala las versiones exactas registradas en el archivo de requerimientos:
```bash
pip install -r requirements.txt
```
Para verificar que no existen inconsistencias entre librerías:
```bash
pip check
```

### 4. Configurar variables de entorno
Copia la plantilla `.env.example` para generar tu archivo `.env` local:
- **Git Bash / Linux / macOS:**
  ```bash
  cp .env.example .env
  ```
- **Windows (PowerShell):**
  ```powershell
  Copy-Item .env.example .env
  ```

Abre `.env` en tu editor e introduce tu clave de API válida de Google AI Studio:
```env
GEMINI_API_KEY=AIzaSy...tu_clave_real...
```

### 5. Ejecución del sistema

#### A. Demostración del Asistente Técnico y Pruebas Defensivas
Ejecuta el script principal para validar el flujo completo de servicio técnico (hardware, software, armado y consolas) junto al control de excepciones:
```bash
python main.py
```
**Comportamiento esperado en pantalla:**
* **Caso 1:** Clasificación y diagnóstico inicial en recepción (fallas de consola, calentamiento de notebook, formateos o fallas de encendido devueltas en formato JSON validado).
* **Caso 2:** Procedimiento técnico de taller (aislamiento de microelectrónica en consolas o guía paso a paso de compatibilidad/armado de PC y herramientas en JSON).
* **Caso 3:** Validación defensiva ante una entrada errónea no textual (`[1, 2]`), demostrando la captura limpia de la excepción (`ValueError`) sin arrojar `Traceback` en consola.

#### B. Validación Empírica del Banco de Prompts (Consistencia)
Para auditar la consistencia empírica de los esquemas estructurados a través de 3 llamadas consecutivas por prompt:
```bash
python prompts/test_consistencia.py
```
*(Los resultados se exportan automáticamente en `prompts/registro_resultados.json` confirmando `3/3` respuestas válidas por cada prompt).*

---

## 📋 Registro del Ensayo de Instalación Limpia

- **Fecha:** 2026-10-22
- **Ambiente de prueba:** Directorio aislado temporal fuera del árbol de desarrollo, terminal Git Bash en Windows.
- **Encontrado:** En la primera verificación se revisó que todas las librerías utilizadas (`requests`, `python-dotenv`) estuvieran debidamente congeladas en `requirements.txt` y que `.gitignore` permitiera explícitamente `.env.example` mediante la regla `!.env.example`.
- **Corregido:** Se actualizaron las dependencias con `pip freeze > requirements.txt`, se ajustó `.gitignore` y se validó la carga automática desde `main.py` y `src/consumir_gemini.py`.
- **Resultado tras la corrección:** Clonación remota ejecutada sin anomalías, entorno `.venv` inicializado e instalado al 100% (`pip check` sin conflictos), archivo `.env` configurado a partir de `.env.example` y ejecución de `python main.py` y `python prompts/test_consistencia.py` completada sin intervención manual ni excepciones no controladas.

## Registro del ensayo de rate limit

- **Fecha:** 2026-10-29
- **Peticiones enviadas:** 15
- **Peticiones donde apareció el error 429:** en la petición 0 (inicio del lote tras pruebas previas) y en la petición 7
- **Esperas observadas:** 2.0s y 2.1s (backoff exponencial con jitter del 10%, funcionando según lo diseñado)
- **Costo total del ensayo:** $0.00156
- **Resultado:** todas las 15 peticiones terminaron con éxito tras reintentar automáticamente, registrando costos únicamente en las operaciones completadas.
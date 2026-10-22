# 🛠️ Asistente Técnico para Diagnóstico de Consolas y PC — Gate 1

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Provider](https://img.shields.io/badge/provider-Google%20AI%20Studio-orange.svg)](https://aistudio.google.com/)
[![Model](https://img.shields.io/badge/model-gemini--3.5--flash--lite-green.svg)](https://ai.google.dev/)
[![Status](https://img.shields.io/badge/evaluation-Gate%201%20Ready-brightgreen.svg)]()

Miniaplicación de línea de comandos (CLI) desarrollada en Python para la automatización del **triaje técnico, clasificación de fallas y asistencia diagnóstica preliminar** en talleres especializados de hardware (PlayStation 5, Nintendo Switch y placas madre de PC).

El sistema consume la API de **Google Gemini** aplicando separación de responsabilidades, validación defensiva estricta en cada capa, telemetría de consumo de tokens y forzado de salida estructurada en **JSON tipado** mediante `responseSchema`.

> **Contexto académico:** Entrega oficial de la actividad **U1.6: Gate 1 - Habilitación técnica** de la *Especialización en Desarrollo con IA Generativa (Accenture / Skillnest)*.

---

## 🎯 Problema de Negocio y Alcance

En la recepción y laboratorio de un taller técnico, los tiempos de atención y diagnóstico suelen verse degradados por:
1. Errores de triaje inicial cometidos en el mesón de atención técnica.
2. Demora en la interpretación de códigos de error por fabricante (ej. secuencias de pitidos en PS5, códigos de debug LED DRAM/CPU en motherboards).
3. Tiempo invertido en determinar las líneas de alimentación y componentes críticos a medir con multímetro u osciloscopio en etapas de microelectrónica (ej. circuitos integrados de carga M92T36/BQ24193 en Nintendo Switch).

Esta miniaplicación estandariza y automatiza el análisis inicial de síntomas, devolviendo diagnósticos preliminares fiables y estructurados listos para ser consumidos por sistemas de órdenes de trabajo o interfaces web.

---

## 🏗️ Arquitectura del Software y Flujo de Datos

El diseño modular del proyecto desacopla estrictamente la orquestación, el transporte HTTP y el procesamiento de datos (`src/consumir_gemini.py`), integrando telemetría y programación defensiva:

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

El diagrama de arquitectura exportado en alta resolución se encuentra versionado en `docs/diagrama_arquitectura.png`.

---

## ⚡ Selección de Modelo y Trade-Offs de Ingeniería

De acuerdo con el análisis formal documentado en `docs/decision-arquitectura.md`, se seleccionó **Gemini 3.5 Flash-Lite** (`gemini-3.5-flash-lite`) sobre Gemini 3.1 Pro:

| Criterio Evaluado | Gemini 3.5 Flash-Lite (Seleccionado) | Gemini 3.1 Pro (Descartado) |
| :--- | :--- | :--- |
| **Costo entrada (1M tokens)** | **$0.075 USD** | $1.25 USD *(16.6x más costoso)* |
| **Costo salida (1M tokens)** | **$0.300 USD** | $5.00 USD *(16.6x más costoso)* |
| **Latencia promedio de red** | **~1.82 segundos** | ~4.35 segundos |
| **Idoneidad para el caso** | **Excelente para triaje rápido, extracción de componentes y formato JSON estricto.** | Explicaciones excesivamente extensas y lentas para la atención en mesón. |
| **Estabilidad operativa** | Alta disponibilidad en Free Tier sin agotar cuotas (evita error `429`). | Restricciones estrictas de RPM en cuentas sin facturación vinculada. |

---

## 🔒 Protocolo de Seguridad y Gestión de Secretos

Para dar cumplimiento estricto a las directrices de seguridad del programa y al **criterio no compensable de credenciales protegidas**:
1. **Zero Hardcoded Secrets:** Ninguna credencial sensible, URL interna o token viaja incrustado en el código fuente. Se recuperan en tiempo de ejecución vía `python-dotenv`.
2. **Control en `.gitignore`:** El archivo `.gitignore` excluye deliberadamente cualquier variación de archivos de entorno (`.env`, `*.env`), manteniendo una excepción explícita para la plantilla pública (`!.env.example`).
3. **Auditoría de Historial Git:** El repositorio cuenta con verificación de historial limpio demostrable mediante:

        git log --all --oneline -- .env

   *(Resultado: vacío, confirmando que la clave nunca fue commiteada en el historial).*

---

## 📁 Estructura del Repositorio

    skillnest-git/
    ├── docs/
    │   ├── decision-arquitectura.md          # Justificación técnica de costos, latencias y modelo
    │   ├── diagrama_arquitectura.png         # Diagrama de flujo, excepciones y bifurcación de datos
    │   └── evidencia_peticion_autenticada.md # Evidencia de prueba de red HTTP 200 OK
    ├── prompts/
    │   ├── banco.py                          # Definición de prompts de sistema y schemas JSON tipados
    │   ├── test_consistencia.py              # Validador empírico de consistencia (3 corridas por prompt)
    │   └── registro_resultados.json          # Registro JSON con tasa de éxito 3/3 en adherencia de formato
    ├── src/
    │   └── consumir_gemini.py                # Módulo central desacoplado con manejo robusto de excepciones
    ├── .env.example                          # Plantilla de referencia pública de variables de entorno
    ├── .gitignore                            # Exclusión de credenciales privadas, cache y venv
    ├── main.py                               # Script ejecutable principal de demostración de casos y triaje
    ├── README.md                             # Guía técnica de reproducción autónoma y arquitectura
    └── requirements.txt                      # Especificación inmutable de dependencias del proyecto

---

## 🚀 Guía de Reproducción y Verificación Autónoma

Esta sección permite a un evaluador o desarrollador externo clonar, configurar y ejecutar el proyecto desde cero sin intervención asistida:

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
Instala las versiones exactas registradas en el archivo de requerimientos:

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

### 5. Ejecución del sistema

#### A. Demostración del Asistente Técnico y Pruebas Defensivas
Ejecuta el script principal para validar el flujo completo de triaje técnico y control de excepciones:

    python main.py

**Comportamiento esperado en pantalla:**
* **Caso 1:** Triaje inicial para PlayStation 5 (clasificación, urgencia y confianza devueltos en formato JSON validado).
* **Caso 2:** Aislamiento de etapa de circuito y componentes para Nintendo Switch (lista de circuitos integrados devuelta en JSON).
* **Caso 3:** Validación defensiva ante una entrada errónea no textual (`[1, 2]`), demostrando la captura limpia de la excepción sin arrojar `Traceback` en consola.

#### B. Validación Empírica del Banco de Prompts (Consistencia)
Para auditar la consistencia empírica de los esquemas estructurados a través de 3 llamadas consecutivas por prompt:

    python prompts/test_consistencia.py

*(Los resultados se exportan automáticamente en `prompts/registro_resultados.json` confirmando 100% de cumplimiento).*

---

## 📋 Bitácora del Ensayo de Instalación Limpia

- **Fecha de certificación:** 2026-10-22
- **Ambiente de prueba:** Directorio aislado temporal fuera del árbol de desarrollo, terminal Git Bash en Windows.
- **Resultados del ensayo:**
  1. Clonación remota ejecutada sin anomalías.
  2. Creación e inicialización del entorno `.venv` exitosa.
  3. Ejecución de `pip install -r requirements.txt` completada al 100% sin librerías faltantes ni fallos de compilación (`pip check` reportó `No broken requirements found`).
  4. Generación de `.env` a partir de `.env.example` y ejecución de `main.py` arrojando respuestas estructuradas sin fallos de red ni excepciones no controladas.
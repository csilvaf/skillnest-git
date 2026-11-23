# 🛠️ Asistente Integral de Servicio Técnico (Consolas y PC) — Gate 2

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Provider](https://img.shields.io/badge/provider-Google%20AI%20Studio-orange.svg)](https://aistudio.google.com/)
[![Model](https://img.shields.io/badge/model-gemini--3.5--flash--lite-green.svg)](https://ai.google.dev/)
[![Framework](https://img.shields.io/badge/orchestration-LangChain%20%2B%20LangGraph-purple.svg)](https://www.langchain.com/)
[![VectorDB](https://img.shields.io/badge/database-ChromaDB-blue.svg)](https://www.trychroma.com/)
[![Status](https://img.shields.io/badge/evaluation-Gate%202%20Ready-brightgreen.svg)]()

Servicio IA modular completo desarrollado en Python para la automatización del **triaje técnico, diagnóstico de fallas, RAG sobre manuales de servicio y atención conversacional** en un taller de consolas (PlayStation 5, Nintendo Switch) y computadores.

Esta versión integra **Recuperación Aumentada por Generación (RAG)** con ChromaDB, **orquestación y validación**, **observabilidad** (Trace IDs y logging estructurado) y **gobernanza técnica** (Filtro Anti-Inyección de Prompts y Punto de Supervisión Humana con LangGraph).

> **Contexto académico:** Proyecto evolutivo que abarca la entrega final del **Módulo 2 (U2.8: Gate 2 - Integración y Orquestación)** de la *Especialización en Desarrollo con IA Generativa (Accenture / Skillnest)*.

---

## 🎯 Problema de Negocio y Alcance

En la recepción y laboratorio de un servicio técnico integral, los tiempos de atención y diagnóstico suelen verse afectados por:
1. Errores de clasificación inicial al recibir requerimientos (confundir fallas de software con hardware).
2. Tiempo invertido en buscar manuales técnicos para interpretar códigos de error (ej. Luz azul de PS5, Error 2101-0001 de Switch).
3. Riesgo de que un asistente de IA entregue diagnósticos incorrectos o inventados (alucinaciones).

Esta solución estandariza el diagnóstico mediante RAG. El sistema **solo** responde basándose en los manuales de servicio indexados en su base vectorial, garantizando precisión técnica y evitando alucinaciones que puedan dañar equipos del cliente.

---

## 🏗️ Evolución Módulo 2: Orquestación, RAG y Gobernanza

Durante el Módulo 2, el proyecto evolucionó para convertirse en un sistema seguro, observable y auditable:

### 1. Sistema RAG y Base de Datos Vectorial (Unidad U2.5)
- **Indexación y Recuperación:** Documentación técnica de consolas ingerida, fragmentada (chunking) e indexada en una base de datos vectorial local (`ChromaDB`).
- **Citación Estricta:** El sistema devuelve respuestas fundamentadas, adjuntando explícitamente el nombre del archivo fuente (ej. `[manual_ps5.pdf]`) para asegurar trazabilidad.

### 2. Personalización de Modelos y PEFT (Unidad U2.6)
- **Fine-Tuning Balanceado:** Estructuración de un dataset (`.jsonl`) con ejemplos de diagnóstico equilibrados para evitar sesgos entre fallas de consolas vs PC.
- **Validación Rígida:** Función `chequear_balance` que inspecciona la distribución de datos antes de permitir un tuning job.

### 3. Observabilidad, Seguridad y Gobernanza (Unidad U2.7)
- **Logging Estructurado y Trace ID:** Cada etapa de una consulta (indexación, recuperación, filtrado, consumo de tokens) registra logs en formato JSON asociando un `trace_id` único, asegurando aislamiento entre sesiones concurrentes mediante `contextvars`.
- **Filtro Anti-Inyección (RegExp):** Capa de defensa que audita los documentos recuperados. Si el contexto incluye instrucciones maliciosas (ej. *"ignora todo lo anterior"*), el sistema las bloquea, reporta un `WARNING` en los logs y devuelve una respuesta segura.
- **Punto de Supervisión Humana (LangGraph):** Integración de un grafo de estado que ejecuta un `interrupt()`. Toda actualización crítica (ej. desplegar un nuevo prompt a producción) requiere aprobación humana explícita (`Command(resume=True)`).
- **Matriz de Riesgos:** Documentación que cruza Probabilidad e Impacto de riesgos técnicos (filtración de PII, sesgos, deprecación de modelos), generando alertas automatizadas.

---

## 🔒 Protocolo de Seguridad y Gestión de Secretos

Para cumplir con los criterios no compensables de la rúbrica:
1. **Zero Hardcoded Secrets:** Ninguna API Key se sube a código fuente (se usan en tiempo de ejecución vía `python-dotenv`).
2. **Logs Sanitizados:** Las trazas de observabilidad no imprimen texto crudo ni PII (Información Personal Identificable); solo guardan *hashes*, longitudes y metadatos operativos.
3. **Control en `.gitignore`:** Exclusión deliberada de entornos virtuales y archivos `.env`, permitiendo explícitamente solo `.env.example`.

---

## 📁 Estructura del Repositorio (Gate 2)

```text
skillnest-git/
├── vectorstore/                        # Base de datos vectorial ChromaDB persistida localmente
├── servicio_rag.py                     # Motor principal orquestado: Pipeline RAG y Grafo de Supervisión
├── test_gate2.py                       # Pruebas automatizadas (pytest) de los 4 criterios de rúbrica
├── verificar_entorno.py                # Script de validación de dependencias y estado de base vectorial
├── registro_prompts.py                 # Versionado de prompts con historial y hash (diff de cambios)
├── matriz_riesgos.py                   # Matriz operativa calculando probabilidad e impacto de riesgos
├── .env.example                        # Plantilla pública de variables requeridas
├── .gitignore                          # Exclusión estricta de .env, bases de datos y venv
├── README.md                           # Guía técnica de reproducción autónoma
└── requirements.txt                    # Dependencias inmutables del proyecto
```

---

## 🚀 Guía de Instalación y Ejecución Autónoma

Esta sección permite a un evaluador externo clonar, configurar y validar los 4 criterios no compensables del Gate 2 mediante automatización:

### 1. Clonar el repositorio
```bash
git clone https://github.com/csilvaf/skillnest-git.git
cd skillnest-git
```

### 2. Crear y activar el entorno virtual
*   **Windows (Git Bash):**
```bash
python -m venv .venv
source .venv/Scripts/activate
```
*   **macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias fijadas
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Copia la plantilla `.env.example` para generar tu archivo `.env` local y añade tu API Key:
```bash
cp .env.example .env
```

### 5. Verificación de Entorno
Ejecuta el script de diagnóstico para certificar librerías, claves y directorio RAG:
```bash
python verificar_entorno.py
```

### 6. Ejecución del Servicio (Pipeline RAG Completo)
Este script orquesta el pipeline: indexa documentos base, recupera conocimiento, filtra intentos de inyección maliciosos, genera respuestas citando fuentes, registra el consumo JSON y demuestra el punto de pausa de supervisión humana:
```bash
python servicio_rag.py
```

### 7. Ejecución de Tests Automatizados (Criterios No Compensables)
Valida la rúbrica crítica del Gate 2 de extremo a extremo usando `pytest`:
```bash
python -m pytest test_gate2.py -v --disable-warnings
```
*(Salida esperada: 4 `PASSED` confirmando pipeline sano, citación obligatoria de fuentes, privacidad absoluta en logs y capacidad real de supervisión en LangGraph).*

---

## 📋 Registro de Ensayo Funcional (Gate 2)
- **Fecha:** 2026-11-23
- **Resultado:** Ejecución automatizada vía `pytest` finalizada exitosamente (4/4 passed). El pipeline extrae correctamente los manuales de la base vectorial `ChromaDB`, los logs asocian identificadores únicos (`trace_id`) de manera limpia sin PII, y el grafo supervisor con `interrupt()` frena la ejecución hasta recibir confirmación explícita, cumpliendo íntegramente la exigencia del Módulo 2.

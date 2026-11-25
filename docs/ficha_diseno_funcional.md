# Ficha de Diseño Funcional

## 1. Problema de negocio
El equipo de recepción y laboratorio del servicio técnico de consolas y PC responde unas 25 consultas semanales (estimación) buscando a mano en internet, foros y manuales de servicio. Cada triaje toma cerca de 8 minutos y los diagnósticos varían según la experiencia de quien conteste. Se espera que cualquier integrante del taller obtenga un diagnóstico preciso con su fuente técnica citada en menos de un minuto.

## 2. Requerimientos y alcance (MVP)
### Requerimientos funcionales
- RF-01: El usuario envía una consulta sobre síntomas técnicos a un endpoint y recibe un diagnóstico preliminar en JSON.
- RF-02: Cada respuesta de diagnóstico incluye al menos una fuente citada con el nombre del manual técnico.
- RF-03: El servicio de diagnóstico se levanta desde cero mediante un comando utilizando un contenedor.
- RF-04: Una interfaz web con control de inventario, seguimiento de órdenes multi-usuario y panel de métricas de taller.

### Requerimientos no funcionales
- RNF-01: El endpoint de consulta responde en menos de 5 segundos en al menos 9 de cada 10 consultas de prueba.
- RNF-02: En los registros de las 10 consultas de prueba, ninguna línea contiene el texto completo de la pregunta del cliente ni de los documentos, solo longitudes y conteos.
- RNF-03: El servicio levanta desde cero en un contenedor, siguiendo el README, en menos de 10 minutos.

### Alcance
Imprescindible: RF-01, RF-02, RF-03
Deseable: Ninguno
Fuera de alcance: RF-04 (requiere datos y sistemas reales, excede el presupuesto).

## 3. Arquitectura de la solución
Diagrama: docs/diagrama_arquitectura.png
Modelo: Gemini 3.5 Flash-Lite mediante API, con la clave protegida en archivo .env local.
Vector store: ChromaDB persistido localmente en la carpeta del índice vectorial.
Orquestación: Pipeline RAG y revisión de inyecciones con LangChain y LangGraph.
Exposición: Servicio backend expuesto a través de FastAPI con un endpoint de consulta.
Empaquetado: Imagen construida con Docker aislando el entorno de ejecución.

## 4. Criterios de aceptación
[PENDIENTE: se completa en el Bloque 34]

## 5. Plan de construcción por hitos
[PENDIENTE: se completa en el Bloque 34]

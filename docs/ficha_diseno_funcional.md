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
- CA-01 (RF-01): Al enviar el síntoma "La consola se apaga a los 10 segundos", la respuesta es un JSON con los campos de diagnóstico.
- CA-02 (RF-02): Para esa misma consulta, la respuesta cita explícitamente "manual_ps5.pdf" como fuente técnica.
- CA-03 (RF-02): Al consultar por "Receta de pastel", que los manuales no cubren, la respuesta indica que no hay información y la lista "fuentes" viene vacía.
- CA-04 (RF-03): Al ejecutar el comando de construcción Docker, el servicio levanta exitosamente en el puerto esperado.
- CA-05 (RNF-01): En 10 consultas de prueba de diagnóstico, al menos 9 responden en menos de 5 segundos.
- CA-06 (RNF-02): Tras ejecutar 10 consultas de prueba, ninguna línea del registro de sistema contiene el texto completo de la pregunta.
- CA-07 (RNF-03): Siguiendo únicamente el README en un equipo limpio, el contenedor se construye y el servicio responde en menos de 10 minutos desde el inicio.

## 5. Plan de construcción por hitos
Horas disponibles: 20 h
Margen de imprevistos: 4 h
- H1 (3 h): Servicio FastAPI con el endpoint de consulta. Cubre: RF-01. Se comprueba con: CA-01.
- H2 (3 h): Respuestas con fuente desde el indice persistido ChromaDB. Cubre: RF-02. Se comprueba con: CA-02, CA-03.
- H3 (4 h): Servicio empaquetado y expuesto en un contenedor Docker. Cubre: RF-03. Se comprueba con: CA-04.
- H4 (6 h): Pruebas, documentacion y ensayo de la defensa final. Cubre: RNF-01, RNF-02, RNF-03. Se comprueba con: CA-05, CA-06, CA-07.

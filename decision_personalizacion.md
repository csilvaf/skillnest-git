# Decisión de personalización: clasificador de tickets de servicio técnico

## 1. El problema
El agente que clasifica los ingresos de consolas y equipos no siempre responde con el formato JSON esperado. Aunque el modelo base entiende la diferencia entre una falla de disco duro y una de microelectrónica, de 20 respuestas evaluadas, 6 (30%) no traían los campos estrictos de 'area_tecnica' y 'prioridad'. El problema no es que le falte información, sino que falla la consistencia de la salida estructural.

## 2. Resultado del método de decisión
- **Fine-tuning completo**: 3 puntos
- **PEFT**: 3 puntos
- **RAG**: 0 puntos

**Empate entre: Fine-tuning completo, PEFT**

## 3. Técnica elegida y por qué
Elijo **PEFT**. El método arrojó empate, así que desempato por costo de cómputo y tiempo. Con nuestro dataset de taller (12 ejemplos iniciales, con meta de 150), un adapter pequeño (ADAPTER_SIZE_FOUR) puede aprender a respetar el formato JSON de 'area_tecnica' y 'prioridad' sin necesidad de gastar en un fine-tuning completo de todos los parámetros.

## 4. Qué necesitaría para ejecutarla
Tengo 12 ejemplos validados y etiquetados en el Bloque 29, repartidos de forma equilibrada en 4 áreas (microelectrónica, software, hardware, mantenimiento térmico). Para evitar sobreajuste, necesito al menos 138 ejemplos más para llegar a un baseline de 150. Esto requeriría unas 9.2 horas humanas de revisión a 4 minutos por ticket.
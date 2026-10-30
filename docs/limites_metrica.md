# Límites de la métrica de evaluación

## Qué mide
Coincidencia de palabras entre una respuesta generada y una referencia, contando repeticiones (precisión, cobertura, F1)[cite: 61].

## Modos de falla conocidos
* **Sinónimos y paráfrasis correctas puntúan bajo:** La métrica castiga fuertemente las variaciones técnicas correctas. Ejemplo: consulta sobre los 3 pitidos de PS5, el F1 arrojó `0.24` a pesar de ser un diagnóstico clínicamente acertado[cite: 55, 61].
* **Falsos positivos por coincidencia de vocabulario:** Una respuesta con F1 alto puede invertir el sentido técnico por la ausencia de una sola negación. Ejemplo: en la consulta "¿Puedo limpiar la placa madre con agua?", el F1 fue de `0.70` pero la respuesta omitió el "no", aprobando una práctica destructiva[cite: 54, 55].
* **Penalización por exhaustividad:** Cuando el modelo agrega pasos de diagnóstico extra muy útiles para el técnico (como limpiar los contactos de la RAM), la precisión baja drásticamente por introducir tokens no presentes en una referencia breve (F1 de `0.40` en diagnóstico de video de PC).

## Muestra revisada
10 casos revisados a mano: combinando los 5 con menor F1 y los 5 con mayor F1, seleccionados sobre un lote de respuestas del módulo de diagnóstico de taller técnico el 30-10-2026[cite: 61].

## Recomendación de uso
Usar el F1 únicamente como termómetro general para comparar en volumen entre diferentes versiones del prompt o del modelo de forma automatizada[cite: 61]. Se debe **revisar siempre a mano** cualquier respuesta relacionada con procedimientos eléctricos, limpiezas de hardware o compatibilidad de voltaje, donde la omisión de un "no" puede resultar destructiva para el equipo del cliente[cite: 61].
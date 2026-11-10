# Límites de autonomía: Agente de Servicio Técnico (Consolas y PC)

## Herramientas y nivel de riesgo

| Herramienta | Descripción | Nivel de riesgo | Supervisión requerida |
| :--- | :--- | :--- | :--- |
| `consultar_estado_reparacion_detallado` | Consulta el estado actual y la bitácora de hitos de una orden de reparación (`PS5-202`, `PC-100`). | **Bajo** (solo lectura) | Ninguna (solo lee información en memoria, no modifica ningún estado ni registro del taller). |
| `calcular_presupuesto_trabajo` | Calcula el costo estimado sumando horas de mano de obra ($15.000 CLP/h) y repuestos. | **Bajo** (solo lectura / cálculo) | Ninguna (solo realiza una operación aritmética informativa, no emite cobros ni altera órdenes). |
| `autorizar_reembolso_garantia` | Emite un reembolso económico por garantía asociado a una orden de trabajo. | **Alto** (escritura irreversible con impacto económico) | **Aprobación humana previa obligatoria** mediante `esperar_aprobacion` y auditoría en `registro_aprobaciones`. |

## Herramientas que requieren aprobación humana

* **`autorizar_reembolso_garantia`**:
  * **Motivo de la aprobación:** Mueve dinero de forma irreversible y genera un impacto económico directo para el taller técnico. Un error de razonamiento del modelo (o una inyección de prompt por parte de un usuario pidiendo un monto indebido) no puede ejecutarse de manera desatendida.
  * **Mecanismo implementado en código (`agente.py`):** Antes de procesar la devolución, la herramienta invoca `esperar_aprobacion(mensaje, tiempo_limite_segundos=300)`. Si el supervisor humano no responde `"s"` o si se agota el tiempo límite de espera (timeout), la función aplica un valor por defecto seguro (`False`), cancela el reembolso y registra el evento en `registro_aprobaciones` mediante `registrar_aprobacion()`.

## Revisión de trazas

* **Archivo de persistencia:** `trazas_agente.jsonl` (generado por `registrar_traza()` en cada invocación a `agente_con_memoria`).
* **Frecuencia:**
  * **Semanal** sobre una muestra representativa de interacciones generales (consultas de estado y cálculo de presupuestos).
  * **100% de los casos (revisión total)** en cualquier traza donde se haya invocado la herramienta de riesgo alto `autorizar_reembolso_garantia`, contrastando contra `registro_aprobaciones`.
* **Qué se busca (patrones sospechosos del Bloque 23):**
  1. **La misma herramienta invocada varias veces seguidas con argumentos parecidos:** Detectado automáticamente en primera pasada mediante la función `marcar_repeticiones_sospechosas()`. Indica que una observación fue ambigua o que el agente entró en bucle intentando buscar un código de orden inexistente.
  2. **Invocación de `autorizar_reembolso_garantia` sin registro de aprobación correspondiente:** Señal de alerta crítica en el flujo de supervisión.
  3. **Respuesta final que no coincide con ninguna observación:** Por ejemplo, si el agente inventa que una consola está lista para retiro o informa un presupuesto distinto al retornado por la herramienta en `intermediate_steps`.

## Qué hacer ante un comportamiento inesperado

Si durante la auditoría de `trazas_agente.jsonl` se detecta un patrón anómalo, alucinación de datos o intento de uso indebido de herramientas, se ejecutará este plan en orden estricto:

1. **Desactivar de inmediato la herramienta afectada:** Retirar temporalmente la función (por ejemplo, `autorizar_reembolso_garantia`) de la lista `herramientas` pasada a `create_tool_calling_agent` y `AgentExecutor` en `agente.py`, dejando al agente únicamente en modo informativo de solo lectura.
2. **Aislar y reproducir el caso con la traza:** Extraer el `entrada`, `session_id` y `acciones` desde la línea correspondiente de `trazas_agente.jsonl` y ejecutar una prueba aislada para identificar si el fallo provino del prompt de sistema, de la memoria acumulada o del esquema Pydantic.
3. **Ajustar `args_schema` y el docstring de la herramienta:** Refinar las descripciones de `Field(description=...)` en las clases Pydantic (`ArgumentosEstadoReparacion`, `ArgumentosPresupuesto`, `ArgumentosReembolsoGarantia`) y el docstring de la función para eliminar ambigüedades sobre cuándo debe o no invocarse.
4. **Verificar y reactivar:** Confirmar mediante ejecución controlada y revisión de `intermediate_steps` que el agente elige la herramienta correcta antes de volver a habilitarla en el flujo principal.
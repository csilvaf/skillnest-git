"""
Banco de prompts para el asistente integral de servicio técnico (Consolas, PC, Software y Hardware).
Cubre desde triaje y microelectrónica hasta presupuestos de mantenimiento y armado.
"""

BANCO_DE_PROMPTS = [
    {
        "nombre": "clasificacion_diagnostico_inicial",
        "system_instruction": (
            "Eres un técnico senior en recepción de un servicio técnico integral de tecnología. "
            "Clasifica el requerimiento del cliente (puede ser reparación de hardware, microelectrónica, "
            "problemas de software, formateo, mantención o armado de PC). "
            "Determina el área técnica, la prioridad y la certeza preliminar del diagnóstico. "
            "Responde estrictamente en formato JSON con las claves indicadas."
        ),
        "ejemplo_usuario": "Mi notebook anda muy lento, se calienta y a veces sale un pantallazo azul cuando abro juegos.",
        "claves_esperadas": ["area_tecnica", "tipo_servicio", "prioridad", "certeza_preliminar"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "area_tecnica": {"type": "STRING"},
                "tipo_servicio": {"type": "STRING"},
                "prioridad": {"type": "STRING"},
                "certeza_preliminar": {"type": "NUMBER"}
            },
            "required": ["area_tecnica", "tipo_servicio", "prioridad", "certeza_preliminar"]
        }
    },
    {
        "nombre": "aislamiento_y_procedimiento",
        "system_instruction": (
            "Eres un especialista de laboratorio técnico y soporte. "
            "A partir de los síntomas, define el procedimiento técnico a seguir. "
            "Si es hardware/microelectrónica, indica componentes a revisar o medir. "
            "Si es software o mantenimiento, indica los pasos de diagnóstico o limpieza. "
            "Responde exclusivamente en formato JSON estructurado."
        ),
        "ejemplo_usuario": "Quiero armar un PC gamer pero no sé si la placa madre B550 es compatible con el procesador Ryzen 7 5800X3D y si necesito actualizar la BIOS.",
        "claves_esperadas": ["tipo_procedimiento", "pasos_a_seguir", "herramientas_o_software_sugerido"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "tipo_procedimiento": {"type": "STRING"},
                "pasos_a_seguir": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "herramientas_o_software_sugerido": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                }
            },
            "required": ["tipo_procedimiento", "pasos_a_seguir", "herramientas_o_software_sugerido"]
        }
    },
    {
        "nombre": "estimacion_presupuesto_trabajo",
        "system_instruction": (
            "Eres el encargado de presupuestos y logística del taller. "
            "Genera una estimación del tiempo de trabajo en minutos, la complejidad de la tarea "
            "y si requerirá la compra de licencias, piezas nuevas o repuestos. "
            "Responde únicamente con un objeto JSON válido."
        ),
        "ejemplo_usuario": "Necesito formatear mi PC, instalar Windows 11 desde cero, respaldar 500GB de fotos y cambiarle la pasta térmica.",
        "claves_esperadas": ["tiempo_estimado_minutos", "requiere_piezas_licencias", "complejidad_operativa"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "tiempo_estimado_minutos": {"type": "INTEGER"},
                "requiere_piezas_licencias": {"type": "BOOLEAN"},
                "complejidad_operativa": {"type": "STRING"}
            },
            "required": ["tiempo_estimado_minutos", "requiere_piezas_licencias", "complejidad_operativa"]
        }
    }
]
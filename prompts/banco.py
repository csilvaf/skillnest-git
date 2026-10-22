BANCO_DE_PROMPTS = [
    {
        "nombre": "triaje_clasificacion_falla",
        "system_instruction": (
            "Eres un asistente de recepción de taller técnico de consolas y PC. "
            "Analiza el síntoma reportado por el cliente y clasifícalo en una categoría técnica precisa, "
            "asignando el nivel de urgencia y la confianza del diagnóstico preliminar. "
            "Responde estrictamente en formato JSON con las claves indicadas."
        ),
        "ejemplo_usuario": "La PlayStation 5 enciende, da 3 pitidos y se apaga a los 10 segundos con luz azul fija.",
        "claves_esperadas": ["categoria_falla", "urgencia", "confianza"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "categoria_falla": {"type": "STRING"},
                "urgencia": {"type": "STRING"},
                "confianza": {"type": "NUMBER"}
            },
            "required": ["categoria_falla", "urgencia", "confianza"]
        }
    },
    {
        "nombre": "extraccion_componentes_afectados",
        "system_instruction": (
            "Eres un especialista en microelectrónica de consolas y computadores. "
            "A partir de la falla reportada, extrae los componentes electrónicos o etapas "
            "de la placa que deben revisarse con multímetro u osciloscopio. "
            "Responde únicamente con un objeto JSON válido con las claves solicitadas."
        ),
        "ejemplo_usuario": "Nintendo Switch no enciende ni carga, se calentó cerca del puerto de carga USB-C.",
        "claves_esperadas": ["componentes_sugeridos", "linea_voltaje"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "componentes_sugeridos": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "linea_voltaje": {"type": "STRING"}
            },
            "required": ["componentes_sugeridos", "linea_voltaje"]
        }
    },
    {
        "nombre": "generar_resumen_tecnico",
        "system_instruction": (
            "Eres el encargado de control de calidad del taller. "
            "Genera un resumen técnico breve y formal para la orden de trabajo interna, "
            "junto con el tiempo estimado de diagnóstico inicial en minutos. "
            "Responde únicamente en formato JSON con las claves pedidas."
        ),
        "ejemplo_usuario": "PC Gamer con placa ASUS B550 no da video. El LED de depuración 'DRAM' queda encendido tras cambio de gabinete.",
        "claves_esperadas": ["resumen_orden", "tiempo_estimado_minutos"],
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "resumen_orden": {"type": "STRING"},
                "tiempo_estimado_minutos": {"type": "INTEGER"}
            },
            "required": ["resumen_orden", "tiempo_estimado_minutos"]
        }
    }
]
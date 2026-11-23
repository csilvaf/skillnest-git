"""
Generador automático de la Decisión Fundamentada de Personalización (Bloque 30)
Dominio: Taller de Servicio Técnico de Consolas y PC.
"""

def recomendar_estrategia(respuestas: dict[str, bool]) -> tuple[dict[str, int], list[str]]:
    puntos = {"RAG": 0, "Fine-tuning completo": 0, "PEFT": 0}
    
    if respuestas["informacion_cambia_seguido"]:
        puntos["RAG"] += 3
    if respuestas["problema_de_formato_o_tono"]:
        puntos["PEFT"] += 2
        puntos["Fine-tuning completo"] += 1
    if respuestas["dataset_grande_y_de_calidad"]:
        puntos["Fine-tuning completo"] += 2
        puntos["PEFT"] += 1
    if respuestas["presupuesto_limitado_o_iterar_rapido"]:
        puntos["RAG"] += 2
        puntos["PEFT"] += 1
    if respuestas["necesita_multiples_variantes"]:
        puntos["PEFT"] += 2
        
    maximo = max(puntos.values())
    ganadoras = [tecnica for tecnica, p in puntos.items() if p == maximo]
    return puntos, ganadoras


def generar_esqueleto_decision(problema: str, puntos: dict, ganadoras: list[str]) -> str:
    empate = len(ganadoras) > 1
    lineas = []
    
    lineas.append("# Decisión de personalización: clasificador de tickets de servicio técnico")
    lineas.append("")
    lineas.append("## 1. El problema")
    lineas.append(problema)
    lineas.append("")
    lineas.append("## 2. Resultado del método de decisión")
    
    for tecnica, p in sorted(puntos.items(), key=lambda x: -x[1]):
        lineas.append(f"- **{tecnica}**: {p} puntos")
        
    lineas.append("")
    if empate:
        lineas.append(f"**Empate entre: {', '.join(ganadoras)}**")
        lineas.append("")
        lineas.append("## 3. Técnica elegida y por qué")
        lineas.append(
            "Elijo **PEFT**. El método arrojó empate, así que desempato por costo de cómputo y tiempo. "
            "Con nuestro dataset de taller (12 ejemplos iniciales, con meta de 150), un adapter pequeño (ADAPTER_SIZE_FOUR) "
            "puede aprender a respetar el formato JSON de 'area_tecnica' y 'prioridad' sin necesidad de gastar en un fine-tuning completo de todos los parámetros."
        )
    else:
        lineas.append("## 3. Técnica elegida y por qué")
        lineas.append(f"La técnica ganadora clara es **{ganadoras[0]}**, dado que resuelve directamente la necesidad.")
        
    lineas.append("")
    lineas.append("## 4. Qué necesitaría para ejecutarla")
    lineas.append(
        "Tengo 12 ejemplos validados y etiquetados en el Bloque 29, repartidos de forma equilibrada "
        "en 4 áreas (microelectrónica, software, hardware, mantenimiento térmico). Para evitar sobreajuste, "
        "necesito al menos 138 ejemplos más para llegar a un baseline de 150. Esto requeriría unas 9.2 horas "
        "humanas de revisión a 4 minutos por ticket."
    )
    
    return "\n".join(lineas)


if __name__ == "__main__":
    # Respuestas aplicadas al Taller Técnico de Consolas (Problema de Formato)
    respuestas_mi_caso = {
        "informacion_cambia_seguido": False,            # Los códigos de error y JSON no cambian seguido.
        "problema_de_formato_o_tono": True,             # Falla en entregar el JSON estructurado consistentemente.
        "dataset_grande_y_de_calidad": True,            # Asumiremos la meta de 150+ tickets reales validados.
        "presupuesto_limitado_o_iterar_rapido": False,  # Asumimos que podemos costear un entrenamiento.
        "necesita_multiples_variantes": False,          # Un solo clasificador para todo el taller.
    }
    
    if any(valor is None for valor in respuestas_mi_caso.values()):
        raise SystemExit("Completa las cinco respuestas con True o False antes de continuar.")
        
    puntos, ganadoras = recomendar_estrategia(respuestas_mi_caso)
    
    problema_taller = (
        "El agente que clasifica los ingresos de consolas y equipos no siempre responde con el formato JSON esperado. "
        "Aunque el modelo base entiende la diferencia entre una falla de disco duro y una de microelectrónica, de 20 "
        "respuestas evaluadas, 6 (30%) no traían los campos estrictos de 'area_tecnica' y 'prioridad'. "
        "El problema no es que le falte información, sino que falla la consistencia de la salida estructural."
    )
    
    documento_final = generar_esqueleto_decision(problema_taller, puntos, ganadoras)
    
    archivo_salida = "decision_personalizacion.md"
    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write(documento_final)
        
    print(f"Resultado del método: {puntos}")
    print(f"Técnica ganadora/empatada: {ganadoras}")
    print(f"\n[OK] Documento de decisión redactado y guardado en '{archivo_salida}'")
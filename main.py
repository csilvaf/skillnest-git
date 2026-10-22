"""
Punto de entrada principal (main.py)
Asistente Técnico para Diagnóstico de Consolas y PC — Gate 1
"""
import os
import sys

# Permitir importaciones directas desde las carpetas del proyecto
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.consumir_gemini import obtener_dato_de_prueba
from prompts.banco import BANCO_DE_PROMPTS


def ejecutar_demostracion():
    print("=" * 70)
    print(" ASISTENTE DE SERVICIO TÉCNICO: CONSOLAS Y PC (GATE 1)")
    print("=" * 70)

    # -------------------------------------------------------------
    # Demostración 1: Triaje técnico en recepción (PlayStation 5)
    # Extraído directamente de tu banco de prompts con salida JSON
    # -------------------------------------------------------------
    prompt_triaje = BANCO_DE_PROMPTS[0]
    print(f"\n--- [Demostración 1: {prompt_triaje['nombre']}] ---")
    print(f"Síntoma ingresado: \"{prompt_triaje['ejemplo_usuario']}\"")
    
    try:
        resultado_triaje = obtener_dato_de_prueba(
            pregunta=prompt_triaje["ejemplo_usuario"],
            system_instruction=prompt_triaje["system_instruction"],
            response_schema=prompt_triaje["response_schema"]
        )
        print("\nDiagnóstico de triaje estructurado (JSON validado):")
        print(resultado_triaje)
    except (ValueError, RuntimeError) as error:
        print(f"Error en Demostración 1: {error}")

    # -------------------------------------------------------------
    # Demostración 2: Aislamiento de microelectrónica (Nintendo Switch)
    # Extraído directamente de tu banco de prompts
    # -------------------------------------------------------------
    prompt_switch = BANCO_DE_PROMPTS[1]
    print("\n" + "-" * 70)
    print(f"--- [Demostración 2: {prompt_switch['nombre']}] ---")
    print(f"Síntoma ingresado: \"{prompt_switch['ejemplo_usuario']}\"")
    
    try:
        resultado_switch = obtener_dato_de_prueba(
            pregunta=prompt_switch["ejemplo_usuario"],
            system_instruction=prompt_switch["system_instruction"],
            response_schema=prompt_switch["response_schema"]
        )
        print("\nComponentes y líneas a medir (JSON validado):")
        print(resultado_switch)
    except (ValueError, RuntimeError) as error:
        print(f"Error en Demostración 2: {error}")

    # -------------------------------------------------------------
    # Demostración 3: Validación defensiva (Tipo de dato inválido [1, 2])
    # -------------------------------------------------------------
    print("\n" + "-" * 70)
    print("--- [Demostración 3: Validación defensiva (Entrada [1, 2])] ---")
    entrada_invalida = [1, 2]
    print(f"Probando entrada no permitida: {entrada_invalida}")
    
    try:
        obtener_dato_de_prueba(entrada_invalida)
    except (ValueError, RuntimeError) as error_capturado:
        print(f"Éxito: Excepción controlada capturada limpiamente -> {error_capturado}")

    print("\n" + "=" * 70)
    print("  Flujo completado exitosamente sin excepciones no controladas.")
    print("=" * 70)


if __name__ == "__main__":
    ejecutar_demostracion()
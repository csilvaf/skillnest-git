"""
Punto de entrada principal (main.py)
Asistente Integral de Servicio Técnico (Consolas, PC, Software y Hardware) — Gate 1
"""
import os
import sys

# Permitir importaciones directas desde las carpetas del proyecto
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.consumir_gemini import obtener_dato_de_prueba
from prompts.banco import BANCO_DE_PROMPTS

def ejecutar_demostracion():
    print("=" * 75)
    print(" ASISTENTE INTEGRAL DE SERVICIO TÉCNICO: HARDWARE Y SOFTWARE (GATE 1)")
    print("=" * 75)

    # -------------------------------------------------------------
    # Demostración 1: Triaje de falla mixta (Hardware/Software)
    # -------------------------------------------------------------
    prompt_triaje = BANCO_DE_PROMPTS[0]
    print(f"\n--- [Caso 1: Recepción - {prompt_triaje['nombre']}] ---")
    sintoma = "Mi notebook se reinicia solo cuando abro juegos pesados y está muy caliente."
    print(f"Requerimiento: \"{sintoma}\"")
    
    try:
        resultado_triaje = obtener_dato_de_prueba(
            pregunta=sintoma,
            system_instruction=prompt_triaje["system_instruction"],
            response_schema=prompt_triaje["response_schema"]
        )
        print("\nDiagnóstico de recepción (JSON validado):")
        print(resultado_triaje)
    except (ValueError, RuntimeError) as error:
        print(f"Error en Demostración 1: {error}")

    # -------------------------------------------------------------
    # Demostración 2: Procedimiento de Armado de PC / Compatibilidad
    # -------------------------------------------------------------
    prompt_procedimiento = BANCO_DE_PROMPTS[1]
    print("\n" + "-" * 75)
    print(f"--- [Caso 2: Taller - {prompt_procedimiento['nombre']}] ---")
    requerimiento = "Quiero armar un PC. Tengo una placa B550 y quiero ponerle un Ryzen 7 5800X3D. ¿Qué hago primero?"
    print(f"Requerimiento: \"{requerimiento}\"")
    
    try:
        resultado_proc = obtener_dato_de_prueba(
            pregunta=requerimiento,
            system_instruction=prompt_procedimiento["system_instruction"],
            response_schema=prompt_procedimiento["response_schema"]
        )
        print("\nProcedimiento y herramientas sugeridas (JSON validado):")
        print(resultado_proc)
    except (ValueError, RuntimeError) as error:
        print(f"Error en Demostración 2: {error}")

    # -------------------------------------------------------------
    # Demostración 3: Validación defensiva (Tipo de dato inválido [1, 2])
    # -------------------------------------------------------------
    print("\n" + "-" * 75)
    print("--- [Caso 3: Validación defensiva de sistema (Entrada [1, 2])] ---")
    entrada_invalida = [1, 2]
    print(f"Probando entrada del sistema no permitida: {entrada_invalida}")
    
    try:
        obtener_dato_de_prueba(entrada_invalida)
    except (ValueError, RuntimeError) as error_capturado:
        print(f"Éxito: Excepción controlada capturada limpiamente -> {error_capturado}")

    print("\n" + "=" * 75)
    print("  Flujo de taller completado exitosamente sin excepciones no controladas.")
    print("=" * 75)


if __name__ == "__main__":
    ejecutar_demostracion()
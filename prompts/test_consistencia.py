import sys
import os
import json
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.consumir_gemini import armar_peticion, enviar_peticion, extraer_texto, parsear_respuesta_json
from prompts.banco import BANCO_DE_PROMPTS


def ejecutar_test_consistencia():
    registro = {}
    print("Iniciando validación de consistencia del banco de prompts...\n")

    for prompt in BANCO_DE_PROMPTS:
        exitos = 0
        intentos = 3
        nombre = prompt["nombre"]

        for intento in range(intentos):
            url, body = armar_peticion(
                pregunta=prompt["ejemplo_usuario"],
                system_instruction=prompt["system_instruction"],
                response_schema=prompt.get("response_schema")
            )

            try:
                respuesta = enviar_peticion(url, body)
                texto = extraer_texto(respuesta)
                datos = parsear_respuesta_json(texto)

                if all(clave in datos for clave in prompt["claves_esperadas"]):
                    exitos += 1
                else:
                    print(f"[{nombre}] Intento {intento + 1} falló: La respuesta no tiene todas las claves esperadas.")
            except (ValueError, RuntimeError) as error:
                print(f"[{nombre}] Intento {intento + 1} falló: {error}")

            time.sleep(1)

        print(f"{nombre}: {exitos}/{intentos} respuestas válidas")
        registro[nombre] = {
            "exitos": exitos,
            "intentos": intentos
        }

    ruta_salida = os.path.join(os.path.dirname(__file__), "registro_resultados.json")
    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        json.dump(registro, archivo, indent=2, ensure_ascii=False)

    print(f"\nResultados guardados exitosamente en: {ruta_salida}")


if __name__ == "__main__":
    ejecutar_test_consistencia()
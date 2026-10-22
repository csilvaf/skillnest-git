import os
import re
import json
import requests
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env en la raíz
load_dotenv()


def armar_peticion(
    pregunta: str,
    system_instruction: str = "Eres un asistente técnico experto.",
    response_schema: dict = None
) -> tuple[str, dict]:

    # Validación defensiva de tipo (evita AttributeError si se pasa una lista como [1, 2])
    if not isinstance(pregunta, str):
        raise ValueError("La pregunta debe ser una cadena de texto.")

    # Validación de contenido vacío o puros espacios en blanco
    if not pregunta.strip():
        raise ValueError("La pregunta no puede estar vacía.")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("No se encontró GEMINI_API_KEY en las variables de entorno.")

    modelo = "gemini-3.5-flash-lite"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"

    body = {
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {"parts": [{"text": pregunta}]}
        ]
    }

    if response_schema is not None:
        body["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }

    return url, body


def enviar_peticion(url: str, body: dict) -> dict:
    try:
        respuesta = requests.post(url, json=body)
    except requests.exceptions.ConnectionError:
        raise RuntimeError("No se pudo conectar con el servicio. Intenta de nuevo en unos segundos.")

    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llegó en el formato esperado.")


def extraer_texto(datos: dict) -> str:
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError(f"La respuesta no trae el texto generado en el lugar esperado: {datos}")


def parsear_respuesta_json(texto: str) -> dict:

    texto_limpio = texto.strip()
    texto_limpio = re.sub(r"^```json\s*", "", texto_limpio)
    texto_limpio = re.sub(r"^```\s*", "", texto_limpio)
    texto_limpio = re.sub(r"\s*```$", "", texto_limpio)
    texto_limpio = texto_limpio.strip()

    try:
        datos = json.loads(texto_limpio)
    except json.JSONDecodeError:
        raise ValueError("La respuesta del modelo no es un JSON válido.")

    return datos


def obtener_dato_de_prueba(
    pregunta: str,
    system_instruction: str = "Eres un asistente técnico conciso.",
    response_schema: dict = None
):

    url, body = armar_peticion(pregunta, system_instruction, response_schema)
    datos = enviar_peticion(url, body)
    texto = extraer_texto(datos)

    if response_schema:
        return parsear_respuesta_json(texto)
    return texto


if __name__ == "__main__":
    pregunta_prueba = "Si la conexion esta OK dime La conexion con Gemini esta OK"
    system_prompt = "Responde únicamente lo solicitado de forma exacta y breve."
    try:
        resultado = obtener_dato_de_prueba(pregunta_prueba, system_prompt)
        print(f"[RESPUESTA]: {resultado}")
    except (ValueError, RuntimeError) as error:
        print(f"No se pudo completar la operación: {error}")
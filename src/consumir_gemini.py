import os
import re
import json
import time
from typing import Callable, Any
import requests
from dotenv import load_dotenv

load_dotenv()


def armar_peticion(
    pregunta: str,
    system_instruction: str = "Eres un asistente técnico experto.",
    response_schema: dict = None
) -> tuple[str, dict]:

    if not isinstance(pregunta, str):
        raise ValueError("La pregunta debe ser una cadena de texto.")

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
        respuesta = requests.post(url, json=body, timeout=10)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        raise TimeoutError("No se pudo contactar al proveedor. Puede ser momentáneo.")
    
    if respuesta.status_code in (401, 403):
        raise ValueError("Credencial inválida o sin permiso. Revisa tu GEMINI_API_KEY.")
    if respuesta.status_code == 429 or respuesta.status_code >= 500:
        raise TimeoutError("Límite de peticiones excedido o error del servidor. Hay que esperar y reintentar.")

    try:
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llegó en el formato esperado.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Error HTTP no contemplado: {e}")


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


def con_reintento(funcion: Callable[[], Any], intentos: int = 3, espera_segundos: int = 2) -> Any:
    for intento in range(1, intentos + 1):
        try:
            return funcion()
        except TimeoutError:
            if intento == intentos:
                # Si es el último intento, se convierte en RuntimeError para el cliente
                raise RuntimeError("El servicio no respondió tras varios intentos. Intenta más tarde.")
            print(f"Intento {intento} de {intentos} falló por límite de uso o red. Reintentando en {espera_segundos}s...")
            time.sleep(espera_segundos)


def obtener_dato_de_prueba(
    pregunta: str,
    system_instruction: str = "Eres un asistente técnico conciso.",
    response_schema: dict = None
):
    url, body = armar_peticion(pregunta, system_instruction, response_schema)
    
    datos = con_reintento(lambda: enviar_peticion(url, body))
    
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
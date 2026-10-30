import os
import re
import json
import time
import random
from typing import Callable, Any
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-3.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
)
headers = {"Content-Type": "application/json"}

COSTO_POR_1000_TOKENS = 0.002
costo_total_sesion = 0.0


def calcular_costo_peticion(
    datos: dict,
    precio_entrada: float = 0.00000010,
    precio_salida: float = 0.00000040
) -> float:

    uso = datos.get("usageMetadata", {})
    tokens_entrada = uso.get("promptTokenCount", 0)
    tokens_salida = uso.get("candidatesTokenCount", 0)
    costo_entrada = tokens_entrada * precio_entrada
    costo_salida = tokens_salida * precio_salida
    return costo_entrada + costo_salida


def registrar_costo(respuesta: dict) -> float:

    global costo_total_sesion
    uso = respuesta.get("usageMetadata", {})
    total_tokens = uso.get("totalTokenCount", 0)
    costo_estimado = (total_tokens / 1000) * COSTO_POR_1000_TOKENS
    costo_total_sesion += costo_estimado
    print(
        f"Operación: {total_tokens} tokens, "
        f"costo estimado: ${costo_estimado:.5f} "
        f"(acumulado: ${costo_total_sesion:.5f})"
    )
    return costo_estimado


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

    # Si system_instruction viene vacío, enviamos un texto base seguro para no romper la API
    instruccion = system_instruction if system_instruction else "Eres un asistente técnico conciso."

    body = {
        "systemInstruction": {
            "parts": [{"text": instruccion}]
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


def enviar_peticion(url_o_cuerpo: str | dict, body: dict = None) -> dict:

    if body is None and isinstance(url_o_cuerpo, dict):
        url_destino = URL
        cuerpo_json = url_o_cuerpo
    else:
        url_destino = url_o_cuerpo
        cuerpo_json = body

    try:
        respuesta = requests.post(url_destino, json=cuerpo_json, headers=headers, timeout=10)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        raise TimeoutError("No se pudo contactar al proveedor. Puede ser momentáneo.")

    if respuesta.status_code in (401, 403):
        raise ValueError("Credencial inválida o sin permiso. Revisa tu GEMINI_API_KEY.")

    if respuesta.status_code == 429:
        headers_resp = getattr(respuesta, "headers", {})
        segundos = headers_resp.get("Retry-After") if isinstance(headers_resp, dict) else None
        if segundos:
            raise TimeoutError(f"Se ha alcanzado el límite de peticiones. Intenta más tarde en {segundos} segundos.")
        raise TimeoutError("El proveedor no pudo procesar la petición. Hay que esperar y reintentar.")

    if respuesta.status_code >= 500:
        raise TimeoutError("Error temporal del servidor del proveedor. Hay que esperar y reintentar.")

    try:
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llegó en el formato esperado.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Error HTTP no contemplado: {e}")


def con_reintento(
    funcion: Callable[[], Any],
    intentos: int = 3,
    espera_base: float = 2,
    espera_maxima: float = 30,
) -> Any:

    for intento in range(1, intentos + 1):
        try:
            return funcion()
        except TimeoutError:
            if intento == intentos:
                raise
            espera = min(espera_base * (2 ** (intento - 1)), espera_maxima)
            espera_con_jitter = espera + random.uniform(0, espera * 0.1)
            print(f"Intento {intento} de {intentos} falló. Reintentando en {espera_con_jitter:.1f}s...")
            time.sleep(espera_con_jitter)


def extraer_texto(datos: dict) -> str:
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError(f"La respuesta no trae el texto generado en el lugar esperado: {datos}")


def parsear_respuesta_json(texto: str) -> dict:
    texto_limpio = texto.strip()
    texto_limpio = re.sub(r"^```(?:json)?\s*", "", texto_limpio)
    texto_limpio = re.sub(r"\s*```$", "", texto_limpio)
    texto_limpio = texto_limpio.strip()

    try:
        datos = json.loads(texto_limpio)
    except json.JSONDecodeError:
        raise ValueError("La respuesta del modelo no es un JSON válido.")

    return datos


def consultar_modelo(
    pregunta: str,
    system_instruction: str = "Eres un asistente técnico conciso.",
    response_schema: dict = None
):

    url, body = armar_peticion(pregunta, system_instruction, response_schema)
    try:
        respuesta = con_reintento(lambda: enviar_peticion(url, body))
    except TimeoutError:
        raise RuntimeError("El servicio no respondió tras varios intentos. Intenta más tarde.")

    # El costo se registra únicamente cuando la petición tuvo éxito
    registrar_costo(respuesta)
    texto = extraer_texto(respuesta)

    if response_schema:
        return parsear_respuesta_json(texto)
    return texto


def obtener_dato_de_prueba(
    pregunta: str,
    system_instruction: str = "Eres un asistente técnico conciso.",
    response_schema: dict = None
):
    return consultar_modelo(pregunta, system_instruction, response_schema)


if __name__ == "__main__":
    print("--- Prueba individual del cliente modular ---")
    try:
        respuesta = consultar_modelo("¿Cuál es la capital de Chile? Responde en una oración corta.")
        print(f"Respuesta: {respuesta.strip()}")
        print(f"Costo acumulado de la sesión: ${costo_total_sesion:.5f}")
    except (ValueError, RuntimeError) as error:
        print(f"No se pudo completar la operación: {error}")
import os
import time
import random
from typing import Callable, Any
import requests
from dotenv import load_dotenv
from src.consumir_gemini import (
    armar_peticion,
    extraer_texto,
    parsear_respuesta_json,
    calcular_costo_peticion,
)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-3.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
)
headers = {"Content-Type": "application/json"}

COSTO_POR_1000_TOKENS = 0.002
costo_total_sesion = 0.0


def enviar_peticion(url_o_cuerpo: str | dict, body: dict = None) -> dict:
    """Envía la solicitud HTTP POST y clasifica los códigos HTTP en excepciones de negocio."""
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

    if respuesta.status_code == 429 or respuesta.status_code >= 500:
        raise TimeoutError("El proveedor no pudo procesar la petición. Hay que esperar y reintentar.")

    respuesta.raise_for_status()
    return respuesta.json()


def con_reintento(
    funcion: Callable[[], Any],
    intentos: int = 3,
    espera_base: float = 2,
    espera_maxima: float = 30,
) -> Any:
    """Ejecuta una función y reintenta con backoff exponencial, techo y jitter ante TimeoutError."""
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


def registrar_costo(respuesta: dict) -> float:
    """Calcula el costo de la operación exitosa y lo acumula en costo_total_sesion."""
    global costo_total_sesion
    uso = respuesta.get("usageMetadata", {})
    total_tokens = uso.get("totalTokenCount", 0)
    costo_estimado = (total_tokens / 1000) * COSTO_POR_1000_TOKENS
    costo_total_sesion += costo_estimado
    return costo_estimado


def consultar_modelo(
    pregunta: str,
    system_instruction: str = "Eres un asistente técnico conciso.",
    response_schema: dict = None
):
    """Interfaz pública del cliente modular."""
    url, body = armar_peticion(pregunta, system_instruction, response_schema)
    try:
        respuesta = con_reintento(lambda: enviar_peticion(url, body))
    except TimeoutError:
        raise RuntimeError("El servicio no respondió tras varios intentos. Intenta más tarde.")

    registrar_costo(respuesta)
    texto = extraer_texto(respuesta)

    if response_schema:
        return parsear_respuesta_json(texto)
    return texto
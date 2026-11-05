"""
Enrutamiento condicional y Manejo de Errores (Bloques 19 y 20)
Dominio: Taller de Servicio Técnico de Consolas y PC.
"""
import os
import logging
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch, RunnablePassthrough, RunnableLambda

load_dotenv()

# Configuración de logging para registrar errores de forma silenciosa
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =================================================================
# 1. Definición de Plantillas y Cadenas de Destino
# =================================================================

plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica el siguiente mensaje de un cliente del taller técnico en una sola "
    "palabra: pregunta, queja o sugerencia. Responde solo con esa palabra.\n\n"
    "Mensaje: {mensaje}"
)

cadena_pregunta = (
    PromptTemplate.from_template(
        "Eres un técnico experto. Responde a esta pregunta técnica sobre hardware, "
        "PC o consolas con precisión y de forma directa:\n\n{mensaje}"
    )
    | ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0.1)
    | StrOutputParser()
)

cadena_queja = (
    PromptTemplate.from_template(
        "Eres el encargado de atención al cliente del taller. Responde a esta queja "
        "por una reparación o servicio con mucha empatía, reconociendo el problema "
        "antes de ofrecer una solución de revisión de garantía:\n\n{mensaje}"
    )
    | ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0.3)
    | StrOutputParser()
)

cadena_sugerencia = (
    PromptTemplate.from_template(
        "Eres el administrador del taller. Agradece amablemente esta sugerencia del "
        "cliente y explica que se evaluará para mejorar nuestro servicio:\n\n{mensaje}"
    )
    | ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0.3)
    | StrOutputParser()
)

respuesta_generica = RunnableLambda(
    lambda x: "Gracias por tu mensaje. Un miembro de nuestro equipo técnico te va a responder pronto."
)


# =================================================================
# 2. Funciones Constructoras (Desacopladas para Testing y Seguridad)
# =================================================================

def construir_paso_clasificacion(modelo):
    return (
        plantilla_clasificacion
        | modelo
        | StrOutputParser()
        | (lambda texto: texto.strip().lower())
    )

def construir_cadena_queja_segura(cadena_principal):
    """Aplica el Plan B (fallback) si la cadena principal falla."""
    return cadena_principal.with_fallbacks([respuesta_generica])

def construir_cadena_con_enrutamiento(
    paso_clasificacion,
    cadena_queja=None,
    cadena_sugerencia=None,
    cadena_pregunta=None,
):
    cadena_queja = cadena_queja or RunnablePassthrough()
    cadena_sugerencia = cadena_sugerencia or RunnablePassthrough()
    cadena_pregunta = cadena_pregunta or RunnablePassthrough()
    
    bifurcacion = RunnableBranch(
        (lambda x: x["categoria"] == "queja", cadena_queja),
        (lambda x: x["categoria"] == "sugerencia", cadena_sugerencia),
        cadena_pregunta,
    )
    return RunnablePassthrough.assign(categoria=paso_clasificacion) | bifurcacion

def procesar_mensaje_seguro(cadena, mensaje):
    """Red de seguridad global: intenta ejecutar la cadena y atrapa cualquier excepción general."""
    try:
        return cadena.invoke({"mensaje": mensaje})
    except Exception as error:
        logger.error(f"Error procesando mensaje: {error}")
        return "No pudimos procesar tu mensaje en este momento. Intenta de nuevo más tarde."


# =================================================================
# 3. Ejecución de Prueba en Vivo
# =================================================================

if __name__ == "__main__":
    modelo_base = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0.0)
    
    # Ensamblaje con seguridad inyectada
    paso_clasif = construir_paso_clasificacion(modelo_base)
    cadena_queja_protegida = construir_cadena_queja_segura(cadena_queja)
    
    cadena_enrutada = construir_cadena_con_enrutamiento(
        paso_clasificacion=paso_clasif,
        cadena_queja=cadena_queja_protegida,
        cadena_sugerencia=cadena_sugerencia,
        cadena_pregunta=cadena_pregunta,
    )

    mensajes_prueba = [
        "¿Cuánta memoria RAM soporta como máximo una placa madre B550?",
        "Llevé mi PS5 a limpieza de metal líquido y ahora se apaga sola, ¡pésimo servicio!"
    ]

    print("=" * 70)
    print(" PRUEBA DE ENRUTAMIENTO CON MANEJO DE ERRORES (BLOQUE 20)")
    print("=" * 70)

    for msg in mensajes_prueba:
        print(f"\n[Mensaje Cliente]: {msg}")
        # En vez de usar .invoke() directo, usamos nuestra red de seguridad
        resultado = procesar_mensaje_seguro(cadena_enrutada, msg)
        print(f"[Respuesta Generada]: {resultado}")
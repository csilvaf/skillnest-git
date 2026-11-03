"""
Enrutamiento condicional según el tipo de entrada (Bloque 19)
Dominio: Taller de Servicio Técnico de Consolas y PC.
"""
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch, RunnablePassthrough

load_dotenv()

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


# =================================================================
# 2. Funciones Constructoras (Desacopladas para Testing)
# =================================================================

def construir_paso_clasificacion(modelo):
    """Crea el paso que clasifica y normaliza la salida a minúsculas sin espacios."""
    return (
        plantilla_clasificacion
        | modelo
        | StrOutputParser()
        | (lambda texto: texto.strip().lower())
    )

def construir_cadena_con_enrutamiento(
    paso_clasificacion,
    cadena_queja=None,
    cadena_sugerencia=None,
    cadena_pregunta=None,
):
    """Construye la bifurcación conectando la clasificación con las rutas."""
    cadena_queja = cadena_queja or RunnablePassthrough()
    cadena_sugerencia = cadena_sugerencia or RunnablePassthrough()
    cadena_pregunta = cadena_pregunta or RunnablePassthrough()
    
    bifurcacion = RunnableBranch(
        (lambda x: x["categoria"] == "queja", cadena_queja),
        (lambda x: x["categoria"] == "sugerencia", cadena_sugerencia),
        cadena_pregunta, # Ruta por defecto si no es queja ni sugerencia
    )
    
    return (
        RunnablePassthrough.assign(categoria=paso_clasificacion)
        | bifurcacion
    )


# =================================================================
# 3. Ejecución de Prueba en Vivo
# =================================================================

if __name__ == "__main__":
    modelo_base = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0.0)
    
    # Armamos la cadena completa inyectando nuestras piezas
    paso_clasif = construir_paso_clasificacion(modelo_base)
    cadena_enrutada = construir_cadena_con_enrutamiento(
        paso_clasificacion=paso_clasif,
        cadena_queja=cadena_queja,
        cadena_sugerencia=cadena_sugerencia,
        cadena_pregunta=cadena_pregunta,
    )

    mensajes_prueba = [
        "¿Cuánta memoria RAM soporta como máximo una placa madre B550?",
        "Llevé mi PS5 a limpieza de metal líquido hace una semana y ahora se apaga sola, ¡pésimo servicio!",
        "Sería bueno que implementen un sistema web para ver el estado de mi reparación con un código."
    ]

    print("=" * 70)
    print(" PRUEBA DE ENRUTAMIENTO CONDICIONAL (TALLER TÉCNICO)")
    print("=" * 70)

    for msg in mensajes_prueba:
        print(f"\n[Mensaje Cliente]: {msg}")
        resultado = cadena_enrutada.invoke({"mensaje": msg})
        print(f"[Respuesta Generada]: {resultado}")
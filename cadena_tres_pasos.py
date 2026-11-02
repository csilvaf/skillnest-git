"""
Primer chain de tres pasos con LangChain (Bloque 18)
Dominio: Taller de Servicio Técnico de Consolas y PC.
"""
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


def construir_cadena(modelo):
    """
    Construye y devuelve una chain de tres pasos encadenados usando el operador '|'.
    Recibe el modelo como parámetro para permitir la inyección de mocks en pruebas unitarias.
    """
    # -------------------------------------------------------------
    # Paso 1: Extraer síntomas y componentes sospechosos
    # -------------------------------------------------------------
    plantilla_extraccion = PromptTemplate.from_template(
        "Eres un técnico de recepción. Lee el reporte de falla de un equipo y extrae "
        "los 3 puntos técnicos clave (síntomas, posible componente afectado y etapa), "
        "uno por línea, sin desarrollarlos:\n\n{reporte_falla}"
    )
    paso_extraccion = plantilla_extraccion | modelo | StrOutputParser()

    # -------------------------------------------------------------
    # Paso 2: Diagnóstico preliminar en lenguaje claro para el cliente
    # -------------------------------------------------------------
    plantilla_diagnostico = PromptTemplate.from_template(
        "A partir de estos puntos técnicos clave:\n{puntos_clave}\n\n"
        "Redacta una explicación clara y entendible para el dueño del equipo, "
        "en un solo párrafo conciso, sin tecnicismos innecesarios."
    )
    paso_diagnostico = plantilla_diagnostico | modelo | StrOutputParser()

    # -------------------------------------------------------------
    # Paso 3: Formatear como lista de viñetas Markdown para la orden de taller
    # -------------------------------------------------------------
    plantilla_formato = PromptTemplate.from_template(
        "Convierte la siguiente explicación en una lista de viñetas Markdown de máximo "
        "3 líneas para la orden interna de trabajo del taller, sin introducción:\n\n{explicacion}"
    )
    paso_formato = plantilla_formato | modelo | StrOutputParser()

    # -------------------------------------------------------------
    # Conexión de los tres pasos con funciones intermedias (lambdas)
    # -------------------------------------------------------------
    cadena_completa = (
        paso_extraccion
        | (lambda puntos: {"puntos_clave": puntos})
        | paso_diagnostico
        | (lambda texto: {"explicacion": texto})
        | paso_formato
    )

    return cadena_completa


if __name__ == "__main__":
    load_dotenv()
    
    # Inicialización del modelo Gemini Flash con baja temperatura para consistencia
    modelo = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        temperature=0.1
    )

    cadena = construir_cadena(modelo)

    reporte_ejemplo = (
        "PlayStation 5 enciende, la luz pasa de azul a blanca, pero a los 2 minutos "
        "el ventilador se acelera al máximo, emite 3 pitidos y se apaga de golpe. "
        "La carcasa se siente sumamente caliente cerca de los disipadores."
    )

    print("=" * 70)
    print(" EJECUTANDO CHAIN DE 3 PASOS EN TALLER TÉCNICO (BLOQUE 18)")
    print("=" * 70)
    print(f"\n[Entrada - Reporte]:\n{reporte_ejemplo}\n")

    resultado = cadena.invoke({"reporte_falla": reporte_ejemplo})

    print("[Salida Final - Viñetas Markdown Generadas]:")
    print(resultado)
    print("=" * 70)
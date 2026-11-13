"""
Recuperación semántica y prompt dinámico con fuente citada (Bloque 26)
Dominio: Taller de Servicio Técnico de Consolas y PC.
"""
import os
import re
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma

load_dotenv()

if not os.environ.get("GEMINI_API_KEY"):
    raise SystemExit('Falta GEMINI_API_KEY. Defínela en tu archivo ".env" y vuelve a ejecutar.')

PROMPT_TEMPLATE = """Responde la pregunta usando SOLO el contexto de abajo. Cita la
fuente de cada afirmacion con su numero entre corchetes, como [1]. Si el contexto no
alcanza para responder, dilo explicitamente en vez de inventar.

Contexto:
{contexto}

Pregunta: {pregunta}
Respuesta:"""


# =================================================================
# 1. Funciones Core del Bloque 26: formatear_contexto y construir_prompt
# =================================================================

def formatear_contexto(chunks_recuperados: list[Document]) -> tuple[str, dict[int, str]]:
    """
    Arma un bloque de contexto numerado para el prompt, y un mapa
    {numero: fuente} para reconstruir la cita después.
    """
    lineas = []
    citas = {}
    for i, doc in enumerate(chunks_recuperados, start=1):
        fuente = doc.metadata.get("fuente", "desconocida")
        lineas.append(f"[{i}] {doc.page_content}")
        citas[i] = fuente
    contexto = "\n\n".join(lineas)
    return contexto, citas


def construir_prompt(
    pregunta: str,
    persist_directory: str = "vectorstore/",
    k: int = 3,
) -> tuple[str, dict[int, str]]:
    """
    Recupera los k chunks más relevantes para la pregunta (sin reindexar) y arma
    el prompt dinámico con contexto numerado, listo para pasarle al modelo.
    """
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    chunks_recuperados = retriever.invoke(pregunta)

    contexto, citas = formatear_contexto(chunks_recuperados)
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)
    return prompt, citas


# =================================================================
# 2. Generación de Respuesta y Verificación de Citas Reales
# =================================================================

def extraer_texto_modelo(respuesta_ai) -> str:
    """Normaliza el contenido devuelto por Gemini a texto plano."""
    contenido = respuesta_ai.content
    if isinstance(contenido, list):
        return "".join(
            bloque["text"]
            for bloque in contenido
            if isinstance(bloque, dict) and bloque.get("type") == "text"
        )
    return str(contenido)


def responder_con_rag(
    pregunta: str,
    persist_directory: str = "vectorstore/",
    k: int = 3,
) -> dict:
    """Construye el prompt dinámico, invoca al modelo y reconstruye las fuentes citadas."""
    prompt, citas = construir_prompt(pregunta, persist_directory=persist_directory, k=k)
    modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
    respuesta_raw = modelo.invoke(prompt)
    respuesta_texto = extraer_texto_modelo(respuesta_raw)

    # Extraer números entre corchetes [1], [2], etc. con regex y validar contra citas
    indices_citados = [int(num) for num in re.findall(r"\[(\d+)\]", respuesta_texto)]
    fuentes_verificadas = {
        idx: citas.get(idx, "Cita inválida / no encontrada")
        for idx in indices_citados
    }

    return {
        "prompt": prompt,
        "citas": citas,
        "respuesta": respuesta_texto,
        "fuentes_verificadas": fuentes_verificadas,
    }


# =================================================================
# 3. Ejecución de los 3 Escenarios de Prueba del Bloque 26
# =================================================================

if __name__ == "__main__":
    print("=" * 70)
    print(" PASO 0: VERIFICACIÓN DE FORMATO DEL DICCIONARIO CITAS (DEMO LOCAL)")
    print("=" * 70)
    chunks_ejemplo = [
        Document(
            page_content="Falla típica PlayStation 5: luz azul fija y se apaga",
            metadata={"fuente": "manual_fallas_ps5.md"},
        ),
        Document(
            page_content="Nintendo Switch que no carga: revisar chip M92T36",
            metadata={"fuente": "guia_microelectronica_switch.md"},
        ),
    ]
    _, citas_ejemplo = formatear_contexto(chunks_ejemplo)
    print("Diccionario citas de ejemplo:", citas_ejemplo)

    # Escenario 1A: Primera pregunta sobre el corpus del taller
    print("\n" + "=" * 70)
    print(" ESCENARIO 1A: PREGUNTA 1 SOBRE EL CORPUS (MANTENIMIENTO PS5)")
    print("=" * 70)
    pregunta_1 = "¿Qué compuesto lleva el procesador de la PS5 y por qué no debo usar pasta térmica normal?"
    res_1 = responder_con_rag(pregunta_1, persist_directory="vectorstore/", k=3)
    print(res_1["prompt"])
    print("\nMapa de citas disponible:", res_1["citas"])
    print("Respuesta del modelo:", res_1["respuesta"])
    print("Verificación de la cita [1] en diccionario:", res_1["citas"].get(1))

    # Escenario 1B: Segunda pregunta distinta (confirmando que cambia el contexto recuperado)
    print("\n" + "=" * 70)
    print(" ESCENARIO 1B: PREGUNTA 2 DISTINTA (NINTENDO SWITCH NO CARGA)")
    print("=" * 70)
    pregunta_2 = "Llegó una consola portátil de Nintendo que no sube batería tras usar un dock alternativo, ¿qué chips reviso?"
    res_2 = responder_con_rag(pregunta_2, persist_directory="vectorstore/", k=3)
    print(res_2["prompt"])
    print("\nMapa de citas disponible:", res_2["citas"])
    print("Respuesta del modelo:", res_2["respuesta"])
    print("Fuentes citadas reconstruidas:", res_2["fuentes_verificadas"])

    # Escenario 2: Pregunta fuera del corpus (debe decir explícitamente que no alcanza)
    print("\n" + "=" * 70)
    print(" ESCENARIO 2: PREGUNTA QUE EL CORPUS NO PUEDE RESPONDER")
    print("=" * 70)
    pregunta_fuera = "¿Cuál es el procedimiento para calibrar los lentes de unas gafas Apple Vision Pro?"
    res_3 = responder_con_rag(pregunta_fuera, persist_directory="vectorstore/", k=3)
    print(res_3["prompt"])
    print("\nMapa de citas disponible:", res_3["citas"])
    print("Respuesta del modelo:", res_3["respuesta"])
    print("=" * 70)
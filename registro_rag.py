"""
Instrumentación de latencia por etapa y costo en tokens del flujo RAG (Bloque 28)
Dominio: Taller de Servicio Técnico de Consolas y PC.
"""
import os
import time
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

if not os.environ.get("GEMINI_API_KEY"):
    raise SystemExit('Falta GEMINI_API_KEY. Defínela en tu archivo ".env" y vuelve a ejecutar.')

PROMPT_TEMPLATE = """Responde la pregunta usando SOLO el contexto de abajo. Cita la \
fuente de cada afirmacion con su numero entre corchetes, como [1]. Si el contexto no \
alcanza para responder, dilo explicitamente en vez de inventar.

Contexto:
{contexto}

Pregunta: {pregunta}
Respuesta:"""


def formatear_contexto(chunks_recuperados: list) -> str:
    """Arma el bloque de contexto numerado para el prompt."""
    lineas = []
    for i, doc in enumerate(chunks_recuperados, start=1):
        lineas.append(f"[{i}] {doc.page_content}")
    return "\n\n".join(lineas)


@contextmanager
def medir(tiempos: dict, etapa: str):
    """Context manager que mide en segundos de alta precisión la duración de una etapa."""
    inicio = time.perf_counter()
    yield
    tiempos[etapa] = time.perf_counter() - inicio


def registrar_consulta(
    pregunta: str,
    persist_directory: str = "vectorstore/",
    k: int = 3,
) -> dict:
    """
    Corre una consulta RAG real midiendo tiempo por etapa (embed_y_busqueda vs generacion)
    y extrayendo los tokens reales consumidos desde respuesta.usage_metadata.
    """
    tiempos = {}
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    chat_model = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

    with medir(tiempos, "embed_y_busqueda"):
        vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        chunks = retriever.invoke(pregunta)

    contexto = formatear_contexto(chunks)
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)

    with medir(tiempos, "generacion"):
        respuesta = chat_model.invoke(prompt)

    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pregunta": pregunta,
        "k": k,
        "tiempos_ms": {etapa: round(s * 1000, 2) for etapa, s in tiempos.items()},
        "tiempo_total_ms": round(sum(tiempos.values()) * 1000, 2),
        "tokens": dict(respuesta.usage_metadata) if respuesta.usage_metadata else None,
    }
    return registro


def guardar_registro_jsonl(
    registro: dict,
    archivo_salida: str = "registros_latencia_costo.jsonl",
) -> None:
    """Agrega un registro como una línea JSON en registros_latencia_costo.jsonl."""
    with open(archivo_salida, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    ARCHIVO_JSONL = "registros_latencia_costo.jsonl"

    # Limpiamos corridas de prueba previas para dejar un registro limpio y representativo
    if os.path.exists(ARCHIVO_JSONL):
        os.remove(ARCHIVO_JSONL)

    print("=" * 70)
    print(" PASO 1: REGISTRANDO 3 CONSULTAS DISTINTAS DEL CONJUNTO (k=3)")
    print("=" * 70)

    preguntas_evaluacion = [
        "¿Qué compuesto lleva el procesador de la PS5 y por qué no debo usar pasta térmica normal?",
        "Llegó una consola portátil de Nintendo que no sube batería tras usar un dock alternativo, ¿qué chips reviso?",
        "¿Qué indican 1 pitido largo y 2 cortos en la placa madre de un PC?",
    ]

    for pregunta in preguntas_evaluacion:
        reg = registrar_consulta(pregunta, persist_directory="vectorstore/", k=3)
        guardar_registro_jsonl(reg, ARCHIVO_JSONL)
        print(json.dumps(reg, indent=2, ensure_ascii=False))

    print("\n" + "=" * 70)
    print(" PASO 2: MISMA PREGUNTA CON k=3 Y k=6 (IMPACTO EN INPUT_TOKENS)")
    print("=" * 70)

    pregunta_comparativa = "¿Cuál es el protocolo de respaldo antes de formatear un computador de cliente?"

    reg_k3 = registrar_consulta(pregunta_comparativa, persist_directory="vectorstore/", k=3)
    guardar_registro_jsonl(reg_k3, ARCHIVO_JSONL)

    reg_k6 = registrar_consulta(pregunta_comparativa, persist_directory="vectorstore/", k=6)
    guardar_registro_jsonl(reg_k6, ARCHIVO_JSONL)

    tokens_k3 = reg_k3["tokens"]["input_tokens"] if reg_k3["tokens"] else None
    tokens_k6 = reg_k6["tokens"]["input_tokens"] if reg_k6["tokens"] else None
    print(f"k=3 -> input_tokens: {tokens_k3} (tiempo_total_ms: {reg_k3['tiempo_total_ms']} ms)")
    print(f"k=6 -> input_tokens: {tokens_k6} (tiempo_total_ms: {reg_k6['tiempo_total_ms']} ms)")

    print("\n" + "=" * 70)
    print(" PASO 3: CONFIRMANDO EL ARCHIVO DE REGISTROS (JSONL)")
    print("=" * 70)
    with open(ARCHIVO_JSONL, encoding="utf-8") as f:
        lineas = [json.loads(linea) for linea in f if linea.strip()]
    print(f"{ARCHIVO_JSONL} tiene {len(lineas)} líneas (una por corrida):")
    for r in lineas:
        t_in = r["tokens"]["input_tokens"] if r["tokens"] else None
        print(
            f"  k={r['k']} | input_tokens={t_in} | "
            f"embed_y_busqueda={r['tiempos_ms']['embed_y_busqueda']} ms | "
            f"generacion={r['tiempos_ms']['generacion']} ms | "
            f"total={r['tiempo_total_ms']} ms | {r['pregunta'][:40]}..."
        )
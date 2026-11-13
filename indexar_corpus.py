"""
Receta modular de Indexación y Persistencia en ChromaDB con Metadata e IDs (Bloques 24, 25 y 26)
Dominio: Taller de Servicio Técnico de Consolas y PC.
"""
import os
import time
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

if not os.environ.get("GEMINI_API_KEY"):
    raise SystemExit('Falta GEMINI_API_KEY. Defínela en tu archivo ".env" y vuelve a ejecutar.')

PERSIST_DIR = "vectorstore/"
MODELO_EMBEDDINGS = "models/gemini-embedding-001"


# =================================================================
# 1. Corpus del Taller Técnico, Metadatas (Fuentes) e IDs
# =================================================================

CORPUS_TALLER = [
    "Falla típica PlayStation 5: Si la consola enciende, muestra luz azul fija y se apaga a los dos segundos sin dar video, suele ser falla en la fuente de poder o un corto en la línea de 12v de la placa principal.",
    "Nintendo Switch que no carga ni enciende: Revisar inmediatamente el chip M92T36 o BQ24193. Ambos integrados controlan la carga por USB-C y son propensos a quemarse por el uso de docks genéricos.",
    "Pitidos de placa madre PC: 1 pitido largo y 2 cortos indica error en la tarjeta de video (GPU) o la memoria VRAM. Verificar que la tarjeta esté bien insertada en el puerto PCIe y conectada a la fuente.",
    "Formateo y respaldo seguro: Antes de formatear cualquier PC de cliente e instalar Windows limpio, se debe crear una carpeta cifrada en el servidor local con la clave única del ticket y respaldar la carpeta Usuarios completa.",
    "Mantenimiento térmico: A diferencia de la PS4 que usa pasta térmica convencional, el procesador (APU) de la PS5 viene de fábrica con metal líquido. Nunca aplicar pasta normal en la PS5 porque causará sobrecalentamiento instantáneo.",
]

# Nombres de archivo reconocibles del proyecto para trazabilidad de citas (Bloque 26)
METADATAS_TALLER = [
    {"fuente": "manual_fallas_ps5.md"},
    {"fuente": "guia_microelectronica_switch.md"},
    {"fuente": "codigos_post_bios_pc.md"},
    {"fuente": "protocolo_respaldo_windows.md"},
    {"fuente": "manual_mantenimiento_termico.md"},
]

# IDs predecibles requeridos para etiquetar la evaluación en el Bloque 27
IDS_TALLER = [f"doc{i}" for i in range(len(CORPUS_TALLER))]


# =================================================================
# 2. Utilidades de Validación Local y Reintentos (Bloque 25)
# =================================================================

def validar_integridad_chunks(chunks: list, corpus: list[str]) -> dict:
    """Verifica localmente que no existan chunks vacíos ni duplicados."""
    vacios = [i for i, c in enumerate(chunks) if not c.page_content.strip()]
    textos = [c.page_content for c in chunks]
    hay_duplicados = len(textos) != len(set(textos))
    total_chars_chunks = sum(len(c.page_content) for c in chunks)
    total_chars_corpus = sum(len(d) for d in corpus)

    return {
        "vacios": vacios,
        "hay_duplicados": hay_duplicados,
        "total_chars_chunks": total_chars_chunks,
        "total_chars_corpus": total_chars_corpus,
        "es_valido": (len(vacios) == 0) and (not hay_duplicados),
    }


def con_reintentos(operacion, max_intentos: int = 4, espera_inicial: int = 5):
    """Ejecuta una operación aplicando backoff exponencial ante error 429."""
    espera = espera_inicial
    for intento in range(1, max_intentos + 1):
        try:
            return operacion()
        except Exception as error:
            mensaje = str(error)
            es_limite = "429" in mensaje or "RESOURCE_EXHAUSTED" in mensaje
            if not es_limite or intento == max_intentos:
                raise
            print(
                f"Límite de peticiones alcanzado. Reintento {intento} "
                f"de {max_intentos - 1} en {espera} s..."
            )
            time.sleep(espera)
            espera *= 2


# =================================================================
# 3. Funciones Reutilizables: indexar_corpus y cargar_vectorstore
# =================================================================

def indexar_corpus(
    corpus: list[str] = CORPUS_TALLER,
    persist_directory: str = PERSIST_DIR,
    chunk_size: int = 250,
    chunk_overlap: int = 30,
    metadatas: list[dict] = METADATAS_TALLER,
    ids: list[str] = IDS_TALLER,
) -> Chroma:
    """Parte con metadata, valida, calcula embeddings y persiste en Chroma."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = splitter.create_documents(corpus, metadatas=metadatas)

    reporte = validar_integridad_chunks(chunks, corpus)
    if not reporte["es_valido"]:
        raise ValueError("Error de integridad en los chunks: existen vacíos o duplicados.")

    # Si algún documento se partió en más chunks, ajustamos los IDs a la cantidad real
    if len(ids) != len(chunks):
        ids = [f"doc{i}" for i in range(len(chunks))]

    embeddings = GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS)

    vectorstore = con_reintentos(
        lambda: Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            ids=ids,
            persist_directory=persist_directory,
        )
    )
    print(f"Reindexados {len(chunks)} chunks en {persist_directory}, ahora con metadata e ids")
    return vectorstore


def cargar_vectorstore(persist_directory: str = PERSIST_DIR) -> Chroma:
    """Reconecta a un vector store ya indexado en disco, sin recalcular nada."""
    embeddings = GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS)
    return Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )


if __name__ == "__main__":
    indexar_corpus()
    vs = cargar_vectorstore()
    print("Total de chunks verificados en disco:", vs._collection.count())
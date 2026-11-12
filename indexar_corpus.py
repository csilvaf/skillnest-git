"""
Receta modular de Indexación y Persistencia en ChromaDB (Bloques 24 y 25)
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

PERSIST_DIR = os.path.abspath("vectorstore")
COLLECTION_NAME = "corpus_taller_tecnico"
MODELO_EMBEDDINGS = "models/gemini-embedding-001"


# =================================================================
# 1. Utilidades de Validación Local y Reintentos (Bloque 25)
# =================================================================

def validar_integridad_chunks(chunks: list, corpus: list[str]) -> dict:
    """
    Verifica localmente (sin gastar llamadas a la API) que ningún chunk haya
    quedado vacío, que no existan duplicados y reporta el conteo de caracteres.
    """
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
    """
    Ejecuta una operación de red (como la indexación de embeddings) aplicando
    backoff exponencial (5s, 10s, 20s) si aparece un error 429 RESOURCE_EXHAUSTED.
    """
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
# 2. Funciones Reutilizables: indexar_corpus y cargar_vectorstore
# =================================================================

def indexar_corpus(
    corpus: list[str],
    persist_directory: str = PERSIST_DIR,
    chunk_size: int = 250,
    chunk_overlap: int = 30,
    collection_name: str = COLLECTION_NAME,
) -> Chroma:
    """Parte, valida, calcula embeddings con reintentos y persiste un corpus en Chroma."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = splitter.create_documents(corpus)

    reporte = validar_integridad_chunks(chunks, corpus)
    print(f"chunks vacíos: {reporte['vacios']}")
    print(f"hay duplicados: {reporte['hay_duplicados']}")
    print(f"total de caracteres en los chunks: {reporte['total_chars_chunks']}")
    print(f"total de caracteres en el corpus original: {reporte['total_chars_corpus']}")

    if not reporte["es_valido"]:
        raise ValueError("Error de integridad en los chunks: existen vacíos o duplicados.")

    embeddings = GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS)

    # IDs explícitos predecibles para evitar duplicar chunks al re-ejecutar
    ids_explicitos = [f"{collection_name}_chunk_{i}" for i in range(len(chunks))]

    try:
        vectorstore = con_reintentos(
            lambda: Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                ids=ids_explicitos,
                collection_name=collection_name,
                persist_directory=persist_directory,
            )
        )
        print(f"Indexados {len(chunks)} chunks en {persist_directory}")
        return vectorstore
    except Exception as error:
        mensaje = str(error)
        if "API key" in mensaje or "401" in mensaje or "403" in mensaje:
            print('La API rechazó tu clave. Revisa el valor de GEMINI_API_KEY en tu ".env".')
        else:
            print("No se pudo indexar el corpus:", type(error).__name__)
        print("Detalle técnico:", mensaje)
        raise SystemExit(1)


def cargar_vectorstore(
    persist_directory: str = PERSIST_DIR,
    collection_name: str = COLLECTION_NAME,
) -> Chroma:
    """Reconecta a un vector store ya indexado en disco, sin recalcular embeddings."""
    embeddings = GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS)
    return Chroma(
        collection_name=collection_name,
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )


# =================================================================
# 3. Corpus del Taller Técnico y Ejecución de los 5 Pasos
# =================================================================

CORPUS_TALLER = [
    "Falla típica PlayStation 5: Si la consola enciende, muestra luz azul fija y se apaga a los dos segundos sin dar video, suele ser falla en la fuente de poder o un corto en la línea de 12v de la placa principal.",
    "Nintendo Switch que no carga ni enciende: Revisar inmediatamente el chip M92T36 o BQ24193. Ambos integrados controlan la carga por USB-C y son propensos a quemarse por el uso de docks genéricos.",
    "Pitidos de placa madre PC: 1 pitido largo y 2 cortos indica error en la tarjeta de video (GPU) o la memoria VRAM. Verificar que la tarjeta esté bien insertada en el puerto PCIe y conectada a la fuente.",
    "Formateo y respaldo seguro: Antes de formatear cualquier PC de cliente e instalar Windows limpio, se debe crear una carpeta cifrada en el servidor local con la clave única del ticket y respaldar la carpeta Usuarios completa.",
    "Mantenimiento térmico: A diferencia de la PS4 que usa pasta térmica convencional, el procesador (APU) de la PS5 viene de fábrica con metal líquido. Nunca aplicar pasta normal en la PS5 porque causará sobrecalentamiento instantáneo.",
]

if __name__ == "__main__":
    print("=" * 65)
    print(" EJECUTANDO RECETA DE 5 PASOS SOBRE CORPUS DEL TALLER (BLOQUE 25)")
    print("=" * 65)

    # Pasos 1 a 4: Reunir, partir, embebir y persistir
    indexar_corpus(CORPUS_TALLER, PERSIST_DIR, chunk_size=250, chunk_overlap=30)

    # Paso 5: Verificar persistencia reconectando sin recalcular
    vs_recargado = cargar_vectorstore(PERSIST_DIR)
    print("Ruta del índice:", PERSIST_DIR)
    print("Colección:", vs_recargado._collection.name)
    print("Chunks en disco:", vs_recargado._collection.count())
"""
Indexación de Corpus en ChromaDB (RAG - Bloque 24)
Dominio: Taller de Servicio Técnico de Consolas y PC.
"""
import os
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# 1. Cargar el entorno
load_dotenv()
if not os.environ.get("GEMINI_API_KEY"):
    raise SystemExit('Falta GEMINI_API_KEY. Defínela en tu archivo ".env" y vuelve a ejecutar.')

# 2. Definición de tu propio corpus técnico (Mínimo 5 documentos según pauta)
corpus_taller = [
    "Falla típica PlayStation 5: Si la consola enciende, muestra luz azul fija y se apaga a los dos segundos sin dar video, suele ser falla en la fuente de poder o un corto en la línea de 12v de la placa principal.",
    "Nintendo Switch que no carga ni enciende: Revisar inmediatamente el chip M92T36 o BQ24193. Ambos integrados controlan la carga por USB-C y son propensos a quemarse por el uso de docks genéricos.",
    "Pitidos de placa madre PC: 1 pitido largo y 2 cortos indica error en la tarjeta de video (GPU) o la memoria VRAM. Verificar que la tarjeta esté bien insertada en el puerto PCIe y conectada a la fuente.",
    "Formateo y respaldo seguro: Antes de formatear cualquier PC de cliente e instalar Windows limpio, se debe crear una carpeta cifrada en el servidor local con la clave única del ticket y respaldar la carpeta Usuarios completa.",
    "Mantenimiento térmico: A diferencia de la PS4 que usa pasta térmica convencional, el procesador (APU) de la PS5 viene de fábrica con metal líquido. Nunca aplicar pasta normal en la PS5 porque causará sobrecalentamiento instantáneo."
]

print("=== INICIANDO INDEXACIÓN DEL CORPUS DEL TALLER ===")

# 3. Chunking (Estrategia Recursiva)
splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)
chunks = splitter.create_documents(corpus_taller)
print(f"-> Corpus original: {len(corpus_taller)} documentos.")
print(f"-> Después del chunking: {len(chunks)} chunks.")

# 4. Cálculo de Embeddings Reales
try:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # 5. Persistencia en disco (Vector Store)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./vectorstore"
    )
    print(f"-> ¡Éxito! Indexados {len(chunks)} chunks en el directorio './vectorstore'.")

except Exception as error:
    mensaje = str(error)
    if "429" in mensaje or "RESOURCE_EXHAUSTED" in mensaje:
        print("-> Límite de peticiones alcanzado. Espera un minuto y vuelve a ejecutar.")
    else:
        print(f"-> Error inesperado al generar embeddings: {mensaje}")
    raise SystemExit(1)


# 6. Prueba de Reconexión: Verificando persistencia en disco
print("\n=== CONFIRMANDO PERSISTENCIA EN DISCO ===")
vectorstore_recargado = Chroma(
    persist_directory="./vectorstore",
    embedding_function=embeddings,
    collection_name="langchain" # Nombre por defecto usado por from_documents
)

total_chunks_recuperados = vectorstore_recargado._collection.count()
print(f"-> Chunks recuperados al reconectar sin recalcular: {total_chunks_recuperados}")
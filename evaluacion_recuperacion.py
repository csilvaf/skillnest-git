"""
Evaluación de recuperación RAG: Precisión y Exhaustividad (Bloque 27)
Dominio: Taller de Servicio Técnico de Consolas y PC.
"""
import os
from datetime import date
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

if not os.environ.get("GEMINI_API_KEY"):
    raise SystemExit('Falta GEMINI_API_KEY. Defínela en tu archivo ".env" y vuelve a ejecutar.')

# Configuración del retriever
K = 3
PERSIST_DIR = "vectorstore/"
MODELO_EMBEDDINGS = "models/gemini-embedding-001"

# =================================================================
# 1. Conjunto de Evaluación (Preguntas y Chunks Relevantes Etiquetados)
# =================================================================
# Basado en los 5 documentos indexados con IDs 'doc0' a 'doc4' en tu corpus del taller:
# doc0: manual_fallas_ps5.md
# doc1: guia_microelectronica_switch.md
# doc2: codigos_post_bios_pc.md
# doc3: protocolo_respaldo_windows.md
# doc4: manual_mantenimiento_termico.md

casos_evaluacion = [
    {
        "pregunta": "¿Qué compuesto lleva el procesador de la PS5 y por qué no debo usar pasta térmica normal?",
        "ids_relevantes": {"doc4"}
    },
    {
        "pregunta": "Llegó una consola portátil de Nintendo que no sube batería tras usar un dock alternativo, ¿qué chips reviso?",
        "ids_relevantes": {"doc1"}
    },
    {
        "pregunta": "¿Qué indican 1 pitido largo y 2 cortos en la placa madre de un PC?",
        "ids_relevantes": {"doc2"}
    },
    {
        "pregunta": "¿Cuál es el protocolo de respaldo antes de formatear un computador de cliente?",
        "ids_relevantes": {"doc3"}
    },
]


# =================================================================
# 2. Funciones de Métricas (Precisión, Recall, Promedio)
# =================================================================

def precision_at_k(ids_recuperados: list[str], ids_relevantes: set[str]) -> float:
    """Fracción de los IDs recuperados que son relevantes (0.0 si no hay ninguno)."""
    if not ids_recuperados:
        return 0.0
    acertados = [1 for i in ids_recuperados if i in ids_relevantes]
    return len(acertados) / len(ids_recuperados)


def recall_at_k(ids_recuperados: list[str], ids_relevantes: set[str]) -> float | None:
    """Fracción de los IDs relevantes que se recuperaron (None si el caso no tiene relevantes)."""
    if not ids_relevantes:
        return None
    acertados = [1 for i in ids_recuperados if i in ids_relevantes]
    return len(acertados) / len(ids_relevantes)


def promediar(valores) -> float:
    """Promedio que ignora los valores None y evita divisiones por cero."""
    validos = [v for v in valores if v is not None]
    return sum(validos) / len(validos) if validos else 0.0


def evaluar_recuperacion(retriever, casos, k=3):
    """Corre cada caso contra el retriever real y promedia precisión y recall."""
    resultados = []
    for caso in casos:
        chunks = retriever.invoke(caso["pregunta"])
        # Extraemos el ID explícito de cada documento recuperado
        ids_recuperados = [c.id for c in chunks][:k]
        
        p = precision_at_k(ids_recuperados, caso["ids_relevantes"])
        r = recall_at_k(ids_recuperados, caso["ids_relevantes"])
        
        resultados.append({
            "pregunta": caso["pregunta"],
            "precision": p,
            "recall": r
        })

    precision_promedio = promediar(x["precision"] for x in resultados)
    recall_promedio = promediar(x["recall"] for x in resultados)
    return resultados, precision_promedio, recall_promedio


# =================================================================
# 3. Ejecución Principal e Impresión de Resultados
# =================================================================

if __name__ == "__main__":
    print("=" * 70)
    print(" EVALUACIÓN DE RECUPERACIÓN RAG SOBRE RETRIEVER REAL (BLOQUE 27)")
    print("=" * 70)

    embeddings = GoogleGenerativeAIEmbeddings(model=MODELO_EMBEDDINGS)
    vectorstore = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings
    )
    
    print("IDs disponibles en el vector store:", vectorstore.get()["ids"])

    retriever = vectorstore.as_retriever(search_kwargs={"k": K})
    
    resultados, precision_promedio, recall_promedio = evaluar_recuperacion(
        retriever, casos_evaluacion, k=K
    )

    print("\n--- RESULTADOS POR CASO ---")
    for r in resultados:
        recall_txt = "n/a" if r["recall"] is None else f"{r['recall']:.2f}"
        print(f"Precisión: {r['precision']:.2f} | Recall: {recall_txt} | Pregunta: {r['pregunta']}")

    print(f"\nPROMEDIO -> Precisión: {precision_promedio:.3f} | Recall: {recall_promedio:.3f}")

    # =================================================================
    # 4. Guardar registro en resultados_evaluacion.txt (Requerimiento Core)
    # =================================================================
    with open("resultados_evaluacion.txt", "w", encoding="utf-8") as archivo:
        archivo.write(f"Fecha: {date.today()}\n")
        archivo.write(f"Configuracion: k={K}, chunk_size=250, chunk_overlap=30\n\n")
        for r in resultados:
            recall_txt = "n/a" if r["recall"] is None else f"{r['recall']:.2f}"
            archivo.write(f"{r['precision']:.2f} {recall_txt} {r['pregunta']}\n")
        archivo.write(
            f"\npromedio -> precision: {precision_promedio:.3f} recall: {recall_promedio:.3f}\n"
        )

    print("\n[Éxito] Resultados guardados formalmente en 'resultados_evaluacion.txt'")
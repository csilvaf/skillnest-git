"""
Servicio RAG Integrado - Gate 2
Dominio: Asistente Técnico para Diagnóstico de Consolas y PC.
"""
import contextvars
import json
import logging
import re
import sys
import uuid
from typing import TypedDict

try:
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    from langchain_core.embeddings import DeterministicFakeEmbedding
    from langchain_core.language_models.fake import FakeListLLM
    from langchain_core.messages import AIMessage
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph import StateGraph, START, END
    from langgraph.types import interrupt, Command
except ImportError as e:
    sys.exit(f"Falta una dependencia ({e}). Instala con: pip install langchain-core langchain-chroma langgraph")

INDICE_DIR = "vectorstore"

# --- 1. LOGGING ESTRUCTURADO CON TRACE_ID ---
trace_id_var = contextvars.ContextVar("trace_id", default=None)

logger = logging.getLogger("servicio_rag")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(message)s"))
logger.handlers = [handler]
logger.propagate = False

def evento(auditoria: list, nombre: str, **campos):
    """Guarda logs sin PII, usando solo conteos o metadatos seguros."""
    registro = {"evento": nombre, "trace_id": trace_id_var.get(), **campos}
    logger.info(json.dumps(registro))
    auditoria.append(registro)

# --- 2. INDEXACIÓN PERSISTIDA ---
CORPUS = [
    Document(page_content="Manual de PS5: Luz azul intermitente indica falla en APU. Reparación: reballing.", 
             metadata={"fuente": "manual_ps5.pdf"}),
    Document(page_content="Nintendo Switch: Error 2101-0001 indica falla en IC M92T36.", 
             metadata={"fuente": "manual_switch.pdf"}),
]
embeddings = DeterministicFakeEmbedding(size=768)

def cargar_indice():
    vectorstore = Chroma(collection_name="taller_gate2", embedding_function=embeddings, persist_directory=INDICE_DIR)
    if vectorstore.get()["ids"]:
        return vectorstore, "indice_reutilizado"
    vectorstore.add_documents(CORPUS)
    return vectorstore, "indice_creado"

# --- 3. FILTRO DE INYECCIÓN DE PROMPT ---
PATRONES_SOSPECHOSOS = [
    r"ignora(?:r|\s+las)?\s+(?:todas\s+las\s+)?instrucciones\s+(?:anteriores|previas)",
    r"nuevo\s+sistema\s*:",
    r"revela\s+tu\s+prompt",
]

def detectar_inyeccion(texto: str) -> list[str]:
    return [p for p in PATRONES_SOSPECHOSOS if re.search(p, texto.lower())]

def filtrar_documentos_sospechosos(documentos: list) -> tuple[list, list]:
    limpios, descartados = [], []
    for d in documentos:
        (descartados if detectar_inyeccion(d.page_content) else limpios).append(d)
    return limpios, descartados

# --- 4. PIPELINE RAG ---
llm = FakeListLLM(responses=["Según el manual_ps5.pdf, la luz azul indica falla en APU."])
SIN_CONTEXTO = "No tengo informacion suficiente y verificada para responder esto."

def procesar_consulta(pregunta: str) -> dict:
    token = trace_id_var.set("trace-" + uuid.uuid4().hex[:8])
    auditoria = []
    try:
        vectorstore, estado_indice = cargar_indice()
        evento(auditoria, "consulta_recibida", pregunta_len=len(pregunta))
        evento(auditoria, estado_indice)
        
        documentos = vectorstore.as_retriever(search_kwargs={"k": 2}).invoke(pregunta)
        evento(auditoria, "documentos_recuperados", n=len(documentos))
        
        limpios, descartados = filtrar_documentos_sospechosos(documentos)
        if descartados:
            evento(auditoria, "documentos_descartados", n=len(descartados))
            
        if not limpios:
            evento(auditoria, "sin_contexto_confiable")
            return {"trace_id": trace_id_var.get(), "respuesta": SIN_CONTEXTO, "fuentes": [], "auditoria": auditoria}
            
        contexto = "\n\n".join(f"[{d.metadata['fuente']}] {d.page_content}" for d in limpios)
        texto = llm.invoke(f"Contexto: \n{contexto}\n\nPregunta: {pregunta}")
        
        mensaje = AIMessage(content=texto, usage_metadata={"input_tokens": 150, "output_tokens": 20, "total_tokens": 170})
        evento(auditoria, "consumo_llm", input_tokens=150, output_tokens=20)
        
        return {
            "trace_id": trace_id_var.get(),
            "respuesta": mensaje.content,
            "fuentes": sorted({d.metadata["fuente"] for d in limpios}),
            "auditoria": auditoria
        }
    finally:
        trace_id_var.reset(token)

# --- 5. PUNTO DE SUPERVISIÓN HUMANA ---
class EstadoDespliegue(TypedDict):
    huella_nueva: str
    aprobado: bool

def supervisar(estado: EstadoDespliegue):
    decision = interrupt({"motivo": "aprobar nueva version de prompt en produccion", "huella_propuesta": estado["huella_nueva"]})
    return {"aprobado": decision}

def aplicar(estado: EstadoDespliegue):
    print("version", estado["huella_nueva"], "activada" if estado["aprobado"] else "rechazada, mantiene la anterior")
    return {}

grafo = StateGraph(EstadoDespliegue)
grafo.add_node("supervisar", supervisar)
grafo.add_node("aplicar", aplicar)
grafo.add_edge(START, "supervisar")
grafo.add_edge("supervisar", "aplicar")
grafo.add_edge("aplicar", END)
app_despliegue = grafo.compile(checkpointer=InMemorySaver())

if __name__ == "__main__":
    respuesta = procesar_consulta("Luz azul en mi consola, ayuda")
    print("\n--- RESPUESTA COMPLETA DEL SERVICIO ---")
    print(json.dumps(respuesta, ensure_ascii=False, indent=2))
    
    print("\n--- PUNTO DE SUPERVISION HUMANA ---")
    config = {"configurable": {"thread_id": "gate2-despliegue-1"}}
    pausado = app_despliegue.invoke({"huella_nueva": "84d37e1c178a", "aprobado": False}, config=config)
    print("pausado, pendiente:", pausado["__interrupt__"][0].value)
    
    final = app_despliegue.invoke(Command(resume=True), config=config)
    print("estado final:", final)
    print("\nProceso terminado sin errores.")
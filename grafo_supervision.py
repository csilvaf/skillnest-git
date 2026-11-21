from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

class EstadoDespliegue(TypedDict):
    huella_nueva: str
    aprobado: bool

def proponer(estado: EstadoDespliegue):
    print("nodo: proponer_version, version propuesta:", estado["huella_nueva"])
    return {}

def supervisar(estado: EstadoDespliegue):
    decision = interrupt({
        "motivo": "aprobar nueva version de prompt en produccion",
        "huella_propuesta": estado["huella_nueva"],
    })
    return {"aprobado": decision}

def aplicar(estado: EstadoDespliegue):
    if estado["aprobado"]:
        print(f" -> version {estado['huella_nueva']} activada")
    else:
        print(f" -> version {estado['huella_nueva']} rechazada, se mantiene la anterior")
    return {}

grafo = StateGraph(EstadoDespliegue)
grafo.add_node("proponer", proponer)
grafo.add_node("supervisar", supervisar)
grafo.add_node("aplicar", aplicar)
grafo.add_edge(START, "proponer")
grafo.add_edge("proponer", "supervisar")
grafo.add_edge("supervisar", "aplicar")
grafo.add_edge("aplicar", END)

app_despliegue = grafo.compile(checkpointer=InMemorySaver())

if __name__ == "__main__":
    huella_prueba = "d8f9a2b1c4e7" # Huella de simulación
    
    print("=== CAMINO DE APROBACIÓN ===")
    config = {"configurable": {"thread_id": "despliegue-1"}}
    app_despliegue.invoke({"huella_nueva": huella_prueba, "aprobado": False}, config=config)
    
    snapshot = app_despliegue.get_state(config)
    print("pendiente:", snapshot.interrupts[0].value)
    
    app_despliegue.invoke(Command(resume=True), config=config)

    print("\n=== CAMINO DE RECHAZO ===")
    config2 = {"configurable": {"thread_id": "despliegue-2"}}
    app_despliegue.invoke({"huella_nueva": "v_experimental", "aprobado": False}, config=config2)
    app_despliegue.invoke(Command(resume=False), config=config2)
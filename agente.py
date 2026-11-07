"""
Herramienta personalizada e integración de agente con memoria (Bloque 22)
Dominio: Taller de Servicio Técnico de Consolas y PC.
"""
import os
from dotenv import load_dotenv

from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

load_dotenv()

# =================================================================
# 1. Herramientas con argumentos estructurados (args_schema Pydantic)
# =================================================================

class ArgumentosEstadoReparacion(BaseModel):
    codigo_orden: str = Field(
        description="Código de orden de la reparación (por ejemplo, 'PS5-202' o 'PC-100')."
    )
    incluir_historial: bool = Field(
        default=False,
        description="Si es True, incluye el historial técnico completo de la reparación, no solo el estado actual."
    )

class ArgumentosPresupuesto(BaseModel):
    horas_trabajo: float = Field(
        description="Cantidad de horas de mano de obra estimadas."
    )
    costo_repuestos: float = Field(
        description="Costo total de las piezas de repuesto en CLP."
    )

BASE_DATOS_TALLER = {
    "PS5-202": {
        "actual": "Reparado: limpieza y metal líquido aplicados. Listo para retiro.",
        "historial": ["Ingreso por apagones", "Diagnóstico térmico", "Aplicación de metal líquido"]
    },
    "PC-100": {
        "actual": "En diagnóstico: esperando revisión de placa madre.",
        "historial": ["Ingreso sin dar video", "Prueba de RAM descartada"]
    }
}

@tool("consultar_estado_reparacion_detallado", args_schema=ArgumentosEstadoReparacion)
def consultar_estado_reparacion(codigo_orden: str, incluir_historial: bool = False) -> str:
    """
    Consulta el estado de reparación de un equipo en el taller, con opción a ver su bitácora histórica.
    """
    orden = BASE_DATOS_TALLER.get(codigo_orden.upper())
    if orden is None:
        return f"No se encontró ninguna orden de reparación con el código {codigo_orden}."
    
    if not incluir_historial:
        return orden["actual"]
    
    historial_unido = " -> ".join(orden["historial"])
    return f"Estado actual: {orden['actual']}. Historial de hitos: [{historial_unido}]"

@tool("calcular_presupuesto_trabajo", args_schema=ArgumentosPresupuesto)
def calcular_presupuesto_total(horas_trabajo: float, costo_repuestos: float) -> str:
    """
    Calcula el presupuesto total de reparación sumando mano de obra ($15.000 x hora) y repuestos.
    """
    total = (horas_trabajo * 15000) + costo_repuestos
    return f"El presupuesto total de la reparación asciende a ${total:,.0f} CLP."


# =================================================================
# 2. Normalizador de salidas para Gemini
# =================================================================

def normalizar_respuesta(resultado):
    """Convierte la salida estructurada de Gemini en un AIMessage estándar para la memoria."""
    contenido = resultado["output"]
    if isinstance(contenido, list):
        contenido = "".join(
            bloque["text"]
            for bloque in contenido
            if isinstance(bloque, dict) and bloque.get("type") == "text"
        )
    return {
        **resultado,
        "output": AIMessage(content=contenido)
    }


# =================================================================
# 3. Construcción del Agente y Executor
# =================================================================

modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0.1)

herramientas = [consultar_estado_reparacion, calcular_presupuesto_total]

prompt_agente = ChatPromptTemplate.from_messages([
    (
        "system",
        "Eres el asistente del taller de servicio técnico. "
        "Responde de manera amable y precisa usando las herramientas disponibles cuando las necesites."
    ),
    MessagesPlaceholder("chat_history"), 
    ("human", "{entrada}"),
    MessagesPlaceholder("agent_scratchpad"),
])

agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)

ejecutor_agente = AgentExecutor(
    agent=agente,
    tools=herramientas,
    verbose=False,
    return_intermediate_steps=True
)

# Conectamos el normalizador al ejecutor antes de la memoria
agente_normalizado = ejecutor_agente | RunnableLambda(normalizar_respuesta)


# =================================================================
# 4. Integración de la Memoria (RunnableWithMessageHistory)
# =================================================================

historiales = {}

def obtener_historial(session_id: str):
    if session_id not in historiales:
        historiales[session_id] = InMemoryChatMessageHistory()
    return historiales[session_id]

agente_con_memoria = RunnableWithMessageHistory(
    agente_normalizado,
    obtener_historial,
    input_messages_key="entrada",
    history_messages_key="chat_history",
    output_messages_key="output", # Indicamos qué clave exacta guardar en memoria
)

# =================================================================
# 5. Pruebas de Continuidad y Aislamiento de Memoria
# =================================================================

if __name__ == "__main__":
    print("=" * 70)
    print(" PRUEBA DEL AGENTE CON HERRAMIENTAS PERSONALIZADAS Y MEMORIA (B22)")
    print("=" * 70)

    config_cliente1 = {"configurable": {"session_id": "cliente_800"}}
    
    print("\n--- CLIENTE 1 (Turno 1) ---")
    res_1 = agente_con_memoria.invoke(
        {"entrada": "¿Cómo va mi consola orden PS5-202? Dime solo el estado actual."},
        config_cliente1
    )
    print(f"[Agente]: {res_1['output'].content}")

    print("\n--- CLIENTE 1 (Turno 2) ---")
    res_2 = agente_con_memoria.invoke(
        {"entrada": "¿Puedes darme el historial completo de hitos de ese mismo equipo?"},
        config_cliente1
    )
    print(f"[Agente]: {res_2['output'].content}")

    config_cliente2 = {"configurable": {"session_id": "cliente_999"}}
    
    print("\n--- CLIENTE 2 (Turno 1 - Aislamiento) ---")
    res_3 = agente_con_memoria.invoke(
        {"entrada": "¿Qué me dijiste sobre los hitos de mi equipo?"},
        config_cliente2
    )
    print(f"[Agente]: {res_3['output'].content}")
    print("-" * 50)
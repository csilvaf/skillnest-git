"""
Primer agente con herramientas y traza de decisión (Bloque 21)
Dominio: Taller de Servicio Técnico de Consolas y PC.
"""
import os
from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

load_dotenv()

# =================================================================
# 1. Definición de Herramientas (Tools) con manejo interno
# =================================================================

@tool
def consultar_estado_reparacion(codigo_orden: str) -> str:
    """
    Consulta el estado actual de un equipo en el taller a partir de su código de orden.
    Usar cuando el cliente pregunta dónde está su consola o PC, o si ya está reparado.
    """
    base_datos_simulada = {
        "PC-100": "En diagnóstico: esperando revisión de placa madre.",
        "PS5-202": "Reparado: limpieza y metal líquido aplicados. Listo para retiro.",
        "SW-305": "Esperando repuestos: joystick analógico en tránsito."
    }
    
    try:
        return base_datos_simulada[codigo_orden.upper()]
    except KeyError:
        return f"No se encontró ninguna orden de reparación con el código {codigo_orden}."


@tool
def calcular_presupuesto_total(horas_trabajo: str, costo_repuestos: str) -> str:
    """
    Calcula el costo total estimado de una reparación sumando la mano de obra y repuestos.
    El valor de la hora de trabajo técnico es de $15.000 CLP.
    Usar cuando el cliente pregunte cuánto le costará arreglar algo si se sabe el tiempo y repuesto.
    """
    try:
        horas = float(horas_trabajo)
        repuestos = float(costo_repuestos)
        total = (horas * 15000) + repuestos
        return f"El costo total estimado es de ${total:,.0f} CLP."
    except ValueError:
        return "Error al calcular el presupuesto: asegúrese de proveer números válidos."


# =================================================================
# 2. Configuración del Agente y Executor
# =================================================================

modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0.1)

herramientas = [consultar_estado_reparacion, calcular_presupuesto_total]

prompt_agente = ChatPromptTemplate.from_messages([
    (
        "system",
        "Eres el asistente del taller de servicio técnico. "
        "Responde preguntas usando las herramientas disponibles cuando las necesites."
    ),
    ("human", "{entrada}"),
    MessagesPlaceholder("agent_scratchpad"),
])

agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)

ejecutor_agente = AgentExecutor(
    agent=agente,
    tools=herramientas,
    verbose=True, # Muestra la traza en consola
    return_intermediate_steps=True # Permite analizar la traza programáticamente
)

# =================================================================
# 3. Validación y Pruebas del Agente
# =================================================================

if __name__ == "__main__":
    print("=" * 70)
    print(" EJECUTANDO PRUEBAS DEL AGENTE (BLOQUE 21)")
    print("=" * 70)

    consultas_prueba = [
        "¿Dónde está mi pedido PS5-202?", # Debe invocar consultar_estado_reparacion
        "Si me cambian el joystick que cuesta 8000 y se demoran 2 horas, ¿cuánto es el total?", # Debe invocar calcular_presupuesto_total
        "¿A qué hora abren el taller?" # No debe invocar ninguna herramienta
    ]

    for consulta in consultas_prueba:
        print(f"\n[Consulta]: {consulta}")
        resultado = ejecutor_agente.invoke({"entrada": consulta})
        
        # Validación de la traza de decisión
        pasos_intermedios = resultado.get("intermediate_steps", [])
        
        if pasos_intermedios:
            for accion, observacion in pasos_intermedios:
                print(f"[Decisión - Tool usada]: {accion.tool}")
                print(f"[Decisión - Argumentos]: {accion.tool_input}")
                print(f"[Decisión - Observación recibida]: {observacion}")
        else:
            print("[Decisión]: El agente decidió NO usar herramientas para esta consulta.")
            
        print(f"[Respuesta final]: {resultado['output']}\n")
        print("-" * 50)
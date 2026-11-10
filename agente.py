"""
Agente con herramientas estructuradas, memoria, supervisión humana y trazas (Bloques 21, 22 y 23)
Dominio: Taller de Servicio Técnico de Consolas y PC.
"""
import os
import sys
import json
import select
import threading
from datetime import datetime, timezone
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
# 1. Supervisión Humana y Registro de Aprobaciones (Bloque 23)
# =================================================================

registro_aprobaciones = []

def esperar_aprobacion(
    mensaje: str,
    tiempo_limite_segundos: int = 300
) -> bool:
    """
    Solicita confirmación humana por consola con límite de tiempo.
    Incluye soporte POSIX (select.select) y fallback con threading para Windows.
    """
    print(mensaje, end="", flush=True)
    try:
        listo, _, _ = select.select(
            [sys.stdin], [], [], tiempo_limite_segundos
        )
        if not listo:
            return False
        respuesta = sys.stdin.readline()
        return respuesta.strip().lower() == "s"
    except OSError:
        # En Windows, select.select no soporta sys.stdin; usamos un hilo con timeout
        resultado = [None]
        def leer_stdin():
            try:
                resultado[0] = sys.stdin.readline()
            except Exception:
                resultado[0] = None

        hilo = threading.Thread(target=leer_stdin, daemon=True)
        hilo.start()
        hilo.join(tiempo_limite_segundos)
        if resultado[0] is None:
            return False
        return resultado[0].strip().lower() == "s"


def registrar_aprobacion(
    herramienta: str,
    argumentos: dict,
    aprobado: bool,
) -> None:
    """Registra la decisión del supervisor humano con su marca de tiempo."""
    registro_aprobaciones.append({
        "herramienta": herramienta,
        "argumentos": argumentos,
        "aprobado": aprobado,
        "momento": datetime.now().isoformat(),
    })


# =================================================================
# 2. Herramientas con argumentos estructurados (args_schema Pydantic)
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

class ArgumentosReembolsoGarantia(BaseModel):
    codigo_orden: str = Field(
        description="Código de la orden de reparación sobre la que se solicita el reembolso (ej. 'PS5-202')."
    )
    monto: float = Field(
        description="Monto en CLP a reembolsar al cliente."
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
    Riesgo bajo: solo lectura.
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
    Riesgo bajo: cálculo interno sin impacto externo.
    """
    total = (horas_trabajo * 15000) + costo_repuestos
    return f"El presupuesto total de la reparación asciende a ${total:,.0f} CLP."

@tool("autorizar_reembolso_garantia", args_schema=ArgumentosReembolsoGarantia)
def autorizar_reembolso_garantia(codigo_orden: str, monto: float) -> str:
    """
    Genera y emite un reembolso de dinero por garantía para una orden del taller.
    Acción irreversible de riesgo alto: requiere aprobación humana antes de ejecutarse.
    """
    mensaje = (
        f"\n[SUPERVISIÓN HUMANA] El agente quiere reembolsar ${monto:,.0f} CLP "
        f"para la orden {codigo_orden}. ¿Aprobar? (s/n): "
    )
    aprobado = esperar_aprobacion(mensaje)
    registrar_aprobacion(
        herramienta="autorizar_reembolso_garantia",
        argumentos={"codigo_orden": codigo_orden, "monto": monto},
        aprobado=aprobado,
    )

    if not aprobado:
        return f"Reembolso para la orden {codigo_orden} no aprobado por el supervisor humano."

    return f"Reembolso de ${monto:,.0f} CLP generado exitosamente para la orden {codigo_orden}."


# =================================================================
# 3. Normalizador de salidas y Registro de Trazas JSONL (Bloque 23)
# =================================================================

def normalizar_respuesta(resultado: dict) -> dict:
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

def registrar_traza(
    session_id: str,
    entrada: str,
    resultado: dict,
) -> None:
    """
    Guarda una interacción del agente como una línea JSON en trazas_agente.jsonl:
    qué se preguntó, qué herramientas se usaron y con qué argumentos, y la respuesta final.
    """
    salida = resultado.get("output", "")
    respuesta_texto = salida.content if hasattr(salida, "content") else str(salida)

    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "entrada": entrada,
        "acciones": [
            {
                "herramienta": accion.tool,
                "argumentos": accion.tool_input,
                "observacion": observacion,
            }
            for accion, observacion in resultado.get("intermediate_steps", [])
        ],
        "respuesta_final": respuesta_texto,
    }

    with open("trazas_agente.jsonl", "a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")


def marcar_repeticiones_sospechosas(
    archivo: str = "trazas_agente.jsonl",
) -> None:
    """
    Recorre el archivo de trazas y marca las sesiones donde la misma herramienta
    se invocó dos o más veces seguidas de forma consecutiva.
    """
    try:
        with open(archivo, encoding="utf-8") as f:
            registros = [json.loads(linea) for linea in f if linea.strip()]
    except FileNotFoundError:
        print(
            f"No se encontró {archivo}. Corre registrar_traza al menos una vez "
            f"antes de revisar repeticiones."
        )
        return

    for registro in registros:
        herramientas_usadas = [
            a["herramienta"] for a in registro.get("acciones", [])
        ]
        for i in range(1, len(herramientas_usadas)):
            if herramientas_usadas[i] == herramientas_usadas[i - 1]:
                print(
                    f"Revisar: {registro['session_id']} usó "
                    f"{herramientas_usadas[i]} dos veces seguidas"
                )
                break


# =================================================================
# 4. Construcción del Agente, Executor y Memoria
# =================================================================

modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

herramientas = [
    consultar_estado_reparacion,
    calcular_presupuesto_total,
    autorizar_reembolso_garantia,
]

prompt_agente = ChatPromptTemplate.from_messages([
    (
        "system",
        "Eres el asistente del taller de servicio técnico de consolas y PC. "
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
    return_intermediate_steps=True,
)

agente_normalizado = ejecutor_agente | RunnableLambda(normalizar_respuesta)

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
    output_messages_key="output",
)


# =================================================================
# 5. Ejecución de Pruebas (Memoria + Aprobación Humana + Trazas JSONL)
# =================================================================

if __name__ == "__main__":
    print("=" * 70)
    print(" PRUEBA INTEGRAL DEL AGENTE: MEMORIA, SUPERVISIÓN Y TRAZAS (B22 y B23)")
    print("=" * 70)

    config_cliente1 = {"configurable": {"session_id": "cliente_800"}}
    
    # Turno 1: Herramienta de riesgo bajo (lectura)
    entrada_1 = "¿Cómo va mi consola orden PS5-202? Dime solo el estado actual."
    print(f"\n--- CLIENTE 1 (Turno 1: Riesgo Bajo) ---\n[Usuario]: {entrada_1}")
    res_1 = agente_con_memoria.invoke({"entrada": entrada_1}, config_cliente1)
    registrar_traza("cliente_800", entrada_1, res_1)
    print(f"[Agente]: {res_1['output'].content}")

    # Turno 2: Continuidad con memoria (riesgo bajo con historial)
    entrada_2 = "¿Puedes darme el historial completo de hitos de ese mismo equipo?"
    print(f"\n--- CLIENTE 1 (Turno 2: Memoria) ---\n[Usuario]: {entrada_2}")
    res_2 = agente_con_memoria.invoke({"entrada": entrada_2}, config_cliente1)
    registrar_traza("cliente_800", entrada_2, res_2)
    print(f"[Agente]: {res_2['output'].content}")

    # Turno 3: Herramienta de riesgo alto (requiere aprobación humana por consola)
    entrada_3 = "Solicito un reembolso por garantía de 45000 CLP para esa misma orden PS5-202."
    print(f"\n--- CLIENTE 1 (Turno 3: Riesgo Alto con Supervisión) ---\n[Usuario]: {entrada_3}")
    res_3 = agente_con_memoria.invoke({"entrada": entrada_3}, config_cliente1)
    registrar_traza("cliente_800", entrada_3, res_3)
    print(f"[Agente]: {res_3['output'].content}")
    print(f"[Registro de aprobaciones]: {registro_aprobaciones}")

    # Sesión 2: Aislamiento entre sesiones
    config_cliente2 = {"configurable": {"session_id": "cliente_999"}}
    entrada_4 = "¿Qué me dijiste sobre los hitos de mi equipo?"
    print(f"\n--- CLIENTE 2 (Turno 1: Aislamiento de Sesión) ---\n[Usuario]: {entrada_4}")
    res_4 = agente_con_memoria.invoke({"entrada": entrada_4}, config_cliente2)
    registrar_traza("cliente_999", entrada_4, res_4)
    print(f"[Agente]: {res_4['output'].content}")

    print("\n--- REVISIÓN AUTOMÁTICA DE REPETICIONES EN TRAZA ---")
    marcar_repeticiones_sospechosas("trazas_agente.jsonl")
    print("=" * 70)
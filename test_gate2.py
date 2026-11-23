"""
Pruebas automatizadas de los 4 criterios no compensables (Gate 2)
"""
import logging
from servicio_rag import procesar_consulta, app_despliegue

# Dato sensible que NUNCA debe aparecer en los logs
CORREO = "cesar.silva@example.com"
PREGUNTA = f"¿Cuál es la falla de luz azul? Mi correo es {CORREO}"

def ejecutar_servicio(pregunta):
    res = procesar_consulta(pregunta)
    return res["respuesta"], res["fuentes"]

def crear_supervision():
    return app_despliegue, {"huella_nueva": "abc123", "aprobado": False}

# --- PRUEBAS ---
def test_1_pipeline_sin_excepciones():
    respuesta, _ = ejecutar_servicio(PREGUNTA)
    assert respuesta.strip(), "el servicio devolvio una respuesta vacia"

def test_2_respuesta_cita_fuente():
    respuesta, fuentes = ejecutar_servicio(PREGUNTA)
    assert fuentes, "el servicio no devolvio ninguna fuente"
    assert any(f in respuesta for f in fuentes), "la respuesta no menciona su fuente"

def test_3_logs_sin_contenido_crudo(caplog):
    with caplog.at_level(logging.DEBUG):
        ejecutar_servicio(PREGUNTA)
    texto_logs = "\n".join(r.getMessage() + str(r.__dict__) for r in caplog.records)
    assert CORREO not in texto_logs, "un dato sensible aparece en los logs"
    assert PREGUNTA not in texto_logs, "la consulta completa aparece en los logs"

def test_4_supervision_pausa_y_reanuda():
    from langgraph.types import Command
    app, entrada = crear_supervision()
    config = {"configurable": {"thread_id": "test-gate2"}}
    
    pausado = app.invoke(entrada, config=config)
    assert "__interrupt__" in pausado, "el grafo no se detuvo en el punto de supervision"
    
    final = app.invoke(Command(resume=True), config=config)
    assert "__interrupt__" not in final, "el grafo sigue pausado despues de reanudar"
    assert final["aprobado"] is True, "la decision no quedo registrada"
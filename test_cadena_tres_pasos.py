"""
Pruebas unitarias para el chain de tres pasos con LangChain (Bloque 18).
Utiliza mocks con AIMessage para evitar consumo de tokens reales.
"""
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage
from cadena_tres_pasos import construir_cadena


def test_cadena_conecta_los_tres_pasos():
    """
    Verifica que la chain ejecute ordenadamente los 3 pasos,
    llamando al modelo 3 veces y retornando el formato final.
    """
    modelo_falso = MagicMock()
    modelo_falso.side_effect = [
        AIMessage(content="Punto 1: Sobrecalentamiento\nPunto 2: Ventilador al 100%\nPunto 3: Apagado térmico"),
        AIMessage(content="El equipo se apaga por seguridad debido a acumulación excesiva de calor en el disipador."),
        AIMessage(content="- Diagnóstico: Falla térmica crítica.\n- Acción: Limpieza y cambio de metal líquido.\n- Prioridad: Alta.")
    ]

    cadena = construir_cadena(modelo_falso)
    resultado = cadena.invoke({"reporte_falla": "PS5 se apaga con 3 pitidos"})

    # Validaciones obligatorias de la pauta
    assert modelo_falso.call_count == 3
    assert "Diagnóstico: Falla térmica crítica" in resultado
    assert resultado.startswith("- ")
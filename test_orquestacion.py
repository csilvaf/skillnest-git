"""
Pruebas unitarias para el manejo de errores (Bloque 20).
Verifica los fallbacks específicos y la red de try/except global.
"""
import pytest
from unittest.mock import MagicMock
from langchain_core.runnables import RunnableLambda

from enrutamiento import (
    construir_cadena_con_enrutamiento,
    construir_cadena_queja_segura,
    procesar_mensaje_seguro,
)

def test_cadena_queja_usa_fallback_ante_fallo_del_modelo():
    """Valida que un error de red en la ruta de queja dispare la respuesta genérica del fallback."""
    def fallar_a_proposito(x):
        raise ConnectionError("Error de red simulado")

    # Simulamos que el modelo principal de la queja se cayó
    cadena_queja_falsa = RunnableLambda(fallar_a_proposito)
    cadena_queja_segura = construir_cadena_queja_segura(cadena_queja_falsa)

    resultado = cadena_queja_segura.invoke({"mensaje": "esto no funciona"})
    
    # Confirmamos que devolvió el fallback y no reventó el script
    assert "equipo" in resultado.lower()


def test_procesar_mensaje_seguro_no_propaga_excepciones():
    """Valida que un fallo catastrófico al principio del flujo sea atrapado por el try/except general."""
    clasificacion_falsa = MagicMock()
    # Forzamos un fallo ANTES de que se enrute nada (en la clasificación)
    clasificacion_falsa.side_effect = ConnectionError("Fallo de API crítico simulado")

    cadena_falsa = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa
    )

    # Invocamos la función segura
    resultado = procesar_mensaje_seguro(cadena_falsa, "mensaje de prueba")
    
    # Comprobamos que atrapó la excepción y devolvió el mensaje blindado al usuario
    assert "no pudimos procesar" in resultado.lower()
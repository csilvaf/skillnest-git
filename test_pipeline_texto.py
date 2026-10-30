"""
Pruebas unitarias para el Pipeline de Texto (Bloque 15).
"""
import pytest
from pipeline_texto import procesar_texto

def test_procesar_texto_normaliza_mayusculas_y_puntuacion():
    """Confirma que la limpieza elimina signos extraños y convierte a minúsculas."""
    resultado = procesar_texto("¡Hola, MUNDO!")
    assert resultado == ["hola", "mundo"]

def test_procesar_texto_solo_puntuacion_devuelve_lista_vacia():
    """Valida el caso límite donde la entrada, al limpiarse, no deja palabras."""
    resultado = procesar_texto("...???!!!")
    assert resultado == []

def test_procesar_texto_valida_tipo():
    """Asegura que el paso de limpieza atrape tipos inválidos con un TypeError."""
    with pytest.raises(TypeError):
        procesar_texto(None)
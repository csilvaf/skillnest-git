"""
Pruebas unitarias para el enrutamiento condicional (Bloque 19).
Verifica las rutas de queja, pregunta, sugerencia, default y la normalización.
"""
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage

from enrutamiento import (
    construir_cadena_con_enrutamiento,
    construir_paso_clasificacion,
)

def test_enrutamiento_va_a_cadena_queja():
    clasificacion_falsa = MagicMock(return_value="queja")
    cadena_queja_falsa = MagicMock(return_value="Respuesta de queja generada")

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_queja=cadena_queja_falsa,
    )
    resultado = cadena.invoke({"mensaje": "esto se volvió a dañar"})
 
    assert cadena_queja_falsa.called
    assert resultado == "Respuesta de queja generada"


def test_enrutamiento_va_a_cadena_pregunta():
    clasificacion_falsa = MagicMock(return_value="pregunta")
    cadena_pregunta_falsa = MagicMock(return_value="Respuesta técnica generada")
 
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_pregunta=cadena_pregunta_falsa,
    )
    resultado = cadena.invoke({"mensaje": "¿qué pasta térmica recomiendan?"})
 
    assert cadena_pregunta_falsa.called
    assert resultado == "Respuesta técnica generada"


def test_enrutamiento_va_a_cadena_sugerencia():
    clasificacion_falsa = MagicMock(return_value="sugerencia")
    cadena_sugerencia_falsa = MagicMock(return_value="Respuesta de sugerencia generada")

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_sugerencia=cadena_sugerencia_falsa,
    )
    resultado = cadena.invoke({"mensaje": "deberían abrir los domingos"})

    assert cadena_sugerencia_falsa.called
    assert resultado == "Respuesta de sugerencia generada"


def test_enrutamiento_usa_default_ante_categoria_desconocida():
    clasificacion_falsa = MagicMock(return_value="insulto_aleatorio")
    cadena_default_falsa = MagicMock(return_value="Respuesta por defecto (pregunta)")

    # Al no coincidir con queja ni sugerencia, debe caer en cadena_pregunta (el default del branch)
    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_pregunta=cadena_default_falsa,
    )
    resultado = cadena.invoke({"mensaje": "texto incomprensible"})

    assert cadena_default_falsa.called
    assert resultado == "Respuesta por defecto (pregunta)"


def test_clasificacion_normaliza_antes_de_comparar():
    """Valida que un texto con mayúsculas, espacios y saltos de línea se limpie a minúsculas."""
    modelo_falso = MagicMock()
    # Usamos AIMessage porque StrOutputParser necesita un objeto de mensaje real, no un string
    modelo_falso.return_value = AIMessage(content="   QueJa \n")
 
    paso_clasificacion = construir_paso_clasificacion(modelo_falso)
    resultado = paso_clasificacion.invoke({"mensaje": "mi equipo vino roto"})
 
    assert resultado == "queja"
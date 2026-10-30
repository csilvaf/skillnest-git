from unittest.mock import patch, Mock
import pytest
import cliente
from cliente import enviar_peticion, con_reintento, registrar_costo, consultar_modelo


@pytest.fixture(autouse=True)
def reiniciar_costo_total():
    """Reinicia el acumulador global de costos antes de cada prueba para evitar contaminación."""
    cliente.costo_total_sesion = 0.0
    yield


# =====================================================================
# 1. Pruebas para enviar_peticion (401/403, 429/500+, y 200 OK)
# =====================================================================

def test_enviar_peticion_credencial_invalida():
    respuesta_falsa = Mock(status_code=401)

    with patch("cliente.requests.post", return_value=respuesta_falsa):
        with pytest.raises(ValueError):
            enviar_peticion({"pregunta": "test"})


def test_enviar_peticion_sin_permiso_403():
    respuesta_falsa = Mock(status_code=403)

    with patch("cliente.requests.post", return_value=respuesta_falsa):
        with pytest.raises(ValueError):
            enviar_peticion({"pregunta": "test"})


def test_enviar_peticion_limite_de_uso():
    respuesta_falsa = Mock(status_code=429)

    with patch("cliente.requests.post", return_value=respuesta_falsa):
        with pytest.raises(TimeoutError):
            enviar_peticion({"pregunta": "test"})


def test_enviar_peticion_error_servidor_500():
    respuesta_falsa = Mock(status_code=503)

    with patch("cliente.requests.post", return_value=respuesta_falsa):
        with pytest.raises(TimeoutError):
            enviar_peticion({"pregunta": "test"})


def test_enviar_peticion_exito():
    respuesta_falsa = Mock(status_code=200)
    respuesta_falsa.json.return_value = {"texto": "respuesta simulada"}

    with patch("cliente.requests.post", return_value=respuesta_falsa):
        resultado = enviar_peticion({"pregunta": "test"})

    assert resultado == {"texto": "respuesta simulada"}


# =====================================================================
# 2. Pruebas para con_reintento (reintento en timeout, agotamiento y no reintento en ValueError)
# =====================================================================

def test_con_reintento_espera_entre_intentos():
    intentos = {"n": 0}

    def funcion_que_falla_una_vez():
        intentos["n"] += 1
        if intentos["n"] == 1:
            raise TimeoutError("simulado")
        return "ok"

    with patch("cliente.time.sleep") as mock_sleep:
        resultado = con_reintento(funcion_que_falla_una_vez)

    assert resultado == "ok"
    mock_sleep.assert_called_once()


def test_con_reintento_agota_intentos():
    def siempre_falla():
        raise TimeoutError("simulado")

    with patch("cliente.time.sleep") as mock_sleep:
        with pytest.raises(TimeoutError):
            con_reintento(siempre_falla, intentos=3)

    assert mock_sleep.call_count == 2


def test_con_reintento_no_reintenta_value_error():
    intentos = {"n": 0}

    def falla_con_value_error():
        intentos["n"] += 1
        raise ValueError("credencial inválida")

    with patch("cliente.time.sleep") as mock_sleep:
        with pytest.raises(ValueError):
            con_reintento(falla_con_value_error, intentos=3)

    assert intentos["n"] == 1
    mock_sleep.assert_not_called()


# =====================================================================
# 3. Pruebas para registrar_costo (cálculo por operación y acumulación)
# =====================================================================

def test_registrar_costo_acumula():
    respuesta_falsa = {"usageMetadata": {"totalTokenCount": 1000}}
    costo_1 = registrar_costo(respuesta_falsa)
    costo_2 = registrar_costo(respuesta_falsa)

    assert costo_1 == cliente.COSTO_POR_1000_TOKENS
    assert costo_2 == cliente.COSTO_POR_1000_TOKENS
    assert cliente.costo_total_sesion == pytest.approx(cliente.COSTO_POR_1000_TOKENS * 2)


# =====================================================================
# 4. Pruebas para consultar_modelo (flujo exitoso, conversión a RuntimeError y propagación de ValueError)
# =====================================================================

def test_consultar_modelo_flujo_exitoso():
    respuesta_api_falsa = {
        "candidates": [{"content": {"parts": [{"text": "Diagnóstico exitoso"}]}}],
        "usageMetadata": {"totalTokenCount": 500}
    }

    with patch.dict("os.environ", {"GEMINI_API_KEY": "clave_test"}):
        with patch("cliente.con_reintento", return_value=respuesta_api_falsa):
            resultado = consultar_modelo("Mi consola no enciende")

    assert resultado == "Diagnóstico exitoso"
    assert cliente.costo_total_sesion == pytest.approx(0.5 * cliente.COSTO_POR_1000_TOKENS)


def test_consultar_modelo_convierte_error():
    error_simulado = TimeoutError("simulado")

    with patch.dict("os.environ", {"GEMINI_API_KEY": "clave_test"}):
        with patch("cliente.con_reintento", side_effect=error_simulado):
            with pytest.raises(RuntimeError):
                consultar_modelo("pregunta de prueba")

    # Verifica que si falla, no registre costo
    assert cliente.costo_total_sesion == 0.0


def test_consultar_modelo_propaga_value_error():
    error_credencial = ValueError("Credencial inválida")

    with patch.dict("os.environ", {"GEMINI_API_KEY": "clave_test"}):
        with patch("cliente.con_reintento", side_effect=error_credencial):
            with pytest.raises(ValueError):
                consultar_modelo("pregunta de prueba")
"""
Preparación, balanceo y validación de dataset propio para PEFT (Bloque 29)
Dominio: Taller de Servicio Técnico de Consolas y PC.
Tarea de comportamiento consistente: Clasificar tickets de ingreso en texto libre
hacia un JSON estandarizado con "area_tecnica" y "prioridad".
"""
import json
import time
from collections import Counter
from google import genai
from google.genai import types


# =================================================================
# Paso 1: Dataset propio del taller (12 ejemplos, 4 categorías balanceadas)
# =================================================================

ejemplos_raw: list[tuple[str, dict[str, str]]] = [
    # Categoría 1: microelectronica (3 ejemplos)
    (
        "La PlayStation 5 prende con luz azul por dos segundos, hace un clic en la fuente y se apaga por completo sin dar video.",
        {"area_tecnica": "microelectronica", "prioridad": "alta"},
    ),
    (
        "Mi Nintendo Switch dejó de cargar después de conectarla a un dock alternativo y huele a quemado cerca del puerto USB-C.",
        {"area_tecnica": "microelectronica", "prioridad": "alta"},
    ),
    (
        "El conector HDMI de mi Xbox Series X tiene los pines hundidos y la placa no envía señal de imagen al televisor.",
        {"area_tecnica": "microelectronica", "prioridad": "media"},
    ),
    # Categoría 2: mantenimiento_termico (3 ejemplos)
    (
        "Mi PS5 suena como turbina de avión a los diez minutos de jugar y me aparece el aviso de consola demasiado caliente.",
        {"area_tecnica": "mantenimiento_termico", "prioridad": "alta"},
    ),
    (
        "Quisiera agendar una limpieza preventiva de polvo y cambio de pasta térmica para mi notebook gamer antes del verano.",
        {"area_tecnica": "mantenimiento_termico", "prioridad": "baja"},
    ),
    (
        "La tarjeta gráfica de mi PC llega a 92 grados jugando y los ventiladores hacen ruido de roce al girar rápido.",
        {"area_tecnica": "mantenimiento_termico", "prioridad": "media"},
    ),
    # Categoría 3: software_sistema (3 ejemplos)
    (
        "Mi computador de trabajo da pantallazo azul cada vez que abro el navegador y necesito rescatar la carpeta de facturación hoy.",
        {"area_tecnica": "software_sistema", "prioridad": "alta"},
    ),
    (
        "Necesito formatear mi PC desde cero, instalar Windows 11 limpio y dejar respaldada la carpeta de fotos familiares.",
        {"area_tecnica": "software_sistema", "prioridad": "media"},
    ),
    (
        "La consola PS4 pide conectar un pendrive con el archivo de reinstalación del sistema versión 11.50 en modo seguro.",
        {"area_tecnica": "software_sistema", "prioridad": "baja"},
    ),
    # Categoría 4: hardware_armado (3 ejemplos)
    (
        "Compré un procesador Ryzen 7 5800X3D para mi placa B550 y al instalarlo el PC no da video y prende el LED DRAM.",
        {"area_tecnica": "hardware_armado", "prioridad": "media"},
    ),
    (
        "Quiero cotizar el armado de un PC desde cero con las piezas que traje en caja y dejar ordenado el manejo de cables.",
        {"area_tecnica": "hardware_armado", "prioridad": "baja"},
    ),
    (
        "Mi PC da 1 pitido largo y 2 cortos al encender tras mover el gabinete de oficina y necesito volver a trabajar urgente.",
        {"area_tecnica": "hardware_armado", "prioridad": "alta"},
    ),
]

examples: list[types.TuningExample] = [
    types.TuningExample(
        text_input=texto,
        output=json.dumps(salida, ensure_ascii=False),
    )
    for texto, salida in ejemplos_raw
]


# =================================================================
# Paso 2: Función para revisar el balance entre categorías
# =================================================================

def chequear_balance(
    datos_raw: list[tuple[str, dict[str, str]]], clave: str
) -> Counter:
    """Cuenta cuántos ejemplos existen por cada valor de la clave indicada."""
    categorias = Counter(salida[clave] for _, salida in datos_raw)
    return categorias


# =================================================================
# Paso 3: Función para validar el dataset antes de enviar a entrenar
# =================================================================

def validar_dataset(
    lista_examples: list[types.TuningExample],
    claves_esperadas: tuple[str, ...],
) -> list[str]:
    """
    Verifica localmente que no existan entradas/salidas vacías, textos duplicados,
    JSON malformados ni diccionarios sin las claves requeridas.
    """
    problemas: list[str] = []
    vistos: set[str] = set()

    for i, ej in enumerate(lista_examples):
        if not ej.text_input or not ej.text_input.strip():
            problemas.append(f"ejemplo {i}: text_input vacio")
        if not ej.output or not ej.output.strip():
            problemas.append(f"ejemplo {i}: output vacio")
            continue

        if ej.text_input in vistos:
            problemas.append(f"ejemplo {i}: text_input duplicado")
        vistos.add(ej.text_input)

        try:
            salida = json.loads(ej.output)
        except json.JSONDecodeError:
            problemas.append(f"ejemplo {i}: output no es JSON valido")
            continue

        for clave in claves_esperadas:
            if clave not in salida:
                problemas.append(f'ejemplo {i}: output no tiene la clave "{clave}"')

    return problemas


# =================================================================
# Paso 4: Seguimiento de estado asíncrono de un trabajo de tuning
# =================================================================

def esperar_a_que_termine(
    client: genai.Client, nombre_trabajo: str, intervalo_segundos: int = 30
) -> types.TuningJob:
    """Consulta periódicamente el estado de un trabajo de tuning hasta un estado final."""
    estados_finales = {
        types.JobState.JOB_STATE_SUCCEEDED,
        types.JobState.JOB_STATE_FAILED,
        types.JobState.JOB_STATE_CANCELLED,
        types.JobState.JOB_STATE_PARTIALLY_SUCCEEDED,
    }
    while True:
        trabajo = client.tunings.get(name=nombre_trabajo)
        print(f"estado actual: {trabajo.state}")
        if trabajo.state in estados_finales:
            return trabajo
        time.sleep(intervalo_segundos)


# =================================================================
# Ejecución y Verificación de los 3 Escenarios de Prueba
# =================================================================

if __name__ == "__main__":
    CLAVES_TAREA = ("area_tecnica", "prioridad")

    print("=" * 60)
    print("PASO 1: balance de MI dataset")
    print("=" * 60)
    balance = chequear_balance(ejemplos_raw, "area_tecnica")
    for categoria, cuenta in balance.most_common():
        print(f"{categoria}: {cuenta}")

    maximo = max(balance.values())
    minimo = min(balance.values())
    print(f"razon max/min: {maximo / minimo:.1f}x")

    print("\n" + "=" * 60)
    print("PASO 2: validacion de MI dataset")
    print("=" * 60)
    problemas = validar_dataset(examples, claves_esperadas=CLAVES_TAREA)
    print(f"{len(examples)} ejemplos, {len(problemas)} problemas encontrados")
    for p in problemas:
        print(" -", p)

    print("\n" + "=" * 60)
    print("PASO 3: rompo un ejemplo a proposito (prueba del validador)")
    print("=" * 60)
    examples_con_fallo = list(examples)
    # Rompemos el ejemplo en índice 3 con un JSON inválido (comillas simples)
    examples_con_fallo[3] = types.TuningExample(
        text_input="Consola se apaga por calor extremo.",
        output="{'area_tecnica': 'mantenimiento_termico'}",
    )
    problemas_detectados = validar_dataset(examples_con_fallo, claves_esperadas=CLAVES_TAREA)
    print(f"{len(examples_con_fallo)} ejemplos, {len(problemas_detectados)} problemas encontrados")
    for p in problemas_detectados:
        print(" -", p)

    print("\n" + "=" * 60)
    print("PASO 4: configuracion PEFT armada y verificada con tipos del SDK")
    print("=" * 60)
    dataset_sdk = types.TuningDataset(examples=examples)
    config_peft = types.CreateTuningJobConfig(
        tuning_mode=types.TuningMode.TUNING_MODE_PEFT_ADAPTER,
        adapter_size=types.AdapterSize.ADAPTER_SIZE_FOUR,
        epoch_count=5,
        tuned_model_display_name="clasificador-tickets-taller-tecnico",
    )
    print("tuning_mode:", config_peft.tuning_mode)
    print("adapter_size:", config_peft.adapter_size)
    print("epoch_count:", config_peft.epoch_count)
    print("ejemplos listos en TuningDataset:", len(dataset_sdk.examples))
"""
Pipeline de texto y métricas de evaluación (Bloques 15 y 16)
Limpieza, tokenización y cálculo de Precisión, Cobertura y F1.
"""
import re
import json
from collections import Counter
from typing import List, Dict
from cliente import consultar_modelo


def limpiar_texto(texto: str) -> str:
    if not isinstance(texto, str):
        raise TypeError(f"limpiar_texto espera str, no {type(texto).__name__}")
    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def tokenizar(texto_limpio: str) -> List[str]:
    return texto_limpio.split()


def procesar_texto(texto: str) -> List[str]:
    texto_limpio = limpiar_texto(texto)
    return tokenizar(texto_limpio)


# --- Nuevas funciones del Bloque 16 ---

def contar_coincidencias(tokens_referencia: List[str], tokens_respuesta: List[str]) -> int:
    """Cuenta coincidencias usando intersección de Counters para respetar repeticiones."""
    conteo_referencia = Counter(tokens_referencia)
    conteo_respuesta = Counter(tokens_respuesta)
    interseccion = conteo_referencia & conteo_respuesta
    return sum(interseccion.values())


def calcular_precision_cobertura_f1(tokens_referencia: List[str], tokens_respuesta: List[str]) -> Dict[str, float]:
    """Calcula las 3 métricas base a partir de las listas de tokens."""
    coincidencias = contar_coincidencias(tokens_referencia, tokens_respuesta)
    
    if not tokens_respuesta or not tokens_referencia:
        return {"precision": 0.0, "cobertura": 0.0, "f1": 0.0}
        
    precision = coincidencias / len(tokens_respuesta)
    cobertura = coincidencias / len(tokens_referencia)
    
    if precision + cobertura == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * cobertura / (precision + cobertura)
        
    return {"precision": precision, "cobertura": cobertura, "f1": f1}


def calcular_metricas(texto_referencia: str, texto_respuesta: str) -> Dict[str, float]:
    """Orquestador: procesa ambos textos y devuelve sus métricas."""
    tokens_ref = procesar_texto(texto_referencia)
    tokens_resp = procesar_texto(texto_respuesta)
    return calcular_precision_cobertura_f1(tokens_ref, tokens_resp)


def resumir_metricas(resultados: List[dict]) -> Dict[str, float]:
    """Calcula el promedio de las métricas de toda la sesión."""
    if not resultados:
        return {"precision_promedio": 0.0, "cobertura_promedio": 0.0, "f1_promedio": 0.0}
    n = len(resultados)
    return {
        "precision_promedio": sum(r["precision"] for r in resultados) / n,
        "cobertura_promedio": sum(r["cobertura"] for r in resultados) / n,
        "f1_promedio": sum(r["f1"] for r in resultados) / n,
    }


if __name__ == "__main__":
    print("--- Generación y Evaluación de Métricas (Bloque 16) ---")
    
    # Casos de prueba enfocados en tu taller técnico
    casos = [
        (
            "¿Qué significa que la PS5 dé 3 pitidos y se apague?",
            "los tres pitidos y apagado en ps5 suelen indicar una falla en la fuente de poder o sobrecalentamiento crítico"
        ),
        (
            "¿Para qué sirve la pasta térmica en el procesador?",
            "la pasta térmica mejora la transferencia de calor entre el procesador y el disipador rellenando imperfecciones microscópicas"
        ),
        (
            "¿Qué componente reviso primero si el PC no da video pero encienden los ventiladores?",
            "se debe revisar la memoria ram limpiando los contactos o probando un módulo a la vez"
        )
    ]
    
    resultados = []
    
    for consulta, referencia in casos:
        print(f"\nProcesando consulta: '{consulta}'")
        # Generamos respuesta real usando tu cliente
        respuesta = consultar_modelo(consulta, "Eres un técnico experto. Responde directo y en una sola oración concisa.")
        
        # Calculamos métricas formales
        metricas = calcular_metricas(referencia, respuesta)
        
        resultados.append({
            "consulta": consulta,
            "respuesta": respuesta,
            **metricas
        })
    
    # 1. Guardar resultados en archivo JSON para persistencia
    with open("resultados_metricas.json", "w", encoding="utf-8") as archivo:
        json.dump(resultados, archivo, indent=2, ensure_ascii=False)
    print("\n[+] Resultados guardados en 'resultados_metricas.json'")
    
    # 2. Resumir e imprimir promedios
    resumen = resumir_metricas(resultados)
    print(f"\n--- Resumen General ---")
    print(f"Precisión Promedio: {resumen['precision_promedio']:.2f}")
    print(f"Cobertura Promedio: {resumen['cobertura_promedio']:.2f}")
    print(f"F1 Promedio:        {resumen['f1_promedio']:.2f}")
    
    # 3. Detectar el peor caso (menor F1) para análisis cualitativo
    peores_casos = sorted(resultados, key=lambda r: r["f1"])
    peor = peores_casos[0]
    print(f"\n--- Peor caso detectado (F1: {peor['f1']:.2f}) ---")
    print(f"Consulta:  {peor['consulta']}")
    print(f"Respuesta: {peor['respuesta']}")
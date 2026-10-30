"""
Pipeline de procesamiento de texto (Bloque 15)
Limpia, normaliza y tokeniza cadenas para métricas de evaluación.
"""
import re
from typing import List
from cliente import consultar_modelo

def limpiar_texto(texto: str) -> str:
    """Normaliza el texto: minúsculas y sin puntuación."""
    if not isinstance(texto, str):
        raise TypeError(f"limpiar_texto espera str, no {type(texto).__name__}")
    
    texto = texto.lower()
    # Mantiene solo palabras (incluye acentos en Python 3) y espacios
    texto = re.sub(r"[^\w\s]", "", texto)
    # Colapsa múltiples espacios y quita espacios extra en bordes
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

def tokenizar(texto_limpio: str) -> List[str]:
    """Convierte texto limpio en una lista de tokens separados por espacios."""
    return texto_limpio.split()

def procesar_texto(texto: str) -> List[str]:
    """Orquestador: recibe texto crudo y devuelve una lista de tokens."""
    texto_limpio = limpiar_texto(texto)
    return tokenizar(texto_limpio)

if __name__ == "__main__":
    print("--- Pipeline Aplicado a Salidas Reales (Bloque 15) ---")
    
    consulta = "La consola PS5 da 3 pitidos y se apaga. ¿Qué puede ser en 1 línea?"
    referencia = "los tres pitidos y apagado en ps5 suelen indicar una falla en la fuente de poder o sobrecalentamiento crítico"
    
    print(f"Consulta: {consulta}")
    respuesta = consultar_modelo(consulta, "Eres un técnico. Responde en una oración.")
    
    crudo_ref = referencia.split()
    crudo_resp = respuesta.split()
    
    comunes_crudo = set(crudo_ref) & set(crudo_resp)
    pct_crudo = len(comunes_crudo) / len(set(crudo_ref)) if crudo_ref else 0.0
    
    tokens_ref = procesar_texto(referencia)
    tokens_resp = procesar_texto(respuesta)
    
    comunes_proc = set(tokens_ref) & set(tokens_resp)
    pct_proc = len(comunes_proc) / len(set(tokens_ref)) if tokens_ref else 0.0
    
    print(f"\nRespuesta modelo: {respuesta}")
    print(f"[Caso 1] Coincidencia texto crudo:     {pct_crudo * 100:.1f}%")
    print(f"[Caso 1] Coincidencia texto procesado: {pct_proc * 100:.1f}%")
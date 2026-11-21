def puntaje_riesgo(probabilidad: int, impacto: int) -> int:
    return probabilidad * impacto

def categoria_riesgo(puntaje: int) -> str:
    if puntaje >= 15: return "CRITICO"
    if puntaje >= 9: return "ALTO"
    if puntaje >= 4: return "MEDIO"
    return "BAJO"

def esta_en_el_limite(probabilidad: int, impacto: int) -> bool:
    categoria_actual = categoria_riesgo(puntaje_riesgo(probabilidad, impacto))
    vecinos = [
        (probabilidad + 1, impacto), (probabilidad - 1, impacto),
        (probabilidad, impacto + 1), (probabilidad, impacto - 1),
    ]
    for p2, i2 in vecinos:
        if not (1 <= p2 <= 5 and 1 <= i2 <= 5):
            continue
        if categoria_riesgo(puntaje_riesgo(p2, i2)) != categoria_actual:
            return True
    return False

mis_riesgos = [
    {
        "riesgo": "Inyeccion de prompt via diagnostico del cliente recuperado",
        "probabilidad": 4, "impacto": 4,
        "mitigacion": "Filtro de patrones + delimitacion de contexto (Bloque 31)"
    },
    {
        "riesgo": "Filtracion de datos (PII) del cliente en logs crudos",
        "probabilidad": 3, "impacto": 5,
        "mitigacion": "Registrar huella (hash) en vez de texto completo (Bloque 31)"
    },
    {
        "riesgo": "Sesgo en diagnosticos por tuning desbalanceado (Ej: predominancia fallas PS5)",
        "probabilidad": 3, "impacto": 3,
        "mitigacion": "Chequeo de balance riguroso por area_tecnica (Bloque 29)"
    },
    {
        "riesgo": "Modelo de embeddings text-embedding-004 queda deprecado",
        "probabilidad": 2, "impacto": 4,
        "mitigacion": "Revision constante de vigencia de modelos en API (Bloque 28)"
    },
    {
        "riesgo": "Diagnosticos errados por manuales de hardware no reindexados",
        "probabilidad": 3, "impacto": 2,
        "mitigacion": "Actualizacion incremental del corpus con IDs (Bloque 25)"
    }
]

if __name__ == "__main__":
    for r in mis_riesgos:
        r["puntaje"] = puntaje_riesgo(r["probabilidad"], r["impacto"])
        r["categoria"] = categoria_riesgo(r["puntaje"])
        r["al_limite"] = esta_en_el_limite(r["probabilidad"], r["impacto"])

    for r in sorted(mis_riesgos, key=lambda x: -x["puntaje"]):
        marca = "[AL LIMITE]" if r["al_limite"] else ""
        print(f"{r['categoria']:8} ({r['puntaje']:2}) - {r['riesgo']} {marca}")
        if r["al_limite"]:
            print(f"   -> revisar con otra persona: {r['riesgo']}")
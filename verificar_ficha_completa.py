import os, re, sys
from ficha_datos import RUTA, cargar
from verificar_ficha import verificar

REVISION = "docs/revision_alcance.md"
MIN_HITOS, MAX_HITOS = 3, 6

def verificar_pendientes(ficha):
    errores = []
    for numero in (4, 5):
        if "[PENDIENTE" in ficha[f"texto{numero}"] or "[COMPLETAR" in ficha[f"texto{numero}"]:
            errores.append(f"la seccion {numero} todavia tiene marcas")
    return errores

def verificar_criterios(ficha):
    errores, avisos = [], []
    existentes = set(ficha["rf"]) | set(ficha["rnf"])
    if not ficha["criterios"]: errores.append("la seccion 4 no tiene criterios (formato CA-NN)")
    escritos = len(re.findall(r"(?m)^-\s*CA", ficha["texto4"]))
    if escritos != len(ficha["criterios"]): errores.append(f"{escritos - len(ficha['criterios'])} criterio(s) no siguen el formato")
    
    cubiertos = set()
    for c in ficha["criterios"]:
        if not c["cubre"]: errores.append(f"{c['id']} no indica que RNF o RF cubre")
        for rid in c["cubre"]:
            if rid not in existentes: errores.append(f"{c['id']} cubre {rid}, que no existe")
            cubiertos.add(rid)
        if not re.search(r"\d", c["texto"]): avisos.append(f"{c['id']} no tiene ningun dato concreto")
            
    for rid in ficha["cajones"]["Imprescindible"] + list(ficha["rnf"]):
        if rid not in cubiertos: errores.append(f"{rid} no tiene criterio de aceptacion")
    return errores, avisos

def verificar_plan(ficha):
    errores = []
    hitos, ids_ca = ficha["hitos"], {c["id"] for c in ficha["criterios"]}
    existentes = set(ficha["rf"]) | set(ficha["rnf"])
    
    escritos = len(re.findall(r"(?m)^-\s*H\d", ficha["texto5"]))
    if escritos != len(hitos): errores.append("hitos no siguen el formato - H1 (3h): descripcion. Cubre: RF-NN. Se comprueba con: CA-NN.")
    if not MIN_HITOS <= len(hitos) <= MAX_HITOS: errores.append(f"hay {len(hitos)} hitos y se piden entre {MIN_HITOS} y {MAX_HITOS}")
    
    if ficha["disponibles"] is None or ficha["margen"] is None:
        errores.append("faltan las lineas 'Horas disponibles:' y 'Margen de imprevistos:'")
    else:
        tope = ficha["disponibles"] - ficha["margen"]
        total = sum(h["horas"] for h in hitos)
        if total > tope: errores.append(f"los hitos suman {total:.1f} h y el tope es {tope:.1f} h")
            
    cubiertos, probados = set(), set()
    for h in hitos:
        if not h["cubre"]: errores.append(f"{h['id']} no indica que RF o RNF cubre")
        if not h["criterios"]: errores.append(f"{h['id']} no tiene criterio de aceptacion")
        for rid in h["cubre"]:
            if rid not in existentes: errores.append(f"{h['id']} cubre {rid}, que no existe")
            cubiertos.add(rid)
        for cid in h["criterios"]:
            if cid not in ids_ca: errores.append(f"{h['id']} usa {cid}, que no existe")
            probados.add(cid)
            
    for rid in ficha["cajones"]["Imprescindible"]:
        if rid not in cubiertos: errores.append(f"{rid} imprescindible sin hito que lo cubra")
    for cid in sorted(ids_ca - probados):
        errores.append(f"{cid} no lo comprueba ningun hito")
    return errores

def verificar_revision(ruta=REVISION):
    if not os.path.exists(ruta): return [f"falta {ruta}: registra la revision cruzada"]
    with open(ruta, encoding="utf-8") as archivo: texto = archivo.read()
    hallazgos = re.findall(r"(?m)^-\s*Hallazgo\s*\d+(?: \([^)]*\))?:\s*.+$", texto)
    decisiones = re.findall(r"(?m)^\s{2}Decisión: (?:aceptado|rechazado|aplazado)\b", texto)
    errores = []
    if len(hallazgos) < 2: errores.append(f"hay {len(hallazgos)} hallazgos y se piden 2")
    if len(decisiones) != len(hallazgos): errores.append("cada hallazgo necesita su linea 'Decisión:' con exactamente 2 espacios")
    return errores

if __name__ == "__main__":
    if not os.path.exists(RUTA): sys.exit(f"No existe {RUTA}")
    with open(RUTA, encoding="utf-8") as archivo: errores, avisos = verificar(archivo.read())
    if not errores:
        ficha = cargar()
        errores = verificar_pendientes(ficha)
        if not errores:
            err_crit, avisos_ca = verificar_criterios(ficha)
            errores += err_crit
            avisos += avisos_ca
            errores += verificar_plan(ficha)
            if not errores: errores += verificar_revision()
            
    for aviso in avisos: print("AVISO:", aviso)
    for error in errores: print("ERROR:", error)
    if errores:
        print(f"\n{len(errores)} problema(s) por resolver")
        sys.exit(1)
    print("Ficha verificada: las cinco secciones son coherentes")

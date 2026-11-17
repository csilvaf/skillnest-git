"""
Chequeo automático (Preflight) del flujo RAG sin llamar a la API (Bloque 28)
"""
import os


def preflight_check(persist_directory: str, gitignore_path: str = ".gitignore") -> list[str]:
    """Confirma, sin llamar a ninguna API, que lo básico del flujo está en orden."""
    problemas = []

    if not os.path.isdir(persist_directory):
        problemas.append(f"{persist_directory} no existe: ¿corriste la indexación?")

    if os.path.exists(gitignore_path):
        with open(gitignore_path, encoding="utf-8") as archivo:
            contenido = archivo.read()
        nombre_carpeta = persist_directory.rstrip("/")
        if nombre_carpeta not in contenido:
            problemas.append(f"{persist_directory} no está en {gitignore_path}")
    else:
        problemas.append(f"no existe {gitignore_path} en este proyecto")

    return problemas


if __name__ == "__main__":
    problemas = preflight_check("vectorstore/")
    if problemas:
        print("Preflight con problemas:")
        for problema in problemas:
            print("-", problema)
    else:
        print("Preflight OK: la carpeta del indice existe y esta en .gitignore")
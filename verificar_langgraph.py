import sys
from importlib.metadata import version, PackageNotFoundError

print("Python:", sys.version.split()[0])

for paquete in ["langgraph", "langgraph-checkpoint-sqlite"]:
    try:
        print(f"{paquete}: {version(paquete)}")
    except PackageNotFoundError:
        print(f"{paquete}: NO instalado")

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

print("imports de la leccion: ok")
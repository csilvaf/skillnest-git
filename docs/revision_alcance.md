# Revisión del alcance
Revisor: Nombre Apellido (autorrevisión)
Fecha: 2026-11-27

- Hallazgo 1 (criterio 4): CA-03 es el caso negativo, pero no especificaba explícitamente qué ocurre con la lista de fuentes cuando la pregunta está fuera de dominio.
  Decisión: aceptado. Cambio: CA-03 ahora exige que la lista de fuentes se devuelva vacía cuando no hay información.
- Hallazgo 2 (criterio 5): El hito H4 agrupa todas las pruebas de RNF, por lo que requiere probar contenedores y logs al mismo tiempo, lo que puede dificultar el testing progresivo.
  Decisión: rechazado. Motivo: Centralizar la auditoría de seguridad y despliegue al final asegura que todo funciona orquestado y empaquetado cumpliendo con RNF-01, RNF-02 y RNF-03 en un ambiente unificado.

# Verificación de la corrección EXT-Q68 — 2026-08-27

Contrato: `ontology_version=3.0.0`, `query_count=115`,
`reasoning_contract=rdfs-literal-value-space-v1`.

## Resultados comprobados

- Suite automatizada: 107 tests aprobados. `continuum-bench validate`:
  `ok=true`, cero incumplimientos tras los tres perfiles de inferencia.
- Monolito: ambos smokes completos con los tres perfiles; acumulativo de
  16 etapas y escalabilidad de 5 y 25 usuarios, una repetición por perfil.
- Docker particionado, cinco nodos, RDFS/OWL RL/RDFS+OWL RL:
  acumulativo de 16 etapas, 3.072 comparaciones con el monolito, cero fallos;
  escalabilidad de 5 y 25 usuarios, 690 comparaciones, cero fallos.
  Se verifican bindings mediante digest, cardinalidad y resultados ASK.
- Cuatro productos reales: Jena 6.0.0, RDF4J 6.0.0,
  RDFLib 7.6.0 + OWL-RL 7.6.2 con el adaptador corregido y Oxigraph 0.5.9.
  Una repetición y un warm-up por producto/dataset. Cero fallos de expectativa
  en acumulativo y escalabilidad; EXT-Q68 devuelve cero en las etapas 13–16
  y en ambos bloques, para los cuatro productos.
- Acuerdo observable RDFS: 1.024/1.024 casos acumulativos y 230/230 de
  escalabilidad. El acuerdo de cardinalidad exacta entre los tres productos
  RDFS es 971/1.024 y 220/230: los cierres de datatypes no son idénticos.
  No se presenta el acuerdo observable como equivalencia exacta universal.

## Artefactos

- `monolith/{cumulative,scalability}/`: resultados de los dos smokes locales.
- `docker/sharded/{cumulative,scalability}/result-validation.csv`:
  comparación de la topología con el monolito.
- `engines/{cumulative,scalability}/query-runs.csv`:
  medidas y expectativas por producto/consulta.
- `engines/{cumulative,scalability}/rdfs-equivalence-summary.json`:
  resumen del acuerdo entre implementaciones RDFS.
- `engines/figures/`: PNG, PDF y SVG regenerados de ambos smokes.

## Límites

Es una verificación funcional, no una campaña de rendimiento para publicación:
se usaron contenedores aislados en puertos 18191–18195 y 18291–18294, mientras
había otros procesos en el equipo. Se reconstruyó la imagen Python con la
corrección y se reutilizó la imagen Java local ya disponible. Los contenedores
temporales se retiraron al terminar; no se reiniciaron los servicios del usuario.
No se ejecutó aquí el clúster Raspberry físico. Sus workers usan el mismo
adaptador y deben redesplegarse/reiniciarse antes de repetir la campaña.

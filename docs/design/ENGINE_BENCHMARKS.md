# Benchmark con motores semánticos independientes

## Objetivo

Este experimento ejecuta exactamente el mismo grafo N-Triples y el mismo
catálogo SPARQL en implementaciones independientes. Complementa los perfiles
RDFS, OWL RL y RDFS+OWL RL del benchmark Python: esos perfiles sirven para
comparar semánticas, mientras que este experimento permite comparar productos.

| Servicio | Versión fijada o registrada | Régimen | Función |
|---|---:|---|---|
| Apache Jena | 6.0.0 | RDFS | Razonador independiente |
| Eclipse RDF4J | 6.0.0 | RDFS | Razonador independiente |
| RDFLib + OWL-RL | registrada en `metadata.json` | RDFS | Referencia Python |
| Oxigraph | registrada en `metadata.json` | sin inferencia | Control del coste SPARQL |

Oxigraph no se presenta como razonador. Es el control que permite observar el
coste de carga y consulta cuando no se materializan consecuencias RDFS.

Jena usa `ReasonerRegistry.getRDFSReasoner()`. RDF4J usa
`SchemaCachingRDFSInferencer` sobre `MemoryStore`. RDFLib usa el cierre
`RDFS_Semantics` de OWL-RL. RDF4J 6 requiere Java 25; la imagen de compilación y
la de ejecución están fijadas a esa versión.

## Ejecución automática

Los comandos normales incluyen todos los motores, levantan el Compose semántico,
esperan a que responda `/health` y lo retiran al finalizar:

```bash
.venv/bin/continuum-smoke-cumulative
.venv/bin/continuum-smoke-scalability
.venv/bin/continuum-bench benchmark cumulative
.venv/bin/continuum-bench benchmark scalability
.venv/bin/continuum-bench benchmark all
```

No se indican motores ni endpoints. `--python-only` omite deliberadamente los
productos externos. `--keep-engine-services` deja los servicios arrancados para
diagnóstico. El subcomando `engines` se conserva como interfaz avanzada para
endpoints personalizados.

Los motores se ejecutan secuencialmente para evitar que compitan entre sí por
CPU y memoria durante una medición. Todos tienen el mismo límite de 2 CPU y
3 GiB. Antes de medir se ejecuta por defecto un warm-up por motor y dataset,
excluido de los CSV. Puede cambiarse con `--warmups N`; para una prueba puramente
funcional y más rápida se admite `--warmups 0`. La terminal informa de warm-up,
motor, régimen de inferencia, repetición, etapa/categoría o bloque/usuarios.
No se lanzan healthchecks periódicos durante la medición: el coordinador
comprueba `/health` de forma síncrona antes del experimento.

## Contrato común de medición

Cada servicio implementa:

- `GET /health`: nombre, versión y régimen de inferencia;
- `POST /prepare`: carga del N-Triples y preparación/materialización;
- `POST /queries`: ejecución secuencial del lote SPARQL.

El coordinador genera una serialización canónica para todos los servicios y
recoge:

- triples de entrada, salida e inferidos;
- tiempo de carga, razonamiento y preparación;
- tiempo de cada consulta y tiempo de pared del lote;
- número de filas o valor `ASK`;
- expectativa funcional de la consulta.

`metadata.json` registra el número de warm-ups y las versiones comunicadas por
cada servicio.

En RDF4J la inferencia ocurre durante la inserción. Por ello `load_ms` se deja a
cero y el intervalo conjunto carga+inferencia se registra como `reasoning_ms`;
la métrica comparable entre los cuatro productos es `prepare_ms`.

## Validación cruzada

La conformidad tiene dos niveles:

1. **Resultado observable obligatorio**: mismo valor `ASK` o misma clase de
   cardinalidad (cero/no-cero) y cumplimiento de la expectativa del catálogo.
   Una discrepancia detiene el comando con código no cero.
2. **Cardinalidad exacta diagnóstica**: compara el número exacto de filas. Se
   conserva, pero no es una condición de fallo porque los motores aplican
   variantes de entailment de datatypes y pueden producir bindings duplicados
   distintos sin cambiar la decisión.

También se informa por separado del acuerdo exacto Jena/RDF4J. Los artefactos
son:

```text
outputs/engines/<suite>/
  query-runs.csv
  summary.csv
  metadata.json
  rdfs-equivalence.csv
  rdfs-equivalence-summary.json
outputs/engines/figures/
  engines-cumulative.{png,pdf,svg}
  engines-scalability.{png,pdf,svg}
```

Para los perfiles smoke, el subdirectorio `engines` queda dentro del
`output_dir` de su configuración.

## Regenerar o mostrar figuras

```bash
# Regenerar
.venv/bin/continuum-bench plot engines

# Regenerar y abrir
.venv/bin/continuum-bench plot engines --show

# Resultados smoke en otro directorio
.venv/bin/continuum-bench \
  --config configs/smoke-scalability.toml \
  plot engines --engine-dir outputs/engines-smoke --show

# Si solo se ejecutó una suite
.venv/bin/continuum-bench plot engines \
  --engine-suite cumulative \
  --engine-dir outputs/engines-smoke-cumulative --show
```

Las figuras usan mediana y rango mínimo-máximo por repetición, marcadores
distintos, etiquetas explícitas del régimen y exportación vectorial. En una
corrida smoke con una repetición el rango es necesariamente cero; no debe usarse
como resultado estadístico de un artículo.

## Referencias de implementación

- Apache Jena, inferencia:
  https://jena.apache.org/documentation/inference/index.html
- Eclipse RDF4J, Repository y Sail:
  https://rdf4j.org/documentation/programming/repository/
- Eclipse RDF4J, Server y requisito de Java:
  https://rdf4j.org/documentation/tools/server-workbench/
- Oxigraph:
  https://github.com/oxigraph/oxigraph

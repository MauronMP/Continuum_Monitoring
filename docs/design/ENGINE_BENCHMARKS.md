# Benchmark con motores semánticos independientes

## Objetivo

Este experimento ejecuta exactamente el mismo grafo N-Triples v3.0.0 y las 115
consultas del mismo catálogo SPARQL en implementaciones independientes. Complementa los perfiles
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
`RDFS_Semantics` de OWL-RL con el adaptador de igualdad de literales descrito
abajo. Jena 6 requiere Java 21 o posterior y RDF4J 6
requiere Java 25; por eso la imagen común de compilación y ejecución queda
fijada a Java 25, el requisito más restrictivo.

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

- `GET /health`: servicio, protocolo v2, nombre, versión y régimen de inferencia;
- `POST /prepare`: carga del N-Triples y preparación/materialización;
- `POST /queries`: ejecución secuencial del lote SPARQL.

El coordinador genera una serialización canónica para todos los servicios y
recoge:

- triples de entrada, salida e inferidos;
- tiempo de carga, razonamiento y preparación;
- tiempo de cada consulta y tiempo de pared del lote;
- número de filas o valor `ASK`;
- expectativa funcional de la consulta.

`metadata.json` registra el número de warm-ups, las versiones comunicadas por
cada servicio, `ontology_version=3.0.0`, `query_count=115` y el hash del grafo.
Incluye también `reasoning_contract=rdfs-literal-value-space-v1`. Los comandos
de figuras rechazan resultados v2, v3 anteriores a esta corrección o metadatos
incompletos, para no mezclar cierres semánticos diferentes.

En RDF4J la inferencia ocurre durante la inserción. Por ello `load_ms` se deja a
cero y el intervalo conjunto carga+inferencia se registra como `reasoning_ms`;
la métrica comparable entre los cuatro productos es `prepare_ms`.

## Corrección RDFS de literales y EXT-Q68

La implementación OWL-RL instalada (7.6.2) sustituía literales al comparar sus
valores Python: `True == 1` y `False == 0`. Esto añadía enteros a las propiedades
booleanas `hasNoiseApplied` y `hasAnonymizationApplied` del gradiente de
referencia. EXT-Q68 detectaba tres bindings de incumplimiento artificiales,
aunque el dato afirmado era válido. El acumulativo notificaba cuatro fallos
(etapas 13–16) y el smoke de escalabilidad dos (bloques de 5 y 25 usuarios).

`DatatypeAwareRDFSSemantics` corrige exclusivamente esa sustitución mediante
igualdad de valor RDF sensible al datatype e idioma. Conserva equivalencias
numéricas válidas y no cambia ni relaja EXT-Q68. Se usa en el monolito, el
servicio RDFLib y los workers Docker/físicos. Los perfiles OWL RL y combinado
mantienen sus implementaciones originales.

El identificador de contrato se publica en `/health` de los workers y del
servicio RDFLib. Los coordinadores rechazan imágenes antiguas; deben
reconstruirse y volver a ejecutarse los benchmarks de las arquitecturas que
se quieran comparar. Los CSV antiguos se conservan, pero no se convierten
en resultados corregidos modificando sus metadatos.

La regresión cubre las 115 consultas por el camino real N-Triples/preparación/
consulta para RDFLib y Oxigraph, con 0, 5 y 25 usuarios, y casos inválidos
explícitos de privacidad. `validate` comprueba además las 32 consultas de
incumplimiento **después** de cada materialización.

Referencia de la regla original:
[código RDFSClosure de OWL-RL](https://owl-rl.readthedocs.io/en/latest/_modules/owlrl/RDFSClosure.html).

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
  plot engines \
  --engine-dir outputs/smoke-scalability/engines --show

# Si solo se ejecutó una suite
.venv/bin/continuum-bench plot engines \
  --engine-suite cumulative \
  --engine-dir outputs/smoke-cumulative/engines --show
```

Las figuras usan mediana y rango mínimo-máximo por repetición, marcadores
distintos, etiquetas explícitas del régimen y exportación vectorial. En una
corrida smoke con una repetición el rango es necesariamente cero; no debe usarse
como resultado estadístico de un artículo.

## Referencias de implementación

- Apache Jena, inferencia:
  https://jena.apache.org/documentation/inference/index.html
- Apache Jena, descarga y requisito Java 21+:
  https://jena.apache.org/download/
- Eclipse RDF4J 6, descarga y requisito Java 25+:
  https://rdf4j.org/download/
- Eclipse RDF4J, Repository y Sail:
  https://rdf4j.org/documentation/programming/repository/
- Eclipse RDF4J, Server y requisito de Java:
  https://rdf4j.org/documentation/tools/server-workbench/
- Oxigraph:
  https://github.com/oxigraph/oxigraph

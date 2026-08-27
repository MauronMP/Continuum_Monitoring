# Trazabilidad de artefactos v3.0.0

| Necesidad | Artefacto verificable |
|---|---|
| Fuente ontológica v3 | `ontology/legacy/smartcity_continuum-v3.0.0.ttl` |
| Fuente SPARQL v3 | `queries/legacy/sparql_battery-v3.0.0.sparql` |
| Contrato de release ejecutable | `continuum_bench.specification` |
| Núcleo estándar del continuum | `ontology/core` y `ontology/modules` |
| Extensión temática de bienestar | `ontology/domains/wellbeing` |
| Restricciones cerradas | `ontology/shapes` y consultas `violation` |
| ABox y escenarios S1–S17 | `ontology/examples/reference-system.ttl` |
| 115 consultas núcleo/tema | `queries/catalog.csv` y ficheros `.rq` |
| Routing, privacidad y merge | `queries/execution-plan.toml` |
| Placement cloud/fog/edge | `configs/ontology-placement.toml` y `ontology/profiles` |
| 72 RF, 39 RNF y 5 RV | `docs/reference/RN_RNF.md` |
| 79 políticas y 55 mecanismos | `docs/reference/Políticas.md` |
| Generación reproducible | `tools/migrate_assets.py` |
| Datos sintéticos por volumen | `continuum_bench.synthetic` |
| Acumulativo y escalabilidad | `continuum_bench.benchmark` |
| Carga multidimensional | `continuum_bench.load_benchmark` |
| Scale-out/hardware/distribuida | `continuum_bench.experiments` |
| Jena/RDF4J/RDFLib/Oxigraph | `continuum_bench.engines` y `engine-service` |
| Docker de cinco nodos | `docker-compose.yml`, `distributed.py`, `sharded.py` |
| Continuum físico | `physical_cluster.py`, `physical.py`, `sharded.py` |
| Equivalencia | conjunto/digest canónico y `result-validation.csv` |
| Gráficas de publicación | `plotting.py`, `reporting.py` y `experiment_analysis.py` |

Cada fila del catálogo contiene `purpose`, `requirements` y `policies`. La
validación comprueba que todos esos IDs existen en el grafo v3; por tanto esta
tabla de alto nivel no sustituye la trazabilidad consulta-a-requisito ejecutable.

La cobertura directa del catálogo recibido es 102/116 requisitos (87,93 %) y
69/79 políticas (87,34 %). No hay referencias a IDs inexistentes. Permanecen
sin consulta explícita:

- requisitos: `RF-07`, `RF-41`, `RF-44`, `RF-52`, `RF-69`, `RNF-03`,
  `RNF-10`, `RNF-11`, `RNF-23`, `RNF-24`, `RNF-26`, `RNF-31`, `RNF-37` y
  `RNF-38`;
- políticas: `P-ADAPT-08`, `P-CONS-06`, `P-GOV-02`, `P-MODEL-09`,
  `P-NODE-06`, `P-OPS-04`, `P-OPS-06`, `P-VAL-02`, `P-VAL-05` y
  `P-ZONE-04`.

Estas listas se calculan también en `validate`; son una limitación de cobertura
de la batería, no una violación de sintaxis o integridad de la ontología.


sudo apt update
sudo apt install -y ca-certificates curl

sudo install -m 0755 -d /etc/apt/keyrings

sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc

sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo apt update

sudo apt install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
  sudo systemctl status docker
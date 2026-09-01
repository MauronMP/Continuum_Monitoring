# Ontology diagrams for publication

English conceptual views of release **3.0.0**, revision
`3.0.0-en-datatypes-v1`. The figures are generated from the actual ontology
files listed in `configs/benchmark.toml`; they are not hand-drawn substitutes
for the schema.

## Choose a view

| View | Files | Intended use |
| --- | --- | --- |
| Simplified conceptual graph | [PDF](figures/ontology-simplified.pdf), [SVG](figures/ontology-simplified.svg), [PNG](figures/ontology-simplified.png) | Main paper figure: 15 distinct classes and 15 asserted relations, arranged in three panels. |
| Complete conceptual graph | [PDF](figures/ontology-complete.pdf), [SVG](figures/ontology-complete.svg), [PNG](figures/ontology-complete.png) | Zoomable supplementary map: every declared class and property. Do not shrink it into a paper column. |
| Complete schema atlas | [PDF](ontology-atlas.pdf) | Readable A4 reference: classes, parents, properties, domains, ranges and provenance, grouped by module. |
| Monochrome simplified graph | [SVG](figures/ontology-simplified-monochrome.svg) | Grayscale publication; module names are included in the boxes. |
| Module detail | [SVG directory](figures/modules/) | Nine focused schema views, retaining relevant cross-module context. Large modules still require zoom. |

The simplified graph has three panels: **(a)** consent and policy governance,
**(b)** monitoring, deployment and adaptation, and **(c)** model learning and
optional wellbeing data. Repeated boxes denote the same class IRI, not copies
of an OWL class. The selection is explicit in `SIMPLIFIED_PROPERTIES` in the
generator and in `manifest.json`; it is deliberately non-exhaustive.

## What “complete” means

The complete view covers the **asserted class/property schema**, not every
triple or individual in the ontology:

| Inventory | Count |
| --- | ---: |
| Named classes | 146 |
| Anonymous union expressions | 11 |
| Object properties | 165 |
| Datatype properties | 98 |
| Annotation properties | 14 |
| Subclass axioms | 70 |

Inputs are the 14 local runtime files, whose union contains 7,966 triples.
This includes `ontology/modules/deployment.ttl`: its four classes and six
properties describe benchmark placement. The canonical single-file ontology
`ontology/legacy/smartcity_continuum-v3.0.0.ttl` has 142 named classes and 271
properties; the diagrams include that schema **plus the deployment extension**.
The sources and their SHA-256 hashes are recorded in
[manifest.json](manifest.json) and [data/schema.json](data/schema.json).

The nine display groups are foundation, topology, observability, governance,
orchestration, federated learning, deployment, optional wellbeing, and external
standards/SHACL declarations. These are visual groupings of the current modules,
not a proposal to change ontology ownership or placement.

Individual users, policies, requirements, scenarios, events and SHACL constraint
instances are not expanded. Class/individual punning is explicitly marked.
Import IRIs are not fetched from the network, no reasoner runs, and inferred
closure is not mixed with asserted structure. These diagrams do **not** replace
the Turtle source, SHACL validation, OWL consistency checks or benchmark results.

## Reading the notation

- Boxes represent classes. Colors identify modules. Context classes in module
  views have gray, dashed boxes.
- Solid labeled arrows project an object property's **asserted domain to its
  asserted range**. They do not assert that every instance has that property,
  specify cardinalities, or describe an execution workflow.
- A dashed line with a hollow arrowhead points from a subclass to its parent.
- `OR` boxes preserve explicit `owl:unionOf` expressions; dotted links identify
  their members. Multiple separately asserted domains/ranges mean `AND`, not
  `OR`. The generator keeps that distinction.
- Datatype properties appear as attributes with their declared ranges.
- `Not declared` means that the source supplies no domain/range constraint.
  The diagram never invents one. Fully unscoped object properties, annotation
  properties and additional schema axioms have separate registry boxes.
- Labels in the simplified view are English display names. The full view uses
  prefixed names. Full IRIs are preserved in SVG tooltips and editable exports.
- Invisible DOT edges only control panel layout; they are neither rendered nor
  exported as semantic relations in GraphML/CSV.

This is a documented conceptual notation, not a claim of conformance to a
specific UML/OWL visual-notation standard.

## Formats and editing

- **PDF**: vector artwork for LaTeX and manuscript submission. Use the original
  PDF, not a screenshot of it.
- **SVG**: scalable, editable graphics for vector editors, browsers and document
  tools supporting SVG. SVG is a W3C format; see the
  [SVG specification](https://www.w3.org/TR/SVG2/).
- **DOT**: editable graph/layout sources in `sources/`, using the
  [Graphviz DOT language](https://graphviz.org/doc/info/lang.html).
- **GraphML**: `sources/ontology.graphml` exports schema terms as nodes and
  schema axioms as edges, with original IRIs. Unlike the conceptual view, a
  property is itself a node linked to its domain/range. It has no fixed layout.
  It is a graph-editor interchange file, **not** a lossless OWL serialization.
- **CSV/JSON**: `data/` contains the class/property inventory, expressions,
  labels, comments, source attribution and schema edges for auditing/reuse.
- **PNG**: convenient previews only. The large map is intentionally size-limited
  in PNG; use SVG/PDF to inspect its text or submit it as supplementary material.

There is no single universally accepted journal figure format. Check the target
journal's requirements for dimensions, fonts, color and accessibility. The
manifest reports the minimum font size both at native size and when fitted to
180 x 230 mm. For this render, the simplified graph retains approximately
8.4 pt text at that fit; the complete graph is **not legible** at that size.
The atlas uses 8 pt table text at native A4 size. Do not rasterize the vector
figures merely to assign a nominal DPI.

## Regenerate

Run from the repository root. Viewing the committed figures requires no Python,
Graphviz, Java, Docker or reasoners. Regeneration needs the project's Python
environment plus Graphviz; ReportLab is optional and only needed for the atlas.

```bash
# Ubuntu/Debian, including Raspberry Pi OS
sudo apt-get update
sudo apt-get install graphviz

# macOS with Homebrew: use this instead of apt-get
brew install graphviz

# Install the optional atlas dependency into the existing project environment
.venv/bin/python -m pip install -e ".[diagrams]"

# Regenerate both views, module details, inventories and the atlas
.venv/bin/python -m continuum_bench.diagrams
```

The two OS-specific installation alternatives are not commands to run together.
On Windows, install Graphviz with `dot` on `PATH` and substitute
`.venv\Scripts\python.exe` for `.venv/bin/python`. All subprocesses use argument
lists, and neither rendering nor extraction relies on a Unix shell.

```bash
# Graphviz figures without ReportLab / without rebuilding the atlas
.venv/bin/python -m continuum_bench.diagrams --no-atlas

# No Graphviz or ReportLab: only editable sources and inventories
.venv/bin/python -m continuum_bench.diagrams \
  --sources-only --output outputs/ontology-diagram-sources

# Explicit configuration, destination and per-process timeout
.venv/bin/python -m continuum_bench.diagrams \
  --config configs/benchmark.toml --output ontology/diagrams --timeout 120

# Diagram regression tests (Graphviz/ReportLab integrations skip if unavailable)
.venv/bin/python -m pytest tests/test_diagrams.py
```

For a nonstandard installation, `--dot /path/to/dot` selects Graphviz and
`--atlas-python /path/to/python` selects a Python interpreter with ReportLab.
These are optional overrides, not machine-specific requirements.

The generator checks the English release identity, completeness and visible
SVG edge labels. It fails clearly on unsupported class expressions or a changed
simplified selection rather than silently misrepresenting them. The extracted
schema/DOT/GraphML ordering is deterministic for the current skolemized inputs;
layout and PDF bytes can differ with Graphviz versions, fonts and operating
systems. Pin those dependencies for camera-ready reproducibility.

Generated files with the same names are overwritten; ontology inputs and
unrelated files are not changed or deleted. With `--sources-only` or `--no-atlas`,
older rendered files in that destination are **not refreshed or removed**. Use
a fresh destination for partial exports. Only trust rendered outputs accompanied
by a `manifest.json` with `status="complete"`, `rendered=true`, and matching input
hashes. A full run also records `atlas_pages`.

## Include in a paper

Use [paper-example.tex](paper-example.tex) as a complete LaTeX example, compiling
from the repository root:

```bash
mkdir -p outputs/ontology-paper-example
pdflatex -halt-on-error -interaction=nonstopmode \
  -output-directory=outputs/ontology-paper-example \
  ontology/diagrams/paper-example.tex
```

The example fits the simplified PDF on one page and supplies an English caption
that states the selection, source release and notation limits. Adjust it to the
journal template. Submit the complete SVG/PDF and atlas as supplements instead
of shrinking the full map into that figure.

Suggested caption for the complete map:

> Asserted class/property schema of the continuum monitoring ontology v3.0.0
> (revision 3.0.0-en-datatypes-v1), including the benchmark deployment extension.
> The map covers 146 named classes, 165 object properties, 98 datatype properties
> and 14 annotation properties. Solid arrows project declared domain/range
> relations; hollow arrows indicate subclass axioms. OR expressions and missing
> domain/range declarations remain explicit. Individual instances and inferred
> closure are not expanded. The accompanying module views and schema atlas
> provide readable detail.

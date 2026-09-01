"""Graphviz views plus standards-based, editable graph and inventory exports."""

from __future__ import annotations

from collections import defaultdict
import csv
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import subprocess
import textwrap
import xml.etree.ElementTree as ET

from .model import EX, MODULES, Node, Property, Schema, simplified


def _quote(value: object) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def _wrap(value: str, width: int = 24) -> str:
    return "\n".join(textwrap.wrap(value, width=width, break_long_words=True,
                                  break_on_hyphens=False))


def _html(value: str, width: int = 40) -> str:
    return '<BR ALIGN="LEFT"/>'.join(escape(line) for line in _wrap(value, width).splitlines())


def _legend(simple: bool, modules: set[str], monochrome: bool = False, *, context: bool = False) -> str:
    cells = []
    size = 10 if simple else 9
    for module, (label, fill, _) in MODULES.items():
        if module in modules:
            if monochrome:
                fill = '#FFFFFF'
            cells.append(f'<TD BGCOLOR="{fill}" CELLPADDING="5">'
                         f'<FONT POINT-SIZE="{size}">{escape(label)}</FONT></TD>')
    rows = ['<TR>' + ''.join(cells[i:i + 3]) + '</TR>' for i in range(0, len(cells), 3)]
    note = ("Selected schema relations; repeated boxes denote the same class."
            if simple else "Solid: object property | Hollow arrow: subclass | Dotted: OR/AND membership")
    rows.append(f'<TR><TD COLSPAN="3"><FONT POINT-SIZE="{size}">{escape(note)}</FONT></TD></TR>')
    if not simple:
        rows.append('<TR><TD COLSPAN="3"><FONT POINT-SIZE="9">'
                    'Attributes: datatype properties | Registries: unscoped properties / metadata'
                    '</FONT></TD></TR>')
        if context:
            rows.append('<TR><TD COLSPAN="3"><FONT POINT-SIZE="9">'
                        'Dashed gray class boxes: cross-module context'
                        '</FONT></TD></TR>')
    return '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="3">' + ''.join(rows) + '</TABLE>>'


def _simplified_panels(schema: Schema, monochrome: bool) -> str:
    selected, properties = simplified(schema)
    lookup = {prop.id.rsplit('#', 1)[-1]: prop for prop in properties}
    panels = [
        ('a', 'Consent and policy governance', (
            'hasConsentRecord', 'hasSemanticContract', 'auditsContract',
            'appliedPolicy', 'tracedToPolicy')),
        ('b', 'Monitoring, deployment and adaptation', (
            'evaluatesNode', 'hasNodeState', 'hasDecisionAlternative',
            'resultedInAction', 'affectsModel', 'hostedAt')),
        ('c', 'Model learning and optional wellbeing data', (
            'updatesModel', 'transfersData', 'generatedBy', 'hasWearable')),
    ]
    modules = {schema.nodes[key].module for key in selected}
    lines = ['digraph ontology {',
        'graph [rankdir=TB, bgcolor="white", newrank=true, margin=0,',
        '       pad="0.16", nodesep="0.25", ranksep="0.28", splines=polyline,',
        '       fontname="Helvetica", fontnames="svg", labelloc=b, outputorder=edgesfirst];',
        'node [shape=box, style="rounded,filled", color="#52606D", fontcolor="#17212B",',
        '      fontname="Helvetica", fontsize=11, margin="0.12,0.08", penwidth=1];',
        'edge [fontname="Helvetica", fontsize=10, color="#64717D", fontcolor="#26323C",',
        '      penwidth=0.9, arrowsize=0.65];',
        f'label={_legend(True, modules, monochrome)};']
    for number, (panel, heading, names) in enumerate(panels):
        props = [lookup[name] for name in names]
        identifiers = {key for prop in props for key in prop.domains + prop.ranges}
        lines += [f'subgraph cluster_{panel} {{',
                  f'sortv={number}; label={_quote("(" + panel + ") " + heading)};',
                  'labelloc=t; labeljust=l; fontsize=12; color="#DDE2E6"; margin=12;']
        for identifier in sorted(identifiers):
            node = schema.nodes[identifier]
            label = _wrap(node.label, 17)
            if monochrome:
                label += '\n[' + MODULES[node.module][0].split(' (')[0] + ']'
            lines.append(f'{_quote(panel + ":" + identifier)} [label={_quote(label)}, '
                         f'fillcolor="{"#FFFFFF" if monochrome else MODULES[node.module][1]}", '
                         f'tooltip={_quote(identifier)}];')
        for prop in props:
            lines.append(f'{_quote(panel + ":" + prop.domains[0])} -> '
                         f'{_quote(panel + ":" + prop.ranges[0])} '
                         f'[label={_quote(_wrap(prop.label, 17))}, tooltip={_quote(prop.id)}];')
        lines.append('}')
    # Invisible layout constraints stack the panels without introducing a
    # conceptual relation. Graphviz packing can lose edge labels in some builds.
    lines += [
        f'{_quote("a:" + EX + "SemanticContract")} -> '
        f'{_quote("b:" + EX + "EvaluationState")} [style=invis, weight=100];',
        f'{_quote("b:" + EX + "AIModel")} -> '
        f'{_quote("c:" + EX + "FederatedLearningSession")} [style=invis, weight=100];',
        f'{_quote("b:" + EX + "NodeState")} -> '
        f'{_quote("c:" + EX + "FederatedLearningSession")} [style=invis, weight=100];',
    ]
    lines.append('}')
    return '\n'.join(lines) + '\n'


def dot_view(schema: Schema, *, simple: bool = False, module: str | None = None,
             monochrome: bool = False) -> str:
    if simple:
        return _simplified_panels(schema, monochrome)
    properties = list(schema.properties)
    selected = {node.id for node in schema.nodes.values()
                if node.kind in {"class", "expression"}
                and (module is None or node.module == module)}
    if module:
        properties = [prop for prop in properties if prop.module == module]
    selected.update(key for prop in properties for key in prop.domains + prop.ranges
                    if schema.nodes[key].kind in {"class", "expression"})
    # Expand expression operands and parent classes, including cross-module
    # context. Retain AND vs OR instead of inventing independent domains.
    while True:
        extra = {edge.target for edge in schema.edges if edge.source in selected
                 and edge.kind in {"union_member", "intersection_member", "subclass"}}
        if extra <= selected:
            break
        selected |= extra

    used_modules = {schema.nodes[key].module for key in selected} | {p.module for p in properties}
    lines = [
        'digraph ontology {',
        '  graph [rankdir=TB, bgcolor="white", margin=0, pad="0.20", nodesep="0.28",',
        '         ranksep="0.65", splines=polyline, outputorder=edgesfirst,',
        '         fontname="Helvetica", fontnames="svg", labelloc=b, labeljust=c];',
        '  node [shape=box, style="rounded,filled", color="#52606D",',
        '        fillcolor="white", fontcolor="#17212B", fontname="Helvetica",',
        '        fontsize=11, margin="0.10,0.07", penwidth=1.0];',
        '  edge [color="#64717D", fontcolor="#26323C", fontname="Helvetica",',
        '        fontsize=9, arrowsize=0.65, penwidth=0.8];',
        f'  label={_legend(False, used_modules, context=module is not None)};',
    ]
    attributes: dict[str, list[Property]] = defaultdict(list)
    helper_nodes: dict[str, tuple[str, str]] = {}
    helper_edges: list[tuple[str, str]] = []
    scope_cache: dict[tuple[str, str], str] = {}

    def scope(prop: Property, direction: str) -> str:
        key = (prop.id, direction)
        if key in scope_cache:
            return scope_cache[key]
        values = prop.domains if direction == "domain" else prop.ranges
        if len(values) == 1:
            identifier = values[0]
            selected.add(identifier)
        elif not values:
            identifier = f"diagram:undeclared:{prop.module}:{direction}"
            helper_nodes[identifier] = (f"{direction.title()}\nnot declared", prop.module)
        else:
            identifier = f"diagram:intersection:{prop.id}:{direction}"
            helper_nodes[identifier] = ("AND", prop.module)
            for value in values:
                selected.add(value)
                helper_edges.append((identifier, value))
        scope_cache[key] = identifier
        return identifier

    for prop in properties:
        if prop.kind == "datatype_property":
            attributes[scope(prop, "domain")].append(prop)
        elif prop.kind == "object_property" and (prop.domains or prop.ranges):
            scope(prop, "domain")
            scope(prop, "range")

    def class_node(node: Node) -> str:
        _, fill, _ = MODULES[node.module]
        context = module is not None and node.module != module
        if monochrome or context:
            fill = "#F5F5F5" if context else "#FFFFFF"
        extra = f', tooltip={_quote(node.id)}'
        if context:
            extra += ', style="rounded,dashed,filled"'
        if node.kind == "expression":
            members = [e.kind for e in schema.edges if e.source == node.id
                       and e.kind in {"union_member", "intersection_member"}]
            heading = "OR" if "union_member" in members else "AND"
        else:
            heading = node.qname
        rows = [f'<TR><TD BGCOLOR="{fill}" ALIGN="LEFT"><B>{_html(heading, 30)}</B>'
                + ('<BR/><FONT POINT-SIZE="8">class / individual (punning)</FONT>' if node.punned else '')
                + '</TD></TR>']
        for prop in attributes.get(node.id, []):
            text = f'{prop.qname}: {schema.constraints(prop.ranges)}'
            rows.append(f'<TR><TD ALIGN="LEFT" TOOLTIP={_quote(prop.id)}>'
                        f'<FONT POINT-SIZE="9">{_html(text)}</FONT></TD></TR>')
        table = '<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="5">' + ''.join(rows) + '</TABLE>'
        return f'  {_quote(node.id)} [label=<{table}>, fillcolor="{fill}"{extra}];'

    for identifier in sorted(selected):
        lines.append(class_node(schema.nodes[identifier]))
    for identifier, (label, _) in sorted(helper_nodes.items()):
        rows = [f'<TR><TD><I>{_html(label)}</I></TD></TR>']
        for prop in attributes.get(identifier, []):
            rows.append(f'<TR><TD ALIGN="LEFT" TOOLTIP={_quote(prop.id)}>'
                        f'<FONT POINT-SIZE="9">{_html(prop.qname + ": " + schema.constraints(prop.ranges))}'
                        '</FONT></TD></TR>')
        lines.append(f'  {_quote(identifier)} [style="dashed,filled", fillcolor="#F4F4F4", '
                     'label=<<TABLE BORDER="0" CELLBORDER="0" CELLPADDING="5">'
                     + ''.join(rows) + '</TABLE>>];')

    for prop in properties:
        if prop.kind != "object_property" or not (prop.domains or prop.ranges):
            continue
        source = scope(prop, "domain")
        target = scope(prop, "range")
        label = _wrap(prop.qname, 32)
        lines.append(f'  {_quote(source)} -> {_quote(target)} [label={_quote(label)}, '
                     f'tooltip={_quote(prop.id)}];')

    for edge in schema.edges:
        if edge.source not in selected or edge.target not in selected:
            continue
        if edge.kind == "subclass":
            lines.append(f'  {_quote(edge.target)} -> {_quote(edge.source)} '
                         '[dir=back, arrowtail=empty, style=dashed, color="#8A939B", weight=2];')
        elif edge.kind in {"union_member", "intersection_member"}:
            lines.append(f'  {_quote(edge.source)} -> {_quote(edge.target)} '
                         '[style=dotted, arrowhead=none, color="#8A939B"];')
    for source, target in helper_edges:
        lines.append(f'  {_quote(source)} -> {_quote(target)} '
                     '[style=dotted, arrowhead=none];')
    registries: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for prop in properties:
        if prop.kind == "annotation_property":
            registries['Annotation properties'].append((prop.qname, prop.id))
        if prop.kind == "object_property" and not (prop.domains or prop.ranges):
            registries['Object properties with undeclared domain and range'].append((prop.qname, prop.id))
        if prop.characteristics:
            registries['Property characteristics'].append(
                (prop.qname + ': ' + ', '.join(prop.characteristics), prop.id))
    prop_ids = {p.id for p in properties}
    for edge in schema.edges:
        if edge.kind in {"subproperty", "inverse", "equivalent_property", "equivalent_class", "disjoint"}:
            if module is None or edge.source in selected | prop_ids:
                registries['Additional schema axioms'].append(
                    (f'{schema.text(edge.source)} {edge.kind} {schema.text(edge.target)}', ''))
    for label, values in sorted(registries.items()):
        table = f'<TR><TD ALIGN="LEFT"><B>{_html(label)}</B></TD></TR>'
        for value, identifier in values:
            tooltip = f' TOOLTIP={_quote(identifier)}' if identifier else ''
            table += f'<TR><TD ALIGN="LEFT"{tooltip}><FONT POINT-SIZE="9">{_html(value)}</FONT></TD></TR>'
        lines.append(f'  {_quote("registry:" + label)} [style="filled", fillcolor="#F4F4F4", '
                     f'label=<<TABLE BORDER="0" CELLBORDER="0" CELLPADDING="5">{table}</TABLE>>];')
    lines.append('}')
    return '\n'.join(lines) + '\n'


def verify_complete_coverage(schema: Schema, source: str, svg_file: Path | None = None) -> dict:
    """Fail rather than publish a full-map claim when a term disappears."""
    classes = {node.id for node in schema.nodes.values() if node.kind == 'class'}
    properties = {prop.id for prop in schema.properties}
    declarations = {line.strip().split(' [', 1)[0] for line in source.splitlines()
                    if ' [label=' in line and ' -> ' not in line}
    missing_classes = {key for key in classes if _quote(key) not in declarations}
    missing_properties = {key for key in properties if _quote(key) not in source}
    if svg_file is not None:
        ns = {'s': 'http://www.w3.org/2000/svg'}
        svg = ET.parse(svg_file).getroot()
        titles = {group.findtext('s:title', namespaces=ns)
                  for group in svg.findall('.//s:g[@class="node"]', ns)}
        tooltips = {anchor.attrib.get('{http://www.w3.org/1999/xlink}title')
                    for anchor in svg.findall('.//s:a', ns)}
        missing_classes |= classes - titles
        missing_properties |= properties - tooltips
    if missing_classes or missing_properties:
        raise ValueError(f'Incomplete full diagram: classes={sorted(missing_classes)}, '
                         f'properties={sorted(missing_properties)}')
    return {'all_named_classes': True, 'all_declared_properties': True,
            'verified_classes': len(classes), 'verified_properties': len(properties),
            'checked': 'DOT and rendered SVG' if svg_file else 'DOT source only',
            'abox_instances_expanded': False}


def verify_edge_labels(svg_file: Path, expected: dict[str, str]) -> None:
    """Check visible labels, not just invisible tooltips or DOT declarations."""
    ns = {'s': 'http://www.w3.org/2000/svg'}
    root = ET.parse(svg_file).getroot()
    actual: dict[str, str] = {}
    for group in root.findall('.//s:g[@class="edge"]', ns):
        text = ''.join(''.join(element.itertext()) for element in group.findall('.//s:text', ns))
        for anchor in group.findall('.//s:a', ns):
            identifier = anchor.attrib.get('{http://www.w3.org/1999/xlink}title')
            if identifier:
                actual[identifier] = ''.join(text.split())
    missing = [key for key, text in expected.items() if actual.get(key) != ''.join(text.split())]
    if missing:
        raise ValueError(f'Missing or incorrect visible edge labels in {svg_file.name}: {missing}')


def render_graphviz(dot_file: Path, destination: Path, *, executable: str,
                    formats: tuple[str, ...] = ("svg", "pdf", "png"),
                    preview_dpi: int = 180, timeout: float = 120) -> dict:
    metrics: dict[str, object] = {}
    destination.parent.mkdir(parents=True, exist_ok=True)
    for format_ in formats:
        output = destination.with_suffix('.' + format_)
        command = [executable, '-T' + format_, str(dot_file), '-o', str(output)]
        if format_ == 'png':
            # Only PNG is size-limited. SVG/PDF keep their native, scalable size.
            command += [f'-Gdpi={preview_dpi}', '-Gsize=16,16']
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=timeout, check=False)
        if result.returncode:
            raise RuntimeError(f'Graphviz failed for {dot_file.name}: {result.stderr}')
        if result.stderr.strip():
            metrics.setdefault('warnings', []).append(result.stderr.strip())
        if not output.is_file() or not output.stat().st_size:
            raise RuntimeError(f'Empty Graphviz output: {output}')
        if format_ == 'svg':
            svg = ET.parse(output).getroot()
            metrics['width_pt'] = float(svg.attrib['width'].removesuffix('pt'))
            metrics['height_pt'] = float(svg.attrib['height'].removesuffix('pt'))
            texts = svg.findall('.//{http://www.w3.org/2000/svg}text')
            metrics['minimum_font_pt'] = min(float(t.attrib['font-size']) for t in texts)
            metrics['minimum_font_at_180mm_pt'] = (
                metrics['minimum_font_pt'] * (180 / 25.4 * 72) / metrics['width_pt']
            )
            metrics['minimum_font_fit_180x230mm_pt'] = metrics['minimum_font_pt'] * min(
                (180 / 25.4 * 72) / metrics['width_pt'],
                (230 / 25.4 * 72) / metrics['height_pt'],
            )
    return metrics


def export_data(schema: Schema, directory: Path) -> dict[str, object]:
    directory.mkdir(parents=True, exist_ok=True)
    data = schema.export()
    (directory / 'schema.json').write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    for name, rows in [('nodes', data['nodes']), ('relations', data['edges']),
                       ('properties', data['properties'])]:
        with (directory / (name + '.csv')).open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [])
            writer.writeheader()
            for row in rows:
                writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
                                 for key, value in row.items()})
    return data


def graphml(schema: Schema) -> str:
    namespace = 'http://graphml.graphdrawing.org/xmlns'
    ET.register_namespace('', namespace)
    ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root = ET.Element('{' + namespace + '}graphml', {
        '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation':
            namespace + ' http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd',
    })
    def tag(name: str) -> str:
        return '{' + namespace + '}' + name
    for key in ('iri', 'label', 'qname', 'kind', 'module', 'predicate', 'index'):
        ET.SubElement(root, tag('key'), {'id': key, 'for': 'all', 'attr.name': key, 'attr.type': 'string'})
    graph = ET.SubElement(root, tag('graph'), {'id': 'ontology-schema', 'edgedefault': 'directed'})
    identifiers = {key: 'n' + sha256(key.encode()).hexdigest()[:20] for key in schema.nodes}
    for node in sorted(schema.nodes.values(), key=lambda item: item.id):
        element = ET.SubElement(graph, tag('node'), {'id': identifiers[node.id]})
        for key, value in dict(iri=node.id, label=node.label, qname=node.qname,
                               kind=node.kind, module=node.module).items():
            ET.SubElement(element, tag('data'), {'key': key}).text = value
    for index, edge in enumerate(schema.edges):
        element = ET.SubElement(graph, tag('edge'), {'id': f'e{index}',
            'source': identifiers[edge.source], 'target': identifiers[edge.target]})
        for key, value in dict(kind=edge.kind, label=edge.kind, predicate=edge.predicate,
                               index=str(edge.index)).items():
            ET.SubElement(element, tag('data'), {'key': key}).text = value
    ET.indent(root)
    return ET.tostring(root, encoding='unicode', xml_declaration=True) + '\n'

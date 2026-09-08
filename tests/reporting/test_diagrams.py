"""Conceptual figures must not silently lose terms or change OWL semantics."""

from dataclasses import replace
from hashlib import sha256
import json
import shutil
import xml.etree.ElementTree as ET

import pytest
from rdflib import Graph, OWL, RDF, URIRef

from continuum_bench.diagrams.__main__ import main
from continuum_bench.diagrams.model import EX, MODULES, SKOLEM, extract_schema, simplified
from continuum_bench.diagrams.render import (
    dot_view, graphml, render_graphviz, verify_complete_coverage, verify_edge_labels,
)


@pytest.fixture
def schema(config):
    return extract_schema(config)


def test_inventory_covers_the_actual_runtime_schema(config, schema):
    source = Graph()
    for path in config.ontology_files:
        source.parse(config.resolve(path))
    expected = {str(term) for term in source.subjects(RDF.type, OWL.Class)
                if isinstance(term, URIRef) and not str(term).startswith(SKOLEM)}
    assert {n.id for n in schema.nodes.values() if n.kind == 'class'} == expected
    expected_properties = {str(term) for kind in (OWL.ObjectProperty, OWL.DatatypeProperty,
                                                OWL.AnnotationProperty)
                           for term in source.subjects(RDF.type, kind)}
    assert {p.id for p in schema.properties} == expected_properties
    assert schema.export()['counts'] == {
        'named_classes': 146, 'anonymous_expressions': 11, 'object_properties': 165,
        'datatype_properties': 98, 'annotation_properties': 14,
        'subclass_axioms': 70, 'source_triples': 7966,
    }
    assert len(schema.sources) == 14
    assert EX + 'RF-22' not in schema.nodes  # no expansion of the ABox
    assert schema.nodes[EX + 'UrbanZone'].punned
    assert schema.nodes[EX + 'DeploymentFragment'].module == 'deployment'
    assert {n.module for n in schema.nodes.values()} <= MODULES.keys()


def test_exports_are_deterministic_and_preserve_input_hashes(config, schema):
    other = extract_schema(config)
    assert schema.export() == other.export()
    assert dot_view(schema) == dot_view(other)
    assert graphml(schema) == graphml(other)
    for source in schema.sources:
        assert source['sha256'] == sha256((config.root / source['path']).read_bytes()).hexdigest()


def test_simplified_arrows_are_asserted_not_invented(schema):
    classes, properties = simplified(schema)
    assert len(classes) == 15
    assert len(properties) == 15
    for prop in properties:
        for key, kind in [(prop.domains[0], 'domain'), (prop.ranges[0], 'range')]:
            assert any(e.source == prop.id and e.target == key and e.kind == kind for e in schema.edges)
    source = dot_view(schema, simple=True)
    assert sum(' -> ' in line and 'tooltip="' + EX in line
               for line in source.splitlines()) == 15
    assert 'style=invis' in source  # explicitly non-semantic layout links
    assert 'hosted at' in source
    schema.properties = [p for p in schema.properties if p.id != EX + 'hasConsentRecord']
    with pytest.raises(ValueError, match='missing properties'):
        simplified(schema)


def test_union_and_intersection_are_not_conflated(config, tmp_path):
    path = tmp_path / 'schema.ttl'
    path.write_text('''
        @prefix ex: <http://example.org/smartcity#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        ex:A a owl:Class . ex:B a owl:Class . ex:C a owl:Class .
        ex:union a owl:ObjectProperty ; rdfs:domain [a owl:Class; owl:unionOf (ex:A ex:B)];
            rdfs:range ex:C .
        ex:multiple a owl:ObjectProperty ; rdfs:domain ex:A, ex:B; rdfs:range ex:C .
        ex:unknown a owl:ObjectProperty .
    ''', encoding='utf-8')
    schema = extract_schema(replace(config, ontology_files=(path,)))
    props = {p.id: p for p in schema.properties}
    assert schema.constraints(props[EX + 'union'].domains) == '(ex:A OR ex:B)'
    assert schema.constraints(props[EX + 'multiple'].domains) == 'ex:A AND ex:B'
    assert schema.constraints(props[EX + 'unknown'].domains) == 'not declared'
    source = dot_view(schema)
    assert 'diagram:intersection:' + EX + 'multiple:domain' in source
    assert '>OR<' in source
    assert 'owl:Thing' not in source
    assert verify_complete_coverage(schema, source)['verified_properties'] == 3


def test_unsupported_expression_fails_instead_of_inventing_a_label(config, tmp_path):
    path = tmp_path / 'restriction.ttl'
    path.write_text('''
        @prefix ex: <http://example.org/smartcity#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        ex:p a owl:ObjectProperty; rdfs:domain [a owl:Restriction; owl:onProperty ex:p].
    ''', encoding='utf-8')
    with pytest.raises(ValueError, match='Unsupported or ambiguous'):
        extract_schema(replace(config, ontology_files=(path,)))


def test_complete_coverage_guard_detects_removed_class_and_property(schema):
    source = dot_view(schema)
    coverage = verify_complete_coverage(schema, source)
    assert coverage['verified_classes'] == 146
    assert coverage['verified_properties'] == 277
    without_class = '\n'.join(line for line in source.splitlines()
                              if not line.startswith('  "' + EX + 'User" [label='))
    with pytest.raises(ValueError, match='Incomplete full diagram'):
        verify_complete_coverage(schema, without_class)
    with pytest.raises(ValueError, match='Incomplete full diagram'):
        verify_complete_coverage(schema, source.replace(EX + 'hasConsentRecord', 'removed-iri'))


def test_graphml_is_a_self_contained_graph_with_original_iris(schema):
    root = ET.fromstring(graphml(schema))
    ns = {'g': 'http://graphml.graphdrawing.org/xmlns'}
    nodes = root.findall('.//g:node', ns)
    edges = root.findall('.//g:edge', ns)
    assert len(nodes) == len(schema.nodes)
    assert len(edges) == len(schema.edges)
    ids = {node.attrib['id'] for node in nodes}
    assert len(ids) == len(nodes)
    assert {node.find('g:data[@key="iri"]', ns).text for node in nodes} == set(schema.nodes)
    assert all(edge.attrib['source'] in ids and edge.attrib['target'] in ids for edge in edges)
    assert any(edge.find('g:data[@key="kind"]', ns).text == 'union_member' for edge in edges)


def test_module_view_keeps_external_parent_classes_as_context(schema):
    source = dot_view(schema, module='wellbeing')
    assert '"http://www.w3.org/ns/sosa/Sensor" [label=' in source
    assert 'style="rounded,dashed,filled"' in source
    assert 'margin=0' in source  # SVG/PDF use the same figure bounding box


def test_sources_only_needs_no_external_process_and_does_not_modify_ontology(config, tmp_path, monkeypatch):
    before = {p: sha256(config.resolve(p).read_bytes()).hexdigest() for p in config.ontology_files}
    def forbidden(*args, **kwargs):
        raise AssertionError('An external process should not run in sources-only mode')
    monkeypatch.setattr('continuum_bench.diagrams.__main__.subprocess.run', forbidden)
    output = tmp_path / 'diagrams'
    assert main(['--config', str(config.root / 'configs/benchmark.toml'),
                 '--output', str(output), '--sources-only']) == 0
    manifest = json.loads((output / 'manifest.json').read_text())
    assert manifest['status'] == 'complete'
    assert manifest['rendered'] is False
    assert manifest['complete']['checked'] == 'DOT source only'
    assert len(list((output / 'sources/modules').glob('*.dot'))) == 9
    assert not (output / 'figures').exists()
    assert before == {p: sha256(config.resolve(p).read_bytes()).hexdigest() for p in config.ontology_files}


def test_cli_missing_graphviz_is_actionable_and_leaves_no_outputs(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr('continuum_bench.diagrams.__main__.shutil.which', lambda _: None)
    output = tmp_path / 'diagrams'
    assert main(['--output', str(output), '--no-atlas']) == 2
    assert 'Graphviz is required' in capsys.readouterr().err
    assert not output.exists()


def test_cli_rejects_mislabelled_release(schema, tmp_path, monkeypatch, capsys):
    schema.identity['revisions'] = ['outdated-release']
    monkeypatch.setattr('continuum_bench.diagrams.__main__.extract_schema', lambda _: schema)
    output = tmp_path / 'diagrams'
    assert main(['--output', str(output), '--sources-only']) == 2
    assert 'does not match the English project release' in capsys.readouterr().err
    assert not output.exists()


@pytest.mark.parametrize('value', ['0', '-1', 'nan', 'inf'])
def test_cli_rejects_invalid_timeout(value):
    with pytest.raises(SystemExit) as error:
        main(['--timeout', value])
    assert error.value.code == 2


@pytest.mark.skipif(not shutil.which('dot'), reason='Optional Graphviz renderer is not installed')
def test_rendered_svg_contains_every_term_and_visible_edge_label(schema, tmp_path):
    for simple in (True, False):
        source = dot_view(schema, simple=simple)
        path = tmp_path / ('simplified.dot' if simple else 'complete.dot')
        path.write_text(source, encoding='utf-8')
        metrics = render_graphviz(path, path.with_suffix(''), executable=shutil.which('dot'), formats=('svg',))
        assert metrics['minimum_font_fit_180x230mm_pt'] > 0
        svg = path.with_suffix('.svg')
        properties = simplified(schema)[1] if simple else schema.properties
        expected = {p.id: p.label if simple else p.qname for p in properties
                    if p.kind == 'object_property' and (p.domains or p.ranges)}
        verify_edge_labels(svg, expected)
        if not simple:
            assert verify_complete_coverage(schema, source, svg)['checked'] == 'DOT and rendered SVG'
        # Regression: a tooltip is not evidence that its label was rendered.
        tree = ET.parse(svg)
        ns = {'s': 'http://www.w3.org/2000/svg'}
        for edge in tree.findall('.//s:g[@class="edge"]', ns):
            for parent in edge.iter():
                for child in list(parent):
                    if child.tag == '{http://www.w3.org/2000/svg}text':
                        parent.remove(child)
        tree.write(svg)
        with pytest.raises(ValueError, match='visible edge labels'):
            verify_edge_labels(svg, expected)


def test_atlas_can_be_generated_when_optional_reportlab_is_installed(schema, tmp_path):
    pytest.importorskip('reportlab')
    from continuum_bench.diagrams.atlas import build_atlas
    from continuum_bench.specification import ONTOLOGY_REVISION, ONTOLOGY_VERSION
    data = schema.export()
    data.update(modules=MODULES, ontology_revision=ONTOLOGY_REVISION, ontology_version=ONTOLOGY_VERSION)
    destination = tmp_path / 'atlas.pdf'
    assert build_atlas(data, destination) >= 10
    assert destination.read_bytes().startswith(b'%PDF-')

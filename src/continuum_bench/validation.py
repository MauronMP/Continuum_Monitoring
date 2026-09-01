from __future__ import annotations

from typing import Any

from rdflib import OWL, RDF
from rdflib.compare import isomorphic

from .config import BenchmarkConfig
from .ontology import (
    contradiction_count, datatype_range_errors, load_graph, validate_shacl,
)
from .partitioning import build_fragments, privacy_violations
from .queries import check_expectation, execute_query, load_catalog
from .reasoners import materialize
from .specification import acceptance_status, validate_release_contract
from .synthetic import add_synthetic_data
from .topology import load_topology


def validate_project(config: BenchmarkConfig) -> dict[str, Any]:
    ontology_paths = [config.resolve(path) for path in config.ontology_files]
    shape_paths = [config.resolve(path) for path in config.shape_files]
    graph = load_graph(ontology_paths)
    range_errors = datatype_range_errors(graph)
    specs = load_catalog(config.resolve(config.query_catalog), config.root)
    release_contract = validate_release_contract(graph, specs)

    expectation_errors: list[str] = []
    query_measurements = []
    for spec in specs:
        measurement = execute_query(graph, spec)
        query_measurements.append(measurement)
        error = check_expectation(spec, measurement)
        if error:
            expectation_errors.append(error)

    reasoner_results: dict[str, Any] = {}
    for reasoner in config.reasoners:
        measurement = materialize(graph, reasoner)
        # Checking only asserted data missed the RDFS True == 1 regression.
        # Reference cardinalities for reports may legitimately grow under
        # entailment, but a violation query must still return zero rows.
        inferred_expectation_errors = [
            error
            for spec in specs
            if spec.kind == "violation"
            and (
                error := check_expectation(
                    spec, execute_query(measurement.graph, spec)
                )
            )
        ]
        reasoner_results[reasoner] = {
            "duration_ms": measurement.duration_ms,
            "input_triples": measurement.input_triples,
            "output_triples": measurement.output_triples,
            "inferred_triples": measurement.inferred_triples,
            "owl_nothing_instances": contradiction_count(measurement.graph),
            "datatype_range_errors": datatype_range_errors(measurement.graph),
            "violation_query_errors": inferred_expectation_errors,
        }

    conforms, shacl_report = validate_shacl(graph, shape_paths)
    distribution_users = min(config.scale_users, default=1)
    topology = load_topology(
        config.resolve(config.topology_file),
        "docker",
    )
    fragments = build_fragments(
        config,
        distribution_users,
        topology=topology,
    )
    expected_distributed = load_graph(ontology_paths)
    add_synthetic_data(
        expected_distributed,
        distribution_users,
        config.seed,
    )
    distribution_union_matches = isomorphic(
        fragments.union(),
        expected_distributed,
    )
    distribution_privacy_errors = {
        role: privacy_violations(
            fragment,
            role,
            fragments.sensitive_resources,
            authority=topology.node(role).authority,
        )
        for role, fragment in fragments.graphs.items()
        if not topology.node(role).authority
    }
    profile_graph = load_graph(
        {
            config.root / profile
            for profile in fragments.placement_profiles.values()
        }
    )
    known_ontologies = set(graph.subjects(RDF.type, OWL.Ontology)) | set(
        profile_graph.subjects(RDF.type, OWL.Ontology)
    )
    unresolved_profile_imports = sorted(
        {
            str(imported)
            for imported in profile_graph.objects(None, OWL.imports)
            if imported not in known_ontologies
        }
    )
    acceptance = acceptance_status(specs, query_measurements)
    return {
        "ok": (
            not expectation_errors
            and not range_errors
            and release_contract["ok"]
            and conforms
            and distribution_union_matches
            and not any(distribution_privacy_errors.values())
            and not unresolved_profile_imports
            and all(
                item["owl_nothing_instances"] == 0
                and not item["datatype_range_errors"]
                and not item["violation_query_errors"]
                for item in reasoner_results.values()
            )
        ),
        "ontology_files": [str(path) for path in ontology_paths],
        "triples": len(graph),
        "query_count": len(specs),
        "topology": topology.public(),
        "datatype_range_errors": range_errors,
        "owl_dl_consistency": {
            "status": "not_checked",
            "check_command": "python3 tools/check_owl_consistency.py --require-dl-profile",
            "interpretation": (
                "Datatype guards, SHACL and zero owl:Nothing instances do not "
                "establish OWL consistency. Run the separate HermiT check."
            ),
        },
        "query_expectation_errors": expectation_errors,
        "release_contract": release_contract,
        "scientific_acceptance": acceptance,
        "shacl_conforms": conforms,
        "shacl_report": shacl_report,
        "distribution": {
            "synthetic_users": distribution_users,
            "union_matches_monolith": distribution_union_matches,
            "privacy_errors": distribution_privacy_errors,
            "substrate_triples_by_role": (
                fragments.substrate_triples_by_role
            ),
            "placement_profiles": fragments.placement_profiles,
            "profile_triples": len(profile_graph),
            "unresolved_profile_imports": unresolved_profile_imports,
            "storage_replication_factor": (
                sum(len(item) for item in fragments.graphs.values())
                / len(expected_distributed)
                if expected_distributed
                else 0.0
            ),
        },
        "reasoners": reasoner_results,
    }

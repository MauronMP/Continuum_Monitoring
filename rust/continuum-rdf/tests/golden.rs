use continuum_rdf::query::store_from_graph;
use continuum_rdf::{execute_query, graph_digest, materialize, parse_ntriples};
use serde::Deserialize;
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Deserialize)]
struct Expected {
    input_graph_digest: String,
    input_triples: usize,
    strict_rdf_reasoned_triples: usize,
    strict_rdf_closure_digest: String,
}

#[derive(Deserialize)]
struct Catalog {
    queries: Vec<QueryEntry>,
}

#[derive(Deserialize)]
struct QueryEntry {
    id: String,
    path: PathBuf,
}

#[derive(Deserialize)]
struct QueryExpected {
    query_id: String,
    result_count: usize,
    ask_result: Option<bool>,
    result_digest: String,
}

fn repository_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..")
}

#[test]
fn rust_matches_python_golden_fixtures() {
    let root = repository_root();
    let catalog: Catalog =
        serde_json::from_slice(&fs::read(root.join("queries/manifest.json")).unwrap()).unwrap();
    for users in [1, 10, 50] {
        let case = root.join(format!("tests/fixtures/golden-rdfs/users-{users}"));
        let expected: Expected =
            serde_json::from_slice(&fs::read(case.join("expected.json")).unwrap()).unwrap();
        let query_expected: HashMap<String, QueryExpected> =
            serde_json::from_slice::<Vec<QueryExpected>>(
                &fs::read(case.join("query-results.json")).unwrap(),
            )
            .unwrap()
            .into_iter()
            .map(|item| (item.query_id.clone(), item))
            .collect();
        let mut graph = parse_ntriples(&fs::read(case.join("input.nt")).unwrap()).unwrap();
        assert_eq!(graph.len(), expected.input_triples);
        assert_eq!(graph_digest(&graph), expected.input_graph_digest);
        materialize(&mut graph);
        assert_eq!(graph.len(), expected.strict_rdf_reasoned_triples);
        assert_eq!(graph_digest(&graph), expected.strict_rdf_closure_digest);
        let store = store_from_graph(&graph).unwrap();
        for query in &catalog.queries {
            let outcome =
                execute_query(&store, &fs::read_to_string(root.join(&query.path)).unwrap())
                    .unwrap_or_else(|error| panic!("{} failed: {error}", query.id));
            let reference = &query_expected[&query.id];
            assert_eq!(outcome.result_count, reference.result_count, "{}", query.id);
            assert_eq!(outcome.ask_result, reference.ask_result, "{}", query.id);
            // SPARQL permits implementation-dependent precision for decimal
            // division. BASE-Q33 uses AVG(decimal), so cardinality is the
            // cross-engine contract for that query.
            if query.id != "BASE-Q33" {
                assert_eq!(
                    outcome.result_digest, reference.result_digest,
                    "{}",
                    query.id
                );
            }
        }
    }
}

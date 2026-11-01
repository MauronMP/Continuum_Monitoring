use crate::Graph;
use crate::canonical::sha256_hex;
use anyhow::{Context, Result, bail};
use oxigraph::sparql::{QueryResults, SparqlEvaluator};
use oxigraph::store::Store;
use oxrdf::{GraphName, Quad, Term};
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;
use std::time::Instant;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueryOutcome {
    pub duration_ms: f64,
    pub result_count: usize,
    pub ask_result: Option<bool>,
    pub result_digest: String,
    pub result_keys: Vec<String>,
}

pub fn store_from_graph(graph: &Graph) -> Result<Store> {
    let store = Store::new()?;
    for item in graph {
        store.insert(&Quad::new(
            item.subject.clone(),
            item.predicate.clone(),
            item.object.clone(),
            GraphName::DefaultGraph,
        ))?;
    }
    Ok(store)
}

fn canonical_term(term: Option<&Term>, group_concat: bool) -> String {
    let Some(term) = term else {
        return String::new();
    };
    if group_concat
        && let Term::Literal(literal) = term
        && literal.value().contains(", ")
    {
        let mut values: Vec<&str> = literal.value().split(", ").collect();
        values.sort_unstable();
        let lexical = values.join(", ");
        if let Some(language) = literal.language() {
            return format!("{lexical:?}@{language}");
        }
        if literal.datatype().as_str() == "http://www.w3.org/2001/XMLSchema#string" {
            return format!("{lexical:?}");
        }
        return format!("{lexical:?}^^<{}>", literal.datatype());
    }
    if let Term::Literal(literal) = term {
        let datatype = literal.datatype().as_str();
        let lexical = literal.value();
        if datatype == "http://www.w3.org/2001/XMLSchema#dateTime"
            && let Some(prefix) = lexical.strip_suffix('Z')
        {
            return format!("\"{prefix}+00:00\"^^<{datatype}>");
        }
        let decimal = datatype == "http://www.w3.org/2001/XMLSchema#decimal";
        if decimal && !lexical.contains(['.', 'e', 'E']) {
            return format!("\"{lexical}.0\"^^<{datatype}>");
        }
    }
    term.to_string()
}

pub fn execute_query(store: &Store, query: &str) -> Result<QueryOutcome> {
    let started = Instant::now();
    let result = SparqlEvaluator::new()
        .parse_query(query)
        .context("invalid SPARQL query")?
        .on_store(store)
        .execute()
        .context("SPARQL execution failed")?;
    match result {
        QueryResults::Boolean(value) => {
            let payload = format!("ASK:{value}");
            Ok(QueryOutcome {
                duration_ms: started.elapsed().as_secs_f64() * 1_000.0,
                result_count: usize::from(value),
                ask_result: Some(value),
                result_digest: sha256_hex(payload.as_bytes()),
                result_keys: if value { vec!["true".into()] } else { vec![] },
            })
        }
        QueryResults::Solutions(solutions) => {
            let variables: Vec<String> = solutions
                .variables()
                .iter()
                .map(|variable| variable.as_str().to_owned())
                .collect();
            let group_concat = query.to_ascii_uppercase().contains("GROUP_CONCAT");
            let mut keys = BTreeSet::new();
            for row in solutions {
                let row = row?;
                let values: Vec<String> = (0..variables.len())
                    .map(|index| canonical_term(row.get(index), group_concat))
                    .collect();
                let canonical = variables
                    .iter()
                    .chain(std::iter::once(&"\u{1e}".to_owned()))
                    .chain(values.iter())
                    .cloned()
                    .collect::<Vec<_>>()
                    .join("\u{1f}");
                if std::env::var_os("CONTINUUM_DEBUG_QUERY_ROWS").is_some() {
                    eprintln!("{}", serde_json::to_string(&values)?);
                }
                keys.insert(sha256_hex(canonical.as_bytes()));
            }
            let result_keys: Vec<String> = keys.into_iter().collect();
            Ok(QueryOutcome {
                duration_ms: started.elapsed().as_secs_f64() * 1_000.0,
                result_count: result_keys.len(),
                ask_result: None,
                result_digest: sha256_hex(result_keys.join("\n").as_bytes()),
                result_keys,
            })
        }
        QueryResults::Graph(_) => {
            bail!("CONSTRUCT/DESCRIBE queries are not part of the benchmark catalog")
        }
    }
}

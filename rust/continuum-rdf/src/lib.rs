//! Deterministic RDF/RDFS data plane used by the continuum benchmark.

pub mod canonical;
pub mod partition;
pub mod query;
pub mod rdfs;
pub mod synthetic;

pub use canonical::{Graph, canonical_ntriples, graph_digest, parse_ntriples};
pub use partition::partition_graph;
pub use query::{QueryOutcome, execute_query};
pub use rdfs::{ReasoningReport, materialize};
pub use synthetic::{add_synthetic_abox, synthetic_triple_count};

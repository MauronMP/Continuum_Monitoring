use crate::Graph;
use sha2::{Digest, Sha256};

/// Replicates schema triples and deterministically assigns each synthetic
/// ABox subject to one participant. Returns complete replicas when requested.
#[must_use]
pub fn partition_graph(graph: &Graph, participants: usize, replicated: bool) -> Vec<Graph> {
    assert!(participants > 0, "at least one participant is required");
    if replicated {
        return vec![graph.clone(); participants];
    }
    let mut output = vec![Graph::new(); participants];
    for triple in graph {
        let subject = triple.subject.to_string();
        let shared_node = subject.contains("synthetic:edge-")
            || subject.contains("synthetic:node-state-")
            || subject.contains("synthetic:trust-assessment-");
        if !triple.to_string().contains("urn:continuum:synthetic:") || shared_node {
            for fragment in &mut output {
                fragment.insert(triple.clone());
            }
        } else {
            let index = subject
                .trim_end_matches('>')
                .rsplit('-')
                .next()
                .and_then(|value| value.parse::<usize>().ok());
            let owner = index.map_or_else(
                || {
                    let digest = Sha256::digest(subject.as_bytes());
                    u64::from_be_bytes(digest[..8].try_into().expect("digest prefix")) as usize
                        % participants
                },
                |value| value % participants,
            );
            output[owner].insert(triple.clone());
        }
    }
    output
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::parse_ntriples;

    #[test]
    fn schema_is_replicated_and_abox_has_one_owner() {
        let graph = parse_ntriples(
            b"<urn:schema> <urn:p> <urn:o> .\n<urn:continuum:synthetic:user-1> <urn:p> <urn:o> .\n",
        )
        .unwrap();
        let parts = partition_graph(&graph, 2, false);
        assert!(parts.iter().all(|part| {
            part.iter()
                .any(|triple| triple.subject.to_string() == "<urn:schema>")
        }));
        assert_eq!(
            parts
                .iter()
                .filter(|part| part
                    .iter()
                    .any(|triple| triple.subject.to_string().contains("synthetic")))
                .count(),
            1
        );
    }
}

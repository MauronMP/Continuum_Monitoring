use anyhow::{Context, Result};
use oxrdf::Triple;
use oxrdfio::{RdfFormat, RdfParser};
use sha2::{Digest, Sha256};
use std::collections::HashSet;

pub type Graph = HashSet<Triple>;

pub fn parse_ntriples(bytes: &[u8]) -> Result<Graph> {
    RdfParser::from_format(RdfFormat::NTriples)
        .for_slice(bytes)
        .map(|result| result.map(|quad| Triple::new(quad.subject, quad.predicate, quad.object)))
        .collect::<Result<HashSet<_>, _>>()
        .context("invalid N-Triples input")
}

#[must_use]
pub fn canonical_ntriples(graph: &Graph) -> Vec<u8> {
    let mut lines: Vec<String> = graph.iter().map(|triple| format!("{triple} .")).collect();
    lines.sort_unstable();
    let mut output = lines.join("\n").into_bytes();
    if !output.is_empty() {
        output.push(b'\n');
    }
    output
}

#[must_use]
pub fn sha256_hex(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

#[must_use]
pub fn graph_digest(graph: &Graph) -> String {
    sha256_hex(&canonical_ntriples(graph))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonicalization_is_order_independent() {
        let first =
            parse_ntriples(b"<urn:b> <urn:p> <urn:o> .\n<urn:a> <urn:p> <urn:o> .\n").unwrap();
        let second =
            parse_ntriples(b"<urn:a> <urn:p> <urn:o> .\n<urn:b> <urn:p> <urn:o> .\n").unwrap();
        assert_eq!(canonical_ntriples(&first), canonical_ntriples(&second));
        assert_eq!(graph_digest(&first), graph_digest(&second));
    }
}

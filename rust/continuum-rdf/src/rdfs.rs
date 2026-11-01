use crate::Graph;
use oxrdf::{Literal, NamedNode, NamedOrBlankNode, Term, Triple};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::time::Instant;

const RDF_TYPE: &str = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type";
const RDF_PROPERTY: &str = "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property";
const RDFS_RESOURCE: &str = "http://www.w3.org/2000/01/rdf-schema#Resource";
const RDFS_CLASS: &str = "http://www.w3.org/2000/01/rdf-schema#Class";
const RDFS_LITERAL: &str = "http://www.w3.org/2000/01/rdf-schema#Literal";
const RDFS_DATATYPE: &str = "http://www.w3.org/2000/01/rdf-schema#Datatype";
const RDFS_DOMAIN: &str = "http://www.w3.org/2000/01/rdf-schema#domain";
const RDFS_RANGE: &str = "http://www.w3.org/2000/01/rdf-schema#range";
const RDFS_SUBCLASS: &str = "http://www.w3.org/2000/01/rdf-schema#subClassOf";
const RDFS_SUBPROPERTY: &str = "http://www.w3.org/2000/01/rdf-schema#subPropertyOf";
const RDFS_MEMBER: &str = "http://www.w3.org/2000/01/rdf-schema#member";
const RDFS_CONTAINER_MEMBERSHIP: &str =
    "http://www.w3.org/2000/01/rdf-schema#ContainerMembershipProperty";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReasoningReport {
    pub triples_before_reasoning: usize,
    pub triples_after_reasoning: usize,
    pub inferred_triples: usize,
    pub reasoning_seconds: f64,
    pub cycles: usize,
}

fn nn(value: &str) -> NamedNode {
    NamedNode::new_unchecked(value)
}

fn subject(term: &Term) -> Option<NamedOrBlankNode> {
    match term {
        Term::NamedNode(node) => Some(NamedOrBlankNode::NamedNode(node.clone())),
        Term::BlankNode(node) => Some(NamedOrBlankNode::BlankNode(node.clone())),
        Term::Literal(_) => None,
    }
}

fn named_or_blank(term: &Term) -> Option<NamedOrBlankNode> {
    match term {
        Term::NamedNode(node) => Some(NamedOrBlankNode::NamedNode(node.clone())),
        Term::BlankNode(node) => Some(NamedOrBlankNode::BlankNode(node.clone())),
        Term::Literal(_) => None,
    }
}

fn triple(s: NamedOrBlankNode, p: NamedNode, o: Term) -> Triple {
    Triple::new(s, p, o)
}

fn matching<'a>(graph: &'a Graph, predicate: &str) -> impl Iterator<Item = &'a Triple> {
    graph
        .iter()
        .filter(move |item| item.predicate.as_str() == predicate)
}

fn numeric_value(literal: &Literal) -> Option<String> {
    let datatype = literal.datatype().as_str();
    let numeric = matches!(
        datatype,
        "http://www.w3.org/2001/XMLSchema#decimal"
            | "http://www.w3.org/2001/XMLSchema#double"
            | "http://www.w3.org/2001/XMLSchema#float"
            | "http://www.w3.org/2001/XMLSchema#integer"
            | "http://www.w3.org/2001/XMLSchema#int"
            | "http://www.w3.org/2001/XMLSchema#long"
            | "http://www.w3.org/2001/XMLSchema#short"
            | "http://www.w3.org/2001/XMLSchema#nonNegativeInteger"
            | "http://www.w3.org/2001/XMLSchema#positiveInteger"
            | "http://www.w3.org/2001/XMLSchema#nonPositiveInteger"
            | "http://www.w3.org/2001/XMLSchema#negativeInteger"
    );
    numeric.then(|| {
        literal.value().parse::<f64>().ok().map_or_else(
            || literal.value().to_owned(),
            |value| format!("{value:.15e}"),
        )
    })
}

fn literal_substitutions(graph: &Graph) -> HashSet<Triple> {
    let mut groups: HashMap<String, Vec<Literal>> = HashMap::new();
    for item in graph {
        if let Term::Literal(literal) = &item.object
            && let Some(value) = numeric_value(literal)
        {
            groups.entry(value).or_default().push(literal.clone());
        }
    }
    let mut additions = HashSet::new();
    for literals in groups.values() {
        if literals.len() < 2 {
            continue;
        }
        for item in graph {
            let Term::Literal(current) = &item.object else {
                continue;
            };
            if literals.contains(current) {
                for replacement in literals {
                    additions.insert(triple(
                        item.subject.clone(),
                        item.predicate.clone(),
                        Term::Literal(replacement.clone()),
                    ));
                }
            }
        }
    }
    additions
}

/// Materializes the same non-axiomatic RDFS rules used by the former Python
/// reference. The fixed-point algorithm favors clarity and determinism; the
/// benchmark records its cost explicitly.
#[allow(clippy::collapsible_if)]
pub fn materialize(graph: &mut Graph) -> ReasoningReport {
    let before = graph.len();
    let started = Instant::now();
    graph.extend(literal_substitutions(graph));
    let initial = graph.clone();
    for item in &initial {
        graph.insert(triple(
            item.subject.clone(),
            nn(RDF_TYPE),
            nn(RDFS_RESOURCE).into(),
        ));
        if let Some(s) = subject(&item.object) {
            graph.insert(triple(s, nn(RDF_TYPE), nn(RDFS_RESOURCE).into()));
        }
    }

    let mut cycles = 0;
    loop {
        cycles += 1;
        let snapshot = graph.clone();
        let mut additions = HashSet::new();
        for item in &snapshot {
            additions.insert(triple(
                NamedOrBlankNode::NamedNode(item.predicate.clone()),
                nn(RDF_TYPE),
                nn(RDF_PROPERTY).into(),
            ));

            if item.predicate.as_str() == RDFS_DOMAIN {
                if let NamedOrBlankNode::NamedNode(property) = &item.subject {
                    for statement in snapshot
                        .iter()
                        .filter(|candidate| candidate.predicate == *property)
                    {
                        additions.insert(triple(
                            statement.subject.clone(),
                            nn(RDF_TYPE),
                            item.object.clone(),
                        ));
                    }
                }
            }
            if item.predicate.as_str() == RDFS_RANGE {
                if let NamedOrBlankNode::NamedNode(property) = &item.subject {
                    for statement in snapshot
                        .iter()
                        .filter(|candidate| candidate.predicate == *property)
                    {
                        if let Some(object) = subject(&statement.object) {
                            additions.insert(triple(object, nn(RDF_TYPE), item.object.clone()));
                        }
                    }
                }
            }
            if item.predicate.as_str() == RDFS_SUBPROPERTY {
                if let Term::NamedNode(parent) = &item.object {
                    for upper in matching(&snapshot, RDFS_SUBPROPERTY).filter(|candidate| {
                        candidate.subject == NamedOrBlankNode::NamedNode(parent.clone())
                    }) {
                        additions.insert(triple(
                            item.subject.clone(),
                            nn(RDFS_SUBPROPERTY),
                            upper.object.clone(),
                        ));
                    }
                    if let NamedOrBlankNode::NamedNode(child) = &item.subject {
                        for statement in snapshot
                            .iter()
                            .filter(|candidate| candidate.predicate == *child)
                        {
                            additions.insert(triple(
                                statement.subject.clone(),
                                parent.clone(),
                                statement.object.clone(),
                            ));
                        }
                    }
                }
            }
            if item.predicate.as_str() == RDF_TYPE
                && item.object == Term::NamedNode(nn(RDF_PROPERTY))
            {
                if let NamedOrBlankNode::NamedNode(property) = &item.subject {
                    additions.insert(triple(
                        item.subject.clone(),
                        nn(RDFS_SUBPROPERTY),
                        property.clone().into(),
                    ));
                }
            }
            if item.predicate.as_str() == RDF_TYPE && item.object == Term::NamedNode(nn(RDFS_CLASS))
            {
                additions.insert(triple(
                    item.subject.clone(),
                    nn(RDFS_SUBCLASS),
                    nn(RDFS_RESOURCE).into(),
                ));
                if let Some(class) = subject(&Term::from(item.subject.clone())) {
                    additions.insert(triple(
                        item.subject.clone(),
                        nn(RDFS_SUBCLASS),
                        Term::from(class),
                    ));
                }
            }
            if item.predicate.as_str() == RDFS_SUBCLASS {
                if let Some(child) = named_or_blank(&Term::from(item.subject.clone())) {
                    for instance in matching(&snapshot, RDF_TYPE)
                        .filter(|candidate| candidate.object == Term::from(child.clone()))
                    {
                        additions.insert(triple(
                            instance.subject.clone(),
                            nn(RDF_TYPE),
                            item.object.clone(),
                        ));
                    }
                }
                if let Some(parent) = subject(&item.object) {
                    for upper in matching(&snapshot, RDFS_SUBCLASS)
                        .filter(|candidate| candidate.subject == parent)
                    {
                        additions.insert(triple(
                            item.subject.clone(),
                            nn(RDFS_SUBCLASS),
                            upper.object.clone(),
                        ));
                    }
                }
            }
            if item.predicate.as_str() == RDF_TYPE
                && item.object == Term::NamedNode(nn(RDFS_CONTAINER_MEMBERSHIP))
            {
                additions.insert(triple(
                    item.subject.clone(),
                    nn(RDFS_SUBPROPERTY),
                    nn(RDFS_MEMBER).into(),
                ));
            }
            if item.predicate.as_str() == RDF_TYPE
                && item.object == Term::NamedNode(nn(RDFS_DATATYPE))
            {
                additions.insert(triple(
                    item.subject.clone(),
                    nn(RDFS_SUBCLASS),
                    nn(RDFS_LITERAL).into(),
                ));
            }
        }
        let old_len = graph.len();
        graph.extend(additions);
        if graph.len() == old_len {
            break;
        }
    }
    let after = graph.len();
    ReasoningReport {
        triples_before_reasoning: before,
        triples_after_reasoning: after,
        inferred_triples: after - before,
        reasoning_seconds: started.elapsed().as_secs_f64(),
        cycles,
    }
}

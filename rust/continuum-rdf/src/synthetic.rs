use crate::Graph;
use anyhow::Result;
use oxrdf::{Literal, NamedNode, NamedOrBlankNode, Term, Triple};

const COMON: &str = "http://example.org/monitoringcontinuum#";
const SYN: &str = "urn:continuum:synthetic:";
const RDF_TYPE: &str = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type";
const XSD: &str = "http://www.w3.org/2001/XMLSchema#";
const SOSA_RESULT_TIME: &str = "http://www.w3.org/ns/sosa/resultTime";
const SAREF_ATTACHED: &str = "https://saref.etsi.org/saref4ehaw/isAttachedTo";

#[must_use]
pub fn synthetic_triple_count(users: usize) -> usize {
    users * 70 + users.div_ceil(100) * 21
}

fn iri(value: impl Into<String>) -> NamedNode {
    NamedNode::new_unchecked(value.into())
}
fn c(local: &str) -> NamedNode {
    iri(format!("{COMON}{local}"))
}
fn s(local: impl AsRef<str>) -> NamedNode {
    iri(format!("{SYN}{}", local.as_ref()))
}
fn typed(value: impl Into<String>, datatype: &str) -> Literal {
    Literal::new_typed_literal(value, iri(format!("{XSD}{datatype}")))
}
fn add(graph: &mut Graph, subject: &NamedNode, predicate: NamedNode, object: impl Into<Term>) {
    graph.insert(Triple::new(
        NamedOrBlankNode::NamedNode(subject.clone()),
        predicate,
        object,
    ));
}
fn add_c(graph: &mut Graph, subject: &NamedNode, predicate: &str, object: &str) {
    add(graph, subject, c(predicate), c(object));
}
fn add_i(graph: &mut Graph, subject: &NamedNode, predicate: &str, object: &NamedNode) {
    add(graph, subject, c(predicate), object.clone());
}
fn add_type(graph: &mut Graph, subject: &NamedNode, class: &str) {
    add(graph, subject, iri(RDF_TYPE), c(class));
}
fn time(index: usize) -> Literal {
    // The benchmark only needs deterministic, ordered timestamps. Keeping
    // them in January avoids calendar rollover for the configured scenarios.
    let day = 1 + index / 86_400;
    let second = index % 86_400;
    let hour = second / 3_600;
    let minute = second % 3_600 / 60;
    let second = second % 60;
    typed(
        format!("2026-01-{day:02}T{hour:02}:{minute:02}:{second:02}Z"),
        "dateTime",
    )
}
fn random_unit(state: &mut u64) -> f64 {
    *state = state.wrapping_add(0x9E37_79B9_7F4A_7C15);
    let mut z = *state;
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    ((z ^ (z >> 31)) >> 11) as f64 / ((1_u64 << 53) as f64)
}

/// Adds a deterministic monitoring ABox. Every entity contributes semantic
/// relationships used by the real query catalog; no padding triples are used.
pub fn add_synthetic_abox(graph: &mut Graph, users: usize, seed: u64) -> Result<usize> {
    let before = graph.len();
    let mut random_state = seed;
    let mut nodes = Vec::new();
    let mut node_states = Vec::new();
    for index in 0..users.div_ceil(100) {
        let node = s(format!("edge-{index:05}"));
        let state = s(format!("node-state-{index:05}"));
        let trust = s(format!("trust-assessment-{index:05}"));
        nodes.push(node.clone());
        node_states.push(state.clone());
        add_type(graph, &node, "EdgeNode");
        add(graph, &node, c("hasElasticity"), typed("false", "boolean"));
        add_i(graph, &node, "hasNodeState", &state);
        add_c(graph, &node, "governedBy", "P-NODE-01");
        add_type(graph, &state, "NodeState");
        add_c(graph, &state, "hasAvailability", "Available");
        add_c(graph, &state, "hasCommunication", "StableComm");
        add_c(graph, &state, "hasWorkload", "MediumWorkload");
        add_c(graph, &state, "hasResidualCapacity", "MediumResidual");
        add_c(graph, &state, "hasOperationalStatus", "Operational");
        add(
            graph,
            &state,
            c("hasTrustScore"),
            typed(
                format!("{:.4}", 0.80 + random_unit(&mut random_state) * 0.19),
                "decimal",
            ),
        );
        add_i(graph, &state, "hasTrustAssessment", &trust);
        add(
            graph,
            &state,
            c("resourceUsagePercent"),
            typed("50.0", "decimal"),
        );
        add(graph, &state, c("queuedRequests"), typed("2", "integer"));
        add(graph, &state, c("validFrom"), time(index));
        add_type(graph, &trust, "TrustAssessment");
        add_i(graph, &trust, "trustAssessmentForState", &state);
        add(graph, &trust, c("hasTrustScore"), typed("0.90", "decimal"));
        add(
            graph,
            &trust,
            c("trustRuleVersion"),
            Literal::new_simple_literal("SYN-TRUST-v1"),
        );
        add(graph, &trust, c("trustWindowStart"), time(index));
        add(graph, &trust, c("trustWindowEnd"), time(index + 1));
    }
    let ranges = ["RangeLocalOnly", "RangeCommunityAgg", "RangeGlobalAgg"];
    for index in 0..users {
        let user = s(format!("user-{index:08}"));
        let wearable = s(format!("wearable-{index:08}"));
        let device_state = s(format!("device-state-{index:08}"));
        let user_state = s(format!("user-state-{index:08}"));
        let observation = s(format!("observation-{index:08}"));
        let parametrized = s(format!("parametrized-data-{index:08}"));
        let context = s(format!("data-context-{index:08}"));
        let identifier = s(format!("pseudonym-{index:08}"));
        let consent = s(format!("consent-record-{index:08}"));
        let contract = s(format!("contract-{index:08}"));
        let authorization = s(format!("authorization-{index:08}"));
        let relation = s(format!("relation-{index:08}"));
        let node = &nodes[index % nodes.len()];
        let node_state = &node_states[index % node_states.len()];
        let consent_range = ranges[index % ranges.len()];
        add_type(graph, &user, "User");
        add_c(graph, &user, "hasActiveConsentRange", consent_range);
        add_i(graph, &user, "hasIdentifier", &identifier);
        add_i(graph, &user, "hasConsentRecord", &consent);
        add_i(graph, &user, "hasSemanticContract", &contract);
        add_i(graph, &user, "hasAuthorizationDecision", &authorization);
        add(graph, &wearable, iri(SAREF_ATTACHED), user.clone());
        add_i(graph, &user, "hasUserState", &user_state);
        add_c(graph, &user, "locatedInZone", "CityCentreZone");
        add_c(graph, &user, "governedBy", "P-CONS-01");
        add_type(graph, &identifier, "PseudonymousIdentifier");
        add(
            graph,
            &identifier,
            c("identifierValue"),
            Literal::new_simple_literal(format!("SYN-{index:08}")),
        );
        add(
            graph,
            &identifier,
            c("identifierScope"),
            Literal::new_simple_literal("benchmark-rust-v1"),
        );
        add_type(graph, &consent, "ConsentRecord");
        add_i(graph, &consent, "consentSubject", &user);
        add_c(graph, &consent, "hasConsentRange", consent_range);
        add_c(
            graph,
            &consent,
            "hasProcessingPurpose",
            "PurposeLocalPrediction",
        );
        add_c(
            graph,
            &consent,
            "hasAuthorizedDataCategory",
            "PhysiologicalParametrizedCategory",
        );
        add(graph, &consent, c("validFrom"), time(index));
        add_type(graph, &wearable, "SmartWatch");
        add_i(graph, &wearable, "hasDeviceState", &device_state);
        add_i(graph, &wearable, "connectsTo", node);
        add_type(graph, &device_state, "DeviceState");
        add_c(graph, &device_state, "hasBatteryLevel", "BatteryMedium");
        add_c(graph, &device_state, "hasConnectionStatus", "Connected");
        add(
            graph,
            &device_state,
            c("parametrizedDataReady"),
            typed("true", "boolean"),
        );
        add(graph, &device_state, c("validFrom"), time(index + 10_000));
        add_type(graph, &user_state, "UserState");
        add_c(graph, &user_state, "hasMobility", "Walking");
        add_c(graph, &user_state, "hasPersonStatus", "Calm");
        add_c(graph, &user_state, "hasPredictedStressLevel", "StressLow");
        add(graph, &user_state, c("validFrom"), time(index + 20_000));
        add_i(graph, &user_state, "derivedFrom", &observation);
        add_type(graph, &observation, "StressObservation");
        add(
            graph,
            &observation,
            iri(SOSA_RESULT_TIME),
            time(index + 20_000),
        );
        add_type(graph, &context, "DataContext");
        add_i(graph, &context, "contextDeviceState", &device_state);
        add_i(graph, &context, "contextNodeState", node_state);
        add_c(graph, &context, "contextProcessingLevel", "FullProcessing");
        add_c(graph, &context, "contextZone", "CityCentreZone");
        add_c(graph, &context, "contextPurpose", "PurposeLocalPrediction");
        add(graph, &context, c("validFrom"), time(index + 20_000));
        add_type(graph, &parametrized, "PhysiologicalParametrizedData");
        add_i(graph, &parametrized, "generatedBy", &wearable);
        add_c(
            graph,
            &parametrized,
            "hasDataCategory",
            "PhysiologicalParametrizedCategory",
        );
        add_i(graph, &parametrized, "hasDataContext", &context);
        add_c(
            graph,
            &parametrized,
            "hasDataCriticality",
            "NormalPriorityData",
        );
        add_c(graph, &parametrized, "hasDataSensitivity", "SensitiveData");
        add(
            graph,
            &parametrized,
            c("isRedundant"),
            typed("false", "boolean"),
        );
        add(
            graph,
            &parametrized,
            c("sendTimestamp"),
            time(index + 20_001),
        );
        add_i(graph, &parametrized, "sentToNode", node);
        add_type(graph, &contract, "SemanticContract");
        add_i(graph, &contract, "contractSubject", &user);
        add_c(graph, &contract, "hasConsentRange", consent_range);
        add_c(
            graph,
            &contract,
            "hasProcessingPurpose",
            "PurposeLocalPrediction",
        );
        add_c(graph, &contract, "governedBy", "P-CONS-02");
        add(graph, &contract, c("validFrom"), time(index));
        add_type(graph, &authorization, "AuthorizationDecision");
        add_c(graph, &authorization, "basedOnZone", "CityCentreZone");
        add_c(
            graph,
            &authorization,
            "hasEffectiveConsentRange",
            consent_range,
        );
        add_c(
            graph,
            &authorization,
            "hasAuthorizationOutcome",
            "AuthorizationGranted",
        );
        add_i(graph, &authorization, "basedOnConsentRecord", &consent);
        add_i(graph, &authorization, "basedOnContract", &contract);
        add(graph, &authorization, c("validFrom"), time(index));
        add_type(graph, &relation, "NodeUserRelation");
        add_i(graph, &relation, "relatesNode", node);
        add_i(graph, &relation, "relatesUser", &user);
        add_c(graph, &relation, "hasDistance", "Close");
        add(
            graph,
            &relation,
            c("isPreferredNode"),
            typed("true", "boolean"),
        );
        add(graph, &relation, c("validFrom"), time(index));
    }
    debug_assert_eq!(graph.len() - before, synthetic_triple_count(users));
    Ok(graph.len() - before)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn generator_is_deterministic_and_has_no_padding() {
        for users in [1, 50, 100, 500] {
            let mut first = Graph::new();
            let mut second = Graph::new();
            assert_eq!(
                add_synthetic_abox(&mut first, users, 2026).unwrap(),
                synthetic_triple_count(users)
            );
            add_synthetic_abox(&mut second, users, 2026).unwrap();
            assert_eq!(first, second);
        }
    }
}

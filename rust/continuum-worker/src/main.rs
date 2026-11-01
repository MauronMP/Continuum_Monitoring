use anyhow::Result;
use axum::{
    Json, Router,
    body::Bytes,
    extract::{DefaultBodyLimit, State},
    http::{HeaderMap, StatusCode},
    response::IntoResponse,
    routing::{get, post},
};
use continuum_rdf::query::store_from_graph;
use continuum_rdf::{QueryOutcome, execute_query, graph_digest, materialize, parse_ntriples};
use oxigraph::store::Store;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use std::env;
use std::sync::{
    Arc, RwLock,
    atomic::{AtomicUsize, Ordering},
};
use std::time::Instant;
use tokio::net::TcpListener;
use tokio::sync::{OwnedSemaphorePermit, Semaphore};

const PROTOCOL_VERSION: &str = "continuum-rdf-worker-v1";

#[derive(Clone)]
struct AppState {
    data: Arc<RwLock<WorkerData>>,
    semantic_queue: Arc<Semaphore>,
    active: Arc<AtomicUsize>,
    waiting: Arc<AtomicUsize>,
    identity: Arc<Identity>,
    max_prepare_bytes: usize,
}

#[derive(Default)]
struct WorkerData {
    store: Option<Store>,
    dataset_digest: Option<String>,
    closure_digest: Option<String>,
    triples: usize,
}

#[derive(Serialize)]
struct Identity {
    service: &'static str,
    protocol_version: &'static str,
    build_id: String,
    rust_version: &'static str,
    build_target: &'static str,
    node_id: String,
    tier: String,
    authority: String,
    topology_fingerprint: String,
    ontology_digest: String,
    query_catalog_digest: String,
    query_count: usize,
}

struct ActiveGuard {
    state: AppState,
    _permit: OwnedSemaphorePermit,
}

impl ActiveGuard {
    async fn acquire(state: &AppState) -> Result<Self, StatusCode> {
        state.waiting.fetch_add(1, Ordering::SeqCst);
        let permit = state
            .semantic_queue
            .clone()
            .acquire_owned()
            .await
            .map_err(|_| StatusCode::SERVICE_UNAVAILABLE)?;
        state.waiting.fetch_sub(1, Ordering::SeqCst);
        state.active.fetch_add(1, Ordering::SeqCst);
        Ok(Self {
            state: state.clone(),
            _permit: permit,
        })
    }
}

impl Drop for ActiveGuard {
    fn drop(&mut self) {
        self.state.active.fetch_sub(1, Ordering::SeqCst);
    }
}

async fn health(State(state): State<AppState>) -> impl IntoResponse {
    let data = state.data.read().expect("worker state poisoned");
    let active = state.active.load(Ordering::SeqCst);
    let waiting = state.waiting.load(Ordering::SeqCst);
    Json(json!({
        "status": "ready", "service": state.identity.service,
        "protocol_version": state.identity.protocol_version, "build_id": state.identity.build_id,
        "rust_version": state.identity.rust_version, "build_target": state.identity.build_target,
        "node_id": state.identity.node_id, "tier": state.identity.tier,
        "authority": state.identity.authority, "topology_fingerprint": state.identity.topology_fingerprint,
        "ontology_digest": state.identity.ontology_digest,
        "query_catalog_digest": state.identity.query_catalog_digest,
        "query_count": state.identity.query_count, "idle": active == 0 && waiting == 0,
        "max_prepare_bytes": state.max_prepare_bytes,
        "active_requests": active, "queue_depth": waiting,
        "dataset_digest": data.dataset_digest, "closure_digest": data.closure_digest,
        "graph_loaded": data.store.is_some(), "triples": data.triples,
    }))
}

async fn reset(State(state): State<AppState>) -> Result<Json<Value>, StatusCode> {
    let _guard = ActiveGuard::acquire(&state).await?;
    *state
        .data
        .write()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)? = WorkerData::default();
    Ok(Json(json!({"status": "reset"})))
}

async fn prepare(
    State(state): State<AppState>,
    headers: HeaderMap,
    body: Bytes,
) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    let _guard = ActiveGuard::acquire(&state)
        .await
        .map_err(|code| (code, Json(json!({"error": "queue closed"}))))?;
    let load_started = Instant::now();
    let mut graph = parse_ntriples(&body).map_err(invalid_request)?;
    let dataset_digest = graph_digest(&graph);
    let parse_and_digest_seconds = load_started.elapsed().as_secs_f64();
    if let Some(expected) = headers.get("x-expected-dataset-digest")
        && expected.to_str().ok() != Some(dataset_digest.as_str())
    {
        return Err((
            StatusCode::UNPROCESSABLE_ENTITY,
            Json(json!({"status": "semantic_mismatch", "actual": dataset_digest})),
        ));
    }
    let reasoning = materialize(&mut graph);
    let closure_digest = graph_digest(&graph);
    let store_started = Instant::now();
    let store = store_from_graph(&graph).map_err(internal_error)?;
    let store_load_seconds = store_started.elapsed().as_secs_f64();
    let remote_load_seconds = parse_and_digest_seconds + store_load_seconds;
    let triples = graph.len();
    *state
        .data
        .write()
        .map_err(|_| internal_error("worker state poisoned"))? = WorkerData {
        store: Some(store),
        dataset_digest: Some(dataset_digest.clone()),
        closure_digest: Some(closure_digest.clone()),
        triples,
    };
    Ok(Json(
        json!({"status": "prepared", "payload_bytes": body.len(),
        "dataset_digest": dataset_digest, "closure_digest": closure_digest,
        "remote_load_seconds": remote_load_seconds,
        "parse_and_digest_seconds": parse_and_digest_seconds,
        "store_load_seconds": store_load_seconds, "reasoning": reasoning}),
    ))
}

#[derive(Deserialize)]
struct QueryRequest {
    query_id: String,
    query: String,
    round: usize,
}

#[derive(Serialize)]
struct QueryResponse {
    query_id: String,
    round: usize,
    outcome: QueryOutcome,
}

async fn query(
    State(state): State<AppState>,
    Json(request): Json<QueryRequest>,
) -> Result<Json<QueryResponse>, (StatusCode, Json<Value>)> {
    let _guard = ActiveGuard::acquire(&state)
        .await
        .map_err(|code| (code, Json(json!({"error": "queue closed"}))))?;
    let store = state
        .data
        .read()
        .map_err(|_| internal_error("worker state poisoned"))?
        .store
        .clone()
        .ok_or_else(|| {
            (
                StatusCode::CONFLICT,
                Json(json!({"error": "graph_not_loaded"})),
            )
        })?;
    let outcome = execute_query(&store, &request.query).map_err(invalid_request)?;
    Ok(Json(QueryResponse {
        query_id: request.query_id,
        round: request.round,
        outcome,
    }))
}

fn invalid_request(error: impl std::fmt::Display) -> (StatusCode, Json<Value>) {
    (
        StatusCode::BAD_REQUEST,
        Json(json!({"error": error.to_string()})),
    )
}
fn internal_error(error: impl std::fmt::Display) -> (StatusCode, Json<Value>) {
    (
        StatusCode::INTERNAL_SERVER_ERROR,
        Json(json!({"error": error.to_string()})),
    )
}
fn env_value(name: &str, default: &str) -> String {
    env::var(name).unwrap_or_else(|_| default.to_owned())
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();
    let identity = Identity {
        service: "continuum-worker",
        protocol_version: PROTOCOL_VERSION,
        build_id: env_value(
            "CONTINUUM_BUILD_ID",
            &format!(
                "{}-{}-{}",
                env!("CARGO_PKG_VERSION"),
                env!("CONTINUUM_BUILD_TARGET"),
                env!("CONTINUUM_BUILD_RUSTC")
            ),
        ),
        rust_version: env!("CONTINUUM_BUILD_RUSTC"),
        build_target: env!("CONTINUUM_BUILD_TARGET"),
        node_id: env_value("CONTINUUM_NODE_ID", "local"),
        tier: env_value("CONTINUUM_TIER", "local"),
        authority: env_value("CONTINUUM_AUTHORITY", "local"),
        topology_fingerprint: env_value("CONTINUUM_TOPOLOGY_FINGERPRINT", "local"),
        ontology_digest: env_value("CONTINUUM_ONTOLOGY_DIGEST", "unconfigured"),
        query_catalog_digest: env_value("CONTINUUM_QUERY_CATALOG_DIGEST", "unconfigured"),
        query_count: env_value("CONTINUUM_QUERY_COUNT", "0").parse().unwrap_or(0),
    };
    let state = AppState {
        data: Arc::new(RwLock::new(WorkerData::default())),
        semantic_queue: Arc::new(Semaphore::new(1)),
        active: Arc::new(AtomicUsize::new(0)),
        waiting: Arc::new(AtomicUsize::new(0)),
        identity: Arc::new(identity),
        max_prepare_bytes: env_value("CONTINUUM_MAX_PREPARE_BYTES", "268435456")
            .parse()
            .unwrap_or(268_435_456),
    };
    let max_prepare_bytes = state.max_prepare_bytes;
    let app = Router::new()
        .route("/health", get(health))
        .route("/reset", post(reset))
        .route(
            "/prepare",
            post(prepare).layer(DefaultBodyLimit::max(max_prepare_bytes)),
        )
        .route("/query", post(query))
        .with_state(state);
    let address = env_value("CONTINUUM_BIND", "0.0.0.0:8391");
    let listener = TcpListener::bind(&address).await?;
    tracing::info!(%address, "continuum worker ready");
    axum::serve(listener, app).await?;
    Ok(())
}

use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use continuum_rdf::query::store_from_graph;
use continuum_rdf::{
    add_synthetic_abox, canonical_ntriples, execute_query, graph_digest, materialize,
    parse_ntriples, partition_graph,
};
use serde::Deserialize;
use serde_json::json;
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(about = "Deterministic RDF operations for Continuum Monitoring")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    Digest {
        input: PathBuf,
    },
    Reason {
        input: PathBuf,
        #[arg(long)]
        output: Option<PathBuf>,
    },
    Query {
        input: PathBuf,
        query: PathBuf,
    },
    Catalog {
        input: PathBuf,
        manifest: PathBuf,
        #[arg(long, default_value = ".")]
        root: PathBuf,
    },
    Generate {
        base: PathBuf,
        #[arg(long)]
        users: usize,
        #[arg(long, default_value_t = 2026)]
        seed: u64,
        #[arg(long)]
        output: PathBuf,
    },
    Partition {
        input: PathBuf,
        #[arg(long)]
        layout: String,
        #[arg(long, value_delimiter = ',')]
        participants: Vec<String>,
        #[arg(long)]
        output_dir: PathBuf,
    },
}

#[derive(Deserialize)]
struct QueryManifest {
    queries: Vec<QueryEntry>,
}

#[derive(Deserialize)]
struct QueryEntry {
    id: String,
    kind: String,
    path: PathBuf,
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Command::Digest { input } => {
            let bytes = fs::read(&input).with_context(|| format!("reading {}", input.display()))?;
            let graph = parse_ntriples(&bytes)?;
            println!(
                "{}",
                serde_json::to_string_pretty(
                    &json!({"triples": graph.len(), "digest": graph_digest(&graph), "bytes": canonical_ntriples(&graph).len()})
                )?
            );
        }
        Command::Reason { input, output } => {
            let bytes = fs::read(&input).with_context(|| format!("reading {}", input.display()))?;
            let mut graph = parse_ntriples(&bytes)?;
            let report = materialize(&mut graph);
            if let Some(path) = output {
                fs::write(path, canonical_ntriples(&graph))?;
            }
            println!(
                "{}",
                serde_json::to_string_pretty(
                    &json!({"report": report, "closure_digest": graph_digest(&graph)})
                )?
            );
        }
        Command::Query { input, query } => {
            let bytes = fs::read(&input).with_context(|| format!("reading {}", input.display()))?;
            let mut graph = parse_ntriples(&bytes)?;
            let reasoning = materialize(&mut graph);
            let store = store_from_graph(&graph)?;
            let query_text = fs::read_to_string(&query)?;
            let outcome = execute_query(&store, &query_text)?;
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({"reasoning": reasoning, "query": outcome}))?
            );
        }
        Command::Catalog {
            input,
            manifest,
            root,
        } => {
            let bytes = fs::read(&input).with_context(|| format!("reading {}", input.display()))?;
            let mut graph = parse_ntriples(&bytes)?;
            let reasoning = materialize(&mut graph);
            let store = store_from_graph(&graph)?;
            let catalog: QueryManifest = serde_json::from_slice(&fs::read(manifest)?)?;
            let mut results = Vec::with_capacity(catalog.queries.len());
            for entry in catalog.queries {
                let text = fs::read_to_string(root.join(entry.path))?;
                let outcome = execute_query(&store, &text)
                    .with_context(|| format!("executing {}", entry.id))?;
                results.push(json!({
                    "query_id": entry.id,
                    "kind": entry.kind,
                    "result_count": outcome.result_count,
                    "ask_result": outcome.ask_result,
                    "result_digest": outcome.result_digest,
                }));
            }
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({"reasoning": reasoning, "queries": results}))?
            );
        }
        Command::Generate {
            base,
            users,
            seed,
            output,
        } => {
            let started = std::time::Instant::now();
            let mut graph = parse_ntriples(&fs::read(base)?)?;
            let base_triples = graph.len();
            let synthetic_triples = add_synthetic_abox(&mut graph, users, seed)?;
            let bytes = canonical_ntriples(&graph);
            fs::write(output, &bytes)?;
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "users": users, "seed": seed, "base_triples": base_triples,
                    "synthetic_triples": synthetic_triples, "actual_input_triples": graph.len(),
                    "dataset_bytes": bytes.len(), "dataset_digest": graph_digest(&graph),
                    "dataset_generation_seconds": started.elapsed().as_secs_f64()
                }))?
            );
        }
        Command::Partition {
            input,
            layout,
            participants,
            output_dir,
        } => {
            let graph = parse_ntriples(&fs::read(input)?)?;
            let started = std::time::Instant::now();
            let fragments = partition_graph(&graph, participants.len(), layout == "replicated");
            let partition_seconds = started.elapsed().as_secs_f64();
            fs::create_dir_all(&output_dir)?;
            let serialize_started = std::time::Instant::now();
            let mut metadata = Vec::new();
            for (participant, fragment) in participants.iter().zip(fragments) {
                let bytes = canonical_ntriples(&fragment);
                fs::write(output_dir.join(format!("{participant}.nt")), &bytes)?;
                metadata.push(json!({"participant": participant, "triples": fragment.len(), "bytes": bytes.len(), "digest": graph_digest(&fragment)}));
            }
            println!(
                "{}",
                serde_json::to_string_pretty(
                    &json!({"layout": layout, "partition_seconds": partition_seconds, "serialize_seconds": serialize_started.elapsed().as_secs_f64(), "fragments": metadata})
                )?
            );
        }
    }
    Ok(())
}

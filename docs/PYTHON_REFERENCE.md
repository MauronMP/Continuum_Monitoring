# Python source reference

Generated from maintained Python files. Regenerate with
`python tools/generate_project_indexes.py`; do not edit generated tables.

Scientific experiment contracts belong in [Experiments](EXPERIMENTS.md),
commands in [Complete execution](COMPLETE_EXECUTION.md). There are two
evaluation batteries; regression tests are engineering checks.

This inventory covers every Python file in `src/`, `tools/` and `tests/`.
Module descriptions and exposed definitions identify code responsibilities,
not evidence that every modelled capability is implemented.

## src/continuum_bench

| File | Responsibility | Main definitions |
| --- | --- | --- |
| [__init__.py](../src/continuum_bench/__init__.py) | Policy-driven monitoring evaluation for the physical computing continuum. | Module constants/imports. |
| [__main__.py](../src/continuum_bench/__main__.py) | Implementation of   main  . | Module constants/imports. |
| [cli.py](../src/continuum_bench/cli.py) | Implementation of cli. | `_family_timeout_updates`, `_parser`, `_manifest_path`, `_target_manifest_path`, `_target_topology`, `_physical_inventory`, `_open_paths`, `_dispatch` (+1 definitions) |
| [config.py](../src/continuum_bench/config.py) | Implementation of config. | `DistributedConfig`, `ExecutionLimits`, `BenchmarkConfig`, `load_config`, `_validate_benchmark` |
| [csv_utils.py](../src/continuum_bench/csv_utils.py) | Robust CSV output shared by benchmark and reporting commands. | `write_dict_rows` |
| [environment.py](../src/continuum_bench/environment.py) | Standard-library-only installation and infrastructure diagnostics. | `Check`, `runtime_checks`, `installed_versions`, `failure_hint`, `project_checks`, `physical_checks`, `owl_reasoner_checks`, `require_checks` (+1 definitions) |
| [lifecycle_limits.py](../src/continuum_bench/lifecycle_limits.py) | Finite connectivity budgets, independent of experimental timing limits. | `connectivity_timeout`, `ssh_probe_timeout`, `health_timeout` |
| [node.py](../src/continuum_bench/node.py) | HTTP worker used by configurable physical topologies. | `_peak_rss_kib`, `_children_usage`, `_current_rss_kib`, `_process_io_bytes`, `_total_memory_kib`, `WorkerPhaseTimeout`, `_worker_timeout`, `_with_transport_metrics` (+4 definitions) |
| [ontology.py](../src/continuum_bench/ontology.py) | Implementation of ontology. | `load_graph`, `graph_digest`, `contradiction_count`, `datatype_range_errors`, `validate_shacl` |
| [owl_materialization.py](../src/continuum_bench/owl_materialization.py) | Local native DL adapters implementing named-class-individual-v1. | `MaterializationError`, `InconsistentOntologyError`, `_classpath`, `MaterializationTimeoutError`, `_run`, `_absolute_owlxml_iris`, `_konclude`, `_local_import_closure` (+1 definitions) |
| [owl_validation.py](../src/continuum_bench/owl_validation.py) | External OWL reasoner validation with explicit availability semantics. | `validate_external_reasoners`, `_run_reasoner`, `_run_owlapi`, `_run_command`, `_execute_json`, `_timeout_output`, `_diagnostic_excerpt`, `_terminate_process_tree` |
| [partitioning.py](../src/continuum_bench/partitioning.py) | Authority- and privacy-aware RDF fragmentation for continuum deployments. | `FragmentSet`, `_copy_namespaces`, `_merge`, `_clone`, `_placement`, `load_substrate`, `_logical_substrate_triple_count`, `load_reference_abox` (+21 definitions) |
| [physical_cluster.py](../src/continuum_bench/physical_cluster.py) | Deployment and lifecycle helpers for an elastic physical topology. | `PhysicalNode`, `PhysicalInventory`, `load_physical_inventory`, `_validate_remote_install_paths`, `remote_reasoner_install_command`, `offline_preflight`, `write_offline_manifest`, `_run` (+14 definitions) |
| [plot_environment.py](../src/continuum_bench/plot_environment.py) | Headless, writable Matplotlib setup shared by report modules. | `configure_matplotlib` |
| [preflight.py](../src/continuum_bench/preflight.py) | Fast workload-capacity checks performed before contacting any worker. | `WorkloadTarget`, `minimum_asserted_triples`, `_targets_from_load`, `_targets_from_experiment`, `validate_workload_targets`, `validate_load_workload`, `validate_experiment_workload`, `validate_default_workloads` |
| [processes.py](../src/continuum_bench/processes.py) | Bounded, streaming subprocess execution with actionable persistent logs. | `CommandFailure`, `_stop_owned_process`, `run_logged` |
| [protocol.py](../src/continuum_bench/protocol.py) | HTTP contract shared by continuum benchmark coordinators and workers. | `_software_build_id`, `worker_health_error` |
| [queries.py](../src/continuum_bench/queries.py) | Implementation of queries. | `QuerySpec`, `QueryMeasurement`, `QueryExecution`, `result_digest`, `load_catalog`, `execute_query_detailed`, `execute_query`, `check_expectation` (+1 definitions) |
| [reasoners.py](../src/continuum_bench/reasoners.py) | Implementation of reasoners. | `DatatypeAwareRDFSSemantics`, `ReasonerEngine`, `available_reasoners`, `reasoner_catalog`, `_materialize_rdfs`, `RDFSReasoner`, `register_reasoner`, `get_reasoner` (+5 definitions) |
| [result_contract.py](../src/continuum_bench/result_contract.py) | Compatibility gate for benchmark artefacts consumed by reports/plots. | `require_release_metadata` |
| [semantic_assets.py](../src/continuum_bench/semantic_assets.py) | Content identity for the semantic inputs shared by physical workers. | `semantic_assets_digest` |
| [specification.py](../src/continuum_bench/specification.py) | Machine-checkable contract for the canonical ontology release. | `release_identity`, `_identifier_values`, `validate_release_contract`, `acceptance_status` |
| [synthetic.py](../src/continuum_bench/synthetic.py) | Implementation of synthetic. | `synthetic_triple_count`, `_time`, `iter_synthetic_triples`, `add_synthetic_data`, `add_synthetic_rules`, `pad_to_target_triples` |
| [topology.py](../src/continuum_bench/topology.py) | Configuration-driven elastic continuum topologies. | `infer_tier`, `default_categories`, `authority_index`, `TopologyNode`, `Topology`, `TopologyManifest`, `_as_path`, `_parse_node` (+9 definitions) |
| [validation.py](../src/continuum_bench/validation.py) | Implementation of validation. | `validate_project` |

## src/continuum_bench/core

| File | Responsibility | Main definitions |
| --- | --- | --- |
| [__init__.py](../src/continuum_bench/core/__init__.py) | Shared domain model for physical continuum ontology monitoring. | Module constants/imports. |
| [contracts.py](../src/continuum_bench/core/contracts.py) | Domain ports with no infrastructure, benchmark or visualization imports. | `Ontology`, `Policy`, `Requirement`, `Query`, `ReasoningResult`, `Reasoner`, `MetricCollector`, `ResultSink` (+2 definitions) |
| [domain.py](../src/continuum_bench/core/domain.py) | Reusable physical-continuum domain concepts. | `GeographicPosition`, `NodeCapacity`, `NodeDynamicState`, `PhysicalContinuumNode`, `ReasonerConfiguration`, `PhysicalContinuum` |

## src/continuum_bench/monitoring

| File | Responsibility | Main definitions |
| --- | --- | --- |
| [__init__.py](../src/continuum_bench/monitoring/__init__.py) | Performance evaluation, experiment orchestration and result analysis. | `export_physical_fragments`, `run_physical_monitoring_suite`, `run_distributed_monitoring_suite` |
| [budget.py](../src/continuum_bench/monitoring/budget.py) | Shared benchmark deadlines and right-censoring helpers. | `unlimited_execution`, `keep_going_execution`, `execution_policy`, `execution_metadata`, `wait_timeout`, `PhaseBudgetTimeout`, `local_phase_timeout`, `remaining_seconds` (+7 definitions) |
| [campaign.py](../src/continuum_bench/monitoring/campaign.py) | Reproducible physical campaigns through infrastructure, reasoner and result ports. | `_percentile`, `execute_campaign`, `run_campaign` |
| [campaign_config.py](../src/continuum_bench/monitoring/campaign_config.py) | Validated, deterministic one-factor-at-a-time physical campaign definitions. | `Workload`, `Axis`, `CampaignConfig`, `load_campaign` |
| [campaign_infrastructure.py](../src/continuum_bench/monitoring/campaign_infrastructure.py) | Physical HTTP transport behind an experiment-independent execution port. | `Infrastructure`, `PhysicalInfrastructure` |
| [campaign_results.py](../src/continuum_bench/monitoring/campaign_results.py) | Versioned JSONL/CSV evidence sink; no plotting dependency. | `StructuredResults` |
| [campaign_runtime.py](../src/continuum_bench/monitoring/campaign_runtime.py) | Worker-side workload execution through reasoner and metric ports. | `CampaignRuntime` |
| [comparative_reporting.py](../src/continuum_bench/monitoring/comparative_reporting.py) | Matched physical comparisons; no inferred node timing or causal policy claims. | `summarize`, `matched_users`, `generate_comparisons` |
| [distributed.py](../src/continuum_bench/monitoring/distributed.py) | Coordinator for replicated elastic continuum benchmarks. | `Endpoint`, `_payload_hint`, `_worker_error_body`, `_deadline_log`, `_request`, `discover`, `_parallel`, `_assignment` (+9 definitions) |
| [distributed_ontology.py](../src/continuum_bench/monitoring/distributed_ontology.py) | Privacy-aware benchmark coordinator for physical continuum nodes. | `_sources`, `_assignment`, `_prepare`, `_query`, `_merge_responses`, `_full_source`, `_baseline_counts`, `_validation_rows` (+9 definitions) |
| [distributed_reasoning_config.py](../src/continuum_bench/monitoring/distributed_reasoning_config.py) | Configuration for distributed reasoning scalability experiments. | `DistributedReasoningConfig`, `load_distributed_reasoning_config`, `validate_distributed_reasoning_config`, `override_distributed_reasoning_config` |
| [distributed_reasoning_scalability.py](../src/continuum_bench/monitoring/distributed_reasoning_scalability.py) | Strong/weak scalability of reasoning over physical continuum nodes. | `_select_endpoints`, `_payload`, `_prepare`, `_safe_ratio`, `_measurement`, `_derive_scaling`, `_derive_normalized_semantics`, `_query_client` (+6 definitions) |
| [distributed_suite.py](../src/continuum_bench/monitoring/distributed_suite.py) | Infrastructure-neutral distributed monitoring suite orchestration. | `run_distributed_monitoring_suite` |
| [experiment_analysis.py](../src/continuum_bench/monitoring/experiment_analysis.py) | Analysis of monitoring experiments on physical continuum nodes. | `_read_csv`, `_float`, `_median`, `_group`, `analyze_experiments` |
| [experiment_config.py](../src/continuum_bench/monitoring/experiment_config.py) | Implementation of experiment config. | `ReasoningProfile`, `ExperimentConfig`, `load_experiment_config`, `select_reasoning_profiles`, `_validate` |
| [experiment_reporting.py](../src/continuum_bench/monitoring/experiment_reporting.py) | Implementation of experiment reporting. | `_summary_path`, `_rows`, `_quality_rows`, `_save`, `_median_groups`, `plot_scale_out`, `plot_reasoning_hardware`, `plot_distributed_ontology` (+4 definitions) |
| [experiments.py](../src/continuum_bench/monitoring/experiments.py) | Three non-confounded experiments for continuum ontology evaluation. | `_write`, `_metadata`, `_save_metadata`, `_target_endpoints`, `_phase_payload`, `_prepare_one`, `_execute_one`, `_replicated_prepare` (+9 definitions) |
| [figure_style.py](../src/continuum_bench/monitoring/figure_style.py) | Shared PNG-only scientific figure output and explicit missing-data panels. | `save_png` |
| [lease.py](../src/continuum_bench/monitoring/lease.py) | Prevent overlapping physical campaigns and lifecycle mutations on one coordinator. | `prevent_coordinator_suspension`, `physical_lease` |
| [load_benchmark.py](../src/continuum_bench/monitoring/load_benchmark.py) | Rate-controlled semantic alert workload for elastic deployments. | `PhaseTimeout`, `_local_timeout`, `_is_timeout`, `discover_load_endpoints`, `_workload_specs`, `_is_alert`, `_percentile`, `_prediction` (+6 definitions) |
| [load_config.py](../src/continuum_bench/monitoring/load_config.py) | Configuration model for the multidimensional event-load benchmark. | `LoadProfile`, `LoadBenchmarkConfig`, `load_load_config`, `select_load_profiles` |
| [load_reporting.py](../src/continuum_bench/monitoring/load_reporting.py) | Publication plots for the multidimensional event-load experiment. | `_read`, `_float`, `_aggregate`, `_save`, `_style`, `_factorized_legend`, `_format_dimension_x`, `_series` (+6 definitions) |
| [metrics.py](../src/continuum_bench/monitoring/metrics.py) | Process measurements, independent from experiment orchestration and plots. | `ProcessMetrics`, `measured` |
| [normalize.py](../src/continuum_bench/monitoring/normalize.py) | Canonical result envelope for the retained scientific benchmark families. | `snapshot_summaries`, `normalize_completed_outputs` |
| [physical.py](../src/continuum_bench/monitoring/physical.py) | Balanced benchmarks for a configuration-driven physical continuum. | `inventory_endpoints`, `_calibrate`, `balanced_assignment`, `_assignment_rows`, `_node_rows`, `_metadata`, `_resource_summary`, `_summary` (+5 definitions) |
| [physical_suite.py](../src/continuum_bench/monitoring/physical_suite.py) | Physical monitoring suite orchestration. | `run_physical_monitoring_suite`, `export_physical_fragments` |
| [progress.py](../src/continuum_bench/monitoring/progress.py) | Durable, human-readable progress for long physical experiments. | `PointProgress` |
| [provenance.py](../src/continuum_bench/monitoring/provenance.py) | Reproduction evidence for the exact source, dependencies and experiment inputs. | `snapshot` |
| [publication.py](../src/continuum_bench/monitoring/publication.py) | Evidence-led physical reports: raw data, censoring, policy costs and PNGs. | `read_csv`, `number`, `write_csv`, `_validation_key`, `validated_evidence_rows`, `figure_group`, `Report`, `generate_report` |
| [report_profiles.py](../src/continuum_bench/monitoring/report_profiles.py) | Display identities for the active physical reasoner matrix. | `observed_profiles`, `outcome` |
| [resource_summary.py](../src/continuum_bench/monitoring/resource_summary.py) | Explicit scope for resources outside the Python worker process. | `native_resources` |
| [suite.py](../src/continuum_bench/monitoring/suite.py) | Sequential, recorded execution of every physical acceptance family. | `suite_plan`, `run_suite` |
| [workloads.py](../src/continuum_bench/monitoring/workloads.py) | Deterministic synthetic policy workloads with disjoint entity ownership. | `build_workload`, `query_for`, `result_keys`, `digest` |

## src/continuum_bench/monitoring/comparison

| File | Responsibility | Main definitions |
| --- | --- | --- |
| [__init__.py](../src/continuum_bench/monitoring/comparison/__init__.py) | Independent, paired evaluation of monitoring decision strategies. | Module constants/imports. |
| [__main__.py](../src/continuum_bench/monitoring/comparison/__main__.py) | Independent command entry point: python -m continuum_bench.monitoring.comparison. | `main` |
| [adapters.py](../src/continuum_bench/monitoring/comparison/adapters.py) | Common decision port and equivalent procedural/semantic implementations. | `term`, `DecisionAdapter`, `StaticAdapter`, `ProceduralAdapter`, `SemanticAdapter`, `build_adapter` |
| [config.py](../src/continuum_bench/monitoring/comparison/config.py) | Strict comparison configuration independent of legacy experiment controls. | `load` |
| [figures.py](../src/continuum_bench/monitoring/comparison/figures.py) | Journal-sized PNG figures, point-level provenance and explicit missing data. | `_metrics`, `_event_value`, `point_table`, `_draw`, `figures`, `paired_cost_figure`, `infrastructure_figures`, `cross_node_summary` |
| [reporting.py](../src/continuum_bench/monitoring/comparison/reporting.py) | PNG-only reports from raw evidence, with paired repetition-level statistics. | `summarize`, `paired_statistics`, `report` |
| [runner.py](../src/continuum_bench/monitoring/comparison/runner.py) | Paired physical execution, durable raw evidence and explicit outcome coverage. | `dump`, `inventory_for`, `jobs`, `run` |
| [statistics.py](../src/continuum_bench/monitoring/comparison/statistics.py) | Repetition-level uncertainty; events are not independent replicates. | `estimate` |
| [transport.py](../src/continuum_bench/monitoring/comparison/transport.py) | Temporary source bundles over SSH, with bounded remote process lifetime. | `source_bundle`, `command`, `invoke`, `probe` |
| [validation.py](../src/continuum_bench/monitoring/comparison/validation.py) | Reject corrupted scientific evidence instead of plotting plausible results. | `nonnegative`, `validate_measurement`, `validate_records` |
| [worker.py](../src/continuum_bench/monitoring/comparison/worker.py) | One isolated physical-host measurement; JSON-only stdout protocol. | `execute`, `_memory` |
| [workload.py](../src/continuum_bench/monitoring/comparison/workload.py) | Deterministic paired workloads and a separately supplied acceptance oracle. | `digest`, `expand`, `trace`, `operational`, `quality` |

## src/continuum_bench/monitoring/policy_evaluation

| File | Responsibility | Main definitions |
| --- | --- | --- |
| [__init__.py](../src/continuum_bench/monitoring/policy_evaluation/__init__.py) | Policy-driven monitoring evaluation, independent from reporting. | Module constants/imports. |
| [config.py](../src/continuum_bench/monitoring/policy_evaluation/config.py) | Configuration contracts for the four policy-monitoring experiments. | `ResourceSpec`, `PolicyRule`, `Scenario`, `StaticPlan`, `ScalabilityLevel`, `PolicyEvaluationConfig`, `_strings`, `load_policy_evaluation_config` (+2 definitions) |
| [model.py](../src/continuum_bench/monitoring/policy_evaluation/model.py) | Domain objects for policy decisions and monitoring plans. | `MonitoringPlan`, `Decision`, `PolicyEngine`, `static_decision` |
| [reporting.py](../src/continuum_bench/monitoring/policy_evaluation/reporting.py) | PNG-only scientific figures for the four policy-monitoring experiments. | `_rows`, `_header`, `_style`, `_group`, `_repetition_means`, `_per_decision_cost`, `plot_effectiveness`, `plot_dynamic_adaptation` (+3 definitions) |
| [resources.py](../src/continuum_bench/monitoring/policy_evaluation/resources.py) | Lightweight process sampling used by policy evaluation runs. | `memory_measurement_kind`, `_rss_mib`, `ResourceMeasurement`, `ResourceSampler` |
| [runner.py](../src/continuum_bench/monitoring/policy_evaluation/runner.py) | Execution of policy effectiveness, adaptation, scalability and cost studies. | `_common`, `_json`, `_truth`, `_items`, `_quality`, `_validate_policy_identifiers`, `_internal_graph`, `_reason` (+10 definitions) |

## src/continuum_bench/monitoring/study

| File | Responsibility | Main definitions |
| --- | --- | --- |
| [__init__.py](../src/continuum_bench/monitoring/study/__init__.py) | Experimental study helpers for policy-category and mobility analysis. | Module constants/imports. |
| [analysis.py](../src/continuum_bench/monitoring/study/analysis.py) | Implementation of analysis. | `analyze_category_costs`, `_aggregate`, `_aggregate_by_policy`, `_summary`, `_numbers`, `_weighted_mean`, `_percentile` |
| [config.py](../src/continuum_bench/monitoring/study/config.py) | Implementation of config. | `WorkloadModel`, `MobilityModel`, `NetworkModel`, `PlacementModel`, `SchedulerModel`, `PolicyCostStudyConfig`, `load_study_config`, `_validate` |
| [mobility.py](../src/continuum_bench/monitoring/study/mobility.py) | Static positions and a registry for future mobility implementations. | `StaticMobility`, `register_mobility_model`, `build_mobility_strategy` |
| [models.py](../src/continuum_bench/monitoring/study/models.py) | Implementation of models. | `Position`, `MobilitySample`, `LinkEstimate`, `QueryFeatures`, `RequestRecord` |
| [network.py](../src/continuum_bench/monitoring/study/network.py) | Implementation of network. | `estimate_link` |
| [placement.py](../src/continuum_bench/monitoring/study/placement.py) | Implementation of placement. | `default_node_positions`, `execution_candidates`, `data_locality_score`, `_tier_from_role` |
| [sparql.py](../src/continuum_bench/monitoring/study/sparql.py) | Implementation of sparql. | `characterize_query`, `_strip_comments` |
| [workload.py](../src/continuum_bench/monitoring/study/workload.py) | Implementation of workload. | `generate_study_trace`, `_write_features`, `_arrival_times`, `_choose_category`, `_weighted_choice`, `_choose_policy`, `_select_endpoint` |

## tools

| File | Responsibility | Main definitions |
| --- | --- | --- |
| [audit_ontology_modules.py](../tools/audit_ontology_modules.py) | Check local ontology import closure, ownership and deployment profiles. | `audit`, `main` |
| [audit_repository.py](../tools/audit_repository.py) | Read-only inventory and syntax audit of all maintained repository files. | `audit`, `main` |
| [bootstrap.py](../tools/bootstrap.py) | Install the coordinator or worker virtual environment safely. | `check_virtualenv`, `install_commands`, `main` |
| [check_distributed_semantics.py](../tools/check_distributed_semantics.py) | Compare local fragment closure/query merge with a canonical native reference. | `main` |
| [check_documentation.py](../tools/check_documentation.py) | Validate active Markdown links and generated English reference manuals. | `documentation_files`, `github_anchor`, `heading_anchors`, `_link_destination`, `check_links`, `check_generated_references`, `main` |
| [check_owl_consistency.py](../tools/check_owl_consistency.py) | Read-only OWLAPI consistency check using an external reasoner classpath. | `parse_report`, `diagnostic_excerpt`, `main` |
| [generate_project_indexes.py](../tools/generate_project_indexes.py) | Generate the Python file reference and consolidated query documentation. | `render`, `main` |
| [generate_reference_docs.py](../tools/generate_reference_docs.py) | Generate the English v4 reference manuals from executable artefacts. | `QueryRow`, `_ident`, `_literal`, `_label`, `_natural_key`, `_ids`, `_csv_ids`, `_queries` (+11 definitions) |
| [install_owl_reasoners.py](../tools/install_owl_reasoners.py) | Install and verify the local native OWL reasoning runtime. | `_run`, `_require`, `install_java_reasoners`, `verify_java_reasoners`, `install_konclude`, `verify_konclude`, `write_environment`, `verify_materializers` (+1 definitions) |
| [render_suite_diagnostics.py](../tools/render_suite_diagnostics.py) | Render explicitly non-publication diagnostics using a suite's archived source. | `main` |
| [review_validation_debt.py](../tools/review_validation_debt.py) | Inventory acceptance debt without manufacturing missing historical evidence. | `review`, `main` |

## tools/owl

| File | Responsibility | Main definitions |
| --- | --- | --- |
| [run_konclude.py](../tools/owl/run_konclude.py) | Run native Konclude after deterministic OWL/XML conversion. | `_input_index`, `main` |
| [verify_materialization.py](../tools/owl/verify_materialization.py) | Verify installed runtimes by real DL entailment and inconsistency checks. | `main` |

## tests/comparison

| File | Responsibility | Main definitions |
| --- | --- | --- |
| [test_comparison.py](../tests/comparison/test_comparison.py) | Behavioral contracts for independent paired decision comparisons. | `workload`, `test_equivalent_operational_plans_against_explicit_fixtures`, `test_inference_actually_changes_selection`, `test_unknown_context_deactivates_all_policies`, `test_oracle_is_not_used_by_adapters`, `test_trace_determinism_and_transitions`, `test_worker_measures_real_decisions_and_cumulative_sum`, `test_schedule_is_paired_and_deterministic` (+19 definitions) |

## tests

| File | Responsibility | Main definitions |
| --- | --- | --- |
| [conftest.py](../tests/conftest.py) | Regression coverage for conftest. | `root`, `config` |

## tests/core

| File | Responsibility | Main definitions |
| --- | --- | --- |
| [test_catalog.py](../tests/core/test_catalog.py) | Regression coverage for catalog. | `test_catalog_contains_every_query_once`, `test_all_queries_execute_and_meet_expectations`, `test_identifier_inventory_preserves_result_bag_with_bound_types` |
| [test_core_contracts.py](../tests/core/test_core_contracts.py) | Regression coverage for core contracts. | `test_geographic_position_rejects_invalid_coordinates`, `test_core_has_no_dependency_on_monitoring_or_adapters`, `test_experiment_can_register_a_reasoner_without_backend_branching` |
| [test_module_boundaries.py](../tests/core/test_module_boundaries.py) | Regression gates for the modular monitoring ontology and namespace migration. | `test_module_imports_are_closed_and_match_physical_profiles`, `test_consent_domains_cover_the_subjects_used_by_the_model`, `test_controlled_identity_constraints_are_not_example_only`, `test_observations_are_numeric_without_invented_units`, `test_multiple_policy_categories_validate_and_are_all_documented` |
| [test_native_reasoners.py](../tests/core/test_native_reasoners.py) | Native execution tests opt in via CONTINUUM_TEST_NATIVE_OWL=1. | `fixture`, `test_public_defaults_and_contracts`, `test_missing_runtime_no_fallback`, `test_imports_rejected_before_execution`, `test_explicit_bad_classpath`, `test_installed_classpath_wins_over_stale_shell`, `test_environment_classpath_without_installation`, `test_corrupt_installation_does_not_fall_back` (+8 definitions) |
| [test_ontology.py](../tests/core/test_ontology.py) | Regression coverage for ontology. | `test_requirement_language_literal_is_not_an_xsd_string`, `test_datatype_guard_respects_subproperties_and_string_subtypes`, `test_modular_ontology_is_english_and_datatype_safe`, `test_validation_rejects_inferred_datatype_clash_without_bottom`, `test_policy_zone_types_use_explicit_owl2_punning`, `test_modular_graph_contains_schema_and_reference_data`, `test_reference_data_conforms_to_shacl`, `test_release_synthetic_data_conforms_to_shacl` (+3 definitions) |
| [test_partitioning.py](../tests/core/test_partitioning.py) | Regression coverage for partitioning. | `test_fragments_reconstruct_canonical_graph`, `test_cloud_and_fog_pass_synthetic_privacy_gate`, `test_reference_links_to_private_objects_stay_at_their_authority`, `test_q17_and_q20_authority_union_matches_canonical`, `test_single_authority_queries_preserve_complete_bindings`, `test_single_authority_aggregates_are_exact_without_synthetic_data`, `test_release_execution_plan_preserves_all_canonical_results`, `test_resource_aggregate_normalizes_equal_numeric_lexical_forms` (+3 definitions) |
| [test_reasoners.py](../tests/core/test_reasoners.py) | Regression coverage for reasoners. | `test_rdfs_does_not_substitute_distinct_literal_value_spaces`, `test_rdfs_preserves_valid_literal_value_equivalences` |
| [test_release.py](../tests/core/test_release.py) | Regression coverage for release. | `test_release_release_inventory_and_traceability`, `test_acceptance_debt_is_reported_without_hiding_structural_validity`, `test_release_catalog_and_execution_plan_are_complete`, `test_acceptance_rejects_inflated_readiness_count_and_empty_campaign` |
| [test_synthetic.py](../tests/core/test_synthetic.py) | Regression coverage for synthetic. | `test_synthetic_growth_is_deterministic_and_monotonic`, `test_zero_users_does_not_change_graph`, `test_streamed_triples_are_identical_to_graph_generation`, `test_synthetic_triple_count_covers_shared_node_groups`, `test_rule_chain_and_exact_triple_padding`, `test_target_triples_rejects_shrinking_the_graph`, `test_neutral_padding_does_not_create_application_users`, `test_padding_rejects_unknown_mode` |

## tests/infrastructure

| File | Responsibility | Main definitions |
| --- | --- | --- |
| [test_cli_physical.py](../tests/infrastructure/test_cli_physical.py) | Regression coverage for cli physical. | `test_physical_layout_defaults_to_distributed`, `test_physical_layout_accepts_replicated`, `test_physical_cli_routes_to_monitoring_module`, `test_physical_cli_applies_independent_limits_and_skip_policy`, `test_physical_prepare_is_offline_and_does_not_take_worker_lease`, `test_new_comparison_defaults_and_invalid_layout`, `test_production_config_continues_after_timeout` |
| [test_environment.py](../tests/infrastructure/test_environment.py) | Regression coverage for environment. | `test_doctor_detects_incomplete_clone`, `test_physical_checks_are_reported` |
| [test_fragment_transport.py](../tests/infrastructure/test_fragment_transport.py) | Workers ingest transported placement, never materialize canonical private source data. | `fragments`, `test_transport_roundtrip_preserves_each_assignment`, `test_transport_rejects_mismatch`, `test_worker_materializes_and_recovers_only_transport`, `test_worker_rejects_missing_fragment_without_local_fallback`, `test_http_prepare_decodes_only_assigned_fragment`, `test_transport_checks_triple_count_after_hash_validation`, `test_coordinator_transports_fragments_and_times_placement` (+2 definitions) |
| [test_installation.py](../tests/infrastructure/test_installation.py) | Regression coverage for installation. | `bootstrap`, `test_runtime_dependencies_match_package`, `test_worker_requirements_are_minimal_and_pinned`, `test_bootstrap_install_is_wheel_only_and_uses_constraints`, `test_bootstrap_rejects_an_old_virtualenv`, `test_bootstrap_rejects_a_copied_virtualenv`, `test_package_version_matches_metadata`, `test_ci_keeps_regressions_without_physical_campaigns` |
| [test_node_telemetry.py](../tests/infrastructure/test_node_telemetry.py) | Regression coverage for node telemetry. | `_runtime`, `test_worker_reports_cpu_and_peak_rss_for_prepare_and_queries`, `test_distributed_prepare_reports_placement_profile`, `test_transport_metrics_report_exact_encoded_body_size`, `test_worker_phase_timeout_interrupts_and_restores_signal_handler`, `test_distributed_summary_aggregates_worker_telemetry`, `test_prepare_separates_child_cpu_and_lifetime_memory` |
| [test_physical_cluster.py](../tests/infrastructure/test_physical_cluster.py) | Regression coverage for physical cluster. | `config`, `test_status_rejects_wrong_worker_contract`, `test_elastic_manifest_is_the_default_physical_inventory`, `test_manifest_ssh_override_updates_remote_paths`, `test_authorize_installs_key_on_each_remote_node`, `test_ssh_lifecycle_commands_disable_password_prompts`, `test_remote_start_records_python_pid_not_background_shell`, `test_remote_start_passes_elastic_manifest_to_worker` (+11 definitions) |
| [test_physical_only.py](../tests/infrastructure/test_physical_only.py) | Keep removed execution targets out of every public benchmark entry point. | `test_benchmark_cli_rejects_nonphysical_execution`, `test_removed_execution_module_and_inventory_are_absent`, `test_container_deployment_assets_are_absent`, `test_removed_local_product_matrix_cannot_reappear`, `test_physical_cli_rejects_retired_comparison_profiles` |
| [test_processes.py](../tests/infrastructure/test_processes.py) | Regression coverage for processes. | `test_streams_and_logs_both_stdout_and_stderr`, `test_failed_command_retains_output_exitcode_and_log`, `test_silent_command_is_bounded`, `test_missing_command_is_actionable`, `test_timeout_must_be_finite_and_positive` |
| [test_semantic_assets.py](../tests/infrastructure/test_semantic_assets.py) | Stale semantic files must not pass worker compatibility checks. | `replica`, `test_semantic_identity_is_path_independent_and_excludes_workload_sizes`, `test_same_version_file_change_alters_semantic_identity`, `test_missing_input_is_not_a_valid_semantic_identity`, `test_worker_rejects_assets_changed_after_startup`, `test_health_contract_checks_semantic_identity`, `test_physical_metadata_records_semantic_inputs_for_both_layouts` |
| [test_topology.py](../tests/infrastructure/test_topology.py) | Regression coverage for topology. | `test_physical_manifest_loads_layered_nodes`, `test_physical_nodes_expose_resources_and_location`, `test_topology_public_shape_is_physical_only`, `test_flat_topology_roundtrip_preserves_unknown_location`, `test_domain_capacity_accepts_all_supported_memory_suffixes`, `test_topology_rejects_nonfinite_capacity_and_incomplete_coordinates` |
| [test_validation_debt.py](../tests/infrastructure/test_validation_debt.py) | Accepted validation debt remains reviewable. | `_debt_tool`, `test_debt_review_retains_missing_evidence_and_rejects_unreviewed_gap` |

## tests/integration

| File | Responsibility | Main definitions |
| --- | --- | --- |
| [test_owl_checker.py](../tests/integration/test_owl_checker.py) | Regression coverage for owl checker. | `checker`, `test_checker_rejects_missing_or_non_boolean_result`, `test_checker_separates_consistency_from_profile`, `test_checker_timeout_is_not_reported_as_consistency`, `test_checker_uses_configured_heap` |
| [test_owl_runtime_installation.py](../tests/integration/test_owl_runtime_installation.py) | Regression coverage for owl runtime installation. | `test_reasoner_pom_isolates_java_dependency_trees`, `test_konclude_wrapper_rejects_help_only_invocation`, `test_konclude_configuration_runs_a_bounded_consistency_operation`, `test_konclude_configuration_recognizes_native_success_output` |
| [test_owl_validation.py](../tests/integration/test_owl_validation.py) | Regression coverage for owl validation. | `test_missing_external_reasoners_are_not_reported_as_success`, `test_modular_compilation_rejects_unresolved_imports`, `test_owlapi_adapter_preserves_machine_readable_consistency`, `test_owlapi_adapter_uses_installed_project_classpath`, `test_owlapi_adapter_prefers_isolated_reasoner_classpath`, `test_command_reasoner_timeout_is_bounded_and_reported`, `test_command_reasoner_accepts_konclude_native_consistency_wording` |

## tests/monitoring

| File | Responsibility | Main definitions |
| --- | --- | --- |
| [test_campaign.py](../tests/monitoring/test_campaign.py) | Campaign contract tests use an in-memory infrastructure port, not remote hosts. | `MemoryInfrastructure`, `Sink`, `campaign`, `test_full_campaign_uses_production_budgets`, `test_equivalent_replicated_and_distributed_workloads`, `test_workload_axes_change_real_graph_size`, `test_timeouts_are_recorded_and_later_points_continue`, `test_structured_results_keep_configuration_and_do_not_overwrite` (+5 definitions) |
| [test_configuration_contracts.py](../tests/monitoring/test_configuration_contracts.py) | Regression coverage for configuration contracts. | `test_benchmark_scale_must_be_strictly_increasing`, `test_benchmark_rejects_unknown_reasoner`, `test_benchmark_rejects_retired_comparison_reasoners`, `test_load_early_stop_dimensions_must_be_ordered`, `test_distributed_ontology_scale_must_be_ordered` |
| [test_distributed.py](../tests/monitoring/test_distributed.py) | Regression coverage for distributed. | `test_physical_role_assignment_routes_every_query_once`, `test_discover_rejects_an_unrelated_health_service`, `test_request_retries_a_transient_disconnect`, `test_parallel_timeout_reports_the_exact_query_batch`, `test_http_application_error_preserves_worker_response`, `test_worker_error_truncation_keeps_cause_and_native_tail`, `test_query_batches_spread_lpt_expensive_prefix_across_rounds`, `test_worker_health_rejects_an_old_ontology_release` (+1 definitions) |
| [test_distributed_reasoning_scalability.py](../tests/monitoring/test_distributed_reasoning_scalability.py) | Regression coverage for distributed reasoning scalability. | `test_unlimited_policy_disables_worker_alarm`, `test_active_distributed_reasoning_matrix_uses_five_backends`, `test_all_experiments_requires_explicit_new_matrix_for_legacy_plans`, `test_independent_cli_timeouts_override_family_toml_values`, `test_distributed_fragments_reach_an_exact_logical_target`, `test_scaling_metrics_pair_each_repetition_with_one_node_baseline`, `test_capacity_treats_timeout_as_right_censoring`, `test_measurement_records_overhead_balance_and_per_node_metrics` (+3 definitions) |
| [test_experiment_config.py](../tests/monitoring/test_experiment_config.py) | Regression coverage for experiment config. | `test_full_experiment_config_uses_non_pruning_production_budgets`, `test_experiment_fixture_config_defines_all_three_families`, `test_reasoning_profile_selection_is_explicit`, `test_experiment_cli_commands_are_distinct` |
| [test_experiment_timeouts.py](../tests/monitoring/test_experiment_timeouts.py) | Regression coverage for experiment timeouts. | `test_scale_out_timeout_skips_repetitions_but_continues_reasoners` |
| [test_lease.py](../tests/monitoring/test_lease.py) | Regression coverage for lease. | `test_physical_campaign_ignores_terminal_suspend`, `test_nonphysical_work_does_not_change_signal_handlers` |
| [test_load_benchmark.py](../tests/monitoring/test_load_benchmark.py) | Regression coverage for load benchmark. | `_config`, `_spec`, `test_full_load_config_covers_all_independent_variables_and_high_scale`, `test_load_workload_covers_every_query_category`, `test_event_stream_measures_latency_throughput_loss_and_alert_accuracy`, `test_event_stream_records_queue_loss`, `test_point_timeout_returns_without_waiting_for_running_worker`, `test_timeout_detection_accepts_common_spellings` (+3 definitions) |
| [test_monitoring_timeouts.py](../tests/monitoring/test_monitoring_timeouts.py) | Regression coverage for monitoring timeouts. | `_statuses`, `test_distributed_scalability_timeout_continues_other_reasoners` |
| [test_patient_load.py](../tests/monitoring/test_patient_load.py) | Regression coverage for patient load. | `test_patient_load_attempts_later_profiles_after_prepare_timeout` |
| [test_physical.py](../tests/monitoring/test_physical.py) | Regression coverage for physical. | `test_physical_inventory_has_expected_addresses`, `test_balancer_assigns_every_query_once_and_uses_fast_node` |
| [test_physical_suite.py](../tests/monitoring/test_physical_suite.py) | Regression coverage for physical suite. | `_result`, `test_all_runs_every_family_before_reporting_invalid_evidence`, `test_timeouts_remain_censored_without_becoming_hard_failures` |
| [test_policy_evaluation.py](../tests/monitoring/test_policy_evaluation.py) | Regression coverage for policy evaluation. | `_read`, `test_policy_engine_matches_configured_ground_truth`, `test_four_policy_evaluations_export_reproducible_csv_and_png`, `test_cost_breakdown_uses_consistent_per_decision_units`, `test_effectiveness_uncertainty_uses_repetitions_not_scenarios`, `test_missing_memory_is_not_reported_as_zero` |
| [test_preflight.py](../tests/monitoring/test_preflight.py) | Regression coverage for preflight. | `test_repository_workloads_pass_capacity_preflight`, `test_preflight_rejects_target_that_would_shrink_graph`, `test_selected_load_profiles_are_checked` |
| [test_progress.py](../tests/monitoring/test_progress.py) | Regression coverage for progress. | `test_progress_is_printed_and_persisted_atomically` |
| [test_study.py](../tests/monitoring/test_study.py) | Regression coverage for study. | `test_policy_cost_study_config_loads`, `test_query_characterization_uses_real_catalog`, `test_generate_study_trace_is_reproducible`, `test_category_cost_analysis_joins_query_metadata`, `test_static_positions_are_reproducible`, `test_future_mobility_requires_an_explicit_plugin`, `test_trace_arrivals_are_replayed_exactly`, `test_weighted_category_selection_respects_zero_weights` |
| [test_suite_workflow.py](../tests/monitoring/test_suite_workflow.py) | The all-tests workflow preserves workload selection and native coverage. | `test_suite_uses_selected_configs_and_topology`, `test_suite_enables_native_tests_and_records_junit` |
| [test_timeout_skip_policy.py](../tests/monitoring/test_timeout_skip_policy.py) | Independent timeout skip scopes, shared by both physical coordinators. | `test_policy_validation`, `test_toml_loads_policy`, `test_typed_timeout_classification_does_not_hide_errors`, `test_streak_reset_reasoner_isolation_and_latched_scopes`, `coordinator`, `test_scalability_setup_skip_scopes`, `test_cumulative_setup_skip_scopes`, `test_threshold_counts_actual_attempts` (+13 definitions) |
| [test_unlimited.py](../tests/monitoring/test_unlimited.py) | Unlimited execution must complete slow work, not hide failed work. | `test_unlimited_local_and_future_waits_exceed_budget`, `test_unlimited_http_disables_worker_alarm_and_socket_deadline`, `test_unlimited_suite_propagates_policy_to_all_physical_families` |

## tests/reporting

| File | Responsibility | Main definitions |
| --- | --- | --- |
| [test_csv_utils.py](../tests/reporting/test_csv_utils.py) | Regression coverage for csv utils. | `_read`, `test_write_dict_rows_uses_ordered_union_of_columns`, `test_write_dict_rows_preserves_previous_file_on_failure` |
| [test_documentation.py](../tests/reporting/test_documentation.py) | Regression coverage for documentation. | `test_active_documentation_links_and_generated_references_are_current` |
| [test_experiment_reporting.py](../tests/reporting/test_experiment_reporting.py) | Regression coverage for experiment reporting. | `test_experiment_coverage_keeps_timeouts_and_failures` |
| [test_load_reporting.py](../tests/reporting/test_load_reporting.py) | Regression coverage for load reporting. | `test_load_plots_use_only_recorded_profiles` |
| [test_normalize.py](../tests/reporting/test_normalize.py) | Regression coverage for normalize. | `test_only_new_summaries_receive_a_canonical_envelope`, `test_envelope_preserves_identity_and_censoring` |
| [test_publication.py](../tests/reporting/test_publication.py) | Regression coverage for publication. | `test_skipped_points_are_not_observed_timeouts`, `test_reference_timeout_retains_timing_but_excludes_point_from_curves`, `test_validation_mismatch_excludes_only_its_exact_point`, `test_patient_suite_applies_budget_and_preserves_all_families`, `test_report_does_not_fabricate_completed_timings`, `test_curves_preserve_zero_measurements_and_png_only`, `test_progression_figure_requires_two_distinct_completed_x_values`, `test_rejected_report_retains_only_integrity_diagnostics` (+21 definitions) |
| [test_result_contract.py](../tests/reporting/test_result_contract.py) | Regression coverage for result contract. | `test_result_contract_accepts_current_metadata`, `test_result_contract_rejects_legacy_results`, `test_result_contract_rejects_results_without_reasoning_contract`, `test_result_contract_rejects_ontology_before_english_correction`, `test_result_contract_rejects_results_from_another_source_build`, `test_result_contract_rejects_same_version_changed_semantic_inputs` |

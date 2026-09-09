# Physical results audit and figure catalogue

## Categories And Policies

- [category-cost-owlrl](categories-and-policies/category-cost-owlrl.png)
- [category-cost-rdfs](categories-and-policies/category-cost-rdfs.png)
- [category-cost-rdfs_owlrl](categories-and-policies/category-cost-rdfs_owlrl.png)
- [category-tail-and-total-rdfs](categories-and-policies/category-tail-and-total-rdfs.png)
- [category-tail-and-total-owlrl](categories-and-policies/category-tail-and-total-owlrl.png)
- [category-tail-and-total-rdfs_owlrl](categories-and-policies/category-tail-and-total-rdfs_owlrl.png)
- [policy-total-cost-rdfs](categories-and-policies/policy-total-cost-rdfs.png)
- [policy-total-cost-owlrl](categories-and-policies/policy-total-cost-owlrl.png)
- [policy-total-cost-rdfs_owlrl](categories-and-policies/policy-total-cost-rdfs_owlrl.png)
- [category-evaluation-methods](categories-and-policies/category-evaluation-methods.png)

## Coverage And Integrity

- [load-failures-and-loss](coverage-and-integrity/load-failures-and-loss.png)
- [execution-coverage](coverage-and-integrity/execution-coverage.png)

## Network Scenarios

- [network-scenarios-and-observed-overhead](network-scenarios/network-scenarios-and-observed-overhead.png)

## Nodes And Layers

- [hardware-rule_count-rdfs](nodes-and-layers/hardware-rule_count-rdfs.png)
- [hardware-target_triples-rdfs](nodes-and-layers/hardware-target_triples-rdfs.png)
- [hardware-users-rdfs](nodes-and-layers/hardware-users-rdfs.png)
- [hardware-rule_count-owlrl](nodes-and-layers/hardware-rule_count-owlrl.png)
- [hardware-target_triples-owlrl](nodes-and-layers/hardware-target_triples-owlrl.png)
- [hardware-users-owlrl](nodes-and-layers/hardware-users-owlrl.png)
- [hardware-rule_count-rdfs_owlrl](nodes-and-layers/hardware-rule_count-rdfs_owlrl.png)
- [hardware-target_triples-rdfs_owlrl](nodes-and-layers/hardware-target_triples-rdfs_owlrl.png)
- [hardware-users-rdfs_owlrl](nodes-and-layers/hardware-users-rdfs_owlrl.png)
- [node-category-sharded-rdfs](nodes-and-layers/node-category-sharded-rdfs.png)
- [node-category-sharded-owlrl](nodes-and-layers/node-category-sharded-owlrl.png)
- [node-category-sharded-rdfs_owlrl](nodes-and-layers/node-category-sharded-rdfs_owlrl.png)
- [node-category-replicated-rdfs](nodes-and-layers/node-category-replicated-rdfs.png)
- [node-category-replicated-owlrl](nodes-and-layers/node-category-replicated-owlrl.png)
- [node-category-replicated-rdfs_owlrl](nodes-and-layers/node-category-replicated-rdfs_owlrl.png)
- [node-expensive-queries-sharded](nodes-and-layers/node-expensive-queries-sharded.png)
- [node-expensive-queries-replicated](nodes-and-layers/node-expensive-queries-replicated.png)
- [continuum-layer-query-work](nodes-and-layers/continuum-layer-query-work.png)

## Queries

- [query-complexity-cost-rdfs](queries/query-complexity-cost-rdfs.png)
- [query-complexity-cost-owlrl](queries/query-complexity-cost-owlrl.png)
- [query-complexity-cost-rdfs_owlrl](queries/query-complexity-cost-rdfs_owlrl.png)
- [expensive-queries-sharded](queries/expensive-queries-sharded.png)
- [expensive-queries-replicated](queries/expensive-queries-replicated.png)

## Recovery And Validation

- [extended-budget-load-validation](recovery-and-validation/extended-budget-load-validation.png)

## Scalability And Placement

- [sharded-cumulative-time](scalability-and-placement/sharded-cumulative-time.png)
- [sharded-cumulative-resources](scalability-and-placement/sharded-cumulative-resources.png)
- [sharded-scalability-time](scalability-and-placement/sharded-scalability-time.png)
- [sharded-scalability-resources](scalability-and-placement/sharded-scalability-resources.png)
- [replicated-cumulative-time](scalability-and-placement/replicated-cumulative-time.png)
- [replicated-scalability-time](scalability-and-placement/replicated-scalability-time.png)
- [physical-scale-out](scalability-and-placement/physical-scale-out.png)
- [distributed-ontology-cost](scalability-and-placement/distributed-ontology-cost.png)
- [placement-scalability-rdfs](scalability-and-placement/placement-scalability-rdfs.png)
- [placement-scalability-owlrl](scalability-and-placement/placement-scalability-owlrl.png)
- [placement-scalability-rdfs_owlrl](scalability-and-placement/placement-scalability-rdfs_owlrl.png)
- [placement-cumulative-rdfs](scalability-and-placement/placement-cumulative-rdfs.png)
- [placement-cumulative-owlrl](scalability-and-placement/placement-cumulative-owlrl.png)
- [placement-cumulative-rdfs_owlrl](scalability-and-placement/placement-cumulative-rdfs_owlrl.png)

## Interpretation and limitations

replicated-cumulative-resources: no completed measurements for the requested metrics; inspect missing telemetry and execution coverage.

replicated-scalability-resources: no completed measurements for the requested metrics; inspect missing telemetry and execution coverage.

Data integrity: 0 failed checks; event conservation, nonnegative metrics and recorded result equivalence checked.

Category/policy costs use matched profile nodes-1, selected for the largest minimum completed coverage across observed reasoners; incomplete requests remain in coverage.

Matched node/category/query comparisons use synthetic_users=10, completed parent runs in both layouts and all three reasoners; worker timings include routing and fan-out.

Policy associations and cumulative category additions are observational. No matched policies-disabled intervention exists here; category costs and cumulative changes do not establish causal policy overhead. Policy weights in cost tables are attribution fractions, not measured decision importance.

Supplementary extended-budget load: 3/3 points completed; 300 processed and 0 lost events. Source: /home/dsdservidor/Documentos/Continuum_Monitoring/outputs/audit/patient-load/physical

Nodes are colocated in one room (operator confirmation). Network-distance plots use explicit analytical scenarios; no geographic node positions or mobility trajectories are inferred.

sharded/cumulative: {'completed': 144}; frequent errors: []

sharded/scalability: {'completed': 33, 'timeout': 3, 'skipped': 18}; frequent errors: [('RuntimeError: Distributed phase \'partitioned-queries-batch-16-of-21\' failed on role=edge3 endpoint=http://10.151.73.173:8391 after 1158.41 ms: HTTPError: HTTP Error 408: Request Timeout; worker_response={"error": "worker phase exceeded 1.0s", "timeout": true}; query_ids=BASE-Q24,EXT-Q25,EXT-Q53,EXT-Q73', 1), ('RuntimeError: Distributed phase \'partitioned-queries-batch-7-of-21\' failed on role=edge1 endpoint=http://10.151.73.34:8391 after 22564.78 ms: HTTPError: HTTP Error 408: Request Timeout; worker_response={"error": "worker phase exceeded 22.3s", "timeout": true}; query_ids=BASE-Q12,EXT-Q15,EXT-Q38,EXT-Q63', 1), ('RuntimeError: Distributed phase \'partitioned-prepare\' failed on role=edge3 endpoint=http://10.151.73.173:8391 after 58191.50 ms: HTTPError: HTTP Error 408: Request Timeout; worker_response={"error": "worker phase exceeded 58.0s", "timeout": true}', 1)]

replicated/cumulative: {'completed': 144}; frequent errors: []

replicated/scalability: {'completed': 27, 'timeout': 3, 'skipped': 24}; frequent errors: [('RuntimeError: Distributed phase \'prepare\' failed on role=edge1 endpoint=http://10.151.73.34:8391 after 58068.58 ms: HTTPError: HTTP Error 408: Request Timeout; worker_response={"error": "worker phase exceeded 58.0s", "timeout": true}', 1), ('RuntimeError: Distributed phase \'prepare\' failed on role=edge3 endpoint=http://10.151.73.173:8391 after 58112.91 ms: HTTPError: HTTP Error 408: Request Timeout; worker_response={"error": "worker phase exceeded 58.0s", "timeout": true}', 1), ('RuntimeError: Distributed phase \'prepare\' failed on role=edge1 endpoint=http://10.151.73.34:8391 after 58161.42 ms: HTTPError: HTTP Error 408: Request Timeout; worker_response={"error": "worker phase exceeded 58.0s", "timeout": true}', 1)]

physical/load: {'timeout': 39, 'skipped': 168}; frequent errors: [('RuntimeError: Distributed phase \'load-prepare\' failed on role=fog endpoint=http://10.151.73.241:8391 after 44162.33 ms: HTTPError: HTTP Error 408: Request Timeout; worker_response={"error": "worker phase exceeded 44.0s", "timeout": true}', 1), ('RuntimeError: Distributed phase \'load-prepare\' failed on role=edge1 endpoint=http://10.151.73.34:8391 after 44134.09 ms: HTTPError: HTTP Error 408: Request Timeout; worker_response={"error": "worker phase exceeded 44.0s", "timeout": true}', 1), ('RuntimeError: Distributed phase \'load-prepare\' failed on role=edge1 endpoint=http://10.151.73.34:8391 after 44235.44 ms: HTTPError: HTTP Error 408: Request Timeout; worker_response={"error": "worker phase exceeded 44.0s", "timeout": true}', 1)]

scale-out: {'completed': 11, 'timeout': 6, 'skipped': 16, 'failed': 2}; frequent errors: [('RuntimeError: Distributed phase \'experiment-balanced-queries\' failed on role=cloud endpoint=http://127.0.0.1:8391 after 8885.81 ms: HTTPError: HTTP Error 408: Request Timeout; worker_response={"error": "worker phase exceeded 8.9s", "timeout": true}; query_ids=EXT-Q15,EXT-Q74,EXT-Q26,EXT-Q73,EXT-Q16,BASE-Q10,EXT-Q22,EXT-Q25,EXT-Q18,EXT-Q13,EXT-Q14,EXT-Q24,...(+103)', 1), ('RuntimeError: Distributed phase \'experiment-balanced-queries\' failed on role=cloud endpoint=http://127.0.0.1:8391 after 7956.58 ms: HTTPError: HTTP Error 408: Request Timeout; worker_response={"error": "worker phase exceeded 8.0s", "timeout": true}; query_ids=EXT-Q15,EXT-Q74,EXT-Q26,EXT-Q73,EXT-Q16,EXT-Q22,BASE-Q10,EXT-Q80,EXT-Q25,EXT-Q18,EXT-Q13,EXT-Q14,...(+103)', 1), ('RuntimeError: Distributed phase \'experiment-balanced-queries\' failed on role=edge1 endpoint=http://10.151.73.34:8391 after 19146.18 ms: HTTPError: HTTP Error 408: Request Timeout; worker_response={"error": "worker phase exceeded 19.1s", "timeout": true}; query_ids=BASE-Q01,BASE-Q02,BASE-Q03,BASE-Q04,BASE-Q05,BASE-Q06,BASE-Q07,BASE-Q08,BASE-Q09,BASE-Q10,BASE-Q11,BASE-Q12,...(+103)', 1)]

reasoning-hardware: {'completed': 126, 'timeout': 44, 'skipped': 505}; frequent errors: [('HTTPError: HTTP Error 408: Request Timeout; worker_response={"error": "worker phase exceeded 44.0s", "timeout": true}', 44)]

distributed-ontology: {'completed': 24, 'timeout': 3, 'skipped': 27}; frequent errors: [('RuntimeError: Distributed phase \'experiment-partitioned-prepare\' failed on role=edge2 endpoint=http://10.151.73.143:8391 after 44448.24 ms: HTTPError: HTTP Error 408: Request Timeout; worker_response={"error": "worker phase exceeded 44.0s", "timeout": true}', 1), ("RuntimeError: Distributed phase 'experiment-federated-queries' failed on role=edge2 endpoint=http://10.151.73.143:8391 after 29306.84 ms: TimeoutError: timed out; query_ids=BASE-Q01,BASE-Q02,BASE-Q03,BASE-Q04,BASE-Q05,BASE-Q09,BASE-Q10,BASE-Q12,BASE-Q13,BASE-Q15,BASE-Q16,BASE-Q17,...(+68)", 1), ("RuntimeError: Distributed phase 'experiment-partitioned-prepare' failed on role=edge1 endpoint=http://10.151.73.34:8391 after 45224.33 ms: TimeoutError: timed out", 1)]

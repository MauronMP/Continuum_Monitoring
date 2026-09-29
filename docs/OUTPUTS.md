# Outputs and Figures

All generated evidence belongs under `outputs/`. The policy evaluation uses this
layout:

```text
outputs/policy-evaluation/
├── configuration.json
├── manifest.json
├── metadata.json
├── effectiveness/
│   ├── policy_effectiveness.csv
│   └── policy-effectiveness.png
├── dynamic-adaptation/
│   ├── dynamic_adaptation.csv
│   └── dynamic-adaptation.png
├── scalability/
│   ├── policy_scalability.csv
│   └── policy-scalability.png
└── computational-cost/
    ├── computational_cost.csv
    └── computational-cost.png
```

Run measurement and plotting separately:

```bash
continuum-bench policy-evaluation all \
  --evaluation-config configs/policy-evaluation.toml \
  --output-dir outputs/policy-evaluation
continuum-bench policy-evaluation plot \
  --output-dir outputs/policy-evaluation
```

Figures are generated only as 300 dpi PNG files. A missing CSV produces no
figure; it is never replaced with fabricated data. The four CSV files remain the
authoritative evidence and can be processed without Matplotlib.

The shared columns are `experiment_id`, `scenario_id`, `strategy`, `load_size`,
`repetition`, `policy_category`, `seed` and `status`. Experiment-specific fields
retain explicit units in their names, such as `_ms`, `_seconds`, `_mib`,
`_percent` and `_bytes`.

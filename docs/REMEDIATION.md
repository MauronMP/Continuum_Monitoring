# Operational remediation

Use the complete six-node topology; obsolete five-node profiles have been removed.
The current installation and restart procedures are in [Installation](INSTALLATION.md)
and [Complete execution](COMPLETE_EXECUTION.md).

## Distinguish failure classes

- Version/digest mismatch: synchronize a frozen release and restart all workers
  before acquiring new evidence. Do not relabel old data as the new revision.
- Busy worker: the single-threaded health endpoint can be unavailable while
  native reasoning runs. Inspect the managed process before declaring a host offline.
- Shutdown exit 22: the existing five-second stop wait can expire before a worker
  disappears. Check the process and retry startup after exit; healthy nodes remain.
- Allocation failure: reducing workload or validating a 64-bit worker installation
  may be necessary. Longer timeouts do not increase address space.
- Semantic mismatch: retain invalid outcomes and investigate source selection,
  fragment closure, merge semantics and backend contracts. Do not bypass validation.
- Missing publication family: acquire it under a compatible frozen release;
  diagnostic plots of partial results do not complete the campaign.

See [Ontology review](ONTOLOGY_REVIEW.md) for recorded model-data debt and
[Ontology distribution](ONTOLOGY_DISTRIBUTION.md) for implementation boundaries.

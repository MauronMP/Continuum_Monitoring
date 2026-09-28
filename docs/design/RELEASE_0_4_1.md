# Release 0.4.1: six-node evidence compatibility

Version 0.4.1 is a correctness release for the six-node physical continuum. It
does not reinterpret results produced by 0.4.0.

The active benchmark matrix is RDFS, HermiT, Openllet, JFact and Konclude for
monitoring, load, campaign and distributed reasoning scalability. Identity,
OWL RL, combined RDFS+OWL RL and ELK remain optional adapter diagnostics and
historical-result labels, but active TOML configurations do not execute them.

The Mist node is a fourth data authority. Increasing the authority count exposed
two execution-plan defects: `EXT-Q36` used the wrong authority key and
`EXT-Q39` combined data from several authorities while declaring a single
source. The corrected plan routes `EXT-Q36` through `UserD`, evaluates
`EXT-Q39` across authorities with set union and keeps transfer identifiers with
their transfer events. Offline validation matches all 115 canonical query
projections for each active backend over six fragments.

Publication reporting now compares recorded metadata with the active software
version and topology. It rejects stale node counts, stale releases,
reconstructed metadata, missing benchmark families, semantic mismatches and
families without completed observations. Figures use a consistent 300-DPI
style, panel labels, sample coverage and an embedded historical-evidence notice
when the inputs are incompatible.

Worker protocol 9 publishes and validates the benchmark release and a build
identifier derived from every installed Python source file, in addition to
ontology, query, reasoning and topology contracts. A worker from another
release or source tree is rejected even when those other fields happen to match.

The physical inventory records the Raspberry Pi hardware architecture as
AArch64. Runtime health records the execution ABI separately; Fog and the three
Edge nodes currently run 32-bit `armhf` Python on an AArch64 kernel.

Existing September 22 results use five nodes and version 0.4.0. They remain
descriptive historical evidence and must not support claims about the current
six-node architecture. A new complete physical suite is required after every
node has the 0.4.1 source and reasoner runtimes.

"""Display identities; historical profiles are never aliases for current engines."""

CURRENT_PROFILES = ("rdfs", "hermit", "openllet", "jfact", "konclude")
LABELS = dict(zip(CURRENT_PROFILES, ("RDFS", "HermiT", "Openllet", "JFact", "Konclude")))
LABELS.update({"owlrl": "OWL RL", "rdfs_owlrl": "RDFS + OWL RL"})
COLORS = dict(zip(LABELS, ("#0072B2", "#E69F00", "#CC79A7", "#56B4E9", "#000000", "#D55E00", "#009E73")))
LAYOUTS = {"distributed": "Distributed", "replicated": "Replicated", "sharded": "Sharded (historical)"}
CURRENT_LAYOUTS = {key: LAYOUTS[key] for key in ("distributed", "replicated")}


def observed_profiles(rows):
    present = {row.get("reasoner", "unknown") for row in rows}
    return [key for key in LABELS if key in present] + sorted(present - LABELS.keys())


def outcome(row):
    value = row.get("status") or "unknown"
    if value == "completed":
        return "completed"
    if value.startswith("skipped"):
        return "skipped"
    if "timeout" in value:
        return "timeout"
    return "failed"

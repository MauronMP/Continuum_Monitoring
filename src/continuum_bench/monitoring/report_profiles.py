"""Display identities for the active physical reasoner matrix."""

CURRENT_PROFILES = (
    "rdfs", "hermit", "openllet", "jfact", "konclude",
)
LABELS = {
    "rdfs": "RDFS", "hermit": "HermiT", "openllet": "Openllet", "jfact": "JFact",
    "konclude": "Konclude",
}
COLORS = dict(zip(
    CURRENT_PROFILES,
    ("#0072B2", "#E69F00", "#56B4E9", "#D55E00", "#000000"),
))
LAYOUTS = {"distributed": "Distributed", "replicated": "Replicated"}
CURRENT_LAYOUTS = dict(LAYOUTS)


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

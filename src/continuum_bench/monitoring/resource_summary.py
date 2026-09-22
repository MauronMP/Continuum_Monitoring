"""Explicit scope for resources outside the Python worker process."""
def native_resources(prepared):
    rows=list(prepared.values())
    cpu=[row.get('children_cpu_ms') for row in rows]
    rss=[row.get('child_peak_rss_kib_lifetime') for row in rows]
    return {
        'node_prepare_children_cpu_ms_sum': sum(cpu) if cpu and all(v is not None for v in cpu) else None,
        'max_child_peak_rss_kib_lifetime': max(rss) if rss and all(v is not None for v in rss) else None,
        'process_resource_scope': 'python-worker-only',
        'children_cpu_scope': 'waited-for-children-preparation-delta',
        'child_memory_scope': 'lifetime-high-water-not-per-point-process-tree-peak',
    }

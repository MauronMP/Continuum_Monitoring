"""Deterministic read-only replica routing; origins always remain in their pools."""
from dataclasses import replace
from threading import Lock
from time import monotonic


class ReplicaRouter:
    def __init__(self, endpoints, owners):
        by_id={e.role:e for e in endpoints}
        if set(owners)-by_id.keys() or set(owners.values())-by_id.keys() or set(owners)&set(owners.values()):
            raise ValueError('Invalid replica ownership map')
        self.pools={e.role:[e] for e in endpoints if e.role not in owners}
        for replica,owner in sorted(owners.items()):self.pools[owner].append(by_id[replica])
        self.records=[];self.lock=Lock()

    def select(self, primary, index):
        pool=self.pools[primary.role]
        return pool[index % len(pool)]

    def request(self, request, primary, index, payload, timeout, context):
        target=self.select(primary,index);started=monotonic();status='completed';error='';response={}
        try:
            response=request(target.url,'/queries',payload,timeout=timeout,retries=0)
            return response
        except Exception as exc:
            status='failed';error=str(exc)
            raise RuntimeError(f'role={primary.role} worker={target.role} endpoint={target.url}; {exc}') from exc
        finally:
            with self.lock:
                self.records.append(dict(**context,logical_owner=primary.role,worker=target.role,
                    endpoint=target.url,is_origin=target.role==primary.role,status=status,
                    elapsed_ms=(monotonic()-started)*1000,process_cpu_ms=response.get('process_cpu_ms'),
                    current_rss_kib=response.get('current_rss_kib'),query_count=response.get('query_count'),error=error))


def expanded_topology(config,count,replicas,base_port):
    """Retain every original host and add copies; never repartition on replica IDs."""
    from ..container_scale.config import logical_topology
    original=logical_topology(config,count);by_id={n.node_id:n for n in original.active_nodes}
    slots={};nodes=list(original.active_nodes)
    entries=[(r['id'],r['owner'],r['host']) for r in replicas]
    if len({e[0] for e in entries})!=len(entries) or set(e[0] for e in entries)&by_id.keys():raise ValueError('Duplicate replica identity')
    for worker,owner,host in entries:
        node=by_id[owner];physical=config.topology.node(host);slot=slots.get(host,0);slots[host]=slot+1
        port=base_port+slot
        if port>65535:raise ValueError('Replica port range exhausted')
        nodes.append(replace(node,node_id=worker,host=physical.host,port=port,endpoint=f'http://{physical.host}:{port}',
            local=physical.local,latitude=physical.latitude,longitude=physical.longitude,altitude_m=physical.altitude_m,region=physical.region))
    return replace(original,nodes=tuple(nodes))


def routing_coverage(records, layout, expected_workers):
    """Require participation in every observed reasoner/concurrency stratum."""
    selected = [r for r in records if r["layout"] == layout]
    strata = sorted({(r.get("reasoner", ""), r.get("concurrency", "")) for r in selected})
    missing = []
    for reasoner, concurrency in strata:
        seen = {r["worker"] for r in selected
                if (r.get("reasoner", ""), r.get("concurrency", "")) == (reasoner, concurrency)}
        missing.append(dict(reasoner=reasoner, concurrency=concurrency,
                            missing_workers=sorted(set(expected_workers) - seen)))
    return dict(complete=bool(strata) and all(not s["missing_workers"] for s in missing),
                strata=missing)


def progress_assessment(before, after):
    """Completion improvement, rather than non-regression, justifies another expansion."""
    before_rate = before["request_failures"] / before["requests"] if before["requests"] else 1
    after_rate = after["request_failures"] / after["requests"] if after["requests"] else 1
    regressed = (after["preparation_failures"] > before["preparation_failures"]
                 or after_rate > before_rate)
    improved = not regressed and (
        after["preparation_failures"] < before["preparation_failures"] or after_rate < before_rate)
    return improved, regressed

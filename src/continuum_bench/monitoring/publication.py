"""Evidence-led physical reports: raw data, censoring, policy costs and PNGs."""
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import textwrap
import warnings

from .. import __version__
from ..plot_environment import configure_matplotlib
configure_matplotlib()
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import numpy as np
from .figure_style import save_png

from .report_profiles import COLORS, LABELS, LAYOUTS, CURRENT_LAYOUTS, observed_profiles, outcome
from ..reasoners import PHYSICAL_REASONERS

STATUS = {'completed':'#009E73','timeout':'#E69F00','skipped':'#999999','failed':'#CC79A7'}
REJECTED_REPORT_FIGURES = frozenset({
    'evidence-readiness',
    'execution-coverage',
    'load-completion-matrix',
    'load-failures-and-loss',
    'semantic-equivalence-coverage',
})
REJECTED_REPORT_TABLES = frozenset({
    'data-integrity.csv',
    'execution-coverage.csv',
    'figure-statistics.csv',
})


def read_csv(path):
    if not path.is_file(): return []
    # Federated result-key bags can exceed Python's default 128-KiB CSV field limit.
    csv.field_size_limit(max(csv.field_size_limit(), 64 * 1024 * 1024))
    with path.open(newline='') as handle: return list(csv.DictReader(handle))


def number(row, key):
    try: value = float(row.get(key,''))
    except (ValueError, TypeError): return None
    return value if math.isfinite(value) else None


def write_csv(path, rows):
    if not rows:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=sorted(set().union(*(r.keys() for r in rows))))
        writer.writeheader(); writer.writerows(rows)


def _validation_key(row):
    """Identify one measured point independently of its individual queries."""

    return (
        row.get('reasoner', ''),
        str(row.get('synthetic_users', 0) or 0),
        str(row.get('repetition', '') or ''),
        str(row.get('stage', '') or ''),
    )


def validated_evidence_rows(rows, validations=()):
    """Return report rows with exact semantic acceptance applied per point.

    Physical timings remain in the raw CSV. A point is eligible for performance
    curves only when its canonical reference completed and every recorded query
    projection matched that reference.
    """

    invalid_points = {
        _validation_key(row) for row in validations
        if row.get('valid', '').lower() != 'true'
    }
    normalized = []
    for source in rows:
        row = dict(source)
        if outcome(row) == 'completed':
            reference_status = row.get('reference_status', '')
            if reference_status and reference_status not in {'completed', 'disabled'}:
                row['status'] = 'unvalidated_results'
                row['error'] = (
                    'Canonical reference did not complete; physical timing is '
                    'retained but excluded from validated performance evidence'
                )
            elif _validation_key(row) in invalid_points:
                row['status'] = 'invalid_results'
                row['error'] = (
                    'Distributed query results differ from canonical reference'
                )
        normalized.append(row)
    return normalized


def figure_group(name):
    if name.startswith(('node-', 'continuum-layer-', 'hardware-')): return 'nodes-and-layers'
    if name.startswith(('query-', 'expensive-')): return 'queries'
    if name.startswith(('category-', 'policy-')): return 'categories-and-policies'
    if name.startswith(('placement-', 'replicated-', 'physical-scale-', 'distributed-')): return 'scalability-and-placement'
    if name.startswith('network-'): return 'network-scenarios'
    if name.startswith('extended-'): return 'recovery-and-validation'
    return 'coverage-and-integrity'


class Report:
    def __init__(self, root, inputs, output, validation_input=None):
        self.root, self.inputs, self.output = root, inputs, output
        self.validation_input=validation_input
        self.figures=[]; self.findings=[]; self.sources={}; self.tables=[]; self.statistics=[]; self.checks=[]
        output.mkdir(parents=True,exist_ok=True)
        self.evidence_context=self._evidence_context()

    def _evidence_context(self):
        """Compare recorded evidence with the active software and topology."""
        from ..protocol import SOFTWARE_BUILD_ID
        from ..topology import load_topology
        topology=load_topology(
            self.root/'configs/topologies/physical/topology.toml', 'physical'
        )
        metadata_paths = [
            self.inputs/'monitoring'/layout/suite/'metadata.json'
            for layout in CURRENT_LAYOUTS for suite in ('cumulative','scalability')
        ] + [
            self.inputs/'load/metadata.json',
            *(
                self.inputs/f'experiments/{name}/metadata.json'
                for name in ('scale-out','reasoning-hardware','distributed-ontology',
                             'distributed-reasoning-scalability')
            ),
        ]
        versions=set(); build_ids=set(); node_counts=set(); fingerprints=set()
        missing_build_ids=[]; missing_fingerprints=[]
        reconstructed=[]; records=[]
        for path in metadata_paths:
            if not path.is_file():
                continue
            try:
                value=json.loads(path.read_text())
            except (OSError,json.JSONDecodeError):
                continue
            runtime_versions=value.get('runtime_versions',{})
            version=(value.get('benchmark_version') or
                     runtime_versions.get('continuum-monitoring-benchmark') or
                     runtime_versions.get('continuum-ontology-benchmark'))
            endpoints=(value.get('endpoints') or value.get('available_endpoints') or
                       value.get('topology',{}).get('endpoint_override') or [])
            count=value.get('node_count') or (len(endpoints) if endpoints else None)
            if version: versions.add(str(version))
            build_id=value.get('software_build_id')
            if build_id:
                build_ids.add(str(build_id))
            else:
                missing_build_ids.append(str(path.resolve()))
            if count: node_counts.add(int(count))
            fingerprint=value.get('topology_fingerprint')
            if fingerprint:
                fingerprints.add(str(fingerprint))
            else:
                missing_fingerprints.append(str(path.resolve()))
            if value.get('metadata_reconstructed_after_failed_validation'):
                reconstructed.append(str(path.resolve()))
            records.append(str(path.resolve()))
        return {
            'current_benchmark_version':__version__,
            'current_software_build_id':SOFTWARE_BUILD_ID,
            'current_topology_node_count':len(topology.active_nodes),
            'current_topology_fingerprint':topology.fingerprint,
            'recorded_benchmark_versions':sorted(versions),
            'recorded_software_build_ids':sorted(build_ids),
            'recorded_topology_node_counts':sorted(node_counts),
            'recorded_topology_fingerprints':sorted(fingerprints),
            'metadata_missing_build_id':missing_build_ids,
            'metadata_missing_topology_fingerprint':missing_fingerprints,
            'reconstructed_metadata':reconstructed,
            'metadata_records':records,
            'version_compatible':not versions or versions=={__version__},
            'build_compatible':(
                bool(records) and not missing_build_ids
                and build_ids=={SOFTWARE_BUILD_ID}
            ),
            'topology_compatible':not node_counts or node_counts=={len(topology.active_nodes)},
            'topology_fingerprint_compatible':(
                bool(records) and not missing_fingerprints
                and fingerprints=={topology.fingerprint}
            ),
        }

    def read(self,path):
        if path.name == "summary.csv" and path.is_file():
            from ..result_contract import require_release_metadata
            require_release_metadata(path.parent)
            metadata=path.parent/"metadata.json"
            if metadata.is_file(): self.sources[str(metadata.resolve())]=hashlib.sha256(metadata.read_bytes()).hexdigest()
        rows=read_csv(path)
        if path.is_file(): self.sources[str(path.resolve())]=hashlib.sha256(path.read_bytes()).hexdigest()
        return rows

    def save(self,fig,name,caption):
        title=name
        for key in sorted(LABELS, key=len, reverse=True):
            title=title.replace(key,LABELS[key])
        title=title.replace('-',' ').replace('_',' ')
        fig.suptitle(title[:1].upper()+title[1:],fontsize=12,fontweight='bold')
        incompatible = (
            not self.evidence_context['version_compatible']
            or not self.evidence_context['build_compatible']
            or not self.evidence_context['topology_compatible']
            or not self.evidence_context['topology_fingerprint_compatible']
        )
        if incompatible:
            caption=(
                'Historical evidence: recorded software build or topology differs from the active '
                f"{self.evidence_context['current_benchmark_version']} "
                f"{self.evidence_context['current_topology_node_count']}-node configuration. "
                + caption
            )
            fig.text(
                .5,
                .92,
                'HISTORICAL / INCOMPATIBLE EVIDENCE — NOT FOR PERFORMANCE CLAIMS',
                ha='center',
                va='center',
                fontsize=9,
                fontweight='bold',
                color='white',
                bbox={'boxstyle':'round,pad=.3','facecolor':'#B2182B','edgecolor':'none'},
            )
        wrapped=textwrap.fill(caption,width=155)
        fig.text(.01,.006,wrapped,fontsize=7.5,ha='left',va='bottom',color='#333333')
        panels=[ax for ax in fig.axes if ax.get_visible() and ax.get_label()!='<colorbar>']
        if len(panels)>1:
            for index,axis in enumerate(panels):
                axis.text(-.10,1.04,f'({chr(97+index)})',transform=axis.transAxes,
                          ha='right',va='bottom',fontsize=9,fontweight='bold')
        bottom=.10+.025*(wrapped.count('\n'))
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',message='This figure includes Axes that are not compatible with tight_layout')
            fig.tight_layout(rect=(0,bottom,1,.85 if incompatible else .94))
        folder = figure_group(name)
        paths = save_png(fig, self.output/folder/name)
        # Remove only this regenerated legacy flat figure; preserve raw evidence.
        (self.output/(name+'.png')).unlink(missing_ok=True)
        self.figures.extend(str(p) for p in paths)

    def coverage(self,datasets):
        fig,ax=plt.subplots(figsize=(12,max(4,len(datasets)*.55)))
        labels=[]; counts=[]
        for name,rows in datasets.items():
            count=Counter(outcome(r) for r in rows); labels.append(name); counts.append(count)
            self.tables.append({'dataset':name,'rows':len(rows),**{s:count[s] for s in STATUS}})
        left=np.zeros(len(labels)); annotation_threshold=max(sum(c.values()) for c in counts)*.025
        for status,color in STATUS.items():
            values=np.array([c[status] for c in counts]);ax.barh(labels,values,left=left,color=color,label=status.title())
            for i,(v,l) in enumerate(zip(values,left)):
                if v >= annotation_threshold:
                    ax.text(l+v/2,i,str(v),ha='center',va='center',fontsize=9)
            left+=values
        ax.invert_yaxis();ax.set_xlabel('Recorded points / rounds (counts, not equivalent workloads)');ax.legend(ncol=4,loc='upper center',bbox_to_anchor=(.5,1.12));ax.grid(axis='x',alpha=.2)
        self.save(fig,'execution-coverage','Skipped points are not measured timeouts. Counts are kept separate; no failed timing is treated as a completed observation.')

    def curves(self,rows,x,metrics,name,group='reasoner',min_distinct_x=1):
        completed=[r for r in rows if outcome(r)=='completed']
        if not completed:
            self.findings.append(
                f'{name}: no completed measurements for the requested metrics; '
                'inspect missing telemetry and execution coverage.'
            )
            return
        distinct_x={value for r in completed if (value:=number(r,x)) is not None}
        if len(distinct_x) < min_distinct_x:
            self.findings.append(
                f'{name}: suppressed because only {len(distinct_x)} distinct '
                f'completed {x} value(s) were recorded; at least '
                f'{min_distinct_x} are required for a progression figure.'
            )
            return
        available=[(key,label,div) for key,label,div in metrics if any(number(r,key) is not None for r in completed)]
        if not available:
            self.findings.append(f'{name}: no completed measurements for the requested metrics; inspect missing telemetry and execution coverage.');return
        fig,axes=plt.subplots(1,len(available),figsize=(6*len(available),4.6),squeeze=False)
        for ax,(key,label,div) in zip(axes[0],available):
            groups=defaultdict(list)
            for row in completed:
                xv,yv=number(row,x),number(row,key)
                if xv is not None and yv is not None:groups[(row.get(group,'unknown'),xv)].append(yv/div)
            for i,series in enumerate(sorted({g[0] for g in groups})):
                points=sorted((xv,values) for (s,xv),values in groups.items() if s==series)
                self.statistics.extend({"figure":name,"metric":key,"series":series,"x":xv,"n":len(values),"median":statistics.median(values),"minimum":min(values),"maximum":max(values)} for xv,values in points)
                xx=[p[0] for p in points];yy=[statistics.median(p[1]) for p in points]
                errors=np.array([[y-min(p[1]) for y,p in zip(yy,points)],[max(p[1])-y for y,p in zip(yy,points)]])
                ax.errorbar(xx,yy,yerr=errors,marker=['o','s','^','D','v'][i%5],capsize=3,
                            color=COLORS.get(series),label=LABELS.get(series,series),linewidth=1.5)
                if len(xx)==1:ax.set_xticks(xx)
            ax.set_xlabel(x.replace('_',' ').title());ax.set_ylabel(label);ax.grid(alpha=.2);ax.legend(fontsize=9)
        self.save(fig,name,f'Completed observations only ({len(completed)}/{len(rows)} rows). Points: median; whiskers: observed min–max, not confidence intervals.')

    def failure_diagnostics(self,rows,name="load-failures-and-loss"):
        dimensions={r.get("dimension") for r in rows}
        dimension=next(iter(dimensions)) if len(dimensions)==1 else "events_per_second"
        xfield={"users":"synthetic_users","rule_count":"rule_count","node_count":"node_count","target_triples":"target_triples"}.get(dimension,"events_per_second")
        counts=Counter((r.get('dimension','unknown'),outcome(r)) for r in rows)
        fig,axes=plt.subplots(1,2,figsize=(15,5))
        labels=sorted({d for d,_ in counts});bottom=np.zeros(len(labels))
        for status,color in STATUS.items():
            vals=[counts[d,status] for d in labels];axes[0].bar(range(len(labels)),vals,bottom=bottom,color=color,label=status.title());bottom+=vals
        axes[0].set_xticks(range(len(labels)),[d.replace('_',' ').title() for d in labels],rotation=25,ha='right',fontsize=9)
        axes[0].set_ylabel('Recorded points');axes[0].legend(fontsize=8)
        measured=[r for r in rows if outcome(r)!='skipped' and number(r,'event_loss_percent') is not None]
        for reasoner in observed_profiles(measured):
            selected=[r for r in measured if r.get('reasoner')==reasoner]
            axes[1].scatter([number(r,xfield) for r in selected],[number(r,'event_loss_percent') for r in selected],label=LABELS.get(reasoner,reasoner),color=COLORS.get(reasoner),alpha=.7)
        ticks=sorted({number(r,xfield) for r in measured if number(r,xfield) is not None})
        if len(ticks)<=8: axes[1].set_xticks(ticks)
        axes[1].set_xlabel(xfield.replace('_',' ').title());axes[1].set_ylabel('Unserved scheduled events (%)');axes[1].set_ylim(-2,102);axes[1].legend();axes[1].grid(alpha=.2)
        self.save(fig,name,'Failure diagnosis, not throughput or packet loss. Unserved events include failed preparation; skipped profiles have no observations.')

    def policy_costs(self):
        events=self.read(self.inputs/'load/event-runs.csv')
        counts=Counter((r.get('profile','unknown'),r.get('reasoner','unknown')) for r in events if r.get('processed','').lower()=='true')
        reasoners={r for _,r in counts}; profiles={p for p,_ in counts}
        shared=[p for p in profiles if all(counts[p,r]>0 for r in reasoners)]
        selected_profile=max(shared,key=lambda p:min(counts[p,r] for r in reasoners)) if shared else None
        if selected_profile:
            events=[r for r in events if r.get('profile')==selected_profile]
            self.findings.append(f'Category/policy costs use matched profile {selected_profile}, selected for the largest minimum completed coverage across observed reasoners; incomplete requests remain in coverage.')
        else:
            self.findings.append('No shared profile with completed requests across reasoners; category comparisons are exploratory workload mixtures.')
        catalog={r['id']:r for r in self.read(self.root/'queries/catalog.csv')}
        groups=defaultdict(list);policies=defaultdict(list)
        for event in events:
            spec=catalog.get(event.get('query_id'))
            if not spec:continue
            key=(event.get('reasoner','unknown'),spec['category']);groups[key].append(event)
            ids=[p.strip() for p in spec['policies'].split(',') if p.strip()]
            for policy in ids:policies[(key[0],policy)].append((event,1/len(ids)))
        summaries=[]
        for (reasoner,category),items in groups.items():
            good=[r for r in items if r.get('processed','').lower()=='true']
            entry={'reasoner':reasoner,'category':category,'attempted':len(items),'completed':len(good),'completion_percent':100*len(good)/len(items)}
            for key in ('engine_duration_ms','latency_ms','process_cpu_ms','current_rss_kib','request_bytes','response_bytes'):
                values=[v for r in good if (v:=number(r,key)) is not None]
                entry[key+'_median']=statistics.median(values) if values else None
                entry[key+'_p95']=float(np.percentile(values,95)) if values else None
                entry[key+'_sum']=sum(values) if values and key!='current_rss_kib' else None
            summaries.append(entry)
        write_csv(self.output/'category-cost-by-reasoner.csv',summaries)
        for reasoner in sorted({r['reasoner'] for r in summaries}):
            selected=sorted([
                r for r in summaries
                if r['reasoner']==reasoner and r['completed'] > 0
                and r['engine_duration_ms_median'] is not None
            ],key=lambda r:r['engine_duration_ms_median'])
            if not selected:continue
            fig,axes=plt.subplots(1,3,figsize=(18,max(5,len(selected)*.32)),sharey=True)
            labels=[f"{r['category']} (n={r['completed']}/{r['attempted']})" for r in selected]
            for ax,key,label,div in zip(axes,['engine_duration_ms_median','process_cpu_ms_median','current_rss_kib_median'],['Median query execution (ms)','Median attributed CPU (ms)','Median process RSS (MiB)'],[1,1,1024]):
                values=[r[key]/div if r[key] is not None else np.nan for r in selected]
                ax.barh(labels,values,color=COLORS.get(reasoner));ax.set_xlabel(label);ax.grid(axis='x',alpha=.2)
            self.save(fig,f'category-cost-{reasoner}',f'Conditional on completed requests; n=completed/attempted. CPU is batch-attributed; RSS is process memory. Matched profile: {selected_profile}.')
        for reasoner in observed_profiles(summaries):
            selected=sorted([
                r for r in summaries
                if r['reasoner']==reasoner and r['completed'] > 0
                and r['engine_duration_ms_sum'] is not None
            ],key=lambda r:r['engine_duration_ms_sum'])
            if not selected:continue
            fig,axes=plt.subplots(1,3,figsize=(18,max(5,len(selected)*.32)),sharey=True)
            labels=[f"{r['category']} (n={r['completed']})" for r in selected]
            for ax,key,label,div in zip(axes,['engine_duration_ms_median','engine_duration_ms_p95','engine_duration_ms_sum'],['Median query time (ms)','p95 query time (ms)','Total observed query time (s)'],[1,1,1000]):
                ax.barh(labels,[r[key]/div if r[key] is not None else np.nan for r in selected],color=COLORS.get(reasoner));ax.set_xlabel(label);ax.grid(axis='x',alpha=.2)
            self.save(fig,f'category-tail-and-total-{reasoner}',f'Matched profile {selected_profile}; completed requests only. Median, tail latency and frequency-weighted cost answer different questions. Small n limits p95 stability.')
        from ..queries import load_catalog
        from .study.sparql import characterize_query
        specs={spec.id:spec for spec in load_catalog(self.root/'queries/catalog.csv',self.root)}
        for reasoner in observed_profiles(events):
            query_groups=defaultdict(list)
            for event in events:
                if event.get('reasoner')==reasoner and event.get('processed','').lower()=='true' and number(event,'engine_duration_ms') is not None:
                    query_groups[event['query_id']].append(number(event,'engine_duration_ms'))
            points=[(qid,characterize_query(specs[qid]).structural_complexity,statistics.median(values),len(values)) for qid,values in query_groups.items() if qid in specs]
            if not points:continue
            fig,ax=plt.subplots(figsize=(10,5))
            ax.scatter([p[1] for p in points],[p[2] for p in points],s=[20+5*p[3] for p in points],alpha=.6,color=COLORS.get(reasoner),label=LABELS.get(reasoner,reasoner))
            for index,(qid,x,y,n) in enumerate(sorted(points,key=lambda p:p[2],reverse=True)[:5]):
                ax.annotate(qid,(x,y),xytext=(.78,.90-index*.1),textcoords='axes fraction',fontsize=9,arrowprops={'arrowstyle':'-','color':'#666666','lw':.6})
            ax.set_yscale('log');ax.set_xlabel('Static SPARQL structural-complexity score');ax.set_ylabel('Median observed query execution (ms)');ax.legend();ax.grid(alpha=.2)
            self.save(fig,f'query-complexity-cost-{reasoner}',f'Matched profile {selected_profile}; point size reflects completed sample count. Static syntax complexity is a descriptor, not a causal runtime model.')
        policy_rows=[]
        for (reasoner,policy),items in policies.items():
            measured=[(r,w) for r,w in items if r.get('processed','').lower()=='true' and number(r,'engine_duration_ms') is not None]
            weight=sum(w for r,w in measured)
            policy_rows.append({'reasoner':reasoner,'policy':policy,'completed_request_equivalents':weight,
                'attributed_query_ms':sum(number(r,'engine_duration_ms')*w for r,w in measured),
                'mean_query_ms':sum(number(r,'engine_duration_ms')*w for r,w in measured)/weight if weight else None})
        write_csv(self.output/'policy-cost-by-reasoner.csv',policy_rows)
        for reasoner in observed_profiles(policy_rows):
            selected=sorted([r for r in policy_rows if r['reasoner']==reasoner and r['mean_query_ms'] is not None],key=lambda r:r['attributed_query_ms'])[-15:]
            if not selected:continue
            fig,ax=plt.subplots(figsize=(10,6));ax.barh([r['policy'] for r in selected],[r['attributed_query_ms']/1000 for r in selected],color=COLORS.get(reasoner));ax.set_xlabel('Attributed total query execution (s)');ax.grid(axis='x',alpha=.2)
            self.save(fig,f'policy-total-cost-{reasoner}',f'Top 15 observed costs in profile {selected_profile}. Multi-policy queries contribute 1/N each. Total cost combines frequency and duration; incomplete workload.')

    def audit(self,datasets):
        for name,rows in datasets.items():
            incomplete_references = sum(
                outcome(row) == 'failed'
                and row.get('status') == 'unvalidated_results'
                for row in rows
            )
            if incomplete_references:
                self.checks.append({
                    'dataset': name,
                    'check': 'canonical reference completed',
                    'rows': len(rows),
                    'invalid': incomplete_references,
                    'status': 'failed',
                })
            for index,row in enumerate(rows):
                if outcome(row)=='skipped':continue
                offered,processed,lost=(number(row,key) for key in ('events_offered','events_processed','events_lost'))
                if all(v is not None for v in (offered,processed,lost)) and offered!=processed+lost:
                    self.checks.append({'dataset':name,'row':index,'check':'event conservation','status':'failed'})
                for field,value in row.items():
                    if field.endswith(('_ms','_kib','_bytes')):
                        v=number(row,field)
                        if v is not None and v<0:self.checks.append({'dataset':name,'row':index,'check':f'negative {field}','status':'failed'})
        for base in (self.inputs/'monitoring',self.inputs/'experiments'):
            for path in base.rglob('result-validation.csv'):
                rows=self.read(path);invalid=sum(r.get('valid','').lower()!='true' for r in rows)
                self.checks.append({'dataset':str(path),'check':'canonical result equivalence','rows':len(rows),'invalid':invalid,'status':'failed' if invalid else 'passed'})
        self.findings.append(f'Data integrity: {sum(r["status"]=="failed" for r in self.checks)} failed checks; event conservation, nonnegative metrics and recorded result equivalence checked.')
        write_csv(self.output/'data-integrity.csv',self.checks)

    def quality_figures(self, datasets):
        """Show semantic acceptance and capacity without turning missing data into zero."""
        validation_groups = []
        for base in (self.inputs/'monitoring', self.inputs/'experiments'):
            for path in sorted(base.rglob('result-validation.csv')):
                rows = self.read(path)
                if rows:
                    validation_groups.append((str(path.relative_to(self.inputs)).replace('/result-validation.csv',''), rows))
        observed = set(observed_profiles(
            [row for _, rows in validation_groups for row in rows]
        ))
        reasoners = [reasoner for reasoner in PHYSICAL_REASONERS if reasoner in observed]
        if validation_groups and reasoners:
            matrix = np.full((len(validation_groups), len(reasoners)), np.nan)
            labels = []
            counts = {}
            for y, (name, rows) in enumerate(validation_groups):
                labels.append(name.replace('monitoring/','').replace('experiments/',''))
                for x, reasoner in enumerate(reasoners):
                    selected = [r for r in rows if r.get('reasoner') == reasoner]
                    if selected:
                        valid = sum(r.get('valid','').lower() == 'true' for r in selected)
                        matrix[y,x] = 100 * valid / len(selected)
                        counts[y,x] = (valid, len(selected))
            fig, ax = plt.subplots(figsize=(max(9, 1.35*len(reasoners)), max(4, .8*len(labels)+2)))
            acceptance_cmap = ListedColormap(['#D55E00', '#009E73'])
            acceptance_norm = BoundaryNorm([-0.5, 99.999999, 100.5], acceptance_cmap.N)
            image = ax.imshow(np.ma.masked_invalid(matrix), norm=acceptance_norm,
                              cmap=acceptance_cmap, aspect='auto')
            ax.set_xticks(range(len(reasoners)), [LABELS.get(r,r) for r in reasoners], rotation=30, ha='right')
            ax.set_yticks(range(len(labels)), labels)
            for (y,x),(valid,total) in counts.items():
                value=matrix[y,x]
                ax.text(x,y,f'{valid}/{total}\n{value:.1f}%',ha='center',va='center',fontsize=8,
                        color='white' if value < 35 else 'black')
            colorbar=fig.colorbar(image,ax=ax,ticks=[50,100])
            colorbar.ax.set_yticklabels(['Mismatch present','All matched'])
            colorbar.set_label('Semantic acceptance')
            ax.set_xlabel('Reasoning backend'); ax.set_ylabel('Recorded validation dataset')
            self.save(fig,'semantic-equivalence-coverage',
                      'Every cell reports valid/checked query projections. Orange cells invalidate performance claims for that backend/dataset; missing cells were not evaluated.')

        scalability = {layout: datasets.get(f'{layout}/scalability', []) for layout in CURRENT_LAYOUTS}
        cumulative = {layout: datasets.get(f'{layout}/cumulative', []) for layout in CURRENT_LAYOUTS}
        profiles = observed_profiles([r for rows in (*scalability.values(), *cumulative.values()) for r in rows])
        if profiles:
            fig, axes = plt.subplots(1,2,figsize=(15,5.5))
            width = .8/max(1,len(CURRENT_LAYOUTS))
            for index,(layout,label) in enumerate(CURRENT_LAYOUTS.items()):
                scale_values=[]; stage_values=[]
                for reasoner in profiles:
                    scale_ok=[number(r,'synthetic_users') for r in scalability[layout]
                              if r.get('reasoner')==reasoner and outcome(r)=='completed' and number(r,'synthetic_users') is not None]
                    stage_ok=[number(r,'stage') for r in cumulative[layout]
                              if r.get('reasoner')==reasoner and outcome(r)=='completed' and number(r,'stage') is not None]
                    scale_values.append(max(scale_ok) if scale_ok else np.nan)
                    stage_values.append(max(stage_ok) if stage_ok else np.nan)
                positions=np.arange(len(profiles))+(index-(len(CURRENT_LAYOUTS)-1)/2)*width
                axes[0].bar(positions,scale_values,width,label=label,alpha=.85)
                axes[1].bar(positions,stage_values,width,label=label,alpha=.85)
                for ax,values in zip(axes,(scale_values,stage_values)):
                    for x,value in zip(positions,values):
                        if np.isfinite(value): ax.text(x,value,f'{value:g}',ha='center',va='bottom',fontsize=8,rotation=90)
            for ax in axes:
                ax.set_xticks(range(len(profiles)),[LABELS.get(r,r) for r in profiles],rotation=30,ha='right')
                ax.grid(axis='y',alpha=.2); ax.legend(fontsize=9)
            axes[0].set_ylabel('Largest completed synthetic-user population')
            axes[0].set_yscale('symlog',linthresh=10)
            axes[1].set_ylabel('Largest completed cumulative stage')
            self.save(fig,'reasoner-capacity-frontier',
                      'Largest semantically valid completed point in the recorded campaign. Missing bars mean no accepted completion; frontiers are tested bounds, not extrapolated capacity.')

        load = datasets.get('physical/load', [])
        if load:
            dimensions=sorted({r.get('dimension','unknown') for r in load})
            reasoners=observed_profiles(load)
            matrix=np.full((len(dimensions),len(reasoners)),np.nan); counts={}
            for y,dimension in enumerate(dimensions):
                for x,reasoner in enumerate(reasoners):
                    selected=[r for r in load if r.get('dimension')==dimension and r.get('reasoner')==reasoner]
                    if selected:
                        completed=sum(outcome(r)=='completed' for r in selected)
                        matrix[y,x]=100*completed/len(selected); counts[y,x]=(completed,len(selected))
            fig,ax=plt.subplots(figsize=(max(8,1.4*len(reasoners)),max(4,.75*len(dimensions)+2)))
            image=ax.imshow(np.ma.masked_invalid(matrix),vmin=0,vmax=100,cmap='Blues',aspect='auto')
            ax.set_xticks(range(len(reasoners)),[LABELS.get(r,r) for r in reasoners],rotation=30,ha='right')
            ax.set_yticks(range(len(dimensions)),[d.replace('_',' ').title() for d in dimensions])
            for (y,x),(completed,total) in counts.items():
                ax.text(x,y,f'{completed}/{total}\n{matrix[y,x]:.0f}%',ha='center',va='center',fontsize=9,
                        color='white' if matrix[y,x]>55 else 'black')
            fig.colorbar(image,ax=ax,label='Completed points (%)')
            ax.set_xlabel('Reasoning backend'); ax.set_ylabel('Load dimension')
            self.save(fig,'load-completion-matrix',
                      'Completed/configured observations by load dimension and backend. A zero is measured coverage failure, not zero latency or zero cost.')

    def acceptance(self, datasets):
        outcomes={name:dict(Counter(outcome(row) for row in rows)) for name,rows in datasets.items()}
        blockers=[]
        failed_checks=sum(row.get('status')=='failed' for row in self.checks)
        if failed_checks:
            blockers.append(f'{failed_checks} recorded data-integrity checks failed')
        required_datasets=(
            'distributed/cumulative','distributed/scalability',
            'replicated/cumulative','replicated/scalability','physical/load',
            'scale-out','reasoning-hardware','distributed-ontology',
            'distributed-reasoning-scalability',
        )
        for required in required_datasets:
            if required not in datasets:
                blockers.append(f'{required} has no recorded dataset')
            elif not any(outcome(row)=='completed' for row in datasets[required]):
                blockers.append(f'{required} has no completed observation')
        if not self.evidence_context['version_compatible']:
            blockers.append(
                'recorded benchmark versions '
                f"{self.evidence_context['recorded_benchmark_versions']} do not match "
                f"active version {self.evidence_context['current_benchmark_version']}"
            )
        if not self.evidence_context['build_compatible']:
            blockers.append(
                'recorded software build identifiers are missing or differ '
                'from the active source tree'
            )
        if not self.evidence_context['topology_compatible']:
            blockers.append(
                'recorded topology sizes '
                f"{self.evidence_context['recorded_topology_node_counts']} do not match "
                f"the active {self.evidence_context['current_topology_node_count']}-node inventory"
            )
        if not self.evidence_context['topology_fingerprint_compatible']:
            blockers.append(
                'recorded topology fingerprints are missing or differ from '
                'the active physical topology'
            )
        if self.evidence_context['reconstructed_metadata']:
            blockers.append('one or more active datasets use reconstructed metadata after a failed run')
        suite_record=None
        suite_root=self.inputs/'suites'
        if suite_root.is_dir():
            candidates=[]
            for path in suite_root.glob('*/suite.json'):
                try:
                    value=json.loads(path.read_text())
                except (OSError,json.JSONDecodeError):
                    continue
                if not value.get('dry_run'):
                    candidates.append((path.stat().st_mtime,path,value))
            if candidates:
                _,path,value=max(candidates,key=lambda item:item[0])
                incomplete=[step.get('name','unknown') for step in value.get('steps',[]) if step.get('status')!='completed']
                suite_record={'path':str(path.resolve()),'incomplete_steps':incomplete}
                if incomplete:
                    blockers.append('latest executed suite is incomplete: '+', '.join(incomplete))
        result={
            'accepted_for_performance_claims':not blockers,
            'status':'accepted' if not blockers else 'rejected',
            'blocking_findings':blockers,
            'dataset_outcomes':outcomes,
            'latest_executed_suite':suite_record,
            'evidence_context':self.evidence_context,
        }
        (self.output/'results-audit.json').write_text(json.dumps(result,indent=2)+'\n')
        return result

    def evidence_readiness(self,datasets,acceptance):
        """Create a normalized coverage panel suitable for scientific review."""
        required=(
            'distributed/cumulative','distributed/scalability',
            'replicated/cumulative','replicated/scalability','physical/load',
            'scale-out','reasoning-hardware','distributed-ontology',
            'distributed-reasoning-scalability',
        )
        labels=[*required,*(name for name in datasets if name not in required)]
        fig,ax=plt.subplots(figsize=(7.2,max(4.4,.42*len(labels)+1.8)))
        left=np.zeros(len(labels))
        missing=[index for index,name in enumerate(labels) if not datasets.get(name)]
        if missing:
            ax.barh(missing,[100]*len(missing),color='#f2f2f2',edgecolor='#777777',
                    hatch='///',height=.72,label='Not recorded')
        for status,color in STATUS.items():
            values=[]
            for name in labels:
                rows=datasets.get(name,[])
                counts=Counter(outcome(row) for row in rows)
                total=sum(counts.values())
                values.append(100*counts[status]/total if total else 0)
            ax.barh(labels,values,left=left,color=color,label=status.title(),height=.72)
            left+=np.asarray(values)
        for y,name in enumerate(labels):
            rows=datasets.get(name,[])
            total=len(rows); completed=sum(outcome(r)=='completed' for r in rows)
            ax.text(101,y,f'{completed}/{total}' if total else 'not recorded',va='center',fontsize=8)
        ax.set_xlim(0,112);ax.invert_yaxis();ax.set_xlabel('Recorded outcome share (%)')
        ax.set_ylabel('Dataset');ax.legend(ncol=5,loc='lower center',bbox_to_anchor=(.5,1.01))
        ax.grid(axis='x')
        self.save(fig,'evidence-readiness',
                  f"Acceptance: {acceptance['status'].upper()}; labels show completed/recorded. "
                  'Normalized outcome coverage. Dataset rows are not equivalent workloads; this panel evaluates evidence completeness rather than performance.')

    def apply_publication_gate(self, acceptance):
        """Remove performance panels when the evidence contract is rejected."""

        if acceptance['accepted_for_performance_claims']:
            return []
        retained=[]; suppressed=[]
        for path in self.figures:
            if Path(path).stem in REJECTED_REPORT_FIGURES:
                retained.append(path)
            else:
                suppressed.append(path)
        self.figures=retained
        self.findings.append(
            f'Publication gate suppressed {len(suppressed)} performance figure(s). '
            'Only coverage and integrity diagnostics remain until the result '
            'contract is accepted.'
        )
        return suppressed

    def apply_table_gate(self, acceptance):
        """Remove derived performance tables when the evidence is rejected."""

        if acceptance['accepted_for_performance_claims']:
            return []
        suppressed=[]
        for path in sorted(self.output.glob('*.csv')):
            if path.name not in REJECTED_REPORT_TABLES:
                suppressed.append(str(path))
                path.unlink()
        retained_figures={Path(path).stem for path in self.figures}
        self.statistics=[
            row for row in self.statistics
            if row.get('figure') in retained_figures
        ]
        self.findings.append(
            f'Publication gate suppressed {len(suppressed)} derived performance '
            'table(s). Diagnostic coverage and integrity tables remain available.'
        )
        return suppressed

    def write_png_quality_audit(self):
        """Record basic raster integrity for exactly the retained PNG files."""

        from PIL import Image, ImageStat

        rows=[]
        for path in sorted(self.output.rglob('*.png')):
            with Image.open(path) as image:
                rgb=image.convert('RGB')
                extrema=ImageStat.Stat(rgb).extrema
                sample=rgb.copy()
                sample.thumbnail((256,256))
                colors=sample.getcolors(maxcolors=256*256)
                rows.append({
                    'path':str(path.relative_to(self.output)),
                    'width':image.width,
                    'height':image.height,
                    'colors_sampled':len(colors) if colors is not None else 256*256,
                    'near_blank':max(high-low for low,high in extrema) < 3,
                })
        path=self.output/'coverage-and-integrity/png-quality-audit.json'
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(rows,indent=2)+'\n')
        return str(path)

    def network_scenarios(self):
        import tomllib
        path=self.root/'configs/network-scenarios.toml'
        settings=tomllib.loads(path.read_text())['network']
        self.sources[str(path.resolve())]=hashlib.sha256(path.read_bytes()).hexdigest()
        distances=settings['distances_km']; bandwidths=settings['bandwidths_mbps']
        speed=settings['propagation_speed_km_s']; base=settings['base_rtt_ms']
        if not all(math.isfinite(float(v)) for v in [*distances,*bandwidths,speed,base]) or not distances or not bandwidths or speed<=0 or base<0 or min(distances)<0 or min(bandwidths)<=0:
            raise ValueError('Network scenarios require nonnegative distances and positive bandwidth/speed')
        events=self.read(self.inputs/'load/event-runs.csv')
        successful=[r for r in events if r.get('processed','').lower()=='true']
        sizes=[number(r,'request_bytes')+number(r,'response_bytes') for r in successful
               if number(r,'request_bytes') is not None and number(r,'response_bytes') is not None]
        if not sizes:
            self.findings.append('Network scenarios omitted: no measured payload sizes.');return
        payload=statistics.median(sizes); estimates=[]
        fig,axes=plt.subplots(1,2,figsize=(13,4.8))
        for bandwidth in bandwidths:
            delay=[base+2*d/speed*1000+payload*8/(bandwidth*1000) for d in distances]
            axes[0].plot(distances,delay,marker='o',label=f'{bandwidth:g} Mbps')
            for d,t in zip(distances,delay):estimates.append({'scenario_distance_km':d,'bandwidth_mbps':bandwidth,'base_rtt_ms':base,'propagation_speed_km_s':speed,'observed_median_payload_bytes':payload,'model_transport_ms':t,'kind':'analytical scenario; not a measured link'})
        axes[0].set_xscale('symlog',linthresh=.1);axes[0].set_xlabel('Scenario distance (km)');axes[0].set_ylabel('Estimated request + response transport (ms)');axes[0].legend();axes[0].grid(alpha=.2)
        for reasoner in observed_profiles(successful):
            values=[v for r in successful if r.get('reasoner')==reasoner and (v:=number(r,'latency_ms')) is not None and (q:=number(r,'engine_duration_ms')) is not None]
            overhead=[max(0,number(r,'latency_ms')-number(r,'engine_duration_ms')) for r in successful if r.get('reasoner')==reasoner and number(r,'latency_ms') is not None and number(r,'engine_duration_ms') is not None]
            if overhead:axes[1].bar(LABELS.get(reasoner,reasoner),statistics.median(overhead),color=COLORS.get(reasoner))
        axes[1].set_ylabel('Observed median non-query latency (ms)');axes[1].grid(axis='y',alpha=.2)
        self.save(fig,'network-scenarios-and-observed-overhead',f'Left: analytical model; payload median={payload:.0f} bytes, base RTT={base:g} ms. Right: queueing + transport + serialization; not a geographic-distance measurement.')
        write_csv(self.output/'network-scenarios.csv',estimates)

    def validation_load(self):
        if self.validation_input is None:return
        rows=self.read(self.validation_input/'summary.csv')
        metadata_path=self.validation_input/'metadata.json'
        metadata=json.loads(metadata_path.read_text()) if metadata_path.is_file() else {}
        budgets=metadata.get('timeouts',{})
        completed=[r for r in rows if outcome(r)=='completed']
        if not completed:
            self.findings.append('Supplementary validation load has no completed points.');return
        fig,axes=plt.subplots(1,2,figsize=(13,5))
        labels=[f"{LABELS.get(r['reasoner'],r['reasoner'])} / {r['profile']} / rep {r['repetition']}" for r in completed]
        left=np.zeros(len(completed))
        for key,label,color in [('prepare_wall_ms','Preparation','#56B4E9'),('workload_wall_ms','Event workload','#E69F00'),('recovery_wall_ms','Recovery','#009E73')]:
            values=[value/1000 if (value:=number(r,key)) is not None else np.nan for r in completed]
            axes[0].barh(labels,values,left=left,label=label,color=color);left+=values
        axes[0].set_xlabel('Observed phase wall time (s)');axes[0].legend(loc='upper center',bbox_to_anchor=(.5,1.16),ncol=3,fontsize=9);axes[0].grid(axis='x',alpha=.2)
        axes[1].barh(labels,[100*float(r['events_processed'])/float(r['events_offered']) for r in completed],color='#009E73')
        for i,r in enumerate(completed):axes[1].text(50,i,f"{r['events_processed']}/{r['events_offered']}",ha='center',va='center')
        axes[1].set_xlim(0,105);axes[1].set_xlabel('Scheduled events processed (%)');axes[1].tick_params(axis='y',labelleft=False)
        self.save(fig,'extended-budget-load-validation',f"Separate validation: request={budgets.get('request_seconds','unknown')} s, point={budgets.get('point_seconds','unknown')} s, recovery={budgets.get('recovery_seconds','unknown')} s. Each bar is one run; no uncertainty estimate.")
        self.findings.append(f'Supplementary extended-budget load: {len(completed)}/{len(rows)} points completed; {sum(int(r["events_processed"]) for r in completed)} processed and {sum(int(r["events_lost"]) for r in completed)} lost events. Source: {self.validation_input}')

    def run(self):
        datasets={}
        for layout in CURRENT_LAYOUTS:
            for suite in ('cumulative','scalability'):
                rows=self.read(self.inputs/f'monitoring/{layout}/{suite}/summary.csv')
                validation_path = self.inputs/f'monitoring/{layout}/{suite}/result-validation.csv'
                validations = self.read(validation_path) if validation_path.is_file() else []
                rows = validated_evidence_rows(rows, validations)
                invalid_points = {
                    _validation_key(row) for row in validations
                    if row.get('valid', '').lower() != 'true'
                }
                if invalid_points:
                    self.findings.append(
                        f'{layout}/{suite}: excluded {len(invalid_points)} '
                        'semantically invalid point(s) from performance curves.'
                    )
                unvalidated = sum(
                    row.get('status') == 'unvalidated_results' for row in rows
                )
                if unvalidated:
                    self.findings.append(
                        f'{layout}/{suite}: retained raw timing for {unvalidated} '
                        'point(s) whose canonical reference did not complete; '
                        'those points are excluded from performance curves.'
                    )
                if rows:
                    datasets[f'{layout}/{suite}']=rows
                    self.curves(rows,'stage' if suite=='cumulative' else 'synthetic_users', [('total_wall_ms','Total wall time (s)',1000),('max_node_reasoning_ms','Critical reasoning (s)',1000),('query_wall_ms','Query wall time (s)',1000)],f'{layout}-{suite}-time',min_distinct_x=2)
                    self.curves(rows,'stage' if suite=='cumulative' else 'synthetic_users',[('total_process_cpu_ms','Aggregate process CPU (s)',1000),('max_node_peak_rss_kib','Maximum node peak RSS (MiB)',1024)],f'{layout}-{suite}-resources',min_distinct_x=2)
        load=self.read(self.inputs/'load/summary.csv')
        if load:datasets['physical/load']=load;self.failure_diagnostics(load)
        for suite in ('scale-out','reasoning-hardware','distributed-ontology','distributed-reasoning-scalability'):
            filename = 'distributed-reasoning-summary.csv' if suite == 'distributed-reasoning-scalability' else 'summary.csv'
            rows=self.read(self.inputs/f'experiments/{suite}/{filename}')
            if not rows:continue
            datasets[suite]=rows
            if suite=='scale-out':self.curves(rows,'node_count',[('queries_per_second','Throughput (queries/s)',1),('query_latency_p95_ms','p95 query latency (ms)',1)],'physical-scale-out',min_distinct_x=2)
            elif suite=='distributed-ontology':self.curves(rows,'synthetic_users',[('total_wall_ms','Total wall time (s)',1000),('max_sum_node_current_rss_kib','Aggregate current RSS (MiB)',1024),('total_process_cpu_ms','Aggregate CPU time (s)',1000)],'distributed-ontology-cost',min_distinct_x=2)
            elif suite=='reasoning-hardware':
                for reasoner in observed_profiles(rows):
                    for dimension in sorted({r['dimension'] for r in rows}):
                        selected=[r for r in rows if r['reasoner']==reasoner and r['dimension']==dimension]
                        self.curves(selected,'dimension_value',[('reasoning_ms','Reasoning time (s)',1000),('process_cpu_ms','Process CPU (s)',1000),('current_rss_kib','Current RSS (MiB)',1024)],f'hardware-{dimension}-{reasoner}',group='role',min_distinct_x=2)
            else:
                self.findings.append(
                    'distributed-reasoning-scalability: comparisons are grouped by reasoning_task; '
                    'RDFS and OWL DL timings are not treated as interchangeable.'
                )
        if not datasets: raise ValueError(f"No physical result summaries below {self.inputs}")
        self.coverage(datasets)
        self.audit(datasets)
        self.quality_figures(datasets)
        self.policy_costs()
        from .comparative_reporting import generate_comparisons
        generate_comparisons(self)
        self.network_scenarios()
        self.validation_load()
        self.findings.append('Nodes are colocated in one room (operator confirmation). Network-distance plots use explicit analytical scenarios; no geographic node positions or mobility trajectories are inferred.')
        for name,rows in datasets.items():
            errors=Counter(r.get('error','') for r in rows if r.get('error') and outcome(r)!='skipped')
            self.findings.append(f'{name}: {dict(Counter(outcome(r) for r in rows))}; frequent errors: {errors.most_common(3)}')
        write_csv(self.output/'execution-coverage.csv',self.tables)
        acceptance=self.acceptance(datasets)
        self.evidence_readiness(datasets,acceptance)
        suppressed=self.apply_publication_gate(acceptance)
        suppressed_tables=self.apply_table_gate(acceptance)
        for row in self.statistics:
            row['publication_eligible']=acceptance['accepted_for_performance_claims']
        write_csv(self.output/'figure-statistics.csv',self.statistics)
        retained={Path(path).resolve() for path in self.figures}
        for path in self.output.rglob('*.png'):
            if path.resolve() not in retained:
                path.unlink()
        png_quality_audit=self.write_png_quality_audit()
        manifest={'figures':self.figures,'sources_sha256':self.sources,'findings':self.findings,
                  'suppressed_figures':suppressed,
                  'suppressed_tables':suppressed_tables,
                  'png_quality_audit':png_quality_audit,
                  'performance_tables_eligible':acceptance['accepted_for_performance_claims'],
                  'acceptance':acceptance,
                  'evidence_context':self.evidence_context,
                  'statistics':'median and observed range; no inferred confidence intervals; incomplete rows excluded from completed-performance curves'}
        (self.output/'report.json').write_text(json.dumps(manifest,indent=2)+'\n')
        index = '# Physical results audit and figure catalogue\n\n'
        index += f"## Acceptance status: {acceptance['status'].upper()}\n\n"
        if acceptance['blocking_findings']:
            index += ''.join(f'- {finding}\n' for finding in acceptance['blocking_findings'])+'\n'
        if suppressed:
            index += (
                'Performance figures were removed from this catalogue because the '
                f'evidence contract is rejected ({len(suppressed)} suppressed). '
                'Raw measurements remain available for diagnosis, not publication.\n\n'
            )
        if suppressed_tables:
            index += (
                'Derived performance tables were also removed from this catalogue '
                f'({len(suppressed_tables)} suppressed). Diagnostic tables remain.\n\n'
            )
        for group in sorted({Path(p).parent.name for p in self.figures}):
            index += '## '+group.replace('-', ' ').title()+'\n\n'
            for path in self.figures:
                if Path(path).parent.name == group:
                    relative = Path(path).relative_to(self.output)
                    index += f'- [{Path(path).stem}]({relative})\n'
            index += '\n'
        index += '## Interpretation and limitations\n\n'+'\n\n'.join(self.findings)+'\n'
        (self.output/'README.md').write_text(index)
        return manifest


def generate_report(root: Path, inputs: Path, output: Path, validation_input: Path | None = None):
    return Report(root,inputs,output,validation_input).run()

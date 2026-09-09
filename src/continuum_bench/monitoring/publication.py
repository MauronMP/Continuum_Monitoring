"""Evidence-led physical reports: raw data, censoring, policy costs and PNGs."""
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

from ..plot_environment import configure_matplotlib
configure_matplotlib()
import matplotlib.pyplot as plt
import numpy as np
from .figure_style import save_png

COLORS = {'rdfs':'#0072B2', 'owlrl':'#D55E00', 'rdfs_owlrl':'#009E73'}
LABELS = {'rdfs':'RDFS', 'owlrl':'OWL RL', 'rdfs_owlrl':'RDFS + OWL RL'}
STATUS = {'completed':'#009E73','timeout':'#E69F00','skipped':'#999999','failed':'#CC79A7'}


def read_csv(path):
    if not path.is_file(): return []
    with path.open(newline='') as handle: return list(csv.DictReader(handle))


def number(row, key):
    try: value = float(row.get(key,''))
    except (ValueError, TypeError): return None
    return value if math.isfinite(value) else None


def outcome(row):
    value = row.get('status','unknown')
    if value == 'completed': return 'completed'
    if value.startswith('skipped'): return 'skipped'
    if 'timeout' in value: return 'timeout'
    return 'failed'


def write_csv(path, rows):
    if not rows: return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=sorted(set().union(*(r.keys() for r in rows))))
        writer.writeheader(); writer.writerows(rows)


class Report:
    def __init__(self, root, inputs, output, validation_input=None):
        self.root, self.inputs, self.output = root, inputs, output
        self.validation_input=validation_input
        self.figures=[]; self.findings=[]; self.sources={}; self.tables=[]; self.statistics=[]; self.checks=[]
        output.mkdir(parents=True,exist_ok=True)

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
        title=name.replace('rdfs_owlrl','RDFS + OWL RL').replace('owlrl','OWL RL').replace('rdfs','RDFS').replace('-',' ').replace('_',' ')
        fig.suptitle(title[:1].upper()+title[1:],fontsize=15,fontweight='bold')
        fig.text(.01,.005,caption,fontsize=9,ha='left',va='bottom')
        fig.tight_layout(rect=(0,.09,1,.94))
        self.figures.extend(str(p) for p in save_png(fig,self.output/name))

    def coverage(self,datasets):
        fig,ax=plt.subplots(figsize=(12,max(4,len(datasets)*.55)))
        labels=[]; counts=[]
        for name,rows in datasets.items():
            count=Counter(outcome(r) for r in rows); labels.append(name); counts.append(count)
            self.tables.append({'dataset':name,'rows':len(rows),**{s:count[s] for s in STATUS}})
        left=np.zeros(len(labels))
        for status,color in STATUS.items():
            values=np.array([c[status] for c in counts]);ax.barh(labels,values,left=left,color=color,label=status.title())
            for i,(v,l) in enumerate(zip(values,left)):
                if v: ax.text(l+v/2,i,str(v),ha='center',va='center',fontsize=9)
            left+=values
        ax.invert_yaxis();ax.set_xlabel('Recorded points / rounds (counts, not equivalent workloads)');ax.legend(ncol=4,loc='upper center',bbox_to_anchor=(.5,1.12));ax.grid(axis='x',alpha=.2)
        self.save(fig,'execution-coverage','Skipped points are not measured timeouts. Counts are kept separate; no failed timing is treated as a completed observation.')

    def curves(self,rows,x,metrics,name,group='reasoner'):
        completed=[r for r in rows if outcome(r)=='completed']
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
        counts=Counter((r.get('dimension','unknown'),r.get('reasoner','unknown'),outcome(r)) for r in rows)
        fig,axes=plt.subplots(1,2,figsize=(15,5))
        labels=sorted({(d,r) for d,r,_ in counts});bottom=np.zeros(len(labels))
        for status,color in STATUS.items():
            vals=[counts[d,r,status] for d,r in labels];axes[0].bar(range(len(labels)),vals,bottom=bottom,color=color,label=status.title());bottom+=vals
        axes[0].set_xticks(range(len(labels)),[f'{d}\n{LABELS.get(r,r)}' for d,r in labels],rotation=70,ha='right',fontsize=8)
        axes[0].set_ylabel('Recorded points');axes[0].legend(fontsize=8)
        measured=[r for r in rows if outcome(r)!='skipped' and number(r,'event_loss_percent') is not None]
        for reasoner in COLORS:
            selected=[r for r in measured if r.get('reasoner')==reasoner]
            axes[1].scatter([number(r,xfield) for r in selected],[number(r,'event_loss_percent') for r in selected],label=LABELS[reasoner],color=COLORS[reasoner],alpha=.7)
        ticks=sorted({number(r,xfield) for r in measured if number(r,xfield) is not None})
        if len(ticks)<=8: axes[1].set_xticks(ticks)
        axes[1].set_xlabel(xfield.replace('_',' ').title());axes[1].set_ylabel('Unserved scheduled events (%)');axes[1].set_ylim(-2,102);axes[1].legend();axes[1].grid(alpha=.2)
        self.save(fig,name,'Failure diagnosis, not throughput or packet loss. Unserved events include failed preparation; skipped profiles have no observations.')

    def policy_costs(self):
        events=self.read(self.inputs/'load/physical/event-runs.csv')
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
            selected=sorted([r for r in summaries if r['reasoner']==reasoner],key=lambda r:r['engine_duration_ms_median'] or -1)
            if not selected:continue
            fig,axes=plt.subplots(1,3,figsize=(18,max(5,len(selected)*.32)),sharey=True)
            labels=[f"{r['category']} (n={r['completed']}/{r['attempted']})" for r in selected]
            for ax,key,label,div in zip(axes,['engine_duration_ms_median','process_cpu_ms_median','current_rss_kib_median'],['Median query execution (ms)','Median attributed CPU (ms)','Median process RSS (MiB)'],[1,1,1024]):
                values=[r[key]/div if r[key] is not None else np.nan for r in selected]
                ax.barh(labels,values,color=COLORS.get(reasoner));ax.set_xlabel(label);ax.grid(axis='x',alpha=.2)
            self.save(fig,f'category-cost-{reasoner}',f'Conditional on completed requests; n=completed/attempted. CPU is batch-attributed; RSS is process memory. Matched profile: {selected_profile}.')
        for reasoner in COLORS:
            selected=sorted([r for r in summaries if r['reasoner']==reasoner],key=lambda r:r['engine_duration_ms_sum'] or -1)
            if not selected:continue
            fig,axes=plt.subplots(1,3,figsize=(18,max(5,len(selected)*.32)),sharey=True)
            labels=[f"{r['category']} (n={r['completed']})" for r in selected]
            for ax,key,label,div in zip(axes,['engine_duration_ms_median','engine_duration_ms_p95','engine_duration_ms_sum'],['Median query time (ms)','p95 query time (ms)','Total observed query time (s)'],[1,1,1000]):
                ax.barh(labels,[r[key]/div if r[key] is not None else np.nan for r in selected],color=COLORS[reasoner]);ax.set_xlabel(label);ax.grid(axis='x',alpha=.2)
            self.save(fig,f'category-tail-and-total-{reasoner}',f'Matched profile {selected_profile}; completed requests only. Median, tail latency and frequency-weighted cost answer different questions. Small n limits p95 stability.')
        from ..queries import load_catalog
        from .study.sparql import characterize_query
        specs={spec.id:spec for spec in load_catalog(self.root/'queries/catalog.csv',self.root)}
        for reasoner in COLORS:
            query_groups=defaultdict(list)
            for event in events:
                if event.get('reasoner')==reasoner and event.get('processed','').lower()=='true' and number(event,'engine_duration_ms') is not None:
                    query_groups[event['query_id']].append(number(event,'engine_duration_ms'))
            points=[(qid,characterize_query(specs[qid]).structural_complexity,statistics.median(values),len(values)) for qid,values in query_groups.items() if qid in specs]
            if not points:continue
            fig,ax=plt.subplots(figsize=(10,5))
            ax.scatter([p[1] for p in points],[p[2] for p in points],s=[20+5*p[3] for p in points],alpha=.6,color=COLORS[reasoner],label=LABELS[reasoner])
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
        for reasoner in COLORS:
            selected=sorted([r for r in policy_rows if r['reasoner']==reasoner and r['mean_query_ms'] is not None],key=lambda r:r['attributed_query_ms'])[-15:]
            if not selected:continue
            fig,ax=plt.subplots(figsize=(10,6));ax.barh([r['policy'] for r in selected],[r['attributed_query_ms']/1000 for r in selected],color=COLORS[reasoner]);ax.set_xlabel('Attributed total query execution (s)');ax.grid(axis='x',alpha=.2)
            self.save(fig,f'policy-total-cost-{reasoner}',f'Top 15 observed costs in profile {selected_profile}. Multi-policy queries contribute 1/N each. Total cost combines frequency and duration; incomplete workload.')

    def audit(self,datasets):
        for name,rows in datasets.items():
            for index,row in enumerate(rows):
                if outcome(row)=='skipped':continue
                offered,processed,lost=(number(row,key) for key in ('events_offered','events_processed','events_lost'))
                if all(v is not None for v in (offered,processed,lost)) and offered!=processed+lost:
                    self.checks.append({'dataset':name,'row':index,'check':'event conservation','status':'failed'})
                for field,value in row.items():
                    if field.endswith(('_ms','_kib','_bytes')):
                        v=number(row,field)
                        if v is not None and v<0:self.checks.append({'dataset':name,'row':index,'check':f'negative {field}','status':'failed'})
        for base in (self.inputs/'physical',self.inputs/'experiments/physical'):
            for path in base.rglob('result-validation.csv'):
                rows=self.read(path);invalid=sum(r.get('valid','').lower()!='true' for r in rows)
                self.checks.append({'dataset':str(path),'check':'canonical result equivalence','rows':len(rows),'invalid':invalid,'status':'failed' if invalid else 'passed'})
        self.findings.append(f'Data integrity: {sum(r["status"]=="failed" for r in self.checks)} failed checks; event conservation, nonnegative metrics and recorded result equivalence checked.')
        write_csv(self.output/'data-integrity.csv',self.checks)

    def network_scenarios(self):
        import tomllib
        path=self.root/'configs/network-scenarios.toml'
        settings=tomllib.loads(path.read_text())['network']
        self.sources[str(path.resolve())]=hashlib.sha256(path.read_bytes()).hexdigest()
        distances=settings['distances_km']; bandwidths=settings['bandwidths_mbps']
        speed=settings['propagation_speed_km_s']; base=settings['base_rtt_ms']
        if not all(math.isfinite(float(v)) for v in [*distances,*bandwidths,speed,base]) or not distances or not bandwidths or speed<=0 or base<0 or min(distances)<0 or min(bandwidths)<=0:
            raise ValueError('Network scenarios require nonnegative distances and positive bandwidth/speed')
        events=self.read(self.inputs/'load/physical/event-runs.csv')
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
        for reasoner in COLORS:
            values=[v for r in successful if r.get('reasoner')==reasoner and (v:=number(r,'latency_ms')) is not None and (q:=number(r,'engine_duration_ms')) is not None]
            overhead=[max(0,number(r,'latency_ms')-number(r,'engine_duration_ms')) for r in successful if r.get('reasoner')==reasoner and number(r,'latency_ms') is not None and number(r,'engine_duration_ms') is not None]
            if overhead:axes[1].bar(LABELS[reasoner],statistics.median(overhead),color=COLORS[reasoner])
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
            values=[(number(r,key) or 0)/1000 for r in completed]
            axes[0].barh(labels,values,left=left,label=label,color=color);left+=values
        axes[0].set_xlabel('Observed phase wall time (s)');axes[0].legend(loc='upper center',bbox_to_anchor=(.5,1.16),ncol=3,fontsize=9);axes[0].grid(axis='x',alpha=.2)
        axes[1].barh(labels,[100*float(r['events_processed'])/float(r['events_offered']) for r in completed],color='#009E73')
        for i,r in enumerate(completed):axes[1].text(50,i,f"{r['events_processed']}/{r['events_offered']}",ha='center',va='center')
        axes[1].set_xlim(0,105);axes[1].set_xlabel('Scheduled events processed (%)');axes[1].tick_params(axis='y',labelleft=False)
        self.save(fig,'extended-budget-load-validation',f"Separate validation: request={budgets.get('request_seconds','unknown')} s, point={budgets.get('point_seconds','unknown')} s, recovery={budgets.get('recovery_seconds','unknown')} s. Each bar is one run; no uncertainty estimate.")
        self.findings.append(f'Supplementary extended-budget load: {len(completed)}/{len(rows)} points completed; {sum(int(r["events_processed"]) for r in completed)} processed and {sum(int(r["events_lost"]) for r in completed)} lost events. Source: {self.validation_input}')

    def run(self):
        datasets={}
        for layout in ('sharded','replicated'):
            for suite in ('cumulative','scalability'):
                rows=self.read(self.inputs/f'physical/{layout}/{suite}/summary.csv')
                if rows:
                    datasets[f'{layout}/{suite}']=rows
                    self.curves(rows,'stage' if suite=='cumulative' else 'synthetic_users', [('total_wall_ms','Total wall time (s)',1000),('max_node_reasoning_ms','Critical reasoning (s)',1000),('query_wall_ms','Query wall time (s)',1000)],f'{layout}-{suite}-time')
                    self.curves(rows,'stage' if suite=='cumulative' else 'synthetic_users',[('total_process_cpu_ms','Aggregate process CPU (s)',1000),('max_node_peak_rss_kib','Maximum node peak RSS (MiB)',1024)],f'{layout}-{suite}-resources')
        load=self.read(self.inputs/'load/physical/summary.csv')
        if load:datasets['physical/load']=load;self.failure_diagnostics(load)
        for suite in ('scale-out','reasoning-hardware','distributed-ontology'):
            rows=self.read(self.inputs/f'experiments/physical/{suite}/summary.csv')
            if not rows:continue
            datasets[suite]=rows
            if suite=='scale-out':self.curves(rows,'node_count',[('queries_per_second','Throughput (queries/s)',1),('query_latency_p95_ms','p95 query latency (ms)',1)],'physical-scale-out')
            elif suite=='distributed-ontology':self.curves(rows,'synthetic_users',[('total_wall_ms','Total wall time (s)',1000),('max_sum_node_current_rss_kib','Aggregate current RSS (MiB)',1024),('total_process_cpu_ms','Aggregate CPU time (s)',1000)],'distributed-ontology-cost')
            else:
                for reasoner in COLORS:
                    for dimension in sorted({r['dimension'] for r in rows}):
                        selected=[r for r in rows if r['reasoner']==reasoner and r['dimension']==dimension]
                        self.curves(selected,'dimension_value',[('reasoning_ms','Reasoning time (s)',1000),('process_cpu_ms','Process CPU (s)',1000),('current_rss_kib','Current RSS (MiB)',1024)],f'hardware-{dimension}-{reasoner}',group='role')
        if not datasets: raise ValueError(f"No physical result summaries below {self.inputs}")
        self.coverage(datasets)
        self.audit(datasets)
        self.policy_costs()
        self.network_scenarios()
        self.validation_load()
        self.findings.append('Nodes are colocated in one room (operator confirmation). Network-distance plots use explicit analytical scenarios; no geographic node positions or mobility trajectories are inferred.')
        for name,rows in datasets.items():
            errors=Counter(r.get('error','') for r in rows if r.get('error') and outcome(r)!='skipped')
            self.findings.append(f'{name}: {dict(Counter(outcome(r) for r in rows))}; frequent errors: {errors.most_common(3)}')
        write_csv(self.output/'execution-coverage.csv',self.tables)
        write_csv(self.output/'figure-statistics.csv',self.statistics)
        manifest={'figures':self.figures,'sources_sha256':self.sources,'findings':self.findings,'statistics':'median and observed range; no inferred confidence intervals; incomplete rows excluded from completed-performance curves'}
        (self.output/'report.json').write_text(json.dumps(manifest,indent=2)+'\n')
        (self.output/'README.md').write_text('# Physical results audit\n\n'+'\n\n'.join(self.findings)+'\n')
        return manifest


def generate_report(root: Path, inputs: Path, output: Path, validation_input: Path | None = None):
    return Report(root,inputs,output,validation_input).run()

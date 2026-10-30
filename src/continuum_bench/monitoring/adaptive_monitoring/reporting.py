"""Separate observed recovery outcomes from plans and missing measurements."""
import csv
import json


def report(directory):
    rows = json.loads((directory/'decisions.json').read_text())
    flat = []
    for row in rows:
        for phase in ('before', 'after'):
            if phase not in row:
                continue
            flat.append(dict(scenario=row['scenario'], layout=row['layout'], attempt=row['attempt'],
                phase=phase, status=row['status'], **{k:row[phase][k] for k in (
                    'preparations','preparation_failures','requests','request_failures','failure_fraction')}))
    if flat:
        with (directory/'outcomes.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(flat[0])); writer.writeheader(); writer.writerows(flat)
    import matplotlib.pyplot as plt
    if rows:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout='constrained')
        labels = [f"{r['scenario']} / {r['layout']} / {r['attempt']}" for r in rows]
        for ax, key, denominator, title in zip(axes,
                ('preparation_failures','request_failures'), ('preparations','requests'),
                ('Preparation failure fraction','Catalog request failure fraction')):
            for offset, phase, color in ((-.18,'before','#777777'),(.18,'after','#0072B2')):
                for i,row in enumerate(rows):
                    data = row.get(phase, {})
                    n = data.get(denominator, 0)
                    if n:
                        value = data[key]/n
                        ax.bar(i+offset,value,width=.34,color=color,label=phase if i==0 else None)
                        ax.text(i+offset,value+.025,f'{data[key]}/{n}',ha='center',fontsize=8)
                    else:
                        ax.text(i+offset,.03,'NA',ha='center',fontsize=8)
            ax.set_ylim(0,1.16); ax.set_yticks([0,.25,.5,.75,1]); ax.set_xlim(-.6,len(rows)-.4); ax.set_title(title); ax.set_xticks(range(len(rows)),labels,rotation=35,ha='right')
        from matplotlib.patches import Patch
        fig.legend(handles=[Patch(color='#777777',label='Before'),Patch(color='#0072B2',label='After')],loc='upper right')
        fig.suptitle('Adaptive monitoring: recorded outcomes\nNA means unavailable; plans are not recoveries. Fractions include failures.')
        fig.savefig(directory/'recovery-outcomes.png',dpi=300,bbox_inches='tight'); plt.close(fig)
    (directory/'README.md').write_text('''# Adaptive monitoring evidence

`decisions.json` records observations, policy bindings, ranked/rejected destinations, executed action, timing and cleanup. `policy.json` snapshots ontology policy declarations and executable experimental grants. `configuration.json` preserves workload and resource limits. `outcomes.csv` separates before and after measurements; unavailable recovery values are NA in the PNG figure.

Execution recovery means the configured preparation and catalog requests completed without failures. Read semantic validation separately; availability does not imply semantic correctness. Duration includes deployment and verification, not production service recovery time. Multiple attempts share a baseline and are not independent samples. The supervisor rebuilds deterministic synthetic state between scenarios, not live patient data or machine images.
''')

    from .comparison import comparison
    comparison(directory)
    from .pool_reporting import report_pools
    report_pools(directory, rows)

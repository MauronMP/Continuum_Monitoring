"""Optional supervised recovery; existing scalability commands stay unchanged."""
from dataclasses import replace
import json
from pathlib import Path

from ..container_scale.config import load
from .policy import load_policy
from .runner import supervise


def register(subparsers):
    parser = subparsers.add_parser('adaptive-monitoring', help='Policy-directed bounded recovery of container scalability scenarios')
    parser.add_argument('action', choices=('plan','run','report'))
    parser.add_argument('--container-config', default='configs/container-scale.toml')
    parser.add_argument('--supervisor-config', default='configs/adaptive-monitoring.toml')
    parser.add_argument('--input-dir', help='Archived container-scale campaign (or supervisor output for report)')
    parser.add_argument('--output-dir', default='outputs/adaptive-monitoring')
    parser.add_argument('--scenario', action='append')
    parser.add_argument('--users', type=int, nargs='+', help='Select configured user-load levels, e.g. 1 50 100 500 1000 2000')
    parser.add_argument('--concurrency', type=int, nargs='+', help='Override concurrent catalog request levels for a NEW baseline only')


def dispatch(args, benchmark):
    if args.action == 'report':
        if not args.input_dir:
            raise ValueError('report requires --input-dir')
        from .reporting import report
        report(benchmark.resolve(Path(args.input_dir)))
        return 0
    from ..budget import unlimited_execution
    if unlimited_execution():
        raise ValueError('Adaptive monitoring requires --timeout-mode bounded; unlimited work cannot be safely supervised')
    if any(getattr(args, name, None) is not None for name in (
        'repetitions', 'timeout_seconds', 'request_timeout_seconds', 'point_timeout_seconds', 'phase_timeout_seconds'
    )):
        raise ValueError('Set workload budgets/repetitions in --container-config for a new baseline; archived recovery preserves them')
    config = load(benchmark.resolve(Path(args.container_config)), benchmark.root)
    policy = load_policy(benchmark.resolve(Path(args.supervisor_config)), benchmark)
    input_dir = benchmark.resolve(Path(args.input_dir)) if args.input_dir else None
    if args.action == 'plan' and input_dir is None:
        raise ValueError('plan requires --input-dir')
    if input_dir:
        archived = json.loads((input_dir/'configuration.json').read_text())
        # Deployment identity must match; workload selection comes from recorded evidence.
        if archived['deployment'] != config.deployment:
            raise ValueError('Archived deployment differs from --container-config')
        config = replace(config, raw=archived)
        for placement in input_dir.glob('placement-*/placement.json'):
            recorded = json.loads(placement.read_text())['physical_hosts']
            if recorded != json.loads(json.dumps([n.public() for n in config.topology.active_nodes])):
                raise ValueError('Physical inventory differs from archived campaign')
    if args.users is not None:
        if args.scenario or any(u < 1 for u in args.users):
            raise ValueError('--users requires positive levels and cannot be combined with --scenario')
        selected = [s for s in config.raw['scenarios'] if s['family']=='users' and s['users'] in args.users]
        if set(args.users)-{s['users'] for s in selected}:
            raise ValueError('Unknown user levels; define them in --container-config first')
        args.scenario = [s['name'] for s in selected]
    if args.concurrency is not None:
        if input_dir or args.action != 'run':
            raise ValueError('--concurrency is only for a new baseline; recorded campaign concurrency is preserved')
        if any(c < 1 for c in args.concurrency):
            raise ValueError('Concurrency levels must be positive')
        for scenario in config.raw['scenarios']:
            if not args.scenario or scenario['name'] in args.scenario:
                scenario['concurrency'] = sorted(set(args.concurrency))
    output = supervise(config, benchmark, policy, benchmark.resolve(Path(args.output_dir)),
        input_dir=input_dir, execute=args.action=='run', scenarios=args.scenario)
    print(f'Results: {output}')
    rows = json.loads((output/'decisions.json').read_text())
    final = {}
    for row in rows:
        final[row.get('containers_per_host', 1), row['scenario'], row['layout']] = row
    return int(args.action=='run' and any(r['status'] not in ('execution_recovered', 'not_needed') for r in final.values()))

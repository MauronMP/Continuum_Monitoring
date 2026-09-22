#!/usr/bin/env python3
"""Write an offline physical readiness manifest without contacting any node."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from continuum_bench.physical_cluster import load_physical_inventory, write_offline_manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--inventory', type=Path)
    parser.add_argument('--topology-name', default='physical')
    parser.add_argument('--ssh-user')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    inventory = load_physical_inventory(
        args.inventory or root / 'configs/topologies/physical/topology.toml',
        ssh_user=args.ssh_user, topology_name=args.topology_name)
    output = args.output or root / 'outputs/validation/readiness/offline-readiness.json'
    manifest = write_offline_manifest(root, inventory, output)
    print(json.dumps({'manifest': str(output), 'local_files_ready': manifest['local_files_ready'],
                      'deployment_ready': False, 'remote_contacted': False}))
    return 0 if manifest['local_files_ready'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

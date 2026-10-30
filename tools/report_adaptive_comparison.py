#!/usr/bin/env python3
"""Regenerate the integrated baseline/adaptive comparison without running workers."""
import argparse
from pathlib import Path

from continuum_bench.monitoring.adaptive_monitoring.comparison import (
    comparison, json_rows, memory_mib, number,
)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    args = parser.parse_args()
    print(comparison(args.input_dir))

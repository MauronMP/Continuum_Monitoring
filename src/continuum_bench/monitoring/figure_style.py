"""Shared PNG-only scientific figure output and explicit missing-data panels."""
from pathlib import Path
import numpy as np


def save_png(figure, base: Path):
    import matplotlib.pyplot as plt
    base.parent.mkdir(parents=True, exist_ok=True)
    for axis in figure.axes:
        if not axis.has_data():
            label = axis.get_ylabel() or axis.get_title() or 'Measurement'
            axis.set_axis_off()
            axis.text(.5, .5, f'{label}\nNo completed measurements\nSee outcome coverage',
                      transform=axis.transAxes, ha='center', va='center', color='#555555', fontsize=11,
                      bbox={'facecolor':'#f3f4f6','edgecolor':'#dddddd','pad':12})
    path = base.with_suffix('.png')
    figure.savefig(path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(figure)
    for suffix in ('.pdf', '.svg'):
        base.with_suffix(suffix).unlink(missing_ok=True)
    return [path]

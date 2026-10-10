"""Compare deterministic pilot outcomes; elapsed time is intentionally excluded."""
import argparse
import csv
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('reproduced', type=Path)
a = p.parse_args()
reference = Path(__file__).resolve().parents[1] / 'results' / 'synthetic-v2'
def rows(path):
    with path.open() as f:
        return [{k: v for k, v in r.items() if k != 'elapsed_seconds'} for r in csv.DictReader(f)]
x, y = rows(reference/'metrics.csv'), rows(a.reproduced/'metrics.csv')
# Timing is reported separately and is not a deterministic outcome.

assert len(x) == len(y) == 5600
for old, new in zip(x, y):
    for key in old:
        if 'elapsed' not in key and 'latency' not in key:
            assert old[key] == new[key], (key, old[key], new[key])
def stable(value):
    if isinstance(value, dict):
        return {k: stable(v) for k, v in value.items() if 'elapsed' not in k and 'latency' not in k}
    if isinstance(value, list): return [stable(v) for v in value]
    return value
for filename in ('summary.json', 'conditions.json', 'paired-comparisons.json'):
    assert stable(json.loads((reference/filename).read_text())) == stable(json.loads((a.reproduced/filename).read_text())), filename
print('PASS: 5600 deterministic outcomes and three aggregate artifacts match.')

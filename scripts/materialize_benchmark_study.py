"""Restore exactly15 frozen inference modules, without scorer or annotations."""
import argparse
import hashlib
import json
from pathlib import Path

NAMES = {'benchmark_study.py','benchmark_runtime.py','factorial_study.py','factorial_runtime.py',
    'obligation_study.py','obligation_runtime.py','study_runtime.py','common_linker.py','semantic_runtime.py',
    'structured_runtime.py','webqsp_runtime.py','tog_adapter.py','compact_tog_adapter.py',
    'indexed_tog_adapter.py','declared_json_tog_adapter.py'}


def materialize(study, destination):
    study, destination = Path(study), Path(destination)
    if destination.exists():raise ValueError('Refuse existing destination')
    data = (study / 'manifest.json').read_bytes()
    if hashlib.sha256(data).hexdigest() != (study / 'manifest.sha256').read_text().strip():raise ValueError('Manifest changed')
    plan = json.loads(data)
    if set(plan['source_hashes']) != NAMES:raise ValueError('Unexpected source set')
    sources = {}
    for name, expected in plan['source_hashes'].items():
        raw = (study / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:raise ValueError('Frozen source changed')
        sources[name] = raw
    package = destination / 'flagship_controller';package.mkdir(parents=True)
    (package / '__init__.py').write_text('"""Isolated frozen benchmark inference; no evaluator/annotations."""\n')
    for name, raw in sources.items():(package / name).write_bytes(raw)
    return len(sources)


if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('study', type=Path);p.add_argument('destination', type=Path)
    args = p.parse_args();print('Restored', materialize(args.study, args.destination), 'inference modules')

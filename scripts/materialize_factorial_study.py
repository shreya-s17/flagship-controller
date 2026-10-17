"""Restore nine frozen factorial inference modules, without evaluation labels."""
import argparse
import hashlib
import json
from pathlib import Path

NAMES = {'factorial-study-source.py': 'factorial_study.py', 'factorial-runtime-source.py': 'factorial_runtime.py',
    'obligation-study-source.py': 'obligation_study.py', 'obligation-runtime-source.py': 'obligation_runtime.py',
    'study-runtime-base-source.py': 'study_runtime.py', 'linker-source.py': 'common_linker.py',
    'semantic-source.py': 'semantic_runtime.py', 'parent-source.py': 'structured_runtime.py',
    'transport-source.py': 'webqsp_runtime.py'}


def materialize(study, destination):
    study, destination = Path(study), Path(destination)
    if destination.exists():
        raise ValueError('Refuse existing destination')
    data = (study / 'manifest.json').read_bytes()
    if hashlib.sha256(data).hexdigest() != (study / 'manifest.sha256').read_text().strip():
        raise ValueError('Manifest changed')
    plan = json.loads(data)
    if set(plan['source_hashes']) != set(NAMES):
        raise ValueError('Unexpected source set')
    sources = {}
    for name, expected in plan['source_hashes'].items():
        data = (study / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Frozen source changed')
        sources[NAMES[name]] = data
    package = destination / 'flagship_controller';package.mkdir(parents=True)
    (package / '__init__.py').write_text('"""Isolated factorial development inference; no evaluation labels."""\n')
    for name, data in sources.items():
        (package / name).write_bytes(data)
    return len(sources)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('study', type=Path)
    parser.add_argument('destination', type=Path);args = parser.parse_args()
    print('Restored', materialize(args.study, args.destination), 'inference modules')

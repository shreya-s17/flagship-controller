"""Create an isolated runnable package from a baseline run's source snapshots.

Never overwrite the working implementation or a prior reproduction directory.
The upstream ToG checkout and model/graph remain separately required.
"""
import argparse
import hashlib
import json
from pathlib import Path

NAMES={'harness-source.py':'baseline_development.py','linker-source.py':'common_linker.py',
    'semantic-source.py':'semantic_runtime.py','parent-source.py':'structured_runtime.py',
    'transport-source.py':'webqsp_runtime.py','adapter-source.py':'tog_adapter.py',
    'compact-adapter-source.py':'compact_tog_adapter.py','indexed-adapter-source.py':'indexed_tog_adapter.py'}


def materialize(study,destination):
    study=Path(study);destination=Path(destination)
    if destination.exists():raise ValueError('Refuse existing destination')
    manifest=json.loads((study/'manifest.json').read_text())
    sources={}
    for name,expected in manifest['source_hashes'].items():
        if name not in NAMES:raise ValueError('Unexpected source snapshot')
        data=(study/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Source snapshot mismatch')
        sources[NAMES[name]]=data
    if not set(NAMES.values())-{'compact_tog_adapter.py','indexed_tog_adapter.py'}<=set(sources):raise ValueError('Missing required runtime source')
    package=destination/'flagship_controller';package.mkdir(parents=True)
    (package/'__init__.py').write_text('"""Isolated archived runtime; no evaluator or benchmark labels."""\n')
    for name,data in sources.items():(package/name).write_bytes(data)
    (destination/'source-provenance.json').write_text(json.dumps({'study_manifest_sha256':hashlib.sha256((study/'manifest.json').read_bytes()).hexdigest(),
        'source_hashes':manifest['source_hashes'],'upstream_commit':manifest['upstream_commit'],
        'scope':'source restoration only; obtain pinned upstream and existing graph/model separately; freeze a NEW output directory before execution'},indent=2)+'\n')
    return len(sources)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('study',type=Path);parser.add_argument('destination',type=Path);args=parser.parse_args()
    print('Restored',materialize(args.study,args.destination),'verified runtime modules')

"""Restore the seven frozen closed-obligation development modules without labels or secrets."""
import argparse
import hashlib
import json
from pathlib import Path

NAMES={'obligation-study-source.py':'obligation_study.py','obligation-runtime-source.py':'obligation_runtime.py',
    'study-runtime-base-source.py':'study_runtime.py','linker-source.py':'common_linker.py',
    'semantic-source.py':'semantic_runtime.py','parent-source.py':'structured_runtime.py','transport-source.py':'webqsp_runtime.py'}


def materialize(study,destination):
    study,destination=Path(study),Path(destination)
    if destination.exists():raise ValueError('Refuse existing destination')
    plan=json.loads((study/'manifest.json').read_text())
    if set(NAMES)!=set(plan['source_hashes']):raise ValueError('Unexpected source file set')
    sources={}
    for name,expected in plan['source_hashes'].items():
        data=(study/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Source snapshot mismatch')
        sources[NAMES[name]]=data
    package=destination/'flagship_controller';package.mkdir(parents=True)
    (package/'__init__.py').write_text('"""Isolated common-state development runtime; no evaluator or labels."""\n')
    for name,data in sources.items():(package/name).write_bytes(data)
    return len(sources)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('study',type=Path);parser.add_argument('destination',type=Path);args=parser.parse_args()
    print('Restored',materialize(args.study,args.destination),'source modules')

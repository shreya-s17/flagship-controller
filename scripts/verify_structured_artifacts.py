"""Verify archived structured runs/studies against their saved source and checksums."""
import hashlib
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
folders=sorted((root/'results').glob('structured-dev-*'))+sorted((root/'results').glob('paired-pilot-*'))
if not folders:raise SystemExit('No structured artifacts found')
for folder in folders:
    if not folder.is_dir():continue
    plan_path=folder/('plan.json' if (folder/'plan.json').exists() else 'manifest.json')
    manifest=json.loads(plan_path.read_text())
    for filename,key in [('runtime-source.py','source_sha256'),('transport-source.py','transport_sha256')]:
        if hashlib.sha256((folder/filename).read_bytes()).hexdigest()!=manifest[key]:raise SystemExit('Source mismatch: '+str(folder/filename))
    if 'harness_sha256' in manifest:
        if hashlib.sha256((folder/'harness-source.py').read_bytes()).hexdigest()!=manifest['harness_sha256']:raise SystemExit('Harness mismatch')
    if not (folder/'predictions.jsonl').exists():
        print(folder.name+': frozen plan/source hashes verified; execution results not yet archived')
        continue
    hashes=json.loads((folder/'checksums.json').read_text())
    for filename,expected in hashes.items():
        if hashlib.sha256((folder/filename).read_bytes()).hexdigest()!=expected:raise SystemExit('Artifact mismatch: '+str(folder/filename))
    rows=[json.loads(x) for x in (folder/'predictions.jsonl').read_text().splitlines()]
    if 'order' in manifest:
        assert [(r['id'],r['variant']) for r in rows]==[(r['id'],r['variant']) for r in manifest['order']],folder
    else:
        assert [r['id'] for r in rows]==manifest['question_ids'],folder
    print(folder.name+': sources, counts/order and '+str(len(hashes))+' checksums verified')
print('Integrity only; not independent semantic or statistical certification.')

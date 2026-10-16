"""Verify archived structured runs/studies against their saved source and checksums."""
import hashlib
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
folders=sorted((root/'results').glob('structured-dev-*'))+sorted((root/'results').glob('paired-pilot-*'))+sorted((root/'results').glob('semantic-dev-*'))+sorted((root/'results').glob('catalog-diagnostic-*'))+sorted((root/'results').glob('baseline-dev-*'))+sorted((root/'results').glob('common-state-dev-*'))
if not folders:raise SystemExit('No structured artifacts found')
for folder in folders:
    if not folder.is_dir():continue
    plan_path=folder/('plan.json' if (folder/'plan.json').exists() else 'manifest.json')
    manifest=json.loads(plan_path.read_text())
    if 'source_hashes' in manifest:
        for filename,expected in manifest['source_hashes'].items():
            if hashlib.sha256((folder/filename).read_bytes()).hexdigest()!=expected:raise SystemExit('Source mismatch: '+str(folder/filename))
    else:
        for filename,key in [('runtime-source.py','source_sha256'),('transport-source.py','transport_sha256')]:
            if hashlib.sha256((folder/filename).read_bytes()).hexdigest()!=manifest[key]:raise SystemExit('Source mismatch: '+str(folder/filename))
    if 'harness_sha256' in manifest:
        if hashlib.sha256((folder/'harness-source.py').read_bytes()).hexdigest()!=manifest['harness_sha256']:raise SystemExit('Harness mismatch')
    hashes=json.loads((folder/'checksums.json').read_text()) if (folder/'checksums.json').exists() else {}
    for filename,expected in hashes.items():
        if hashlib.sha256((folder/filename).read_bytes()).hexdigest()!=expected:raise SystemExit('Artifact mismatch: '+str(folder/filename))
    if manifest.get('kind')=='privileged offline post-run training diagnostic':
        assert hashlib.sha256((folder/'full-audit.json').read_bytes()).hexdigest()==manifest['full_audit_sha256']
        assert len(json.loads((folder/'full-audit.json').read_text())['rows'])==manifest['n_questions']
        print(folder.name+': source and offline full-audit hash/count verified; no inference claims')
        continue
    if not (folder/'predictions.jsonl').exists():
        print(folder.name+': frozen plan/source hashes verified; execution results not yet archived')
        continue
    if not hashes:raise SystemExit('Missing executed artifact checksums: '+str(folder))
    rows=[json.loads(x) for x in (folder/'predictions.jsonl').read_text().splitlines()]
    if 'order' in manifest:
        assert [(r['id'],r.get('seed'),r['variant']) for r in rows]==[(r['id'],r.get('seed'),r['variant']) for r in manifest['order']],folder
    else:
        assert [r['id'] for r in rows]==manifest['question_ids'],folder
    print(folder.name+': sources, counts/order and '+str(len(hashes))+' checksums verified')
for folder in sorted((root/'evaluation').glob('reserved-training-100*')):
    manifest=json.loads((folder/'manifest.json').read_text())
    assert hashlib.sha256((folder/'inputs.jsonl').read_bytes()).hexdigest()==manifest['reserved_inputs_sha256']
    records=[json.loads(x) for x in (folder/'inputs.jsonl').read_text().splitlines()]
    assert [r['id'] for r in records]==manifest['question_ids']
    assert all(r['split']=='train_remaining' and set(r)=={'id','question','split'} for r in records)
    for filename,expected in manifest['source_hashes'].items():
        assert hashlib.sha256((folder/filename).read_bytes()).hexdigest()==expected
    print(folder.name+': reserved question-only inputs/source verified; no execution claim')
print('Integrity only; not independent semantic or statistical certification.')

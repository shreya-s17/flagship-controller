"""Reproduce finite guard and gold-free catalog reports from their bound sources."""
import hashlib
import json
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from flagship_controller import obligation_stress, catalog_intervention_audit

for name in ('closed-guard-stress-001', 'catalog-contrast-001'):
    folder = root / 'results' / name
    for path, expected in json.loads((folder / 'checksums.json').read_text()).items():
        if Path(path).name != path or hashlib.sha256((folder / path).read_bytes()).hexdigest() != expected:
            raise SystemExit('Audit artifact changed: ' + path)
    if name == 'closed-guard-stress-001':
        actual = obligation_stress.execute(folder)
    else:
        manifest = json.loads((folder / 'manifest.json').read_text())
        for path, expected in manifest['source_hashes'].items():
            if hashlib.sha256((root / path).read_bytes()).hexdigest() != expected:
                raise SystemExit('Catalog diagnostic source changed')
        actual = catalog_intervention_audit.check(root / manifest['study'])
    if actual != json.loads((folder / 'report.json').read_text()):
        raise SystemExit('Audit reproduction mismatch: ' + name)
    print(name + ': report reproduced exactly; scope limitations retained')
print('Software/finite-scope verification only; no independent semantic review or publication clearance.')

import hashlib,importlib.util,json,sys
from pathlib import Path
root=Path('/opt/flagship-controller');sys.path[:0]=[str(root),str(root/'scripts')]
from recheck_graph_witnesses import recheck
from flagship_controller.webqsp_runtime import Freebase
from flagship_controller.structured_runtime import StructuredGraph
study=root/'results/common-state-dev-003'
assert json.loads((study/'completion.json').read_text())['completed']==20
assert not (study/'structured-graph-requery-audit.json').exists()
allrows=list(map(json.loads,(study/'predictions.jsonl').read_text().splitlines()))
rows=[r for r in allrows if not r['variant'].startswith('tog-')]
result=recheck(rows,Freebase('http://127.0.0.1:8891/sparql','dki-archive-sha256-01ac8da685b7cc05',max_calls=200))
result['cohort']='structured-controller records only; no baseline semantic certification'
result['auditor_sha256']=hashlib.sha256((root/'scripts/recheck_graph_witnesses.py').read_bytes()).hexdigest()
(study/'structured-graph-requery-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('Witness requery',result['unique_triples'],result['present'],result['not_observed'],result['unknown'],flush=True)
source=root/'evaluation/offline/catalog_audit.py'
spec=importlib.util.spec_from_file_location('catalog_audit',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
fixed=[r for r in allrows if r['variant']=='fixed']
assert len(fixed)==4 and all(r['seed']==17 for r in fixed)
ids={r['id'] for r in fixed}
labels=[r for r in map(json.loads,(root/'benchmark-data/webqsp/evaluation-only.jsonl').read_text().splitlines()) if r['id'] in ids]
assert {r['id'] for r in labels}==ids
folder=root/'results/catalog-diagnostic-002';folder.mkdir(exist_ok=False,mode=0o700)
(folder/'audit-source.py').write_bytes(source.read_bytes())
(folder/'driver-source.py').write_bytes(Path(__file__).read_bytes())
result=module.audit(fixed,labels,StructuredGraph('http://127.0.0.1:8891/sparql','dki-archive-sha256-01ac8da685b7cc05',max_calls=300,timeout=5),on_result=lambda r:print(r['id'],'catalog',r['known_catalog_best_f1'],'all',r['catalog_completely_evaluated'],flush=True))
result['source_predictions_sha256']=hashlib.sha256((study/'predictions.jsonl').read_bytes()).hexdigest()
full=json.dumps(result,indent=2)+'\n';(folder/'full-audit.json').write_text(full);(folder/'full-audit.json').chmod(0o600)
summary={k:v for k,v in result.items() if k not in ('rows','query_audit')}
summary['rows']=[{k:v for k,v in r.items() if k!='candidate_results'} for r in result['rows']]
summary['candidate_detail_location']='full-audit.json, restored losslessly from evidence bundle; offline evaluation only'
(folder/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
manifest={'kind':'privileged offline post-run training diagnostic','source_hashes':{name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in ('audit-source.py','driver-source.py')},'n_questions':4,'full_audit_sha256':hashlib.sha256(full.encode()).hexdigest(),'source_study':'common-state-dev-003','seed':17,'runtime_labels_access':'Annotations read by root only after timed inference; runtime account remains unable to read them.','note':'Label-informed development selection; catalog answer-set upper bound is not semantic proof or certified budget-feasible recovery. No findings supplied to inference.'}
(folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(folder/'checksums.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir()},indent=2)+'\n')
print('Catalog audit complete',result['catalog_exact_found'],result['catalog_completely_evaluated'],result['query_calls'],flush=True)

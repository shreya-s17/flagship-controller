import json,sys
from pathlib import Path
from flagship_controller import benchmark_runtime as runtime, factorial_study as helpers
root=Path(sys.argv[1]);folder=root/'sanity';folder.mkdir(exist_ok=True)
plan=json.loads((root/'study/manifest.json').read_text());record=json.loads((root/'smoke-input.json').read_text())
assert record['split']=='pilot' and record['id']=='WebQTrn-938'
helpers.verify_environment(folder,plan,'http://127.0.0.1:11434/api/chat')
def observe(path):
 def log(event):
  with path.open('a') as stream:stream.write(json.dumps(event)+'\n');stream.flush()
 return log
common=helpers.old.journal(folder,'common',{'stage':'smoke-common','record':record},lambda:runtime.capture(record,'http://127.0.0.1:8891/sparql','http://127.0.0.1:11434/api/chat',plan['model'],plan['snapshot'],17,observe(folder/'common.progress.jsonl')),lambda:runtime.interrupted_capture(record,17,plan['model'],plan['snapshot'],folder/'common.progress.jsonl'))
if not common['internal_ready'] or common['link'] is None:raise RuntimeError('Sanity capture did not reach both intended boundaries')
packet=helpers.old.journal(folder,'catalog-on',{'common':runtime.shared.digest(common)},lambda:runtime.factorial.capture_catalog(common,'on','http://127.0.0.1:8891/sparql','http://127.0.0.1:11434/api/chat',observe(folder/'catalog.progress.jsonl')),lambda:helpers.interrupted_packet(record,17,plan['model'],plan['snapshot'],folder/'catalog.progress.jsonl',common['internal'],stage='catalog',catalog_mode='on',common_sha256=runtime.shared.digest(common)))
rows=[]
for policy in ('repair-C1G1','tog-declared-json'):
 prefix=common['link'] if policy=='tog-declared-json' else packet['internal']
 def operation():
  if policy=='tog-declared-json':return runtime.baseline(common,'http://127.0.0.1:8891/sparql','http://127.0.0.1:11434/api/chat','/opt/flagship-upstream/tog-7ccbb92',observe(folder/(policy+'.progress.jsonl')))
  return runtime.factorial.continue_policy(packet,policy,'http://127.0.0.1:8891/sparql','http://127.0.0.1:11434/api/chat',observe(folder/(policy+'.progress.jsonl')))
 row=helpers.old.journal(folder,policy,{'policy':policy,'record':record},operation,lambda:helpers.old.interrupted_result(record,'interrupted_smoke_unknown_usage',prefix,folder/(policy+'.progress.jsonl')))
 if 'runtime_error' in row['reason'] or 'shared_state_' in row['reason'] or row['reason'].startswith('interrupted'):raise RuntimeError('Sanity operational failure: '+row['reason'])
 rows.append(row)
(folder/'predictions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
(folder/'completion.json').write_text(json.dumps({'completed':2,'shared_link_and_nested_replay':'PASS','scientific_score':None,'purpose':'Known development operational smoke, not new benchmark evidence'},indent=2)+'\n')
print('Known development smoke complete; baseline shares linking only; no benchmark result claimed',flush=True)

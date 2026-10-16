"""Offline scoring for purpose-selected development regressions, not a benchmark.

Hand-authored paraphrases have no labels and are explicitly unscored. Refuse to
analyze an incomplete run. Costs are separated by scored/unscored cohorts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flagship_controller.official_score import score


def analyze(folder,gold):
    plan=json.loads((folder/'manifest.json').read_text())
    records=[json.loads(x) for x in (folder/'predictions.jsonl').read_text().splitlines()]
    if [r['id'] for r in records]!=plan['question_ids']:raise ValueError('Incomplete or reordered development run')
    selected=[r for r in records if r['id'].startswith('WebQTrn-')];ids={r['id'] for r in selected}
    annotations=[r for r in map(json.loads,gold.read_text().splitlines()) if r['id'] in ids]
    result=score(selected,annotations)
    result['scope']='Purpose-selected previously inspected training regression cases; not representative, held-out or evidence of population improvement'
    def costs(rows):return {k:sum(r['cost'][k] for r in rows) for k in ('graph_calls','model_calls','model_tokens','elapsed_seconds')}
    result['cost_over_scored_cases']=costs(selected);result['cost_over_all_cases']=costs(records)
    result['usage_complete_over_all_cases']=all(r['cost'].get('model_usage_complete',False) for r in records)
    result['unscored_handwritten_paraphrases']=[{'id':r['id'],'terminal':r['terminal'],'reason':r['reason']} for r in records if r not in selected]
    result['predictions_sha256']=hashlib.sha256((folder/'predictions.jsonl').read_bytes()).hexdigest()
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path);parser.add_argument('gold',type=Path);args=parser.parse_args()
    print(json.dumps(analyze(args.folder,args.gold),indent=2))

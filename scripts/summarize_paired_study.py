"""Offline selected-slice analysis; gold file must stay inaccessible to runtime."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import random
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flagship_controller.official_score import score


def analyze(folder,gold):
    plan=json.loads((folder/'plan.json').read_text())
    predictions=[json.loads(x) for x in (folder/'predictions.jsonl').read_text().splitlines()]
    if [(r['id'],r['variant']) for r in predictions]!=[(r['id'],r['variant']) for r in plan['order']]:raise ValueError('Incomplete or reordered study')
    labels=[json.loads(x) for x in gold.read_text().splitlines() if x.strip()]
    selected=[r for r in labels if r['id'] in plan['question_ids']]
    report={'scope':'prospectively frozen exploratory training-pilot comparison; not confirmatory or official test',
            'n_questions':len(plan['question_ids']),'plan_sha256':hashlib.sha256((folder/'plan.json').read_bytes()).hexdigest(),
            'variants':{},'stop_error_rates':None,'stop_note':'No independent feasible-continuation labels; rates not identifiable',
            'recovery_note':'Observed failed-first-plan to exact-answer transitions only; not a certified recoverable-case rate or equal-realized-cost H2 result',
            'external_baseline_reproduced':False}
    maps={};metrics={}
    for variant in ('fixed','repair'):
        rows=[r for r in predictions if r['variant']==variant];maps[variant]={r['id']:r for r in rows}
        m=score(rows,selected);metrics[variant]={r['id']:r for r in m['rows']}
        m['cost']={k:sum(r['cost'][k] for r in rows) for k in ('graph_calls','model_calls','model_tokens','elapsed_seconds')}
        m['cost']['model_usage_complete']=all(r['cost'].get('model_usage_complete',False) for r in rows)
        m['reasons']=dict(collections.Counter(r['reason'] for r in rows))
        m['observed_exact_after_reject']=sum(r['terminal']=='ANSWER' and any(t['action']=='REJECT' for t in r['trace']) and metrics[variant][r['id']].get('exact_f1')==1 for r in rows)
        report['variants'][variant]=m
    pairs=[]
    for qid in plan['question_ids']:
        f,r=maps['fixed'][qid],maps['repair'][qid]
        first=lambda row:next((t['program'] for t in row['trace'] if t['action']=='PLAN'),None)
        pairs.append({'id':qid,'both_scorable':metrics['fixed'][qid]['scorable'] and metrics['repair'][qid]['scorable'],
            'f1_delta':metrics['repair'][qid].get('f1',0)-metrics['fixed'][qid].get('f1',0),
            'first_plans_match':first(f)==first(r),'tokens_delta':r['cost']['model_tokens']-f['cost']['model_tokens'],
            'graph_calls_delta':r['cost']['graph_calls']-f['cost']['graph_calls'],
            'seconds_delta':r['cost']['elapsed_seconds']-f['cost']['elapsed_seconds']})
    valid=[r for r in pairs if r['both_scorable']]
    rng=random.Random(17);n=len(valid)
    if n:
        bs=sorted(sum(valid[rng.randrange(n)]['f1_delta'] for _ in range(n))/n for _ in range(10000))
        report['paired_f1_delta']={'mean':sum(r['f1_delta'] for r in valid)/n,'exploratory_95percent_percentile_interval':[bs[249],bs[9749]],'bootstrap_unit':'question','replicates':10000,'seed':17}
    report['pairs']=pairs
    report['limitations']=['Small training-pilot sample; no population or superiority inference','Same-model semantic gate remains uncalibrated','Different realized inference costs and warm-cache effects','First-plan equality is audited, not assumed','Graph snapshot date and full benchmark comparability unverified','No independent semantic or STOP/recoverability adjudication']
    if 'original_predictions_sha256' in plan:
        report['scope']='Exploratory same-state replay of the original training-pilot questions; not independent data or fresh end-to-end timing'
        report['limitations'].append('Costs charge the saved fixed prefix to both; repair elapsed is constructed prefix plus replay/continuation time; fixed elapsed is original. Do not infer latency savings.')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('gold',type=Path);a=p.parse_args()
    print(json.dumps(analyze(a.folder,a.gold),indent=2))

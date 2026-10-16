"""Offline development summary; annotations never enter the runtime package."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flagship_controller.official_score import score


def analyze(folder,gold):
    folder=Path(folder);plan=json.loads((folder/'manifest.json').read_text())
    rows=list(map(json.loads,(folder/'predictions.jsonl').read_text().splitlines()))
    if [(r['id'],r['seed'],r['variant']) for r in rows]!=[(r['id'],r['seed'],r['variant']) for r in plan['order']]:raise ValueError('Incomplete/reordered outputs')
    official={r['id'] for r in rows if r['id'].startswith('WebQTrn-')}
    labels=[r for r in map(json.loads,Path(gold).read_text().splitlines()) if r['id'] in official]
    if {r['id'] for r in labels}!=official:raise ValueError('Missing official annotations')
    methods={}
    for variant in dict.fromkeys(r['variant'] for r in rows):
        selected=[r for r in rows if r['variant']==variant]
        scores={str(seed):score([r for r in selected if r['seed']==seed and r['id'] in official],labels) for seed in plan['seeds']}
        per_question=[]
        for qid in sorted(official):
            values=[r['f1'] for s in scores.values() for r in s['rows'] if r['id']==qid and r['scorable']]
            if values:per_question.append({'id':qid,'mean_f1_across_seeds':sum(values)/len(values),'seeds':len(values)})
        methods[variant]={'official_scores_by_seed':scores,'question_means':per_question,
            'mean_question_f1':sum(r['mean_f1_across_seeds'] for r in per_question)/len(per_question) if per_question else None,
            'charged_cost_all':{key:sum(r['cost'][key] for r in selected) for key in ('model_calls','model_tokens','graph_calls','elapsed_seconds')},
            'physical_new_model_attempts_known':sum(r['cost'].get('physical_new_model_calls') or 0 for r in selected),
            'usage_complete':all(r['cost']['model_usage_complete'] and not r['cost'].get('cost_is_lower_bound') for r in selected),
            'all_outcomes':[{'id':r['id'],'seed':r['seed'],'terminal':r['terminal'],'answers':r['answers'],'reason':r['reason']} for r in selected]}
    prefixes=[]
    for path in sorted((folder/'journal').glob('*-prefix.json')):prefixes.append(json.loads(path.read_text())['value'])
    known_prefix_calls=sum(sum(not e.get('replayed',False) for e in p.get('provider_audit',[])) for p in prefixes)
    new_policy_calls=sum(m['physical_new_model_attempts_known'] for m in methods.values())
    fixed=methods['fixed']['mean_question_f1'];repair=methods['repair']['mean_question_f1']
    return {'scope':'Purpose-selected development mechanics check; no held-out, significance or published-score comparison',
        'executions':len(rows),'unique_question_strings':len(plan['question_ids']),'official_original_questions':len(official),
        'seeds':plan['seeds'],'methods':methods,'repair_minus_fixed_mean_question_f1':repair-fixed if fixed is not None and repair is not None else None,
        'confidence_interval':None,'interval_reason':str(len(official))+' purpose-selected original question(s); no population interval, and repeated seeds are not independent questions',
        'physical_model_attempts_known':{'common_prefix_capture_once':known_prefix_calls,'policy_continuations':new_policy_calls,'total':known_prefix_calls+new_policy_calls},
        'stop_recovery_rates':None,'limits':['Different realized costs and hypothesis spaces','Replayed time is constructed, not fresh end-to-end latency',
            'Handwritten controls unscored','No independent semantic/STOP labels or calibrated reliability','Unknown interrupted costs are lower bounds; null physical counts are not measured zero']}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path);parser.add_argument('gold',type=Path);args=parser.parse_args()
    print(json.dumps(analyze(args.folder,args.gold),indent=2))

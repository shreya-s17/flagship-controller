"""Frozen offline answer-set feasibility analysis; no inference imports."""
import argparse
import hashlib
import json
from pathlib import Path
import random
from .benchmark_audit import check
from .official_score import score


def paired_interval(left, right, resamples=10000, seed=113):
    if set(left) != set(right) or not left:raise ValueError('Identical nonempty question units required')
    ids = sorted(left);deltas = [left[q]-right[q] for q in ids];n = len(ids)
    rng = random.Random(seed);samples = sorted(sum(deltas[rng.randrange(n)] for _ in range(n))/n for _ in range(resamples))
    return {'question_units':n,'mean_difference':sum(deltas)/n,'lower_95':samples[int(.025*resamples)],
            'upper_95':samples[min(resamples-1,int(.975*resamples))],'resamples':resamples,'analysis_seed':seed,
            'scope':'Paired question-cluster percentile bootstrap; descriptive feasibility uncertainty, not power/generalization proof'}


def analyze(folder, gold):
    folder = Path(folder);ledger = check(folder);plan = json.loads((folder/'manifest.json').read_text())
    for name,expected in plan['analysis_source_hashes'].items():
        if Path(name).name!=name or hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()!=expected or hashlib.sha256((folder/'analysis-sources'/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Frozen analysis source changed')
    rows = list(map(json.loads,(folder/'predictions.jsonl').read_text().splitlines()))
    ids = set(plan['question_ids']);labels = [r for r in map(json.loads,Path(gold).read_text().splitlines()) if r['id'] in ids]
    if {r['id'] for r in labels} != ids:raise ValueError('Missing selected-slice annotations')
    methods = {};means = {}
    for policy in plan['policies']:
        selected = [r for r in rows if r['variant']==policy]
        scored = {str(seed):score([r for r in selected if r['seed']==seed],labels) for seed in plan['seeds']}
        per_question = {}
        for qid in plan['question_ids']:
            values = [r['f1'] for s in scored.values() for r in s['rows'] if r['id']==qid and r['scorable']]
            if values:per_question[qid]=sum(values)/len(values)
        means[policy]=per_question
        methods[policy]={'official_scores_by_seed':scored,'question_means':per_question,
            'mean_question_f1':sum(per_question.values())/len(per_question) if per_question else None,
            'planned_outcomes':300,'submitted_outcomes':len(selected),
            'charged_usage':{k:sum(r['cost'][k] for r in selected) for k in ('model_calls','model_tokens','graph_calls','elapsed_seconds')},
            'complete_usage':all(r['cost'].get('model_usage_complete') and not r['cost'].get('cost_is_lower_bound') for r in selected),
            'unknown_usage_records':sum(not r['cost'].get('model_usage_complete') or bool(r['cost'].get('cost_is_lower_bound')) for r in selected),
            'native_semantic_accuracy':None}
    return {'scope':'Reserved training feasibility; no official test or submission-ready certification',
        'executions':len(rows),'questions':100,'seeds':plan['seeds'],'ledger':ledger,'methods':methods,
        'primary_repair_minus_fixed':paired_interval(means['repair-C1G1'],means['fixed-C1G1']),
        'independent_semantic_review':None,'author_review_counted_as_independent':False,
        'early_stop_rate':None,'late_stop_rate':None,'certified_recovery_rate':None,
        'limits':['Selected training cohort, not official test or pretraining-contamination proof',
            'Repeated seeds averaged within question, not treated as independent questions',
            'Common maxima do not mean matched realized cost; replay latency is constructed',
            'Local ToG adaptation is not original-paper reproduction; native judgments remain separate',
            'Frozen hand-designed closed rules are incomplete; no calibrated reliability or novelty established']}


def main():
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('gold',type=Path);a=p.parse_args()
    print(json.dumps(analyze(a.folder,a.gold),indent=2))


if __name__=='__main__':main()

"""Offline factorial development scores, full denominators and physical usage.

Never imported by inference. Labels are read only after completed ledger audit.
"""
import argparse
import json
from pathlib import Path
from .factorial_audit import check
from .official_score import score


def known_total(values):
    return {'known_lower_bound': sum(v for v in values if v is not None),
            'complete': all(v is not None for v in values),
            'unknown_components': sum(v is None for v in values)}


def analyze(folder, gold):
    folder = Path(folder);ledger = check(folder)
    plan = json.loads((folder / 'manifest.json').read_text())
    rows = list(map(json.loads, (folder / 'predictions.jsonl').read_text().splitlines()))
    official = {r['id'] for r in rows if r['id'].startswith('WebQTrn-')}
    labels = [r for r in map(json.loads, Path(gold).read_text().splitlines()) if r['id'] in official]
    if {r['id'] for r in labels} != official:
        raise ValueError('Missing official annotations')
    methods = {}
    for policy in plan['policies']:
        selected = [r for r in rows if r['variant'] == policy]
        scores = {str(seed): score([r for r in selected if r['seed'] == seed and r['id'] in official], labels) for seed in plan['seeds']}
        means = []
        for qid in sorted(official):
            values = [r['f1'] for s in scores.values() for r in s['rows'] if r['id'] == qid and r['scorable']]
            if values:
                means.append({'id': qid, 'mean_f1_across_seeds': sum(values) / len(values), 'seeds': len(values)})
        methods[policy] = {'official_scores_by_seed': scores, 'question_means': means,
            'mean_question_f1': sum(r['mean_f1_across_seeds'] for r in means) / len(means) if means else None,
            'charged_cost_all': {k: sum(r['cost'][k] for r in selected) for k in ('model_calls', 'model_tokens', 'graph_calls', 'elapsed_seconds')},
            'usage_complete': all(r['cost']['model_usage_complete'] and not r['cost'].get('cost_is_lower_bound') for r in selected),
            'repair_plan_events': sum(e['action'] == 'REPAIR_PLAN' for r in selected for e in r.get('trace', [])),
            'all_outcomes': [{'id': r['id'], 'seed': r['seed'], 'terminal': r['terminal'], 'answers': r['answers'], 'reason': r['reason']} for r in selected]}
    common = [json.loads(p.read_text())['value'] for p in sorted((folder / 'journal').glob('*-common.json'))]
    catalogs = [json.loads(p.read_text())['value'] for p in sorted((folder / 'journal').glob('*-catalog-*.json'))
                if p.name.endswith(('-catalog-on.json', '-catalog-off.json'))]
    physical = {}
    for name, key in [('model_attempts', 'physical_new_model_calls'), ('graph_calls', 'physical_new_graph_calls'), ('seconds', 'physical_execution_seconds')]:
        physical[name] = {
            'common_capture': known_total([p['physical_stage'][name] for p in common]),
            'catalog_capture': known_total([p['physical_stage'][name] for p in catalogs]),
            'policy_continuations': known_total([r['cost'].get(key) for r in rows])}
        parts = physical[name]
        parts['total_known_lower_bound'] = sum(v['known_lower_bound'] for v in parts.values())
        parts['complete'] = all(v['complete'] for v in parts.values() if isinstance(v, dict))
    def mean(policy):
        return methods[policy]['mean_question_f1']
    values = [mean(p) for p in ('repair-C0G0', 'repair-C0G1', 'repair-C1G0', 'repair-C1G1', 'fixed-C1G1')]
    a, b, c, d, fixed = values
    contrasts = None if any(v is None for v in values) else {
        'repair_minus_fixed_C1G1': d - fixed,
        'guard_effect_given_C0': b - a, 'guard_effect_given_C1': d - c,
        'catalog_effect_given_G0': c - a, 'catalog_effect_given_G1': d - b,
        'interaction_C_by_G': d - c - b + a}
    return {'scope': 'Failure-informed, reused development strings; descriptive factorial outcomes only',
            'executions': len(rows), 'unique_question_strings': len(plan['question_ids']),
            'official_original_questions': len(official), 'seeds': plan['seeds'], 'ledger_rows_checked': ledger['rows_checked'],
            'methods': methods, 'descriptive_f1_contrasts': contrasts, 'confidence_interval': None,
            'interval_reason': str(len(official)) + ' purpose-selected official originals; no population or statistical superiority claim',
            'physical': physical, 'stop_recovery_rates': None,
            'limits': ['Handwritten controls unscored; repeated seeds and paraphrases are not independent questions',
                       'Unequal realized usage and constructed replay latency; no matched-cost advantage',
                       'Closed ontology/language priors are incomplete and hand-designed',
                       'No independent semantic/STOP/recovery review, external-method reproduction or novelty claim',
                       'The factorial contrast is conditional on the frozen common observed root/schema state, not all possible retrievals']}


def main():
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('folder', type=Path)
    parser.add_argument('gold', type=Path);args = parser.parse_args()
    print(json.dumps(analyze(args.folder, args.gold), indent=2))


if __name__ == '__main__':
    main()

"""Offline trace-based recovery diagnosis; never imported by inference.

An answer after a rejection is a branch observation, not certified recovery.
Scores are read from the separately generated development summary, not labels.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def describe(row, official_score=None):
    attempts = []
    for event in row.get('trace', []):
        action = event['action']
        if action in ('PLAN', 'REPAIR_PLAN'):
            if action == 'REPAIR_PLAN' and (not attempts or not attempts[-1].get('rejection')):
                raise ValueError('Repair has no preceding recorded rejection')
            attempts.append({'action': action, 'program_index': event['program_index'],
                             'program': event['program'], 'acquired_answers': None,
                             'semantic_gate': None, 'rejection': None})
        elif action in ('ACQUIRE', 'SEMANTIC_VERIFY', 'REJECT'):
            if not attempts:
                raise ValueError('Execution event without a recorded plan')
            key = {'ACQUIRE': 'acquired_answers', 'SEMANTIC_VERIFY': 'semantic_gate',
                   'REJECT': 'rejection'}[action]
            attempts[-1][key] = event[{'ACQUIRE': 'answers', 'SEMANTIC_VERIFY': 'gate',
                                     'REJECT': 'reason'}[action]]
    revisions = sum(a['action'] == 'REPAIR_PLAN' for a in attempts)
    exact = bool(official_score['exact_f1']) if official_score and official_score.get('scorable') else None
    answered_after_rejection = bool(revisions and row['terminal'] == 'ANSWER')
    return {'id': row['id'], 'seed': row['seed'], 'variant': row['variant'],
            'terminal': row['terminal'], 'reason': row['reason'], 'answers': row['answers'],
            'attempts': attempts, 'repair_plan_events': revisions,
            'rejection_reasons': [a['rejection'] for a in attempts if a['rejection']],
            'reason_text_withheld_events': sum(e.get('action') == 'REJECTION_REASON_TEXT_WITHHELD'
                                             for e in row.get('semantic_audit', [])),
            'semantic_gate_bypass_events': sum(e.get('action') == 'SEMANTIC_GATE_DISABLED'
                                             for e in row.get('semantic_audit', [])),
            'answered_after_recorded_rejection': answered_after_rejection,
            'official_final_exact': exact,
            'official_exact_after_recorded_rejection': bool(answered_after_rejection and exact),
            'independent_semantic_recovery': None,
            'catalog_size': next((len(e['programs']) for e in row.get('trace', [])
                                  if e['action'] == 'PROGRAM_CATALOG'), None)}


def diagnose(folder):
    folder = Path(folder)
    prediction_bytes = (folder/'predictions.jsonl').read_bytes()
    rows = list(map(json.loads, prediction_bytes.decode().splitlines()))
    plan = json.loads((folder/'manifest.json').read_text())
    completion = json.loads((folder/'completion.json').read_text())
    if completion['completed'] != len(rows) or completion['predictions_sha256'] != hashlib.sha256(prediction_bytes).hexdigest():
        raise ValueError('Incomplete or changed predictions')
    if [(r['id'], r['seed'], r['variant']) for r in rows] != [(r['id'], r['seed'], r['variant']) for r in plan['order']]:
        raise ValueError('Frozen denominator/order differs')
    score_bytes = (folder/'development-score.json').read_bytes()
    scores = json.loads(score_bytes)
    lookup = {(s['id'], int(seed), variant): s for variant, method in scores['methods'].items()
              for seed, scored in method['official_scores_by_seed'].items() for s in scored['rows']}
    details = [describe(r, lookup.get((r['id'], r['seed'], r['variant']))) for r in rows]
    methods = {}
    for variant in dict.fromkeys(r['variant'] for r in rows):
        selected = [r for r in details if r['variant'] == variant]
        methods[variant] = {'outcomes': len(selected),
            'rejections': dict(Counter(reason for r in selected for reason in r['rejection_reasons'])),
            **{key: sum(r[key] for r in selected) for key in ('repair_plan_events',
                'reason_text_withheld_events', 'semantic_gate_bypass_events',
                'answered_after_recorded_rejection', 'official_exact_after_recorded_rejection')}}
    return {'scope': 'Offline branch/official-set diagnosis on inspected development questions; not independent semantic or STOP labels',
            'predictions_sha256': hashlib.sha256(prediction_bytes).hexdigest(),
            'development_score_sha256': hashlib.sha256(score_bytes).hexdigest(),
            'diagnostic_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'methods': methods, 'rows': details, 'certified_recovery_rate': None,
            'limits': ['Final exact set after a rejected plan is not independently certified recovery.',
                       'Provisional acquired answers are not accepted answers.',
                       'No gold query, labels or oracle are supplied to inference.',
                       'Missing catalog alternatives cannot be recovered by reselecting that same catalog.',
                       'Purpose-selected cases and seed repeats do not estimate population effects.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    print(json.dumps(diagnose(args.folder), indent=2))

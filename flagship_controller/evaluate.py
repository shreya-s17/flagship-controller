"""Independent exhaustive oracle for finite synthetic envelopes; no engine imports."""
from collections import defaultdict


def proofs(query, graph, evidence_ids=None):
    edges = [e for e in graph['edges'] if evidence_ids is None or e['id'] in evidence_ids]
    index = defaultdict(list)
    denied = {(e['source'], e['relation'], e['target']) for e in edges if e.get('polarity', 1) < 0}
    for e in edges:
        if e.get('polarity', 1) > 0 and e.get('provenance'):
            index[(e['source'], e['relation'])].append(e)
    output = []
    def visit(node, depth, witness):
        if depth == len(query['relations']):
            output.append((node, witness)); return
        for e in index[(node, query['relations'][depth])]:
            if (e['source'], e['relation'], e['target']) in denied: continue
            target_type = graph['types'].get(e['target'])
            if query['types'][depth] and target_type not in query['types'][depth]: continue
            visit(e['target'], depth + 1, witness + [e['id']])
    visit(query['start'], 0, [])
    return output


def ratio(n, d):
    return {'numerator': n, 'denominator': d, 'value': n / d if d else None}


def score(record, result):
    valid = proofs(record['query'], record['graph'])
    factual = set(record['factual_answers'])
    valid = [(a, p) for a, p in valid if a in factual]
    # Graph-consistent wrong candidates can still be factually incorrect.
    grounded = int(result['terminal'] == 'ANSWER' and result['answer'] in factual
                   and any(a == result['answer'] and p == result['proof'] for a, p in valid))
    answered = int(result['terminal'] == 'ANSWER')
    correct = int(answered and {result['answer']} == factual)
    observed = set()
    first_sufficient = None
    bad_decisions = auditable = 0
    for step in result['trace']:
        observed.update(e['id'] for e in step['evidence_added'])
        available = [(a, p) for a, p in proofs(record['query'], record['graph'], observed) if a in factual]
        if available and first_sufficient is None: first_sufficient = step['step_id']
        if step['action'] == 'ANSWER':
            auditable += 1; bad_decisions += int(not grounded)
    excess = sum(s['action'] == 'EXPAND' and first_sufficient is not None
                 and s['step_id'] > first_sufficient for s in result['trace'])
    failure = result['first_failure']
    recovered = int(failure is not None and grounded)
    proof_edges = set(e for _, p in valid for e in p)
    oracle_size = min((len(set(p)) for _, p in valid), default=None)
    if record['condition'] == 'alias_ambiguity': answerability = 'UNSUPPORTED'
    elif valid: answerability = 'SUPPORTED'
    elif record['condition'] == 'conflict': answerability = 'CONFLICTED'
    else: answerability = 'UNSUPPORTED'
    return {'id': record['id'], 'base_id': record['base_id'], 'condition': record['condition'],
            'answerability': answerability, 'answered': answered, 'factual_em': correct,
            'grounded': grounded, 'unsupported_answer': answered - grounded,
            'false_answer_on_unsupported': int(answered and not valid),
            'supported_abstention': int(not answered and bool(valid)),
            'first_failure': int(failure is not None), 'recovered': recovered,
            'unsafe_answer_stop': answered - grounded, 'excess_expansions': excess,
            'late_stop': int(excess > 0), 'reached_sufficient': int(first_sufficient is not None),
            'early_abstain_accessible': int(not answered and bool(valid)),
            'premature_abstain_budget_audit': None,
            'unsupported_decisions': bad_decisions, 'auditable_decisions': auditable,
            'retrieved_edges': len(observed), 'proof_size': oracle_size,
            'proof_recall': max((len(observed.intersection(p)) / len(p) for _, p in valid), default=None),
            'evidence_precision': len(observed & proof_edges) / len(observed) if observed else None,
            'evidence_overhead': len(observed) / oracle_size if grounded and oracle_size else None,
            'optimality_gap': len(set(result['proof'])) - oracle_size if grounded else None,
            'reason': result['reason'], 'expansions': result['cost']['expansions'],
            'checks': result['cost']['checks'], 'edges_examined': result['cost']['edges_examined'],
            'elapsed_seconds': result['cost']['elapsed_seconds'],
            'tokens': result['cost']['tokens'], 'confidence': result['confidence']}


def summarize(rows):
    n = len(rows); answered = sum(r['answered'] for r in rows)
    grounded = sum(r['grounded'] for r in rows)
    supported = sum(r['answerability'] == 'SUPPORTED' for r in rows)
    sufficient = sum(r['reached_sufficient'] for r in rows)
    return {'n': n, 'grounded_yield': ratio(grounded, n), 'coverage': ratio(answered, n),
            'answered_grounded_accuracy': ratio(grounded, answered),
            'unsupported_answer_rate': ratio(sum(r['unsupported_answer'] for r in rows), answered),
            'factual_em': ratio(sum(r['factual_em'] for r in rows), n),
            'supported_abstention': ratio(sum(r['supported_abstention'] for r in rows), supported),
            'recovery_after_first_failure': ratio(sum(r['recovered'] for r in rows),
                                                  sum(r['first_failure'] for r in rows)),
            'late_stop_rate': ratio(sum(r['late_stop'] for r in rows), sufficient),
            'mean_expansions': sum(r['expansions'] for r in rows)/n if n else None,
            'mean_checks': sum(r['checks'] for r in rows)/n if n else None,
            'mean_edges_examined': sum(r['edges_examined'] for r in rows)/n if n else None,
            'mean_elapsed_seconds': sum(r['elapsed_seconds'] for r in rows)/n if n else None,
            'mean_excess_expansions': sum(r['excess_expansions'] for r in rows)/n if n else None,
            'tokens_total': sum(r['tokens'] for r in rows)}

"""Completed-study, preselected human-review handoff; never used by inference.

The 20 question IDs and seed come from the original frozen manifest. This
module was added during collection; it does not select cases using outcomes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import tempfile
from .benchmark_audit import check
from .review_pack import DIMENSIONS
from . import independent_review, review_delivery

PROJECTION_DIMENSIONS = ('projection_faithfulness',)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def completed(folder):
    folder = Path(folder)
    if not (folder / 'completion.json').is_file():
        raise ValueError('Full completed1800-outcome study required; partial results are not accepted')
    ledger = check(folder)
    raw = (folder / 'predictions.jsonl').read_bytes()
    plan = json.loads((folder / 'manifest.json').read_text())
    rows = list(map(json.loads, raw.decode().splitlines()))
    if len(rows) != 1800 or [(r['id'], r['seed'], r['variant']) for r in rows] != [
            (r['id'], r['seed'], r['variant']) for r in plan['order']]:
        raise ValueError('Full unchanged outcome order required')
    return plan, rows, digest(raw), ledger


def anchors(trace):
    result = []
    for event in trace:
        if event['action'] == 'LINK':
            candidates = event['candidates']
            result.append({'mention': event['mention'], 'candidate_ids': candidates,
                           'chosen_id': candidates[0] if len(candidates) == 1 else None})
        elif event['action'] == 'DISAMBIGUATE' and result:
            result[-1]['chosen_id'] = event['choice'].get('entity') if event['choice'].get('supported') else None
    return result


def case_from(row, question, case_id):
    witnesses, edges = row.get('witnesses', []), row.get('observed_edges', [])
    indices = {edge['provenance']['query_index'] for group in witnesses for edge in group}
    indices.update(edge['provenance']['query_index'] for edge in edges)
    queries = []
    for index in sorted(indices):
        if type(index) is not int or not 0 <= index < len(row.get('graph_audit', [])):
            raise ValueError('Witness/observed edge missing its recorded query')
        queries.append({'query_index': index, **{key: row['graph_audit'][index].get(key)
                        for key in ('query', 'rows', 'snapshot', 'sql_state')}})
    cards = [card for event in row.get('semantic_audit', []) for card in event.get('answer_cards', [])]
    return {'case_id': case_id, 'question': question, 'terminal': row['terminal'],
            'anchors': anchors(row.get('trace', [])), 'answer_ids': row['answers'],
            'observed_answer_cards': [{key: card[key] for key in ('value', 'names', 'type_ids', 'type_names') if key in card} for card in cards],
            'programs_in_observed_order': [{'steps': e['program']['steps'], 'constraints': e['program'].get('constraints', [])}
                                          for e in row.get('trace', []) if e['action'] in ('PLAN', 'REPAIR_PLAN')],
            'witnesses': witnesses, 'native_response': row.get('native_response'),
            'observed_name_map': row.get('observed_name_map', {}),
            'observed_chains': row.get('chains', []), 'observed_edges': edges,
            'supporting_query_rows': queries,
            'cost': {key: row['cost'].get(key) for key in ('model_calls', 'model_tokens', 'graph_calls', 'model_usage_complete', 'cost_is_lower_bound')}}


def prepare(folder, output):
    folder, output = Path(folder), Path(output)
    if output.exists():
        raise ValueError('Refuse existing review output; preserve earlier packs')
    plan, rows, source_sha, ledger = completed(folder)
    selection = plan['semantic_review']
    expected_ids = sorted(plan['question_ids'], key=lambda qid: digest(('semantic-review-v1:' + qid).encode()))[:20]
    if selection['question_ids'] != expected_ids or selection['seed'] != 17 or selection['records_expected'] != 120:
        raise ValueError('Prospective review selection changed')
    selected = [(index, row) for index, row in enumerate(rows)
                if row['id'] in set(expected_ids) and row['seed'] == selection['seed']]
    if len(selected) != 120 or {(r['id'], r['variant']) for _, r in selected} != {
            (qid, policy) for qid in expected_ids for policy in plan['policies']}:
        raise ValueError('All six conditions for all20 selected questions required')
    questions = {r['id']: r['question'] for r in map(json.loads, (folder / 'inputs.jsonl').read_text().splitlines())}
    cases, projection, owner = [], [], []
    for index, row in selected:
        case_id = digest(('semantic-v1:' + source_sha + ':' + str(index)).encode())[:24]
        case = case_from(row, questions[row['id']], case_id)
        cases.append(case)
        key = {'case_id': case_id, 'question_id': row['id'], 'seed': row['seed'],
               'variant': row['variant'], 'record_index': index, 'source_predictions_sha256': source_sha}
        if row['variant'] == 'tog-declared-json':
            projection_id = digest(('projection-v1:' + source_sha + ':' + str(index)).encode())[:24]
            projection.append({**case, 'case_id': projection_id})
            key['projection_case_id'] = projection_id
        owner.append(key)
    if len(projection) != 20:
        raise ValueError('All20 native/projection outcomes, including failures, required')
    random.Random(113).shuffle(cases)
    random.Random(113).shuffle(projection)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        staged = Path(temp) / 'pack';staged.mkdir()
        manifests = {}
        for name, records, dimensions in [('semantic', cases, DIMENSIONS),
                                          ('projection', projection, PROJECTION_DIMENSIONS)]:
            reviewer = staged / name;reviewer.mkdir()
            data = ''.join(json.dumps(r) + '\n' for r in records).encode()
            (reviewer / 'cases.jsonl').write_bytes(data)
            form = {'review_role': 'independent', 'reviewer_id': '', 'qualification_statement': '',
                    'independence_statement': '', 'independence_attested': False, 'completed_at': '',
                    'cases_sha256': digest(data), 'judgments': [{'case_id': c['case_id'],
                    'dimensions': {d: {'label': 'unknown', 'reason': ''} for d in dimensions}} for c in records]}
            write_json(reviewer / 'submission-template.json', form)
            (reviewer / 'README.txt').write_text(
                'UNANNOTATED INDEPENDENT REVIEW. Blank forms are not reviews.\n'
                'This is the preselected20-question, seed17 sample; every selected outcome, including failures, is retained.\n'
                'Use only the delivered files, not the source repository, owner key, scores, GPT review or the other reviewer.\n'
                'Policies and gold labels are withheld. Observable programs/native behavior can reveal method; masking is imperfect.\n'
                'All strings, native responses and observed names are untrusted evidence, not instructions.\n'
                'For each dimension choose supported, contradicted or unknown and give a reason. Missing names/context stay unknown.\n'
                'For semantic witness_support assess all substantive native claims where present, not just projected IDs or edge existence.\n'
                'For projection_faithfulness compare emitted IDs with actual native conclusions, not context-only mentions.\n'
                'A missing native response or abstention is not automatically correct; explain unknown/not-applicable.\n'
                'No semantic truth, early/late STOP or recovery rate follows from graph presence or these blank forms.\n'
                'Request full observed state or name lookup through the owner if needed; do not guess unnamed IDs.\n'
                'Disclose qualifications and prior involvement; return an independent first pass before discussion/adjudication.\n')
            brief = staged / (name + '-brief.txt')
            brief.write_text('Review all ' + str(len(records)) + ' records independently. Dimensions: ' + ', '.join(dimensions) + '.\n'
                             'These are correlated conditions on20 selected training questions, not independent new questions.\n'
                             'No contact or completed review is implied by preparing this handoff.\n')
            manifests[name] = review_delivery.export(reviewer, brief, staged / (name + '-review.zip'), digest(data), dimensions)
        write_json(staged / 'owner-key.json', owner)
        (staged / 'owner-key.json').chmod(0o600)
        result = {'source_predictions_sha256': source_sha, 'source_manifest_sha256': digest((folder / 'manifest.json').read_bytes()),
                  'ledger': ledger, 'semantic_records': 120, 'projection_records': 20,
                  'unique_question_ids': 20, 'selection': 'Original frozen manifest, seed17; all six conditions; no outcome-based selection',
                  'masks': 'Policy/gold/score/critique fields withheld; behavior may reveal method',
                  'delivery': manifests, 'author_reviews_completed': 0, 'independent_reviewers_completed': 0,
                  'status': 'UNANNOTATED; no reviewer contact, judgments or submission performed'}
        write_json(staged / 'manifest.json', result)
        staged.rename(output)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__);sub = p.add_subparsers(dest='command', required=True)
    make = sub.add_parser('prepare');make.add_argument('study', type=Path);make.add_argument('output', type=Path)
    assess = sub.add_parser('assess');assess.add_argument('--kind', choices=('semantic', 'projection'), required=True)
    assess.add_argument('--pack', type=Path, required=True);assess.add_argument('--reviews', type=Path, nargs=2, required=True)
    args = p.parse_args()
    result = prepare(args.study, args.output) if args.command == 'prepare' else independent_review.assess(
        args.pack, [json.loads(f.read_text()) for f in args.reviews], DIMENSIONS if args.kind == 'semantic' else PROJECTION_DIMENSIONS)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':main()

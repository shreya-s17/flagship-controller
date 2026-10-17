"""Gold-free offline catalog contrast on complete captured development states.

Reconstruct the preserved schema-only catalog from the *same* observed roots,
schema and anchors. This is an availability diagnostic, never a new model run,
counterfactual answer score or causal effect estimate.
"""
import argparse
import hashlib
import json
from pathlib import Path
from . import obligation_runtime as runtime
from .common_state_audit import committed


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def signature(candidate):
    program = candidate['program']
    return json.dumps({'steps': program['steps'], 'constraints': sorted(
        program['constraints'], key=lambda c: json.dumps(c, sort_keys=True))}, sort_keys=True)


def compatible(obligation, candidate):
    if obligation is None:
        return None
    try:
        runtime.check_obligation(obligation, candidate['program'])
        return True
    except runtime.Blocked:
        return False


def contrast(packet):
    trace = packet['capture_result']['trace']
    if not packet['internal_ready']:
        return {'id': packet['record']['id'], 'seed': packet['seed'], 'status': 'prefix_not_ready'}
    schema_event = next(e for e in trace if e['action'] == 'SCHEMA')
    captured = next(e['programs'] for e in trace if e['action'] == 'PROGRAM_CATALOG')
    inventory = next(e for e in trace if e['action'] == 'PRIMARY_ANCHOR_JOIN_INVENTORY')
    inputs = next(e['prompt']['inputs'] for e in packet['internal']['model_audit']
                  if e['prompt']['instruction'].startswith('Choose a program'))
    connections = {}
    # Preserve actual resolved entity and connection evidence, including future
    # multiple-anchor cases. No name re-linking or fresh graph access occurs.
    anchor_index = 0
    for e in trace:
        if e['action'] == 'LINK':
            if len(e['candidates']) == 1:
                anchor_index += 1
        elif e['action'] == 'DISAMBIGUATE':
            entity = e['choice']['entity']
            connections[str(anchor_index)] = next(c.get('observed_two_edge_connections', [])
                for c in e['cards'] if c['entity'] == entity)
            anchor_index += 1
    if anchor_index != len(inputs['anchors']):
        raise ValueError('Captured anchor count mismatch')
    old = runtime.base.rank_catalog(packet['record']['question'], runtime.base.program_catalog(
        schema_event['roots'], schema_event['schema'], anchor_index, connections,
        packet['record']['question']), limit=20)
    a = {signature(c) for c in old}; b = {signature(c) for c in captured}
    obligation = inventory['obligation']
    def count(catalog):
        return None if obligation is None else sum(compatible(obligation, c) for c in catalog)
    return {'id': packet['record']['id'], 'seed': packet['seed'], 'status': 'availability_only',
            'obligation': obligation, 'schema_only_count': len(old), 'expanded_count': len(captured),
            'schema_only_rule_compatible': count(old), 'expanded_rule_compatible': count(captured),
            'added_programs': [json.loads(s) for s in sorted(b - a)],
            'removed_programs': [json.loads(s) for s in sorted(a - b)],
            'catalogs_structurally_equal': a == b,
            'answer_correctness': 'not evaluated; no answers/annotations accessed'}


def check(folder):
    folder = Path(folder)
    if sha(folder / 'manifest.json') != (folder / 'manifest.sha256').read_text().strip():
        raise ValueError('Study manifest changed')
    plan = json.loads((folder / 'manifest.json').read_text())
    if sha(folder / 'inputs.jsonl') != plan['input_sha256']:
        raise ValueError('Study inputs changed')
    for name, expected in json.loads((folder / 'checksums.json').read_text()).items():
        if (folder / name).resolve().is_relative_to(folder.resolve()) is False or sha(folder / name) != expected:
            raise ValueError('Study checksum changed: ' + name)
    for name, expected in plan['source_hashes'].items():
        if sha(folder / name) != expected:
            raise ValueError('Frozen source changed')
    if sha(Path(runtime.base.__file__)) != runtime.PARENT_SHA256:
        raise ValueError('Preserved catalog source changed')
    if sha(Path(runtime.__file__)) != plan['source_hashes']['obligation-runtime-source.py']:
        raise ValueError('Rule/catalog version differs from this diagnostic')
    packets = [committed(p)['value'] for p in sorted((folder / 'journal').glob('*-prefix.json'))]
    expected = {(qid, seed) for qid in plan['question_ids'] for seed in plan['seeds']}
    actual = [(p['record']['id'], p['seed']) for p in packets]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError('Incomplete or duplicate captured states')
    return {'scope': __doc__.strip(), 'study_manifest_sha256': sha(folder / 'manifest.json'),
            'runtime_sha256': sha(Path(runtime.__file__)), 'prefixes': len(packets),
            'rows': [contrast(p) for p in packets], 'inference_requests': 0,
            'limits': ['Rule compatibility is not answer correctness or complete semantic scope',
                       'No old-catalog program execution, model reselection or answer scoring',
                       'Removing catalog expansion changes model prompts and can change the first choice',
                       'Matched catalog-versus-guard experiments need separate pre-catalog capture and prospective freezing']}


def main():
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('folder', type=Path)
    args = parser.parse_args();print(json.dumps(check(args.folder), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()

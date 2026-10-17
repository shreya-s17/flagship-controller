"""Independent nested-state/request/usage ledger audit; no semantic certification."""
import argparse
import hashlib
import json
from pathlib import Path
from .common_state_audit import committed, digest

POLICIES = {'repair-C0G0', 'repair-C0G1', 'repair-C1G0', 'repair-C1G1', 'fixed-C1G1'}


def graph_state(events):
    return [{k: e.get(k) for k in ('query', 'rows', 'snapshot', 'sql_state')} for e in events]


def provider_state(events, seed):
    result = []
    for e in events:
        if e['seed'] != seed or e['payload']['options']['seed'] != seed or digest(e['payload']) != e['payload_sha256']:
            raise ValueError('Actual provider request seed/hash mismatch')
        result.append({k: e.get(k) for k in ('payload_sha256', 'response', 'error_type')})
    return result


def prefix_matches(short, full, seed):
    a, b = short['internal'], full['internal']
    ga, gb = graph_state(a['graph_audit']), graph_state(b['graph_audit'])
    pa, pb = provider_state(a['provider_audit'], seed), provider_state(b['provider_audit'], seed)
    if gb[:len(ga)] != ga or pb[:len(pa)] != pa:
        raise ValueError('Nested prefix state/request mismatch')


def check(folder):
    folder = Path(folder);data = (folder / 'manifest.json').read_bytes()
    if hashlib.sha256(data).hexdigest() != (folder / 'manifest.sha256').read_text().strip():
        raise ValueError('Manifest changed')
    plan = json.loads(data)
    if set(plan['policies']) != POLICIES:
        raise ValueError('Unexpected condition set')
    for name, expected in plan['source_hashes'].items():
        if Path(name).name != name or hashlib.sha256((folder / name).read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen source changed')
    if hashlib.sha256((folder / 'inputs.jsonl').read_bytes()).hexdigest() != plan['input_sha256']:
        raise ValueError('Frozen inputs changed')
    raw = (folder / 'predictions.jsonl').read_bytes();rows = list(map(json.loads, raw.decode().splitlines()))
    completion = json.loads((folder / 'completion.json').read_text())
    expected_order = [(i['id'], i['seed'], i['variant']) for i in plan['order']]
    expected_set = {(qid, seed, p) for qid in plan['question_ids'] for seed in plan['seeds'] for p in POLICIES}
    if len(expected_order) != len(expected_set) or set(expected_order) != expected_set:
        raise ValueError('Incomplete/duplicate frozen conditions')
    if [(r['id'], r['seed'], r['variant']) for r in rows] != expected_order:
        raise ValueError('Prediction order/denominator mismatch')
    if completion['completed'] != len(rows) or completion['predictions_sha256'] != hashlib.sha256(raw).hexdigest():
        raise ValueError('Completion mismatch')
    checked = [];common_packets = {};catalog_packets = {}
    for index, row in enumerate(rows):
        seed, qid, policy = row['seed'], row['id'], row['variant']
        mode = 'on' if 'C1' in policy else 'off'
        key = str(seed) + '-' + hashlib.sha256(qid.encode()).hexdigest()[:16]
        common_env = committed(folder / 'journal' / (key + '-common.json'));common = common_env['value']
        if common_env['item'] != {'id': qid, 'seed': seed, 'stage': 'pre_catalog'}:
            raise ValueError('Common journal identity mismatch')
        common_packets[key] = common
        cat_env = committed(folder / 'journal' / (key + '-catalog-' + mode + '.json'));packet = cat_env['value']
        if cat_env['item'] != {'id': qid, 'seed': seed, 'catalog_mode': mode, 'common_sha256': digest(common)}:
            raise ValueError('Catalog journal/common link mismatch')
        if packet['common_sha256'] != digest(common) or packet['catalog_mode'] != mode:
            raise ValueError('Catalog capture/common mismatch')
        catalog_packets[(key, mode)] = packet
        envelope = committed(folder / 'journal' / f'policy-{index:04d}.json')
        if envelope['item'] != {**plan['order'][index], 'prefix_sha256': digest(packet)}:
            raise ValueError('Policy journal/catalog link mismatch')
        if any(row.get(k) != v for k, v in envelope['value'].items()):
            raise ValueError('Prediction/committed outcome mismatch')
        if common['internal_ready'] and packet['internal_ready']:
            prefix_matches(common, packet, seed)
        if row.get('policy_continuation_executed'):
            if row['catalog_mode'] != mode or row['obligation_guard_enabled'] != ('G1' in policy):
                raise ValueError('Executed intervention mismatch')
            state = row['shared_state'];prefix = packet['internal']
            if state['common_pre_catalog_sha256'] != digest(common) or state['catalog_packet_sha256'] != digest(packet):
                raise ValueError('Outcome/nested prefix identity mismatch')
            prefix_matches(packet, {'internal': {'graph_audit': row['graph_audit'], 'provider_audit': row['provider_audit']}}, seed)
            expected_plan = next(e['program'] for e in packet['capture_result']['trace'] if e['action'] == 'PLAN')
            actual_plan = next(e['program'] for e in row['trace'] if e['action'] == 'PLAN')
            if expected_plan != actual_plan:
                raise ValueError('Catalog-specific first PLAN changed')
            cost = row['cost']
            if cost['charged_common_prefix_seconds'] != prefix['seconds']:
                raise ValueError('Prefix time charge mismatch')
            if state['replayed_graph_calls'] != len(prefix['graph_audit']) or state['replayed_model_calls'] != len(prefix['provider_audit']):
                raise ValueError('Replay count mismatch')
            physical = sum(not e.get('replayed', False) for e in row['provider_audit'])
            if cost['physical_new_model_calls'] != physical:
                raise ValueError('Physical provider count mismatch')
            if cost['physical_new_graph_calls'] != cost['graph_calls'] - len(prefix['graph_audit']):
                raise ValueError('Physical graph count mismatch')
        checked.append({'id': qid, 'seed': seed, 'variant': policy, 'terminal': row['terminal'],
                        'catalog_mode': mode, 'status': 'nested-state/request ledger PASS'})
    return {'scope': __doc__.strip(), 'rows_checked': len(checked), 'common_captures': len(common_packets),
            'catalog_captures': len(catalog_packets), 'rows': checked,
            'semantic_review': 'not provided by this audit', 'publication_ready': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('folder', type=Path)
    args = parser.parse_args();print(json.dumps(check(args.folder), indent=2))


if __name__ == '__main__':
    main()

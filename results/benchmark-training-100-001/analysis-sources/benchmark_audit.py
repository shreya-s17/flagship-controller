"""Offline full-denominator nested/baseline ledger checks, never semantics."""
import hashlib
import json
from pathlib import Path
from .common_state_audit import committed, digest
from .factorial_audit import prefix_matches, provider_state


def check(folder):
    folder = Path(folder);raw = (folder / 'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != (folder / 'manifest.sha256').read_text().strip():raise ValueError('Manifest changed')
    plan = json.loads(raw)
    expected={(qid,seed,policy) for qid in plan['question_ids'] for seed in (17,29,43) for policy in
        ('repair-C0G0','repair-C0G1','repair-C1G0','repair-C1G1','fixed-C1G1','tog-declared-json')}
    order=[(r['id'],r['seed'],r['variant']) for r in plan['order']]
    if len(plan['question_ids'])!=100 or len(order)!=1800 or set(order)!=expected:raise ValueError('Invalid full study definition')
    for name, expected in plan['source_hashes'].items():
        if Path(name).name != name or hashlib.sha256((folder / name).read_bytes()).hexdigest() != expected:raise ValueError('Frozen inference source changed')
    if hashlib.sha256((folder / 'inputs.jsonl').read_bytes()).hexdigest() != plan['input_sha256']:raise ValueError('Inputs changed')
    raw = (folder / 'predictions.jsonl').read_bytes();rows = list(map(json.loads, raw.decode().splitlines()))
    done = json.loads((folder / 'completion.json').read_text())
    if done['completed'] != len(rows) or done['predictions_sha256'] != hashlib.sha256(raw).hexdigest():raise ValueError('Completion changed')
    if [(r['id'],r['seed'],r['variant']) for r in rows] != [(r['id'],r['seed'],r['variant']) for r in plan['order']]:raise ValueError('Incomplete/reordered denominator')
    if len(rows) != 1800:raise ValueError('Full1800 planned outcomes required')
    for index, row in enumerate(rows):
        qid, seed, policy = row['id'], row['seed'], row['variant'];key = str(seed) + '-' + hashlib.sha256(qid.encode()).hexdigest()[:16]
        common_env = committed(folder / 'journal' / (key + '-common.json'));common = common_env['value']
        if common_env['item'] != {'id':qid,'seed':seed,'stage':'pre_catalog'}:raise ValueError('Common identity mismatch')
        is_baseline = policy == 'tog-declared-json'
        if is_baseline:
            packet = common;kind = 'common_link';prefix = common['link']
        else:
            mode = 'on' if 'C1' in policy else 'off'
            catalog_env = committed(folder / 'journal' / (key + '-catalog-' + mode + '.json'));packet = catalog_env['value']
            if catalog_env['item'] != {'id':qid,'seed':seed,'catalog_mode':mode,'common_sha256':digest(common)}:raise ValueError('Catalog/common mismatch')
            if packet['common_sha256'] != digest(common) or packet['catalog_mode'] != mode:raise ValueError('Captured catalog mismatch')
            kind = 'catalog';prefix = packet['internal']
            if common['internal_ready'] and packet['internal_ready']:prefix_matches(common, packet, seed)
        envelope = committed(folder / 'journal' / f'policy-{index:04d}.json')
        if envelope['item'] != {**plan['order'][index],'packet_kind':kind,'prefix_sha256':digest(packet)}:raise ValueError('Outcome capture mismatch')
        if any(row.get(k) != v for k,v in envelope['value'].items()):raise ValueError('Prediction differs from committed outcome')
        if row.get('policy_continuation_executed'):
            if prefix is None:raise ValueError('Continuation without captured state')
            prefix_matches({'internal':prefix},{'internal':{'graph_audit':row['graph_audit'],'provider_audit':row['provider_audit']}},seed)
            state = row['shared_state'];cost = row['cost']
            if state['replayed_graph_calls'] != len(prefix['graph_audit']) or state['replayed_model_calls'] != len(prefix['provider_audit']):raise ValueError('Replay count mismatch')
            if cost['charged_common_prefix_seconds'] != prefix['seconds']:raise ValueError('Prefix charge mismatch')
            if cost['physical_new_model_calls'] != sum(not e.get('replayed',False) for e in row['provider_audit']):raise ValueError('Physical model count mismatch')
            if cost['physical_new_graph_calls'] != cost['graph_calls']-len(prefix['graph_audit']):raise ValueError('Physical graph count mismatch')
            if is_baseline:
                if state['prefix_kind'] != 'link' or row['shared_link_packet_sha256'] != digest(common['link']):raise ValueError('Baseline linking mismatch')
            else:
                if row['catalog_mode'] != mode or row['obligation_guard_enabled'] != ('G1' in policy):raise ValueError('Intervention mismatch')
                if state['catalog_packet_sha256'] != digest(packet):raise ValueError('First-choice packet mismatch')
                first = next(e['program'] for e in packet['capture_result']['trace'] if e['action']=='PLAN')
                if next(e['program'] for e in row['trace'] if e['action']=='PLAN') != first:raise ValueError('First choice differs')
        elif row['reason'].startswith('interrupted') and not row['cost'].get('cost_is_lower_bound'):
            raise ValueError('Interrupted usage incorrectly treated as complete')
    return {'rows_checked':len(rows),'question_seed_units':300,'scope':'Source/input/order/nested-link/request/usage integrity; no semantic certification'}

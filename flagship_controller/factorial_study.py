"""Nested-capture factorial development harness; at most ten pilot strings.

Reserved/test execution is refused. Reuses the preserved durable journal and
failure accounting; no evaluation annotations or scorer are imported.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import platform
import random
import re
import tempfile
import urllib.request
from . import factorial_runtime as runtime, obligation_study as old

MODULES = {**old.MODULES, 'factorial-runtime-source.py': Path(runtime.__file__),
           'factorial-study-source.py': Path(__file__)}


def freeze(inputs, output, snapshot, seeds=(17,)):
    output = Path(output)
    if output.exists():
        raise ValueError('New output directory required')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        staged = Path(temporary) / 'study'
        plan = old.freeze(inputs, staged, snapshot, seeds)
        rng = random.Random(113); order = []
        for seed in seeds:
            for qid in plan['question_ids']:
                policies = list(runtime.POLICIES);rng.shuffle(policies)
                order.extend({'id': qid, 'seed': seed, 'variant': policy} for policy in policies)
        plan.update(kind=runtime.VERSION, status='Frozen small factorial development plan; not executed or publication-ready',
            order=order, policies=list(runtime.POLICIES), catalog_modes=['off', 'on'],
            source_hashes={name: old.sha(path.read_bytes()) for name, path in MODULES.items()},
            shared_state='One pre-catalog capture per question/seed; one catalog/firstPLAN per catalog condition; guards share only their own catalog firstPLAN. Captured work charged per condition, physical requests separate.',
            baseline='No external baseline in this engineering comparison; prior local ToG evidence retained',
            ablations={'catalog':'C0 preserves schema catalog/ranking with no primary membership acquisition; C1 expands using observed containment. Compiler and all other guards remain.',
                       'guard':'G0 bypasses closed obligation checks and pruning only; G1 enables them. Same-model/type/witness/resource checks retained.'},
            closed_obligations='Preserved v2 declared incomplete rules, including unmodeled downtown qualifier',
            contrasts=['repair-C1G1 minus fixed-C1G1: revision under the same catalog/closed checks',
                       'C1G1 minus C1G0: closed guard/pruning conditional on expanded catalog',
                       '2x2 catalog/guard contrasts and interaction: exploratory development only'],
            catalog_change='Explicit intervention; distinct catalog prompts/first choices captured separately',
            analysis='Full frozen denominator; originals scored only offline; handwritten cases unscored. No independent recovery rate, significance, generalization or novel-method claim. Prior inspected development inputs are not held-out.',
            live_execution_completed=False)
        old.write_json(staged / 'manifest.json', plan)
        (staged / 'manifest.sha256').write_text(old.sha((staged / 'manifest.json').read_bytes()) + '\n')
        for name, path in MODULES.items():
            (staged / name).write_bytes(path.read_bytes())
        staged.rename(output)
    return plan


def validate(folder):
    folder = Path(folder)
    if old.sha((folder / 'manifest.json').read_bytes()) != (folder / 'manifest.sha256').read_text().strip():
        raise ValueError('Frozen manifest changed')
    plan = json.loads((folder / 'manifest.json').read_text())
    if plan.get('kind') != runtime.VERSION or plan.get('policies') != list(runtime.POLICIES):
        raise ValueError('Unexpected factorial definition')
    if set(plan['source_hashes']) != set(MODULES):
        raise ValueError('Unexpected frozen source set')
    for name, path in MODULES.items():
        if old.sha(path.read_bytes()) != plan['source_hashes'][name] or old.sha((folder / name).read_bytes()) != plan['source_hashes'][name]:
            raise ValueError('Frozen source mismatch: ' + name)
    if old.sha((folder / 'inputs.jsonl').read_bytes()) != plan['input_sha256']:
        raise ValueError('Frozen input mismatch')
    records = [json.loads(line) for line in (folder / 'inputs.jsonl').read_text().splitlines()]
    if not 1 <= len(records) <= 10 or any(set(r) != {'id', 'question', 'split'} or r['split'] != 'pilot' for r in records):
        raise ValueError('Only 1–10 question-only pilot records')
    if [r['id'] for r in records] != plan['question_ids'] or len({r['id'] for r in records}) != len(records):
        raise ValueError('Input order/identity mismatch')
    actual = [(item['id'], item['seed'], item['variant']) for item in plan['order']]
    expected = {(r['id'], seed, policy) for r in records for seed in plan['seeds'] for policy in runtime.POLICIES}
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError('Incomplete/duplicate factorial order')
    return plan, {r['id']: r for r in records}


def verify_environment(folder, plan, model_url):
    if os.environ.get('PYTHONHASHSEED') != '17':
        raise ValueError('Set PYTHONHASHSEED=17 before starting Python')
    root = model_url.rsplit('/api/', 1)[0]
    with urllib.request.urlopen(root + '/api/tags', timeout=10) as response:
        tags = json.load(response)
    matches = [m for m in tags['models'] if m['name'] in (plan['model'], plan['model'] + ':latest')]
    if len(matches) != 1 or matches[0]['digest'] != plan['model_digest_required']:
        raise ValueError('Model digest mismatch')
    show = old.webqsp_runtime.post_json(root + '/api/show', {'model': plan['model']}, 10)
    if not re.search(r'num_ctx\s+4096\b', show.get('parameters', '')) or not re.search(r'num_thread\s+4\b', show.get('parameters', '')):
        raise ValueError('Model configuration mismatch')
    verification = {'model': matches[0], 'parameters': show['parameters'],
                    'template_sha256': old.sha(show.get('template', '').encode()),
                    'python': platform.python_version(), 'platform': platform.platform()}
    path = folder / 'model-verification.json'
    if path.exists():
        if json.loads(path.read_text()) != verification:
            raise ValueError('Execution environment changed across resume')
    else:
        old.write_json(path, verification)


def interrupted_packet(record, seed, model, snapshot, progress, prefix=None, **metadata):
    result = old.interrupted_result(record, 'interrupted_factorial_capture_unknown_usage', prefix, progress)
    return {'record': record, 'seed': seed, 'model': model, 'snapshot': snapshot,
            'internal': {'cost': copy.deepcopy(result['cost']), 'seconds': result['cost']['elapsed_seconds']},
            'internal_ready': False, 'capture_result': result, 'provider_audit': [],
            'physical_stage': {'seconds': None, 'model_attempts': None, 'graph_calls': None}, **metadata}


def execute(folder, endpoint, model_url):
    folder = Path(folder);plan, records = validate(folder)
    if (folder / 'completion.json').exists():
        done = json.loads((folder / 'completion.json').read_text())
        if done['completed'] != len(plan['order']) or done['predictions_sha256'] != old.sha((folder / 'predictions.jsonl').read_bytes()):
            raise ValueError('Completed output mismatch')
        print('Already complete; no requests repeated', flush=True)
        return
    verify_environment(folder, plan, model_url)
    jobs = folder / 'journal';jobs.mkdir(exist_ok=True);results = []
    def observer(path):
        def log(event):
            with path.open('a') as stream:
                stream.write(json.dumps(event) + '\n');stream.flush();os.fsync(stream.fileno())
        return log
    for index, item in enumerate(plan['order']):
        record = records[item['id']];seed = item['seed']
        key = str(seed) + '-' + old.sha(item['id'].encode())[:16]
        common_progress = jobs / (key + '-common.progress.jsonl')
        common = old.journal(jobs, key + '-common', {'id': record['id'], 'seed': seed, 'stage': 'pre_catalog'},
            lambda: runtime.capture_common(record, endpoint, model_url, plan['model'], plan['snapshot'], seed, observer(common_progress)),
            lambda: interrupted_packet(record, seed, plan['model'], plan['snapshot'], common_progress, stage='pre_catalog'))
        mode, _, _ = runtime.settings(item['variant'])
        catalog_progress = jobs / (key + '-catalog-' + mode + '.progress.jsonl')
        packet = old.journal(jobs, key + '-catalog-' + mode,
            {'id': record['id'], 'seed': seed, 'catalog_mode': mode, 'common_sha256': runtime.parent.digest(common)},
            lambda: runtime.capture_catalog(common, mode, endpoint, model_url, observer(catalog_progress)),
            lambda: interrupted_packet(record, seed, plan['model'], plan['snapshot'], catalog_progress, common['internal'],
                                       stage='catalog', catalog_mode=mode, common_sha256=runtime.parent.digest(common)))
        policy_key = f'policy-{index:04d}';progress = jobs / (policy_key + '.progress.jsonl')
        def interrupted_policy():
            result = old.interrupted_result(record, 'interrupted_factorial_policy_unknown_usage', packet['internal'], progress)
            result.update(variant=item['variant'], shared_state={'interrupted': True, 'seed': seed})
            return result
        result = old.journal(jobs, policy_key, {**item, 'prefix_sha256': runtime.parent.digest(packet)},
            lambda: runtime.continue_policy(packet, item['variant'], endpoint, model_url, observer(progress)), interrupted_policy)
        result.update(variant=item['variant'], seed=seed);results.append(result)
        temporary = folder / 'predictions.jsonl.tmp'
        with temporary.open('w') as stream:
            for row in results:
                stream.write(json.dumps(row) + '\n')
            stream.flush();os.fsync(stream.fileno())
        temporary.replace(folder / 'predictions.jsonl')
        print(record['id'], seed, item['variant'], result['terminal'], result['reason'], flush=True)
    old.write_json(folder / 'completion.json', {'completed': len(results),
        'predictions_sha256': old.sha((folder / 'predictions.jsonl').read_bytes()),
        'question_seed_common_prefixes': len(records) * len(plan['seeds']),
        'catalog_prefixes': 2 * len(records) * len(plan['seeds']), 'utc': old.utc(),
        'scope': 'Completed bounded factorial development, including retained failures; not independent semantic review'})


def main():
    parser = argparse.ArgumentParser(description=__doc__);sub = parser.add_subparsers(dest='command', required=True)
    make = sub.add_parser('freeze');make.add_argument('--inputs', type=Path, required=True)
    make.add_argument('--output', type=Path, required=True);make.add_argument('--snapshot', required=True)
    make.add_argument('--seeds', type=int, nargs='+', default=[17])
    run = sub.add_parser('execute');run.add_argument('folder', type=Path)
    run.add_argument('--endpoint', default='http://127.0.0.1:8891/sparql')
    run.add_argument('--model-url', default='http://127.0.0.1:11434/api/chat')
    args = parser.parse_args()
    if args.command == 'freeze':
        print(json.dumps(freeze(args.inputs, args.output, args.snapshot, args.seeds), indent=2))
    else:
        execute(args.folder, args.endpoint, args.model_url)


if __name__ == '__main__':
    main()

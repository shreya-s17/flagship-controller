"""Prospective 100-question training-reservation feasibility study.

Exact reserved bytes only, all six conditions and three seeds. No test input or
gold annotations; later human reviews never change already collected inference.
"""
import argparse
import json
import os
from pathlib import Path
import random
import tempfile
import time
from . import benchmark_runtime as runtime, factorial_study as helpers
from . import factorial_runtime, obligation_runtime, obligation_study, study_runtime
from . import common_linker, semantic_runtime, structured_runtime, webqsp_runtime
from . import tog_adapter, compact_tog_adapter, indexed_tog_adapter, declared_json_tog_adapter

RESERVED_SHA256 = 'caca1ad180cba7e67614a59232da6ea36eac32e9534ad3d6c10ec42a03045dc2'
SEEDS = (17, 29, 43)
MODULES = {Path(m.__file__).name: Path(m.__file__) for m in
    (runtime, helpers, factorial_runtime, obligation_runtime, obligation_study, study_runtime,
     common_linker, semantic_runtime, structured_runtime, webqsp_runtime, tog_adapter,
     compact_tog_adapter, indexed_tog_adapter, declared_json_tog_adapter)}
MODULES[Path(__file__).name] = Path(__file__)
ANALYSIS = ('benchmark_analysis.py','benchmark_audit.py','official_score.py','factorial_audit.py','common_state_audit.py')
sha = helpers.old.sha
write_json = helpers.old.write_json


def records_from(data):
    if sha(data) != RESERVED_SHA256:
        raise ValueError('Only the exact pre-reserved100 input bytes are permitted')
    records = [json.loads(x) for x in data.decode().splitlines()]
    if len(records) != 100 or len({r['id'] for r in records}) != 100 or any(
        set(r) != {'id', 'question', 'split'} or r['split'] != 'train_remaining'
        or not isinstance(r['question'], str) or not r['question'].strip() for r in records):
        raise ValueError('100 distinct question-only train_remaining records required')
    return records


def schedule(records):
    rng = random.Random(113);order = []
    for seed in SEEDS:
        for record in records:
            policies = list(runtime.POLICIES);rng.shuffle(policies)
            order.extend({'id': record['id'], 'seed': seed, 'variant': p} for p in policies)
    return order


def freeze(inputs, output, upstream, snapshot):
    inputs, output = Path(inputs), Path(output)
    if output.exists():
        raise ValueError('New study directory required')
    data = inputs.read_bytes();records = records_from(data)
    if not snapshot:
        raise ValueError('Snapshot identity required')
    tog_adapter.load_upstream(upstream)
    review_ids = sorted((r['id'] for r in records), key=lambda qid: sha(('semantic-review-v1:' + qid).encode()))[:20]
    plan = {'kind': runtime.VERSION, 'status': 'Frozen training-reservation feasibility; not final test or submission readiness',
        'created_utc': helpers.old.utc(), 'input_sha256': RESERVED_SHA256,
        'question_ids': [r['id'] for r in records], 'seeds': list(SEEDS),
        'policies': list(runtime.POLICIES), 'order': schedule(records),
        'source_hashes': {name: sha(path.read_bytes()) for name, path in MODULES.items()},
        'analysis_source_hashes': {name: sha(Path(__file__).with_name(name).read_bytes()) for name in ANALYSIS},
        'snapshot': snapshot, 'model': 'flagship-qwen2.5-7b-q4km',
        'model_digest_required': helpers.old.MODEL_DIGEST,
        'upstream_commit': tog_adapter.UPSTREAM_COMMIT, 'upstream_hashes': tog_adapter.HASHES,
        'budgets': {'model_calls': 10, 'returned_usage_tokens': 16000, 'graph_calls': 80, 'rows': 100,
                    'seconds_admission': 600, 'model_timeout': 120, 'graph_timeout': 30, 'max_observed_prompt_tokens': 3000},
        'inference': {'temperature': 0, 'context': 4096, 'threads': 4, 'max_output_tokens': 512,
                      'python_hash_seed_required': '17', 'schedule_seed': 113},
        'shared_state': 'Common parse/link/root/schema; each catalog captures a separate first PLAN; baseline shares linking only.',
        'primary_analysis': {'contrast': ['repair-C1G1', 'fixed-C1G1'], 'metric': 'official-semantics macro answer-set F1',
            'unit': 'average three seeds within question, then pair all100 questions',
            'interval': '10000 paired question-cluster bootstrap resamples; analysis seed113; descriptive feasibility uncertainty',
            'no_minimum_effect_or_power_claim': True},
        'secondary_analysis': ['exact-set accuracy, coverage and benchmark mismatch among answers',
            '2x2 catalog/closed-guard contrasts conditional on selected roots/schema',
            'local declared-JSON ToG adaptation projected-ID F1; native semantic validity separately reviewed',
            'returned tokens/model/graph/physical attempts; replay time constructed, unequal realized costs'],
        'semantic_review': {'status': 'pending, not a precondition for objective benchmark collection',
            'question_ids': review_ids, 'seed': 17, 'all_six_conditions': True, 'records_expected': 120,
            'selection': '20 question IDs by fixed salted SHA256 before inference; no outcomes/labels',
            'independent_reviewers_planned': 2, 'author_review_counted_separately': True,
            'unknowns_retained': True, 'no_semantic_accuracy_claim_before_actual_judgments': True},
        'failure_accounting': 'Full1800 planned denominator; retain linking/grammar/timeout/budget/serialization failures; no selective retry or replacement. Interrupted admitted work has lower-bound/unknown costs. Integrity mismatch halts.',
        'serialization': 'raw RDF lexical strings / Freebase IDs; date mismatch remains; no gold-driven normalization',
        'baseline': 'Pinned local Qwen/ToG adaptation, not original-paper reproduction; no controller catalog supplied.',
        'protocol_revision': 'Objective benchmark collection can precede human review; semantic/STOP/recovery claims and submission remain gated. This revision is frozen before reserved inference.',
        'analysis_after_completion_only': True, 'tuning_after_first_reserved_request': False,
        'official_test_execution': False, 'independent_reviews_completed_at_freeze': 0,
        'early_late_stop_rates': None, 'certified_recovery_rate': None}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        staged = Path(temporary) / 'study';staged.mkdir()
        (staged / 'inputs.jsonl').write_bytes(data)
        write_json(staged / 'manifest.json', plan)
        (staged / 'manifest.sha256').write_text(sha((staged / 'manifest.json').read_bytes()) + '\n')
        for name, path in MODULES.items():
            (staged / name).write_bytes(path.read_bytes())
        (staged / 'analysis-sources').mkdir()
        for name in ANALYSIS:
            (staged / 'analysis-sources' / name).write_bytes(Path(__file__).with_name(name).read_bytes())
        staged.rename(output)
    return plan


def validate(folder):
    folder = Path(folder);data = (folder / 'manifest.json').read_bytes()
    if sha(data) != (folder / 'manifest.sha256').read_text().strip():
        raise ValueError('Frozen manifest changed')
    plan = json.loads(data);records = records_from((folder / 'inputs.jsonl').read_bytes())
    if plan.get('kind') != runtime.VERSION or plan['question_ids'] != [r['id'] for r in records] or plan['seeds'] != list(SEEDS):
        raise ValueError('Study definition changed')
    if plan['input_sha256'] != RESERVED_SHA256 or plan['policies'] != list(runtime.POLICIES) or plan['order'] != schedule(records):
        raise ValueError('Frozen full denominator/order changed')
    if set(plan['source_hashes']) != set(MODULES):
        raise ValueError('Unexpected source set')
    for name, path in MODULES.items():
        if sha(path.read_bytes()) != plan['source_hashes'][name] or sha((folder / name).read_bytes()) != plan['source_hashes'][name]:
            raise ValueError('Frozen source mismatch: ' + name)
    return plan, {r['id']: r for r in records}


def execute(folder, upstream, endpoint, model_url, max_hours=8):
    if not 0 < max_hours <= 24:
        raise ValueError('Execution window must be in (0,24] hours; resume the same study afterward')
    folder = Path(folder);plan, records = validate(folder)
    if (folder / 'completion.json').exists():
        done = json.loads((folder / 'completion.json').read_text())
        if done['completed'] != len(plan['order']) or done['predictions_sha256'] != sha((folder / 'predictions.jsonl').read_bytes()):
            raise ValueError('Completed output mismatch')
        print('Already complete; no requests repeated', flush=True);return
    tog_adapter.load_upstream(upstream)
    if tog_adapter.HASHES != plan['upstream_hashes']:
        raise ValueError('Pinned baseline source changed')
    helpers.verify_environment(folder, plan, model_url)
    start = time.monotonic();jobs = folder / 'journal';jobs.mkdir(exist_ok=True);results = []
    def observer(path):
        def log(event):
            with path.open('a') as stream:
                stream.write(json.dumps(event) + '\n');stream.flush();os.fsync(stream.fileno())
        return log
    for index, item in enumerate(plan['order']):
        policy_key = f'policy-{index:04d}'
        if index % len(runtime.POLICIES) == 0 and time.monotonic() - start >= max_hours * 3600 and not (jobs / (policy_key + '.json')).exists():
            write_json(folder / 'progress.json', {'status': 'paused at complete question/seed boundary',
                'completed': len(results), 'planned': len(plan['order']), 'next_index': index,
                'predictions_sha256': sha((folder / 'predictions.jsonl').read_bytes()), 'utc': helpers.old.utc()})
            print('Execution window complete; resume unchanged frozen study', flush=True);return
        record = records[item['id']];seed = item['seed'];key = str(seed) + '-' + sha(record['id'].encode())[:16]
        common_progress = jobs / (key + '-common.progress.jsonl')
        common = helpers.old.journal(jobs, key + '-common', {'id': record['id'], 'seed': seed, 'stage': 'pre_catalog'},
            lambda: runtime.capture(record, endpoint, model_url, plan['model'], plan['snapshot'], seed, observer(common_progress)),
            lambda: runtime.interrupted_capture(record, seed, plan['model'], plan['snapshot'], common_progress))
        baseline = item['variant'] == 'tog-declared-json'
        if baseline:
            packet = common;prefix = common['link'];packet_kind = 'common_link'
        else:
            mode, _, _ = factorial_runtime.settings(item['variant'])
            catalog_progress = jobs / (key + '-catalog-' + mode + '.progress.jsonl')
            packet = helpers.old.journal(jobs, key + '-catalog-' + mode,
                {'id': record['id'], 'seed': seed, 'catalog_mode': mode, 'common_sha256': study_runtime.digest(common)},
                lambda: factorial_runtime.capture_catalog(common, mode, endpoint, model_url, observer(catalog_progress)),
                lambda: helpers.interrupted_packet(record, seed, plan['model'], plan['snapshot'], catalog_progress,
                    common['internal'], stage='catalog', catalog_mode=mode, common_sha256=study_runtime.digest(common)))
            prefix = packet['internal'];packet_kind = 'catalog'
        progress = jobs / (policy_key + '.progress.jsonl')
        def interrupted_policy():
            result = helpers.old.interrupted_result(record, 'interrupted_benchmark_policy_unknown_usage', prefix, progress)
            result.update(variant=item['variant'], shared_state={'interrupted': True, 'seed': seed});return result
        operation = (lambda: runtime.baseline(packet, endpoint, model_url, upstream, observer(progress))) if baseline else (
            lambda: factorial_runtime.continue_policy(packet, item['variant'], endpoint, model_url, observer(progress)))
        result = helpers.old.journal(jobs, policy_key, {**item, 'packet_kind': packet_kind, 'prefix_sha256': study_runtime.digest(packet)}, operation, interrupted_policy)
        result.update(variant=item['variant'], seed=seed);results.append(result)
        temporary = folder / 'predictions.jsonl.tmp'
        with temporary.open('w') as stream:
            for row in results:
                stream.write(json.dumps(row) + '\n')
            stream.flush();os.fsync(stream.fileno())
        temporary.replace(folder / 'predictions.jsonl')
        write_json(folder / 'progress.json', {'status': 'running', 'completed': len(results), 'planned': len(plan['order']),
            'last': item, 'predictions_sha256': sha((folder / 'predictions.jsonl').read_bytes()), 'utc': helpers.old.utc()})
        print(record['id'], seed, item['variant'], result['terminal'], result['reason'], flush=True)
    write_json(folder / 'completion.json', {'completed': len(results), 'predictions_sha256': sha((folder / 'predictions.jsonl').read_bytes()),
        'question_seed_common_prefixes': len(records) * len(SEEDS), 'catalog_prefixes': 2 * len(records) * len(SEEDS),
        'utc': helpers.old.utc(), 'scope': 'Completed training-reservation feasibility; semantic judgments and final testing remain separate'})


def main():
    parser = argparse.ArgumentParser(description=__doc__);sub = parser.add_subparsers(dest='command', required=True)
    make = sub.add_parser('freeze');make.add_argument('--inputs', type=Path, required=True)
    make.add_argument('--output', type=Path, required=True);make.add_argument('--snapshot', required=True)
    make.add_argument('--upstream', type=Path, required=True)
    run = sub.add_parser('execute');run.add_argument('folder', type=Path);run.add_argument('--upstream', type=Path, required=True)
    run.add_argument('--endpoint', default='http://127.0.0.1:8891/sparql');run.add_argument('--model-url', default='http://127.0.0.1:11434/api/chat')
    run.add_argument('--max-hours', type=float, default=8)
    args = parser.parse_args()
    if args.command == 'freeze':
        print(json.dumps(freeze(args.inputs, args.output, args.upstream, args.snapshot), indent=2))
    else:
        execute(args.folder, args.upstream, args.endpoint, args.model_url, args.max_hours)


if __name__ == '__main__':
    main()

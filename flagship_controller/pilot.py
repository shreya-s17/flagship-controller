"""Reproducible exploratory synthetic pilot and paired cluster summaries."""
import argparse
import csv
import gzip
import json
import platform
import random
import statistics
import subprocess
from pathlib import Path
from .engine import Config, LocalEvidence, digest, execute
from .synthetic import suite, CONDITIONS
from .evaluate import score, summarize


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def bootstrap_difference(rows, left, right, field='grounded', repetitions=10000):
    groups = {}
    for r in rows:
        groups.setdefault(r['base_id'], {}).setdefault(r['variant'], []).append(r[field])
    deltas = [statistics.mean(v[left])-statistics.mean(v[right]) for v in groups.values()]
    rng = random.Random(17)
    samples = sorted(statistics.mean(rng.choices(deltas, k=len(deltas))) for _ in range(repetitions))
    return {'left': left, 'right': right, 'metric': field, 'clusters': len(deltas),
            'mean_difference': statistics.mean(deltas), 'ci95': [samples[int(.025*repetitions)],
            samples[min(repetitions-1, int(.975*repetitions))]],
            'scope': 'generator-family exploratory interval; not benchmark inference'}


def run_pilot(output, count=50):
    output.mkdir(parents=True, exist_ok=True)
    records = suite(count)
    configs = {f'{bits:04b}': Config(*[x == '1' for x in f'{bits:04b}']) for bits in range(16)}
    manifest = {'protocol': 'synthetic-v2-exploratory', 'date': '2026-10-10',
                'dataset': 'generated typed path graphs', 'base_questions': count,
                'conditions': list(CONDITIONS), 'generator_seed': 17,
                'stochastic_controller': False, 'model': None, 'runtime': platform.python_version(),
                'configs': {k: c.__dict__ for k, c in configs.items()},
                'dataset_sha256': digest(records), 'code_commit': subprocess.check_output(
                    ['git', 'rev-parse', 'HEAD'], text=True).strip(),
                'source_hashes': {str(p): digest(p.read_text()) for p in Path('flagship_controller').glob('*.py')},
                'gold_separation': 'factual_answers and condition labels passed only to evaluator',
                'deviations': ['synthetic graphs instead of WebQSP/CWQ',
                               '32 symbolic checks instead of protocol-v1 cap of 4',
                               'no LLM/NLI, tokens=0, no calibrated probability or human annotation',
                               'query supplies relations/types; no natural-language parsing or linking',
                               'synthetic variants are component controls, not paper reproductions'],
                'primary_hypotheses': {'H1': 'NOT TESTED: no token-bearing model calls',
                                       'H2': 'NOT TESTED: no benchmark/fixed-retry reproduction',
                                       'H3': 'NOT TESTED: no calibrated hybrid/NLI gate'}}
    write_json(output / 'manifest.json', manifest)
    with gzip.open(output / 'dataset.jsonl.gz', 'wt', encoding='utf8') as data:
        for record in records: data.write(json.dumps(record, sort_keys=True) + '\n')
    rows, examples = [], {}
    with gzip.open(output / 'trajectories.jsonl.gz', 'wt', encoding='utf8') as traces:
        for record in records:
            for variant, config in configs.items():
                result = execute(record['query'], LocalEvidence(record['graph']), config)
                row = score(record, result); row['variant'] = variant
                rows.append(row)
                traces.write(json.dumps({'run_id': record['id'] + ':' + variant,
                             'question_id': record['id'], 'variant': variant, 'result': result}) + '\n')
                # Representative trajectories selected by explicit outcome rule, not success-only.
                key = (record['condition'] + ':' + variant)
                if variant in ('1111', '0010', '0110', '1101') and key not in examples:
                    examples[key] = {'row': row, 'result': result}
    with (output / 'metrics.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summaries = {v: summarize([r for r in rows if r['variant'] == v]) for v in configs}
    stratified = {v: {c: summarize([r for r in rows if r['variant'] == v and r['condition'] == c])
                    for c in CONDITIONS} for v in configs}
    write_json(output / 'summary.json', summaries)
    write_json(output / 'conditions.json', stratified)
    write_json(output / 'representative-trajectories.json', examples)
    comparisons = [bootstrap_difference(rows, '1111', v, field) for v in
                   ('0111', '1011', '1101', '1110', '0010')
                   for field in ('grounded', 'expansions')]
    write_json(output / 'paired-comparisons.json', comparisons)
    lines = ['# Synthetic pilot results', '', '**Exploratory development experiment only.** '
             'These results do not establish WebQSP/CWQ performance, novelty or H1–H3.', '',
             f'{count} generated base questions × 7 paired conditions × 16 A/V/R/S variants '
             f'= {len(rows)} executions. No model calls; token use is zero.', '',
             '| A/V/R/S | Grounded / all | Answers / all | Unsupported / answers | Mean expansions | Mean checks |',
             '|---|---:|---:|---:|---:|---:|']
    for v in ('1111', '0111', '1011', '1101', '1110', '0000', '0010', '0110'):
        s = summaries[v]
        def fraction(k):
            m=s[k]; return f"{m['numerator']}/{m['denominator']}" if m['denominator'] else 'NA (0/0)'
        lines.append(f"| {v} | {fraction('grounded_yield')} | {fraction('coverage')} | "
                     f"{fraction('unsupported_answer_rate')} | {s['mean_expansions']:.3f} | {s['mean_checks']:.3f} |")
    lines += ['', 'Bits denote acquisition, verifier feedback, branch recovery and adaptive STOP. '
              '0010 is an unchecked fixed-order search control; 0110 adds symbolic verification '
              'but keeps fixed ID order and terminal search. Neither is CoR/CCoR.', '',
              '## Full controller by condition', '',
              '| Condition | Grounded / all | Answered / all | Supported abstentions / supported |',
              '|---|---:|---:|---:|']
    for c in CONDITIONS:
        s = stratified['1111'][c]
        vals = [s[k] for k in ('grounded_yield','coverage','supported_abstention')]
        lines.append('| '+c+' | '+' | '.join(f"{m['numerator']}/{m['denominator']}" if m['denominator'] else 'NA (0/0)' for m in vals)+' |')
    lines += ['', '## Interpretation and limits', '',
              'The generator includes invalid-type branches, so a symbolic type checker is favored by '
              'construction. Branch ordering and short budgets can still cause avoidable abstention. '
              'No observed gain here should be generalized to natural questions or imperfect verifiers.', '',
              'Noise is on unrelated relations and is therefore filtered by the known query plan. '
              'This is a negative control, not a realistic noisy-retrieval robustness claim. '
              'Alias corruption is an incorrect starting entity, not an implemented ambiguity resolver.', '',
              'Recovery rates conditional on each method’s first failure are diagnostic only: '
              'the initial failed states differ. A matched frozen-state recovery study remains required. '
              'Supported abstention indicates accessible proof exists; budget-constrained continuation '
              'audits are not implemented, so premature-STOP counts remain NA.', '',
              'Checks, graph calls and wall time include controller overhead; wall time is a small '
              'local-Python diagnostic without network/model latency. No GPU saving or token hypothesis is tested.', '',
              'Independent oracle enumerates complete witnesses within the finite envelope. It does not '
              'import the deployed checker. All-query factual correctness is distinct from accessible support.', '',
              'Artifacts: manifest, complete compressed dataset/trajectories, per-run CSV, condition tables, '
              '10,000-replicate paired base-cluster intervals and representative successes/failures.']
    (output / 'report.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines[:18]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('results/synthetic-v2'))
    parser.add_argument('--count', type=int, default=50)
    args = parser.parse_args()
    if args.count < 1: parser.error('count must be positive')
    run_pilot(args.output, args.count)

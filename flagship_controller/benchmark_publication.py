"""Completion-gated paper tables from frozen analysis; no submission or inference.

Packaging code finalized during collection. The frozen five-source analysis,
primary endpoint and prospective human-review sample remain unchanged.
"""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
from . import benchmark_analysis, benchmark_review_pack


def number(value):
    return 'NA' if value is None else f'{value:.6f}'


def csv_text(rows):
    stream = io.StringIO();writer = csv.DictWriter(stream, fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    return stream.getvalue()


def summarize(plan, rows, analysis):
    if analysis['executions'] != 1800 or analysis['questions'] != 100:
        raise ValueError('Full frozen denominator required')
    tables, failures, submitted = [], [], []
    for policy in plan['policies']:
        method = analysis['methods'][policy];scored = list(method['official_scores_by_seed'].values())
        if len(scored) != 3 or method['submitted_outcomes'] != 300 or any(s['submitted'] != 100 for s in scored):
            raise ValueError('Every policy needs all100 questions at all three seeds')
        valid_sets = [{r['id'] for r in s['rows'] if r['scorable']} for s in scored]
        if valid_sets[1:] != valid_sets[:-1]:raise ValueError('Scorable questions differ by seed')
        pooled = [r for s in scored for r in s['rows'] if r['scorable']]
        tables.append({'policy': policy, 'submitted_outcomes': 300, 'scorable_question_units': len(valid_sets[0]),
                       'excluded_question_units': 100-len(valid_sets[0]), 'mean_f1_across_questions': method['mean_question_f1'],
                       'exact_set_rate': sum(r['exact_f1'] for r in pooled)/len(pooled) if pooled else None,
                       'coverage_scorable': sum(r['answered'] for r in pooled)/len(pooled) if pooled else None,
                       'charged_returned_tokens': method['charged_usage']['model_tokens'],
                       'charged_model_calls': method['charged_usage']['model_calls'],
                       'charged_graph_calls': method['charged_usage']['graph_calls'],
                       'usage_complete': method['complete_usage'], 'unknown_usage_records': method['unknown_usage_records']})
        actual = [r for r in rows if r['variant'] == policy]
        for (terminal, reason), count in sorted(Counter((r['terminal'], r['reason']) for r in actual).items()):
            failures.append({'policy': policy, 'terminal': terminal, 'reason': reason, 'outcomes': count})
        for row in actual:
            submitted.append({'question_id': row['id'], 'seed': row['seed'], 'policy': policy,
                              'terminal': row['terminal'], 'reason': row['reason'], 'answers': json.dumps(row['answers'])})
    primary = analysis['primary_repair_minus_fixed']
    report = ['# Reserved-training feasibility results — completed collection', '',
              '**This is a training-reservation feasibility report, not final-test performance or submission approval.**', '',
              'All100 question IDs ×3 seeds ×6 conditions are retained:1800 submitted outcomes. Official scorable exclusions are shown separately. Seeds are averaged within question for the primary paired contrast, not treated as independent question samples.', '',
              '| Condition | Submitted | Scorable questions | Macro F1 | Exact-set rate | Coverage | Usage complete |',
              '|---|---:|---:|---:|---:|---:|---|']
    for row in tables:
        report.append('| ' + row['policy'] + ' | 300 | ' + str(row['scorable_question_units']) + ' | ' +
                      number(row['mean_f1_across_questions']) + ' | ' + number(row['exact_set_rate']) + ' | ' +
                      number(row['coverage_scorable']) + ' | ' + str(row['usage_complete']) + ' |')
    report += ['', 'Primary repair-C1G1 minus fixed-C1G1 F1 difference: ' + number(primary['mean_difference']) +
               '; paired question bootstrap95% interval [' + number(primary['lower_95']) + ', ' + number(primary['upper_95']) +
               '], ' + str(primary['question_units']) + ' scorable question units,10000 resamples, seed113.', '',
               'The interval is descriptive feasibility uncertainty, not a power guarantee or cross-dataset claim. Reused training text, related question families, pretraining overlap, narrow grammar and unresolved Freebase snapshot equivalence limit inference.', '',
               'Cost totals are charged policy work, including replayed prefixes; methods can have unequal realized usage. Incomplete usage totals are lower bounds. Constructed elapsed time is not fresh end-to-end method efficiency, and shared cached stages are not independent physical executions.', '',
               'The local ToG condition is an adaptation under the same local model, not reproduction of original-paper scores. Projected-ID scoring does not certify native semantic correctness. The separate preselected semantic and projection review packets are unannotated.', '',
               'Independent semantic review, early/late STOP and certified recovery rates remain NA. GPT development judgments are supplementary and are not counted as independent evaluation. No calibrated reliability, novel learned control or publication acceptance is established.', '',
               'Files: analysis.json (unaltered frozen analysis result), table.csv, outcomes.csv (all1800 submitted), terminal-reasons.csv, checksums.json and review/ (blank masked handoffs plus separately retained owner key). No author identities, license selection or manuscript submission are performed by this command.', '']
    return tables, failures, submitted, '\n'.join(report)


def finalize(folder, gold, output):
    folder, gold, output = Path(folder), Path(gold), Path(output)
    if output.exists():raise ValueError('Refuse existing finalization output')
    # Reject incomplete collection before touching annotations or producing tables.
    plan, rows, source_sha, ledger = benchmark_review_pack.completed(folder)
    analysis = benchmark_analysis.analyze(folder, gold)
    tables, failures, submitted, report = summarize(plan, rows, analysis)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        staged = Path(temp) / 'report';staged.mkdir()
        (staged / 'analysis.json').write_text(json.dumps(analysis, indent=2) + '\n')
        (staged / 'table.csv').write_text(csv_text(tables))
        (staged / 'terminal-reasons.csv').write_text(csv_text(failures))
        (staged / 'outcomes.csv').write_text(csv_text(submitted))
        (staged / 'report.md').write_text(report)
        review = benchmark_review_pack.prepare(folder, staged / 'review')
        receipt = {'source_predictions_sha256': source_sha, 'source_manifest_sha256': hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest(),
                   'evaluation_annotation_file_sha256': hashlib.sha256(gold.read_bytes()).hexdigest(), 'ledger': ledger,
                   'complete_outcomes':1800, 'questions':100, 'review_records':review['semantic_records'],
                   'independent_reviewers_completed':0, 'official_test_executed':False, 'submission_ready':False,
                   'scope':'Completion-gated reproducible tables; human/snapshot/claim/final-submission gates remain open'}
        (staged/'provenance.json').write_text(json.dumps(receipt,indent=2)+'\n')
        files = {str(p.relative_to(staged)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(staged.rglob('*')) if p.is_file()}
        (staged/'checksums.json').write_text(json.dumps(files,indent=2)+'\n')
        staged.rename(output)
    return receipt


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('study',type=Path);p.add_argument('gold',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();print(json.dumps(finalize(a.study,a.gold,a.output),indent=2))

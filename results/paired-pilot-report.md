# Fixed versus repair: completed exploratory comparison

16 October 2026. Runtime `typed-catalog-repair-v11`. **No repair advantage demonstrated; no submission-ready result.** Ten additional training-pilot questions, distinct from the five used for development, were selected by existing intake order before execution. All selected questions and abstentions are retained. The official test set was not run.

## Original independent executions

[Prospectively frozen plan](paired-pilot-001/plan.json), [compressed raw evidence](../artifacts/live-evidence-2026-10-16/manifest.json), [offline analysis](paired-pilot-001/analysis.json). Completed 15 October, 11:04:59 UTC.

| Control | Exact / 10 | Macro F1 | Answered / 10 | Observed tokens | Model calls | Graph calls | Sum question seconds |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fixed, one program | 4 | 0.4000 | 6 | 21,056 | 34 | 63 | 690.53 |
| Repair, up to two | 3 | 0.3000 | 5 | 22,329 | 35 | 61 | 690.09 |

Question-paired mean F1 difference (repair minus fixed) is −0.10; descriptive 95% percentile bootstrap interval [−0.30, 0.00], 10,000 resamples of ten question units, seed17. This tiny sample does not support population inference. The sole exact-score difference is Eli Whitney: fixed answered exactly, repair failed mention parsing before a program existed. Earlier states are therefore not identical despite common temperature/seed/configuration. First-program equality alone does not prove identical prefixes; a pair of missing plans also compares equal. Timing mixes cache and inference effects; do not claim efficiency from these totals.

## Identical-prefix diagnostic

[Follow-up frozen plan](paired-pilot-002-shared-prefix/plan.json), [equivalence checks](paired-pilot-002-shared-prefix/equivalence-check.json), [compressed predictions](../artifacts/live-evidence-2026-10-16/manifest.json), [analysis](paired-pilot-002-shared-prefix/analysis.json).

Before reading gold outcomes for the original comparison, a follow-up was frozen to reuse every replayable fixed prefix. All ten qualified; no selection by accuracy. Frozen source/model/configuration checks apply. Fixed replay reproduces all ten original terminals, answers, witnesses and resource counts without a physical network request. Repair receives the exact same recorded graph observations and model outputs until continuation. This is a mechanism diagnostic on the SAME ten questions, not ten more independent observations or external preregistration.

| Control | Exact / 10 | Macro F1 | Answered / 10 | Charged tokens | Charged model calls | Charged graph calls |
|---|---:|---:|---:|---:|---:|---:|
| Original fixed prefixes | 4 | 0.4000 | 6 | 21,056 | 34 | 63 |
| Same-prefix bounded repair | 4 | 0.4000 | 6 | 24,527 | 38 | 65 |

Repair adds 3,471 observed tokens (+16.48%), four model calls and two graph calls, with zero additional exact answers and zero exact answers following a rejected first program. This is evidence against benefit of this rule on these cases, not proof that all repair methods fail. All per-question F1 deltas are zero, so the degenerate bootstrap [0,0] reflects this sample only. Prefix charges are accounting constructions; replay time plus original fixed time is NOT fresh end-to-end latency and must not enter an efficiency claim.

## Answer and failure audit

| Question | Fixed outcome | Interpretation |
|---|---|---|
| Musical Annie | Entity not found | Linking failure; not proof no answer exists. |
| Leonardo da Vinci death location | Exact | `people.deceased_person.place_of_death`. |
| Mexico currency | Exact | `location.country.currency_used`. |
| Chicago downtown sights | Answered, no gold overlap | Chosen bibliographic identity path returns Chicago rather than attractions. Semantic gate false acceptance. |
| GEICO insurance types | Answered, no gold overlap | Advertising-character inverse relation returns characters rather than insurance products. Semantic gate false acceptance. |
| Eli Whitney inventions | Exact in fixed and shared-prefix repair | Independent repair run failed earlier mention parsing; not a repair-caused answer regression. |
| Alice Paul birthplace | Entity not found | Linking failure. |
| Yale mascot | Exact | Inverse school-mascot relation. |
| Iran political system | Semantic rejection in both controls | Wrong administrative-children candidate; second attempt does not recover an exact answer. |
| Paul Revere parents | Semantic rejection in both controls | Wrong prominent-type candidate; second attempt does not recover an exact answer. |

The exact cases and errors are inspected after prediction, offline. No evaluator annotation enters the controller. Valid witnessed triples do not establish full question meaning or complete answer scope. Recorded-row witness consistency passes for all 11 answered original records and 12 shared-prefix records. Post-run constant-triple requery found all nine unique accepted triples present in each study (zero missing or unknown); audit files are retained in each folder. Neither check is independent semantic adjudication.

## Scientific decision

Retain fixed control. REVISE repair/verifier design; NO-GO for a repair-benefit, calibrated reliability, token-saving or novel-controller claim. Current STOP rates remain not identifiable without independently labeled budget-feasible continuations. External baseline reproduction and snapshot equivalence remain unresolved. See [publication gates](../evaluation/publication-readiness.md).

## Reproduce offline

From repository root, prepare protected labels from the official WebQSP archive using the README intake command, then:

```sh
python3 scripts/restore_live_evidence.py
python3 scripts/summarize_paired_study.py results/paired-pilot-001 benchmark-data/webqsp/evaluation-only.jsonl
python3 scripts/summarize_paired_study.py results/paired-pilot-002-shared-prefix benchmark-data/webqsp/evaluation-only.jsonl
python3 -m flagship_controller.witness_audit results/paired-pilot-001/predictions.jsonl
python3 -m flagship_controller.witness_audit results/paired-pilot-002-shared-prefix/predictions.jsonl
python3 scripts/verify_structured_artifacts.py
```

Live shared-prefix execution is a separate diagnostic. Freeze to a fresh directory with `python3 -m flagship_controller.shared_prefix_study freeze ORIGINAL NEW`, then execute NEW against the private services. Use the frozen wrapper/runtime/transport and matching model digest. All files are immutable once executed; do not overwrite prior evidence. Historical source copies preserve exact runtime behavior. Offline analysis code is versioned separately from frozen policy code.

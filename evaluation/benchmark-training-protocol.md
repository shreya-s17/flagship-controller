# Prospective reserved-training feasibility benchmark

17 October 2026. Separately implemented after the30-outcome development comparison. This protocol and executable source/analysis freeze precede the first reserved input request. It changes the earlier review ordering: objective benchmark collection may proceed while human review is pending. No author review is relabeled independent, no semantic validity rate is invented and official test remains excluded.

## Cohort and source freeze

Use all100 exact reserved v2 records, input SHA256 `caca1ad180cba7e67614a59232da6ea36eac32e9534ad3d6c10ec42a03045dc2`. Keep `split: train_remaining`; do not rename records to bypass old pilot limits. The new `benchmark_study.py` accepts only these exact bytes and distinct100 question IDs; the original ten-case development harnesses remain unchanged. Selection predated outcomes; textual overlap screening does not prove absence of semantic/pretraining overlap.

[Frozen plan](../results/benchmark-training-100-001/manifest.json) binds15 inference modules, five offline analysis sources, model digest, graph snapshot identifier, upstream source hashes, exact order and all1800 outcomes. Seeds17,29,43 are averaged within question. Scheduling seed113 randomizes all six conditions inside each question/seed. The full plan is fixed even if execution uses multiple windows. There is no removal/replacement of difficult cases, outcome-dependent tuning, selective timeout retry or optional stopping for a favorable result.

## Conditions and information sharing

Five preserved nested factorial conditions are fixed-C1G1 and repair-C0G0/C0G1/C1G0/C1G1. C1 adds graph-observed containment catalog candidates; G1 enables declared closed-obligation checking/pruning. C0/G0 remove only those respective interventions. Structural, type, witness, resource and final same-model checks remain.

The sixth condition is the pinned declared-JSON local ToG adaptation. It is an adaptation to Qwen, question-only linking, indexed pruning and explicit answer declaration, not reproduction of original-paper scores. It receives no controller catalog. One captured state shares parse/link/root/schema; each catalog then captures its own first PLAN, and guard arms share only that mode-specific choice. The baseline replays linking only. Actual provider-payload/query equality is enforced. A separately retained known Whitney development probe must pass operational replay before the first reserved request; a legitimate baseline budget failure is retained rather than treated as a reason to retune on reserved outcomes.

Maximum per-condition admission remains10 model calls,16,000 returned usage tokens,80 graph calls,100 rows/query,600s admission and120s/30s request timeouts, under the existing Qwen digest/context4096/thread4/temperature0 configuration. These are admission limits, not exact hard billing/time caps. Raw RDF lexical values/IDs remain unchanged. Every prefix is charged to its condition; actual physical attempts are separate. Interrupted admitted work becomes explicit unknown-cost/lower-bound failure without retry; integrity mismatch halts.

## Prospective analysis

Primary metric is official-semantics macro answer-set F1 for repair-C1G1 minus fixed-C1G1. First average the three seeds per question, then pair the same question units; report a10,000-resample paired question bootstrap with analysis seed113. Official question-quality admission/exclusions remain visible. Unsupported syntax/linking, truncation, budget and normalization failures stay submitted as abstentions. Do not count1800 executions as independent questions or assume100 questions is adequately powered.

Secondary analysis reports exact-set accuracy, coverage, benchmark mismatch among emitted answers, factorial catalog/guard contrasts and returned-token/model/graph/time vectors. Common maxima do not establish equal realized compute. Baseline projected-ID scoring is separate from native-answer semantic quality. Statistical uncertainty does not remove cohort selection, snapshot mismatch or pretraining contamination. No calibrated confidence, token-saving, learned general recovery, original-baseline reproduction or algorithmic-novelty claim is predeclared. STOP/recovery rates stay unavailable without independently accepted feasible-continuation evidence and explicit denominators.

Offline analysis runs only after the full frozen study completes. The runtime account cannot read benchmark annotations; the isolated15-module inference package contains no scorer. Offline analysis copies are separately archived and never imported by inference. Source modifications after the first reserved request invalidate a single frozen-study claim unless separately versioned and all earlier outcomes preserved.

## Human review

Before inference, select20 question IDs by salted SHA256 (`semantic-review-v1:`), seed17, all six conditions:120 prospective semantic-review records. Include failed, absent and answered outputs; do not choose only errors or successes after scoring. Mask policy/gold scores for two independent reviewers; baseline native output needs its additional projection-faithfulness dimension. Preserve unknowns and disagreements and adjudicate separately. Review may happen after objective output collection, but no independent semantic accuracy claim is made until actual judgments exist.

The owner’s offered [author review](author-review-guide.md) uses the existing development worksheet and stays separate. Blank forms and model critiques are not reviews. Human authorship/affiliations, license/redistribution decisions and owner review of the final submission package are still needed. The current public GitHub checkpoint approval does not constitute paper submission.

## Execution and runtime

The existing CPU server/local model is used; no purchase or paid API is introduced. The six-string factorial check took about27.7 minutes of physical stages for five controls, without the added baseline. Scaling to300 question/seed units plus baseline is expected to take days, with substantial uncertainty; it is not a guaranteed completion time or an efficiency result.

The launcher runs up to nine8-hour execution windows, resuming the exact same durable study between them. Each pause is at a complete question/seed boundary, so an in-flight group can extend the nominal window. It stops on an integrity/runtime-process failure or full completion. No scheduled notifications, reviewer contact, public test run or manuscript submission are created by the launcher. Partial progress remains incomplete, not a scored final sample.

```sh
python3 scripts/materialize_benchmark_study.py results/benchmark-training-100-001 NEW_RUNTIME
PYTHONPATH=NEW_RUNTIME PYTHONHASHSEED=17 python3 -m flagship_controller.benchmark_study execute /ABS/STUDY --upstream /ABS/PINNED/ToG --max-hours 8
# Completed study only, evaluation account:
python3 -m flagship_controller.benchmark_analysis results/benchmark-training-100-001 /EVALUATION_ONLY/annotations.jsonl
```

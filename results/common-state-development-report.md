# Shared-state controls and declared answers — 16 October 2026

**The experimental framework is implemented and exercised; the research is not paper-ready.** This checkpoint adds 10 standalone baseline executions and 30 common-state executions. All reuse the same five development question strings. The common-state subset contains only one official training original plus two handwritten controls. No reserved training or official test question has run.

## Implemented and completed

The new [development harness](../evaluation/common-state-runtime.md) captures one question/linking prefix per question and seed. Four internal controls also replay the same schema, catalog and first program choice; the baseline shares linking only. Every policy is charged the original usage/time. Actual new requests are recorded separately. Source, model, input, request and query checks precede continuation. A durable journal never reruns committed work; interrupted admitted jobs become explicit unknown-cost abstentions, while integrity errors halt execution.

Implemented controls: fixed, bounded repair, final-semantic-gate-off repair and rejection-reason-text-off repair. Gate-off retains compiler, witness, type and budget guards. Reason-text-off retains masking and join acquisition, so it is not complete feedback-off. Seeds propagate through structured/raw requests and baseline subsampling. Current live seeds are17 and29, with temperature0;43 is implemented/tested but not a third live replication. Repeated seeds are not independent questions. Serialization is frozen as raw IDs/literal lexical strings; the known date-zone mismatch is retained.

[Common-state-dev-002](common-state-dev-002/manifest.json) finished all 30 planned outcomes: five policies ×three existing question strings ×two seeds, with six common-prefix captures. There were no interrupted jobs or integrity mismatches. Earlier common-state-dev-001 is an unexecuted plan superseded before inference, with its source retained.

## Actual outcomes and limits

| Development input | Four internal controls, both seeds | Constrained baseline, both seeds |
|---|---|---|
| Mexico currency: the sole official original | Exact official set | Peso plus historical coin: F1 2/3, not exact |
| Inverse peso: handwritten, unscored | Mexico ID returned | Mexico ID returned; fixes the earlier converter's peso-ID error in this check |
| Fictional entity: handwritten, unscored | Shared entity-not-found abstention | Same common failure; no separate retry |

Declared JSON replaces free-text stop parsing and prose extraction with a combined stop/answer-index decision over observed named nodes, including earlier frontiers. Raw provider JSON is retained. This is a further local ToG prompting/decoding adaptation, not original-paper reproduction or a novel algorithm. Correct declared-index mapping does not make the declaration semantically correct: the historical coin remains an answer-scope error. [Raw outcomes, costs and offline scores](common-state-dev-002/development-score.json).

Official F1 is1.0 for each internal control and2/3 for the baseline on **one reused original**, averaged across two seeds. Repair minus fixed is0 there. No population interval, significance claim, native-answer accuracy claim or performance ranking is warranted. No live REPAIR_PLAN or reason-withholding event occurs in this chosen set; the reason-text branch is unit-tested but has no live effect contrast here. Four semantic-audit bypasses occur. These observations test mechanics, not recovery benefit or the safety/effectiveness of removing verification.

Charged costs across all six question/seed instances per policy:

| Policy | Model calls | Returned usage tokens | Graph calls |
|---|---:|---:|---:|
| Fixed |18|11,012|58|
| Repair |18|11,012|58|
| Final semantic gate off |14|7,148|58|
| Rejection reason text off |18|11,011|58|
| Declared-JSON baseline |16|6,788|56|

The physical experiment makes 36 model attempts:14 common captures plus22 continuations, and116 graph attempts. Returned usage is complete. Replayed prefixes explain the difference from summed per-policy charges; this is experimental reuse, not a demonstrated method-efficiency gain. Latency is original prefix plus replay/continuation time, not fresh end-to-end measurement. Cache/CPU conditions and different answer/search scopes remain limitations.

## Preserved unsuccessful baseline revision

[Baseline-dev-004](baseline-dev-004/manifest.json) freezes the preceding free-text FINAL_ANSWER contract. All10 outcomes remain. Its baseline emits no IDs on the three official originals: Mexico and Yale return `{Yes}` plus a JSON name array but omit the marker; GEICO exhausts the model-call budget. Zero projected-ID F1 does not mean the native responses lack answer knowledge. The inverse question reaches an unsupported direct-generation fallback, which is retained but never admitted. The no-match contract fails. [Failure record](baseline-dev-004/failure-diagnosis.json).

V4 structured cost:49 graph calls,17 model calls,10,650 tokens and545.91 summed question-seconds. Baseline:70 graph calls,32 model calls,19,639 tokens and692.03 seconds. Usage is complete. V4 remains unchanged; it is not retrospectively remapped or replaced by successful cases. Across baseline001–004 plus this common-state check,70 executions reuse five strings, not 70 independent examples.

## Verification and handoff

- **161 tests pass**, including a clean-checkout source check; final packaged verification is recorded in [validation metadata](../evaluation/baseline-checkpoint-validation.json). Tests cover seed/request propagation, identical catalog/first-choice replay, narrow ablations, unknown-cost interruption handling, committed-job reuse and tampered-state rejection.
- All18 offline constrained-baseline compatibility fixtures pass. These cover preserved retrieval/beam behavior and the new declared mapping; they are not model-quality evidence.
- The independent [common-state/request audit](common-state-dev-002/common-state-audit.json) passes all 30 rows: exact replayed provider/query observations, actual request seeds/hashes, identical internal catalogs/first choices, physical/charged counters, gate bypass/reason masking and declared-index fidelity. It does not assess semantics.
- Sixteen structured answers pass recorded witness checks. All two unique accepted triples are present on post-run graph requery. V4's four structured answers pass, with all five unique triples present. These are repeated graph facts, not independent semantic labels or proof of question completeness.
- The new [lossless evidence bundle](../artifacts/common-state-evidence-2026-10-16/manifest.json) includes 101 raw trace/journal files. Four bundles now restore 124 original files. Source snapshots restore into four baseline runtimes and both common-state plan versions. Prior bundles/results are unchanged.
- The unchanged 30-case structured pack and a new 26-case native pack are ready locally, both **unannotated; zero reviewers completed**. The 26-case pack covers all four baseline revisions plus six new baseline outcomes and supersedes the untouched15-case pack. Owner mappings/scores/extractor critiques are excluded from delivery. No reviewer was contacted. [Review workflow](../evaluation/independent-review-workflow.md).

## Remaining paper gates

Obtain two qualified independent reviewers; validate first-pass judgments and keep adjudication separate. Use harder inspected development cases to exercise actual failure/revision and assess candidate coverage. Then freeze an adequate100-question feasibility study, including an outcome-independent annotation plan, exact source/controls/seeds/budgets, raw representation and full-denominator analysis. The executable mechanics alone do not justify that larger inference run. The original ten-question negative fixed/repair results remain unchanged.

STOP/recovery rates, calibration, generalization and algorithmic novelty remain unestablished. The [release inventory](../evaluation/private-release-inventory.json) records the absent root license file, unconfirmed human contributions/authorship and unresolved public redistribution/attribution. No public release or submission occurred. The existing rental supports immediate work; no new purchase was made.

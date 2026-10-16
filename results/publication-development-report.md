# Publication-development checkpoint — 16 October 2026

**Restricted development work; not publication-ready results.** Original v11 pilot artifacts and scores are unchanged. This checkpoint implements and tests semantic targeting and recovery diagnosis while reserving later evaluation data.

## What the catalog audit establishes

The privileged offline diagnostic uses the ten completed v11 fixed runs and official training annotations after inference. It makes145 graph requests: eight recorded catalogs are fully evaluated; two cases never formed a catalog. Four catalogs contain an exact-answer set, and fixed control had already found those four. The remaining catalogs contain no exact answer set among their recorded candidates. This explains why resampling those catalogs cannot produce an exact answer there. It does not certify semantic correctness or a budget-feasible continuation rate.

Chicago, Iran and Paul Revere have the annotated first relation in the observed graph inventory but outside the lexical shortlist. GEICO retains it in the shortlist but does not choose it as a root. Alternative relations can legitimately produce exact sets, so matching one annotated chain is not a complete correctness test.

Nine official-query answer sets match annotations exactly. Annie yields `1976-08-10-08:00` with RDF datatype date versus annotation `1976-08-10`: a serialization discrepancy, not a missing result. The official scorer and archived answers are unchanged. A separate, explicit opt-in serialization adapter is implemented and unit-tested, but not applied to these runs or claimed equivalent in temporal meaning. Snapshot identity remains unverified.

[Audit summary](catalog-diagnostic-001/summary.json), [compressed full offline evidence](../artifacts/live-evidence-2026-10-16/manifest.json), [compatibility note](catalog-diagnostic-001/compatibility-notes.json).

## Development revisions and regressions

The same six original cases were purpose-selected: four previously working cases (Maggie Grace, Leonardo da Vinci, Mexico, Yale) and two semantic failures (Chicago, GEICO). Each revision also runs four hand-authored rephrasings. They have no independent labels and receive no benchmark score. These are inspected training cases, not a new representative/held-out sample.

| Revision / original six cases | Exact | Wrong answered | Abstained | Macro F1 | Observed tokens on these six |
|---|---:|---:|---:|---:|---:|
| v12, question requirement ledger |0 |1 |5 |0.0000 |4,777 |
| v13, constrained quotes + name casing + contract lexical ranking |3 |1 |2 |0.5000 |14,453 |

V12 returns ungrounded quote capitalization and cannot resolve a lowercase canonical name; these are retained failures. V13 fixes quotation/casing and returns exact Maggie Grace/Leonardo/Mexico answers, rejects the Chicago plan, but still accepts the wrong GEICO industries and rejects Yale after the parser calls it a musical. The four rephrased questions are behavioral checks only. Changing several components and independently parsing each question precludes a causal component-benefit claim. Latency/cache conditions are uncontrolled; token totals are observations, not efficiency claims.

The wrong GEICO answer in both revisions is Auto Repair/Collision Repair. It has the broadly requested business-industry type, but the path does not establish the intended insurance relation. A requirement ledger and type matching do not automatically solve semantics; the same model still false-accepts.

[Run001 scores and raw record](semantic-dev-001/development-score.json), [run002 scores and raw record](semantic-dev-002/development-score.json). Large raw files are restored losslessly by the README bundle command.

## Targeted follow-up

V14 adds observed schema/type metadata to root retrieval, prioritizing at most eight one-hop compatible roots within the top32. A model-inferred anchor type is a soft hint: after a failed typed lookup, a bounded canonical-key plus English-name match is allowed and logged. This can still resolve the wrong sense or displace a mediated path. No gold relation, answer or topic is supplied to inference.

Four inspected development cases—Maggie Grace, Mexico, GEICO and Yale—test the two diagnosed failures and two positive controls. V14 returns two exact answers (Maggie Grace/Mexico), the same wrong GEICO industries and a Yale linking abstention. Both observed direct industry relations reach the shortlist, but the model omits them when choosing roots. V15 extends soft-type fallback to bounded names/aliases when keys are absent; the single Yale smoke case still abstains on unresolved ambiguity. These outcomes remain in runs003/004. V16 guarantees inclusion of up to two observed direct type-compatible roots before schema/program generation, while retaining remaining model choices. The two-case v16 check matches both official answer sets: Mexico retains the peso result and GEICO returns Insurance Carriers / Fire, Marine, and Casualty Insurance. It uses21 graph calls,8 model calls and5,244 observed tokens across the two cases (254.29 summed question seconds). The GEICO model proposal again omits the correct roots; the deterministic observed-type inclusion retains them, and the selected direct query then returns the official set. This is a targeted regression success, not held-out improvement. [Run005 scores](semantic-dev-005/development-score.json). Yale remains an unresolved linking failure; no larger cohort has run. These smaller checks are reported on their own denominators, not mixed with the six-case table or represented as independent benchmark improvement.

## Data and independent-review preparation

The next cohort reserves100 train_remaining questions by deterministic question-group ordering, without answers or inference. Conservative .85 character-sequence similarity screening excludes two groups near development questions (Molly Ringwald and Buffy role questions) before any experiment. The first flagged reservation remains history. V2 has no flags under that screen; semantic paraphrases and pretraining contamination are not thereby ruled out. [Reserved v2 manifest](../evaluation/reserved-training-100-v2/manifest.json). The cohort is unexecuted and unscored; method/baseline/serialization/metric freeze is still required.

A tested generator prepares30 policy-masked semantic review forms from the original pilot and v13 development run. Explicit policy names, scores and model critiques are removed; observed witnesses/query rows and resolved anchor identities are retained. Masking is imperfect and questions are correlated. Forms remain **unannotated; zero independent reviewers completed**. The owner retains the mapping separately. Counterfactual STOP labels still require fuller state and feasible-continuation evidence; unknown defaults are not measured rates. [Pack status](../evaluation/review-pack-status.json).

## Reproduction and next gate

From a clean checkout, restore the compressed evidence using the README command, then run the unit suite and `scripts/verify_structured_artifacts.py`. The latter checks source/artifact hashes, complete run counts/order and reservation hashes. Prepare official labels separately with the existing intake command; runtime users must not read them. Offline development rescoring uses `scripts/summarize_semantic_development.py`, which refuses incomplete runs and separates scored originals from unscored rephrasings.

Named ToG adaptation is [specified](../evaluation/baseline-reproduction-plan.md), not implemented or reproduced. Next priorities: validate remaining linking and semantic failures, complete baseline sanity checks, collect independent review and freeze an adequate evaluation before running the reserved cohort. Current and historical negative results remain available. There are27 new development executions across the same six original questions and four rephrasings, not27 independent samples. The final targeted run passes recorded-row witness checks and all three unique accepted triples are present on independent graph requery. No novel-method, calibrated-reliability, matched-cost recovery or publication claim is established, and no extra service or hardware purchase was made.

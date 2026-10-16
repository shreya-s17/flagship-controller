# Baseline and linking development checkpoint — 16 October 2026

Latest follow-on: [indexed decoding, semantic projection failures and review preparation](indexed-baseline-development-report.md). Measurements below retain runs001–002 unchanged as history.

**Completed development work, not publication-ready results.** Twenty executions reuse three inspected official training questions (Mexico, GEICO, Yale) and two handwritten controls. There are five question strings, not20 independent examples. Neither the reserved100 training questions nor official test has run. Both frozen development runs finished; unsuccessful outcomes remain unchanged.

## What changed

- The common linker now permits a canonical key supported by an exact observed English alias as well as a name. The graph names Yale “University Yale”; its key and alias identify “Yale University.” This repairs the diagnosed lookup failure without a question-ID/entity-ID rule. Candidate ambiguity still goes through observed cards and a model decision; linking is not certified correct in general.
- A bounded ToG adaptation loads hash-verified upstream function bodies and prompts from a separate pinned checkout, preserving upstream pruning/scoring/stopping logic where documented. A second revision adds lexical top32 relation presentation and charged native-answer extraction. Every departure is in [the adaptation record](../evaluation/tog-adaptation.md). Neither version reproduces the paper's published model/input/resource setting.
- A tested [review-submission validator](../evaluation/independent-review-workflow.md) rejects blank/default forms, mismatched packs and missing judgments, and reports descriptive agreement/disagreements from actual submissions. The existing30-case pack and its blank submission template remain **unannotated; zero independent reviewers completed**. Metadata attestations cannot certify reviewer qualifications/independence.
- Targeted [CoG/CoR method and selected-code inspection](../paper/closest-method-comparison.md) confirms substantial overlap with guidance, guarded relation retention and failure-driven control. No algorithmic novelty is established. Their code is pinned and inspected, not executed or reproduced.

## Completed sanity checks and retained failures

These rows are operational development checks. ID projection, native text, answer-program scope and resource use differ between methods. They are **not a performance ranking** or evidence of population improvement.

| Run/configuration | Three reused official training questions | Handwritten inverse control | Handwritten no-match control |
|---|---|---|---|
|001, structured controller + common linker |3 exact; macro F1 1.0 |Answer returned, unscored |Abstain: entity not found |
|001, full-inventory ToG adaptation |All3 ID outputs abstain; projected F1 0.0 |Native answer text generated; strict converter abstains |Abstain: unsupported contract |
|002, same structured implementation |3 exact; macro F1 1.0 |Answer returned, unscored |Abstain: entity not found |
|002, compact/projected ToG adaptation |Mexico exact; GEICO/Yale abstain; projected F1 1/3 |Abstain: quote not verbatim |Abstain: entity not found |

Original annotations are read only by the separate offline scorer after execution. The handwritten checks have no independent benchmark labels. Small-sample intervals or significance claims are not inferred from these chosen debugging cases. [Run001 score/cost details](baseline-dev-001/development-score.json), [run002 details](baseline-dev-002/development-score.json).

V1 times out on Mexico while scoring the full relation inventory. Its failed request has no returned usage, so known token totals are lower bounds and usage is marked incomplete. GEICO/Yale/inverse responses conclude an answer in ordinary prose after `{Yes}`; the frozen braced-name converter rejects them. Their native text is retained. Zero projected IDs does not establish zero native-answer knowledge. [Failure diagnosis](baseline-dev-001/failure-diagnosis.json).

V2 presents at most32 lexically ranked relation names to reduce context and adds one charged constrained extraction request over final beam candidates. Mexico returns the exact observed peso ID. GEICO has no accepted explicit mapped answer. Yale later proposes a relation absent from the presented set and is rejected. The inverse control's extraction adds quotation marks absent from the native text, so the verbatim-quote guard rejects it. We do not strip those marks retrospectively or rerun until it passes. A future decoder should constrain quotations to observed text spans before another frozen sanity check. Compact retrieval can omit necessary relations and the same-model extractor can make semantic errors. An ID projection also does not score every additional assertion in the original prose; independent native-output review remains necessary.

Across all five inputs per configuration, run001 structured uses49 graph calls,17 model calls and10,650 observed tokens; its baseline uses41 graph calls,16 admitted model attempts and at least8,752 known tokens (one request's usage missing). Run002 structured uses49 graph calls,17 model calls and10,738 tokens; compact baseline uses55 graph calls,23 model calls and12,511 tokens, with complete returned usage. Summed question times are546.53/529.75s in001 and551.13/580.66s in002. Cache/CPU conditions are uncontrolled. Same maximum admission budgets are not equal realized costs, hard time/billing caps or an efficiency advantage.

## Verification and reproduction

108 unit tests pass locally and from a clean checkout after lossless restoration of21 raw trace files, including both isolated archived runtime packages, projection failure guards, common linking-prefix equivalence, review validation and tampered-source rejection. Thirteen offline upstream compatibility fixtures pass for each baseline configuration: prompt construction, score/stop parsing, beam order, inverse direction, unnamed mediators and empty-frontier behavior. These are compatibility checks, not model quality. Frozen manifests preserve source/input/model hashes and execution order; archives retain raw responses, observations, failures and completion records. [Run001 manifest](baseline-dev-001/manifest.json), [run002 manifest](baseline-dev-002/manifest.json).

Recorded-row witness checks cover the four structured-controller answers in each run. All five unique accepted structured triples are present on post-run graph requery in each run, with no missing/unknown result. Those checks confirm graph presence, not question meaning or world truth. No ToG semantic/witness certification is inferred from ID mapping. The runtime account cannot read the evaluation-only annotations, and graph/model services remain on loopback. [Access check](../evaluation/runtime-label-boundary-check.json).

Restore raw traces with `python3 scripts/restore_live_evidence.py`; the original bundle remains unchanged and the new [baseline bundle](../artifacts/baseline-evidence-2026-10-16/manifest.json) is lossless/hash-checked. `scripts/verify_structured_artifacts.py` verifies source, run order/counts and checksums. Use `scripts/materialize_baseline_runtime.py` to restore an exact old runtime into a new isolated directory, rather than execute an old manifest with changed source. [Commands and settings](../evaluation/tog-adaptation.md).

[Clean-checkout verification](../evaluation/baseline-checkpoint-validation.json) passes after final packaging. It covers artifact/source integrity and tests, not scientific validity.

## Next publication gates

1. Constrain extraction quotes to actual native spans, exercise ambiguous/negative cases, and resolve baseline prompt/selection failures without silently relaxing admission or dropping failures. Freeze the final answer representation, including date literals and the relationship between native text and projected-ID metrics.
2. Obtain two qualified independent reviewers and preserve first-pass judgments plus adjudication. STOP/recovery labels need full state and demonstrated feasible continuations; their rates remain NA.
3. Freeze an adequate study with common input/linking states, implemented controls/ablations, seeds, budgets, full-denominator failure accounting and metrics before running the reserved cohort. The [new-control overlap recheck](../evaluation/reservation-overlap-baseline-controls.json) has no flags at the existing .85 text threshold; it does not rule out semantic paraphrases or pretraining contamination.
4. Use the larger results to decide whether a substantive reliability/reproducibility paper is supported. Current repair benefit, calibration, generalization and algorithmic novelty remain unestablished. Public release, authorship/contributions, licenses and submission need final owner review of a concrete package.

The original negative fixed/repair studies remain unchanged. Repository remains private and unsubmitted. No new model subscription, API, GPU or storage purchase was made; immediate development can continue on the existing rental. Broader flagship/baseline/publication tasks remain open.

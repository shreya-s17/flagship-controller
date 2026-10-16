# Indexed baseline and review preparation — 16 October 2026

Latest follow-on: [completed common-state controls and constrained declarations](common-state-development-report.md). Earlier run003 outcomes below remain unchanged.

**Engineering checkpoint completed; larger evaluation and publication remain NO-GO.** Run003 finished all10 executions, reusing the same three official training questions and two handwritten controls. Across001–003 there are30 executions of five question strings, not30 independent examples. No reserved training or official test question has been executed.

## Changes and measured outcomes

The new local ToG adaptation selects relation indices from the actual lexical top32 presentation and extracts IDs only through observed full-name spans in the native response. This removes free-form relation-name and quote generation from those requests. All calls remain charged under the original limits. It changes upstream relation prompting/decoding and answer representation; it is not faithful published-model reproduction or a novel constrained-decoding method. [Exact frozen plan](baseline-dev-003/manifest.json), [departures](../evaluation/tog-adaptation.md).

| Reused development input | Structured controller with common linker | Indexed baseline: actual retained result |
|---|---|---|
| Mexico currency | Exact official answer set | Partial: peso plus a contextual historical coin; F1 2/3 |
| GEICO insurance | Exact official answer set | Abstain at the10-model-call limit |
| Yale mascot | Exact official answer set | Exact official answer set |
| Inverse peso question | Mexico returned; unscored | Native prose concludes Mexico, but ID converter wrongly emits the peso; unscored |
| Fictional entity | Entity-not-found abstention; unscored | Entity-not-found abstention; unscored |

Official answer-set macro F1 on the **three reused originals only** is1.0 for the structured controller and5/9≈.5556 for the projected baseline IDs. Baseline exact-set accuracy is1/3. These are selected debugging outcomes, not a method ranking, native-answer accuracy, held-out improvement or evidence for repair benefit. Handwritten controls receive no invented benchmark labels or scores. [Full score/cost record](baseline-dev-003/development-score.json), [developer failure diagnosis](baseline-dev-003/failure-diagnosis.json).

The important remaining failure is semantic: an actual name span can be context rather than an answer. On Mexico, the extractor selects the historical coin despite the native response recommending pesos for current transactions. On the inverse question, it selects a peso mention from context/question text while asserting that all conclusions are represented, although the final-beam candidates omit the native conclusion Mexico. Those same-model support/completeness flags are demonstrably insufficient in these cases. They are not independent semantic labels. Native responses, wrong IDs and scores are preserved; no retrospective repair or selective rerun replaces them.

Across all five inputs, structured execution uses49 graph calls,17 model calls,10,757 observed tokens and550.17 summed question-seconds. The baseline uses60 graph calls,26 model calls,14,738 tokens and594.61 seconds. Returned usage is complete for both. These sums reflect uncontrolled cache/CPU conditions and different search/answer scopes; equal maxima are not equal realized compute or an efficiency advantage.

## Verification and reproducibility

- **137 unit tests pass**, including clean-checkout tests, old-runtime restoration, guarded relation/span decoding, malformed/blank review rejection, review-delivery allowlisting and offline common-state replay. Final packaging verification is recorded in [validation metadata](../evaluation/baseline-checkpoint-validation.json).
- All16 offline indexed compatibility fixtures pass. These check parsers/transitions, inverse direction, unnamed mediators and empty-frontier behavior; they are not model-quality evidence. [Frozen v3 checks](baseline-dev-003/compatibility.json).
- A separate [request/span ledger audit](baseline-dev-003/indexed-decision-audit.json) verifies the five baseline records against returned requests, presentations, actual source spans and final beam IDs. It passes representation checks **while the semantic failures above remain**. It does not certify conclusions or completeness.
- Recorded-row witness checks cover four structured answers. All five unique accepted structured triples are present on post-run graph requery, with zero missing/unknown. This verifies graph presence, not question meaning. Baseline IDs receive no implied witness certification.
- An [offline shared-link state replay check](baseline-dev-003/shared-link-state-replay-check.json) reproduces the same recorded parse/link events and usage through both method paths on all five inputs, with zero new requests. The earlier run002 check is also retained. This tests a building block, not a shared-catalog/live-continuation study harness or fresh latency.
- The new [lossless bundle](../artifacts/indexed-baseline-evidence-2026-10-16/manifest.json) adds two raw trace files; restoration covers23 original files across three bundles. Earlier bundles and outcomes are unchanged. Run003 has23 checksummed files and isolated source snapshots.

Code inspection during the run found a small-score formatting edge case: upstream parses decimal digits/dots, while Python may print tiny weights with an exponent. Current source **v3.1** fixes decimal formatting and passes its unit test plus16 offline fixtures. Run003 used frozen **v3**, whose source remains unchanged and restorable. No live result is attributed to v3.1; execute it only under a new freeze. The semantic selection failures remain in current source.

## Independent review and next study

Prepared two separate local handoffs: the unchanged30-case structured review pack, and a15-case native-output addendum covering all three baseline revisions, including missing native responses. Both are **unannotated; zero reviewers completed**. Cases are repeated/correlated. The addendum reviews full native claims and projection faithfulness as well as the four semantic dimensions. An allowlisted export excludes owner mappings, scores and extractor critiques; archive/file hashes are recorded. No reviewer was contacted. [Workflow and brief](../evaluation/independent-review-workflow.md), [structured delivery manifest](../evaluation/review-delivery-manifest.json), [native addendum status](../evaluation/native-review-pack-status.json).

The [next-study design](../evaluation/next-study-design.md) specifies the100-question reservation, intended controls, common-state accounting, answer representation, seeds, denominators and analysis. It remains **preparation, not executable freeze**. New shared-catalog/live execution, narrow ablations, complete seed propagation, serialization and safe resume still require implementation. Existing30-case review does not label the new cohort; native review does not certify generalization. STOP/recovery rates remain NA without independently accepted, budget-feasible continuations.

Next: obtain two qualified independent reviewers, repair conclusion-versus-context projection on development without case-ID rules, and finish/test shared-state controls before freezing any larger study. Original negative fixed/repair findings remain unchanged. Novelty, calibration, generalization and publication readiness are unestablished. Existing rental supports immediate work; no new purchase was made. Repository remains private and unsubmitted.

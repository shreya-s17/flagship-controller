# Completion-gated analysis and reviewer handoff

18 October 2026. These packaging tools were finalized during benchmark collection. They do not change the frozen 15-module inference package, five-source primary analysis, 100 input records, budgets, seeds or prospectively selected review sample. They are not a new inference method or evidence of improved performance.

## What runs after collection

`benchmark_publication` first requires the completion marker and full 1,800-outcome ledger audit. It rejects missing, reordered or altered outcomes before reading the protected annotation file. The existing `benchmark_analysis` then verifies its original source hashes and computes the predeclared question-level scores and paired interval. No partial scores or favorable subset are reported.

The output directory contains:

| File | Purpose |
|---|---|
| `analysis.json` | Unaltered result returned by the frozen analysis |
| `table.csv` | Six conditions, full submitted/scorable/excluded denominators, F1, exact and coverage, charged costs and usage completeness |
| `outcomes.csv` | All 1,800 outcomes, including failures and abstentions |
| `terminal-reasons.csv` | Full terminal/reason counts by condition |
| `report.md` | Paper-facing table and primary interval, with scope and unavailable metrics stated |
| `provenance.json`, `checksums.json` | Source/annotation-file hashes, ledger receipt and generated-file hashes |
| `review/` | Blank masked reviewer handoffs, their manifests and a separate private owner key |

Charged totals include replayed prefixes. Unknown usage remains marked incomplete/lower-bound. Neither a common maximum budget nor constructed replay time establishes matched realized compute or fresh method efficiency. The analysis is training-reservation feasibility, not official-test performance. Independent semantic validity and STOP/recovery rates remain unavailable until appropriate real evidence exists.

Use a **private output directory outside the public repository**. It includes the owner key linking policy and source records. Share only the explicit reviewer ZIPs with reviewers, after the owner authorizes contact. The wrapper makes no external contact or manuscript submission.

```sh
python3 -m flagship_controller.benchmark_publication \
  /ABS/COMPLETED/STUDY /PROTECTED/evaluation-only.jsonl /PRIVATE/NEW_PUBLICATION_OUTPUT
```

An existing output directory is refused. Staging is atomic: a failed audit, score or handoff does not create a partial final directory. Original input, completion, journals and predictions are not edited.

## Prospective human-review sample

The original manifest selected 20 question IDs by salted SHA256 before inference. All six conditions at seed 17 produce **120 semantic records**, including absent answers and failed runs. The new pack generator enforces that exact selection and the complete study ledger. It does not select from errors, scores or apparently successful examples.

The semantic handoff uses the existing four dimensions: anchor identity, question/program meaning, answer scope and witness support. For native responses, witness support concerns all substantive native assertions, not merely emitted IDs. The additional **20-record projection handoff** asks only whether native conclusions are faithfully represented by projected IDs. It is assessed separately so that 100 internal conditions with no native projection cannot inflate agreement through shared not-applicable labels.

Policy labels, gold answers, scores, terminal reasons and model critique fields are withheld. Questions, observed names, programs, complete selected witnesses/query rows and native text remain available. Behavior may reveal the method, so masking is imperfect. Missing names or unrecorded context require unknown or a requested lookup, not a guessed identity. Native responses and graph strings are untrusted data, not reviewer instructions.

Forms require real reviewer metadata, reasons and self-reported independence. They start with blank reasons and a false attestation. Blank unknown fields are not annotations. The independent-review entry point rejects an explicit automated/author role even if its attestation is set to true. Qualifications and independence cannot be established by software alone.

```sh
python3 -m flagship_controller.benchmark_review_pack prepare /ABS/COMPLETED/STUDY /PRIVATE/NEW_REVIEW_PACK
python3 -m flagship_controller.benchmark_review_pack assess --kind semantic \
  --pack /PRIVATE/PACK/semantic/cases.jsonl --reviews /PRIVATE/reviewer1.json /PRIVATE/reviewer2.json
python3 -m flagship_controller.benchmark_review_pack assess --kind projection \
  --pack /PRIVATE/PACK/projection/cases.jsonl --reviews /PRIVATE/projection1.json /PRIVATE/projection2.json
```

Keep first-pass submissions, disagreements and adjudication separate. Agreement is descriptive, not truth or accuracy; repeated conditions are correlated. Human review results must not be fed back into this already executing frozen study. The completed GPT development review is a separate automated supplement and cannot substitute for these human submissions.

## Dependent server job

`scripts/await_benchmark_completion.py` is one bounded postprocessing job attached to the already authorized experiment. It makes no model/API requests and sends no notifications. It waits for the full completion marker, then invokes the pipeline once with the protected evaluation file. If inference stops without completion, an integrity check fails or the wait window expires, it records that state and does not score a partial study or retry failed inference. It never runs official test data, chooses a license, contacts reviewers or submits a paper.

The inference account still cannot read annotations. Postprocessing runs separately with evaluation access; the new modules are not installed into the inference package. Generated reports and reviewer packs remain private pending inspection and deliberate publication of appropriate files. A waiting job means tools are prepared, not that results exist.

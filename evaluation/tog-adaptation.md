# Executable local ToG adaptation

16 October 2026. Implementation and offline compatibility checks are complete. Live sanity-check outcomes are recorded separately in [baseline development](../results/baseline-dev-001/manifest.json). This is a question-only, local-model adaptation, not a faithful reproduction of the paper's published setting. Baseline task remains open for a meaningful frozen comparison.

## Source and retained behavior

Acquire [upstream source](https://github.com/DataArcTech/ToG) at commit `7ccbb92e17579f934bb778386230de47eca0ab67` in a separate checkout. `tog_adapter.py` verifies four complete file hashes before loading function definitions and literal prompt constants. Imports, top-level dataset loading, CLI and network setup are not executed. Upstream source is not vendored. Its README states Apache 2.0, but the pinned checkout lacks a separate license file; public redistribution and prompt-evidence licensing remain a release review item.

The adapter invokes upstream relation-search/pruning, entity scoring, entity pruning, reasoning and answer-generation functions. The main search loop retains width3/depth3, previous-relation suppression, relation-score × entity-score ranking, top-width nonzero beam retention, LLM sufficiency checks, half-stop generation and the depth-exhaustion direct-generation fallback. That fallback deliberately remains visible, including its use of parametric knowledge. It is not converted into a witnessed answer by assertion.

## Explicit departures

| Boundary | Local adaptation and consequence |
|---|---|
| Topics | Shared question-only semantic extraction and graph linker, instead of annotated topic IDs. All linking model/graph costs are charged. Same implementation/configuration does not force identical outputs across separate calls. |
| Model | Existing quantized Qwen2.5 7B, context4096, four threads, seed17, temperature0, output cap512. Original exploration defaults to .4 and another backend. No numerical paper-score reproduction claim. |
| Graph | Loopback logged transport; paginated distinct relation inventories; namespace restriction; any partial SQL state, result cap or request failure retained as a failure. Relation inventory cap600; other result sets cap100. No silently incomplete lists. |
| Names | Cached, deterministically sorted English names; unnamed nodes use upstream sentinel. This differs from arbitrary first returned name/sameAs. Logs contain source queries and returned labels. |
| Optional models | LLM pruning only. Embedding/BM25 imports are skipped; disabled paths raise explicitly. No unused embedding download or new dependency. |
| Subsampling | At least20 reached nodes → seeded sample of5 from deterministic graph order, preserving upstream size rule while fixing the seed. Sampling can lose correct answers. |
| Unknown names | Fix upstream name/ID misalignment by removing unknown pairs together when known candidates exist. All-unknown mediator sets remain possible. This correction is an adaptation, not identical bug-for-bug execution. |
| Output validation | Reject invented/unobserved relation choices, excessive width and nonfinite/out-of-range scores. Retain upstream score parser, including its uniform fallback if response count mismatches; raw response remains in audit. |
| Budgets | At most10 admitted model requests,16,000 observed tokens,80 graph calls,600s admission window; model timeout120s and graph timeout30s. Input usage is known after a call; an overrun is charged and causes abstention. These are not equal realized cost or hard billing/time guarantees. No retry. |
| Metrics | Retain native text. Optional grounded-ID output maps only braced answers to unique observed English names. Exact full labels preserve commas; semicolons/separate braces delimit sets. Missing/ambiguous/unobserved mappings abstain, with original native output retained. This may undercount otherwise correct text and is not a replication of paper Hits@1. |
| Meaning/support | Name mapping is not semantic certification or an entailment verifier. All nodes were observed, but selecting one does not prove it satisfies all question constraints or returns the complete set. The structured controller has a different restricted answer-program scope. |

## Reproduction

No extra package is needed for this LLM-only adaptation beyond Python's standard library and the existing graph/model services. Obtain the pinned upstream checkout separately; do not install its unused embedding dependencies.

```sh
git clone https://github.com/DataArcTech/ToG /absolute/path/to/tog-source
git -C /absolute/path/to/tog-source checkout 7ccbb92e17579f934bb778386230de47eca0ab67
python3 scripts/check_tog_adapter.py --upstream /absolute/path/to/tog-source/ToG
python3 -m flagship_controller.baseline_development freeze \
  --inputs evaluation/baseline-sanity-inputs.jsonl --output runs/new-baseline-sanity \
  --upstream /absolute/path/to/tog-source/ToG --snapshot YOUR_SNAPSHOT_ID
python3 -m flagship_controller.baseline_development execute runs/new-baseline-sanity \
  --upstream /absolute/path/to/tog-source/ToG
python3 scripts/summarize_baseline_development.py runs/new-baseline-sanity \
  benchmark-data/webqsp/evaluation-only.jsonl
```

Only the last command reads annotations, offline under the evaluation account. Runtime account must not read them. New output directories are required; source/input/model checks precede requests. The sanity harness refuses non-pilot and more-than-ten-question inputs, including the reserved cohort and official test. Original three benchmark cases are reused development examples. Handwritten inverse and no-match checks remain unscored. Offline compatibility fixtures exercise unchanged prompt construction, score/stop parsing, beam ordering, inverse direction, unnamed mediators and empty-frontier stopping. These do not establish model accuracy, full-code equivalence or a publishable comparison.

## Second development revision: compact presentation and explicit projection

The original full-inventory run is retained in baseline-dev-001. Its first baseline request times out, and three native outputs contain an unbraced answer after `{Yes}`. The frozen v1 converter therefore emits no IDs. That is a representation/runtime failure, not evidence that the baseline knows no answers. No retrospective edits or rescoring replace v1.

`compact_tog_adapter.py` adds two explicit departures in [baseline-dev-002](../results/baseline-dev-002/manifest.json): present at most32 unique relation names ranked lexically from the question before the unchanged upstream relation-pruning prompt; then make one extra charged constrained extraction request on the native response and final beam endpoints. Each selected ID must be a supplied endpoint with an observed full name inside a verbatim native-response quote. The extractor may abstain and cannot invent an ID or quote. It still uses the same uncalibrated model, so quote validation is not semantic proof. Ranking may omit needed relations; extraction can add error, false rejection and cost. This is a more bounded adaptation, not faithful upstream search-space equivalence.

All native text, failed mappings and raw observations remain. The same five purpose-selected questions are rerun; neither study supplies independent performance evidence. Use `--adapter compact-projected` when freezing the second configuration. It consumes the same total maximum budgets, including the extra extraction request. Do not merge revisions or discard timeout/format failures from reported denominators.

## Restore an exact archived runtime

To avoid running an old manifest with today's source, materialize its checked snapshots into a NEW directory:

```sh
python3 scripts/materialize_baseline_runtime.py results/baseline-dev-001 /absolute/path/new-v1-runtime
```

Use `baseline-dev-002` for the second version. From that isolated directory, invoke `python3 -m flagship_controller.baseline_development freeze --help`, then freeze a new run using the archived inputs, separately pinned upstream checkout and graph/model settings. The materializer verifies every source hash before writing and refuses an existing destination. It does not copy annotations, credentials, model weights or the database. The original output directories remain immutable; do not overwrite them to reproduce an experiment.

The v2 projection scores only emitted IDs; it does not automatically score every assertion in the original prose. A response can mix a named observed candidate with unsupported inferences. Preserve the native response and independently assess all its claims before describing it as faithful; ID projection alone must not be called native-answer accuracy or semantic certification. An adequate benchmark must freeze this distinction and any exhaustive-answer normalization rule first.

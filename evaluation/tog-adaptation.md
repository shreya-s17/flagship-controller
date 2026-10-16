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

## Third development revision: indexed relations and native spans

`indexed_tog_adapter.py` explicitly replaces the relation-stage free-text request with a charged JSON request choosing indices from the same lexical top32 presentation. Scores must be finite and in[0,1]; duplicate/out-of-range/boolean indices fail closed. The validated relation names and scores are converted into upstream parser syntax, preserving downstream direction resolution, entity scoring, beam pruning and native stopping. This changes the relation prompt and decoding; it is an additional local adaptation. The original upstream relation prompt is logged for provenance, not described as the prompt sent to the model in this revision. Empty relation lists skip that request.

The answer extractor can choose only indexed, actual full-name occurrences in the native response among named final-beam candidates. Offsets refer to original text, with word-boundary/case-insensitive matching, preserving original casing. Shared/overlapping names for different IDs are omitted as ambiguous. More than64 spans causes abstention. A charged same-model request determines whether a span is an explicit conclusion and whether all concluded answers are represented. These judgments remain uncalibrated and can be wrong. A quoted name can still be merely context; spans prevent fabricated quotes but do not prove meaning, completeness or faithfulness. No-span cases skip extraction and abstain. Native prose is retained for independent review, including extra unsupported assertions.

The frozen [run003 manifest](../results/baseline-dev-003/manifest.json) reuses exactly the five existing development question strings. Prior runs and their scoring are unchanged. Use `--adapter indexed-spans` for a new freeze and `scripts/check_tog_adapter.py --indexed --upstream ...` for offline fixtures. This revision is not a faithful ToG reproduction, a held-out gain or a new constrained-generation algorithm. Costs include every structured selection/extraction call.

While run003 was executing, code inspection identified an independent numeric-format edge case: Python can print tiny finite scores with an exponent, while the upstream parser accepts only decimal digits and dots. Current source v3.1 formats those weights as decimal strings and passes a new small-score test plus16 offline compatibility checks. The run003 archived source remains v3; it was not changed or silently restarted. No live result is attributed to v3.1. Restore run003 snapshots for exact reproduction; freeze a new output directory to execute current source.

## Restore an exact archived runtime (all versions)

To avoid running an old manifest with today's source, materialize its checked snapshots into a NEW directory:

```sh
python3 scripts/materialize_baseline_runtime.py results/baseline-dev-001 /absolute/path/new-v1-runtime
```

Use `baseline-dev-002` for the second version and `baseline-dev-003` for the indexed/spans version. From that isolated directory, invoke `python3 -m flagship_controller.baseline_development freeze --help`, then freeze a new run using the archived inputs, separately pinned upstream checkout and graph/model settings. The materializer verifies every source hash before writing and refuses an existing destination. It does not copy annotations, credentials, model weights or the database. The original output directories remain immutable; do not overwrite them to reproduce an experiment.

The v2 projection scores only emitted IDs; it does not automatically score every assertion in the original prose. A response can mix a named observed candidate with unsupported inferences. Preserve the native response and independently assess all its claims before describing it as faithful; ID projection alone must not be called native-answer accuracy or semantic certification. An adequate benchmark must freeze this distinction and any exhaustive-answer normalization rule first.

## Further declarations and shared-state execution

Run004 requests a free-text FINAL_ANSWER marker but retains all format/budget/fallback failures. The new declared-json-v5 adaptation replaces the native reasoning prompt/parser with one constrained JSON decision and answer-index array over all observed named nodes (cap64), including earlier frontiers. It preserves raw provider JSON and makes no extraction call. Invalid/empty ANSWER or nonempty CONTINUE declarations fail closed; parametric fallback remains unadmitted. This changes upstream stop prompting/decoding and is not faithful paper reproduction or semantic certification. See [measured failures and common-state check](../results/common-state-development-report.md).

The shared-state runtime supplies per-instance seeded structured transport; raw transport uses an optional sender/seed hook and baseline sampling receives the same seed. Defaults remain17 for ordinary standalone models. Historical source snapshots remain immutable. Materialize exact old sources before reproducing an old manifest. [Common-state protocol](common-state-runtime.md).

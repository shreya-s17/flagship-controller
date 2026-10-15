# WebQSP live feasibility report — 15 October 2026

The server, Freebase endpoint, local model and question-only controller are connected. **No answers were produced for the five training-pilot questions.** This is an implementation diagnostic, not successful benchmark completion or evidence for H1–H3.

## Runs and measured results

Three development revisions used the SAME first five records from the previously fixed training-pilot split, in the same order. These are five distinct questions, not fifteen independent observations. No official test questions were executed. Inference was local CPU-only Qwen2.5-7B-Instruct Q4_K_M through Ollama0.40.4; frozen digests/settings and graph provenance are in the [deployment manifest](webqsp-live-001/deployment-manifest.json).

| Revision | Answers / 5 | Local macro F1 | Graph calls | Model calls | Observed input+output tokens | Sum of question times |
|---|---:|---:|---:|---:|---:|---:|
| 001: original exact-name runner | 0 | 0.00 | 3 | 5 | 609 | 34.88s |
| 002: bounded casing variants and optional type-based selection | 0 | 0.00 | 3 | 5 | 609 | 45.92s |
| 003: clearer topic-extraction contract and whole-question guard | 0 | 0.00 | 19 | 7 | 2,548 | 119.13s |

All five submitted records were scorable locally. Exact-match was0 in every revision. Official evaluator parity is not certified. With no answered cases, there is no answered-case precision or reliability advantage to estimate. Revision003 used more tokens without improving yield. Timing includes cache/model-load effects and is not a controlled comparison.

## Failure analysis

Revision001 had three name-linking failures and two model-mediated unsupported-question/mention rejections. Two model replies used the whole question as the topic; one used lower-case `london`. These are different failure modes, not three identical case errors.

Revision002 added original/title/uppercase exact label/alias variants without scanning all labels. London then reached the100-row truncation guard. The other outcomes did not change.

Revision003 added generic extraction examples unrelated to the pilot and rejects whole-question topics. It reached topic disambiguation and real path traversal but ended as follows:

| Training ID | Terminal reason |
|---|---|
| WebQTrn-66 | Missing support for the proposed relation chain |
| WebQTrn-181 | Name/alias results exceeded100 rows |
| WebQTrn-246 | Candidate list exceeded the10-entity selection cap |
| WebQTrn-279 | Candidate list exceeded the10-entity selection cap |
| WebQTrn-321 | Name/alias results exceeded100 rows |

The optional selector may choose only a supplied ID using logged observed types. Membership does not prove the topic is correct: this remains an uncalibrated LLM decision. Unsupported-constraint recognition also changed across prompts: the river question was rejected in early revisions but admitted by003 before a later candidate-cap abstention. This exposes semantic-filter weakness. A downstream abstention is not evidence that unsupported questions are recognized reliably.

## Infrastructure and correctness

The Ubuntu-packaged Virtuoso build misread the archive's identifier tables. That attempt was stopped and preserved; a clean ZIP copy was restored with the provider-recommended official upstream7.2.5 binary. Successful checks returned readable triples, English names, topic candidates and mediator-schema values. They establish basic connectivity/schema access, not complete graph coverage or equivalence to WebQSP's2015-08-09 snapshot. The archive's original snapshot remains unverified; no Wikidata augmentation was added.

The initial query-cost admission threshold rejected a validation query. It was raised to600seconds of estimated cost, matching the provider example; actual execution remains capped at30seconds. Some cold validation requests failed before the final successful saved checks. These were not scored as benchmark answers. Cold-start performance outside this slice remains uncharacterized.

The client explicitly requests a30,000ms timeout and rejects non-success `X-SQL-State`, including Virtuoso's HTTP200 `S1TAT` partial response. Incomplete rows are never accepted as a complete answer set. [Vendor documentation](https://docs.openlinksw.com/virtuoso/anytimequeries/).

All **34 tests pass locally and on the server**, including partial-result rejection, casing, invented disambiguation IDs, whole-question mentions, gold boundaries, ambiguity, row caps and usage accounting. The unprivileged runtime account was directly verified unable to read the root-owned answer-label file. Scoring runs separately afterward.

## Artifacts and reproduction

Directories [001](webqsp-live-001/), [002](webqsp-live-002/) and [003](webqsp-live-003/) contain manifests, complete predictions/traces, provisional offline scores, exact standalone runtime sources and SHA256 checksums. Each archived source hash matches its manifest. Revision001 also contains the shared deployment manifest and successful graph checks. [Machine-readable comparison](webqsp-live-summary.json).

Replay a revision by running its `runtime-source.py` directly with the fixed question-only intake, recorded model/snapshot, private endpoint `http://127.0.0.1:8891/sparql`, and a NEW output directory. Use `--disambiguate` for002/003 only. Complete question/label datasets stay outside Git. Repeat latency/model behavior may vary despite fixed seed and temperature.

## Remaining gate

Build a bounded context-aware entity retriever/linker, explicit supported-constraint handling and evidence-based plan repair. Simply raising caps or choosing the first entity would hide observed failures. Improve on training material, retain failures, then freeze policies before calibration and held-out comparisons. Reproduce named baselines and certify evaluator/snapshot comparability before confirmatory experiments. The flagship parent and benchmark tasks remain open.

No extra server, GPU, storage or model API purchase was made; existing rental continues. Password changes remain deferred at the user's request, services stay loopback-only, and Freebase automatic startup is not enabled.

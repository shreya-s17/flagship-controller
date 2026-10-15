# WebQSP execution pipeline: feasibility stage

15 October deployment update: [live server provenance and limitations](../deployment/live-server.md). The model is installed locally and the private Freebase endpoint uses port8891. Thirty-four tests now pass; the added transport check rejects Virtuoso's HTTP200 anytime/partial responses when `X-SQL-State` signals an incomplete result. A 30,000ms timeout is explicitly requested. The five-question pilot completed with zero answers; [failure analysis](../results/webqsp-live-report.md) documents three training-development revisions. Optional `--disambiguate` enables bounded, uncalibrated type-based topic selection; it is not a trained linker. See the live run record for details; the original implementation-only checkpoint below is historical.

10 October 2026. Implemented and locally tested; no live Freebase or model service was contacted, no model downloaded and no server purchased. Thirty tests pass, including original controller tests and new transport, accounting, gold-boundary, ambiguity, multi-answer, semantic rejection and truncation checks.

## Implemented flow

Question-only input → mention extraction → exact Freebase name/alias candidates → unique entity or abstention → observed relation inventory → model-proposed simple chain → bounded graph acquisition → observed-chain verification → uncalibrated semantic gate → answer set or abstention. Incoming/outgoing relations and CVT mediator chains are supported. Literal RDF metadata is retained. All returned witnesses and graph queries, prompts/responses, usage and terminal reasons are logged. Evaluation labels are read only by the separate offline scorer.

This is a new live-service feasibility runner alongside the existing synthetic engine. It is not the final adaptive controller: the model proposes one fixed chain; recovery currently explores alternate graph branches and reports missing support, without replanning the chain. The `adaptive` CLI variant adds semantic gating; it does not establish learned adaptive acquisition or H1–H3. `fixed-chain` is an internal ungated control, not a published baseline. These names must not be presented as faithful CoR/ToG reproduction.

## Connection and commands

Provide a read-only Freebase SPARQL endpoint with its snapshot ID, and an Ollama-compatible `/api/chat` endpoint with an installed model. The URLs are configurable. Model version/digest, graph bytes/checksum and service version need to be frozen in the deployment record before live runs. The runtime records model name but does not independently resolve a model digest. No default model is silently downloaded.

```sh
python3 -m unittest discover -s tests -v
python3 -m flagship_controller.webqsp_runtime \
  --inputs benchmark-data/webqsp/inputs.jsonl \
  --output runs/webqsp-feasibility-001 \
  --endpoint http://localhost:8890/sparql \
  --snapshot ACTUAL_SNAPSHOT_ID \
  --model-url http://localhost:11434/api/chat \
  --model ACTUAL_INSTALLED_MODEL --limit 5
python3 -m flagship_controller.webqsp_score \
  runs/webqsp-feasibility-001/predictions.jsonl \
  benchmark-data/webqsp/evaluation-only.jsonl
```

Runner selects pilot questions from the intake file; it never executes official test questions. Existing output directories are rejected. Never put secrets in URLs or commit logs containing credentials; these example local connections require no authentication. Authenticated remote deployment is not yet implemented. The services should be reached through local/private access rather than exposing database administration.

## Budgets and validity

Per-question defaults: four model calls, 4,096 observed input+output tokens, 40 graph calls, 100 rows/query, four hops, 100 frontier/witness entries, 180-second wall admission cap and individual HTTP timeouts. Requests are capped and truncation causes abstention rather than an incomplete answer set. A token cap cannot prevent one already-sent request from exceeding the cap: actual input tokens arrive in the provider response; overshoot is charged/logged and suppresses answers. This is not a hard dollar billing cap. A synchronous HTTP call may complete after the wall deadline; the next action then aborts. Model usage absent or malformed responses cause failure, never zero-cost success.

Questions with temporal filters, comparisons, counting, conjunctions, negation, superlatives and other non-chain obligations are unsupported. Detection is model-mediated and can fail. Exact-name linking can miss mentions and abstains on ambiguity; it is not a trained disambiguator. No calibrated confidence is returned. A path in Freebase is observed support, not independent factual validation; semantic checking is an imperfect LLM gate. Types, NLI, diagnosis-conditioned replanning and matched-state recovery from the full protocol are not implemented in this runner.

The local scorer computes exact answer-set match and macro precision/recall/F1 against the best eligible Good/Complete parse. Ineligible cases are explicitly excluded. Official evaluator parity, literal normalization and full-dataset comparability remain to be certified before reporting benchmark results. Do not use the local scorer's fixture tests as real benchmark validation.

## Next gates

1. Verify the server's usable storage, availability and India billing total; approve the specific purchase within the first-month USD100 cap.
2. Deploy and checksum the compatible Freebase snapshot; freeze model digest/service and confirm access. CPU/model feasibility and any paid backend remain to be measured.
3. Run five training-pilot questions with real services; inspect entity linking, plans, raw witness provenance, missing-support reasons, actual costs and evaluator parity. No confirmatory claims from this convenience slice.
4. Improve linking, constraint handling and replanning based on pilot evidence, freeze policies, calibrate separately and reproduce named baselines. Then run protocol comparisons on held-out data.

Sources: https://www.w3.org/TR/sparql11-protocol/ and https://docs.ollama.com/api/chat . The pipeline implements URL-encoded SPARQL POST and non-streaming JSON chat responses per these documented interfaces.

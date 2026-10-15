# Flagship controller

An interpretable verification-guided controller and reproducible synthetic research experiment. The MVP, independent proof evaluator and first paper draft are available. The primary WebQSP and CWQ study remains pending; see the [acceptance record](evaluation/acceptance.md) for the exact completion boundary.

## Review the work

- [Live WebQSP feasibility report](results/webqsp-live-report.md): private Freebase/model deployment and three development revisions on the same five training questions; zero answers, with complete traces and failure analysis. [Server/source record](deployment/live-server.md).
- [First paper draft](paper/first-draft.md): methods, prior work, measured synthetic results and missing benchmark experiments.
- [Synthetic results](results/synthetic-v2/report.md): all 16 component variants and seven paired evidence conditions.
- [Failure analysis](results/failure-analysis.md): recovery, verifier errors, stopping and hypothesis revision.
- [Development protocol](evaluation/synthetic-protocol.md): settings, independent labels, budgets and limitations.
- [Artifacts](artifacts/README.md): full raw dataset, trajectories, metrics, manifests and checksums.

## Run locally

For the synthetic harness, Python 3.10 or newer suffices; no runtime packages, API keys or model downloads are needed. The live WebQSP runner requires the separate graph and model services documented above.

```sh
python3 -m unittest discover -s tests -v
python3 -m flagship_controller.solve examples/query.json --output runs/query.json
python3 -m flagship_controller.pilot
python3 -m flagship_controller.diagnostics
```

The main study contains 5,600 deterministic runs; diagnostics add 5,600 runs for budget and verifier-fault tests. These are generated development fixtures, not benchmark results. The research implementation is engine.py; the original controller.py and five-case demonstration remain available through python3 -m flagship_controller.

## Evidence and control

JSON input declares the start entity, relation sequence and type obligations. The controller observes acquired edges and endpoint types, scores branches heuristically, checks symbolic support and chooses backtracking, answering or abstention. It returns one witness, not general KGQA answer sets. No learned reward model, natural-language parser, calibrated probability or NLI verifier is claimed.

Every trace records states and hashes, candidates, chosen actions and arguments, acquired evidence, support signals, recovery and STOP decisions, graph calls, checks, edge counts and elapsed time. Tokens are zero because no model is called; GPU-seconds are unmeasured. Gold answers and corruption labels are supplied only to the independent evaluator, which does not import the deployed checker.

## Benchmark intake

Download the official [WebQSP archive](https://www.microsoft.com/en-ie/download/details.aspx?id=52763), then run:

```sh
python3 -m flagship_controller.benchmark /absolute/path/WebQSP.zip
```

This separates raw questions from evaluation-only parses and answers. Pilot, calibration and policy groups come from official training data; official test remains unchanged. Intake is not graph execution. Benchmark data is ignored by Git; the archive and compatible Freebase snapshot are not bundled. Never derive controller plans, linking or retrieval envelopes from evaluation gold.

## Research records

- [Notion research hub](https://app.notion.com/p/3f0cb3d4ccd6807abdf1fb5a7ae54b76)
- [Experimental design](https://app.notion.com/p/3f5cb3d4ccd68186b41ef5ae2775d54a)
- [Primary protocol](https://app.notion.com/p/3f5cb3d4ccd68117a4b4ccf55cb48bb4)
- [Flagship Todoist task](https://app.todoist.com/app/task/6hQFhc6wCQ4WGP2J)

No paper code was copied. Synthetic controls are not faithful paper reproductions. Licensing and public release remain project-owner decisions; the repository is private.

## WebQSP service pipeline

The question-only feasibility runner and separate offline scorer are implemented and covered by local tests. See [connection instructions and limitations](evaluation/webqsp-runtime.md). Live-service validation is pending. The runner handles bounded simple chains, exact-name linking, multi-answer evidence and an uncalibrated semantic gate; it does not yet implement full adaptive replanning or general WebQSP constraints.


## Readiness checkpoint — 15 October 2026

The repo is a working prototype, **not a final benchmark or publication artifact**. Read the [acceptance record](evaluation/acceptance.md), [actual failure/STOP analysis](results/live-failure-analysis.md), [contribution decision](paper/contribution-decision.md), [technical-report draft v0](paper/first-draft.md) and [application evidence map](paper/application-evidence-map.md). The three real-service revisions reuse five training questions and all answer 0/5; they do not establish adaptive improvement.

Verify archived live artifacts without a running server:

```sh
python3 scripts/verify_live_artifacts.py
python3 -m unittest discover -s tests -q
```

For offline rescoring with the separately acquired WebQSP annotations (never runtime input):

```sh
python3 -m flagship_controller.webqsp_score results/webqsp-live-003/predictions.jsonl benchmark-data/webqsp/evaluation-only.jsonl
```

Exact historical source/config hashes are preserved per run; deployment and live replay commands are in [the live report](results/webqsp-live-report.md). Re-execution can vary with model output, cold caches and endpoint state. The artifact verifier checks integrity and recorded totals; it does not certify scientific validity or official scorer parity. Next: [controlled-study blockers](evaluation/next-study-checklist.md).

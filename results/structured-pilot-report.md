# Structured controller: development and prospective pilot

15 October 2026. **Working restricted prototype; not a final benchmark or submission-ready paper.** The active controller is `typed-catalog-repair-v11`. This report supersedes the earlier zero-coverage checkpoint for current software readiness; historical traces remain preserved.

## Measured development results

The original three chain-runner revisions all answered 0/ 5 on the same five training questions. Two later catalog revisions reused those questions for development:

| Revision | Answered / 5 | Exact / 5 | Official-semantics macro F1 | Observed tokens | Graph calls | Sum question seconds |
|---|---:|---:|---:|---:|---:|---:|
| Structured catalog v10, run 007 | 3 | 2 | 0.4000 | 13,658 | 35 | 432.40 |
| Compact ranked catalog v11, run 008 | 4 | 3 | 0.6727 | 10,998 | 36 | 305.02 |

These are successive revisions on five distinct questions, not ten independent observations, not a baseline comparison and not held-out improvement. Latency differences include warm-cache and prompt changes; they do not establish a general efficiency advantage.

Latest cases: Maggie Grace/Taken, London postcodes and Madonna films match the official answer sets exactly. The counting/superlative river question is outside the grammar and abstains. The Philippines question returns nine spoken-language entities, including the two accepted official-language answers: precision 2/9, recall 1, F1 4/11. This is an unresolved answer-scope error. In v10 the planner went on from languages to their main countries and the semantic gate incorrectly approved it; its F1 was effectively zero. A same-model verifier is not a reliability guarantee.

## What changed

The runtime uses copied mentions and inferred types, graph-native keys guarded by name/type, bounded disambiguation using observed connections, finite one/two-hop schema-typed programs, explicit joins for all secondary anchors, and a restricted compiler. Candidate retrieval uses declared lexical/type priors: top 32 roots, up to 16 child predicates per root and top 20 programs. These restrictions can miss valid queries. A repair attempt masks the failed program and can acquire observed join options; it never receives gold feedback.

The compact selector and semantic gate retain complete query/row traces while sending bounded views to the model. Observed input prompts above 3,000 tokens are rejected after accounting, within a 4,096 context configuration. Model responses are structurally constrained; all accepted answers still require empirical evaluation. [Detailed specification](../evaluation/structured-controller.md).

## Prospective comparison

[Plan](paired-pilot-001/plan.json) was written before execution, with frozen runtime/transport/harness hashes, model digest/configuration, ten further pilot questions, randomized within-question control order and shared maximum budgets. It compares one fixed program choice against up to two choices with failure feedback and extra observations. It is an exploratory training-pilot study, not formal external preregistration or an official test-set evaluation. **Completed. Fixed F1 .40 versus repair .30; an earlier parsing difference confounds the contrast. A same-prefix follow-up gives .40 versus .40, with +16.48% repair tokens and no exact recovery.** See [full comparison](paired-pilot-report.md).

The method and plan remained fixed during execution. All twenty original predictions, costs and offline scores are archived; the same-prefix follow-up uses the same ten questions and is not independent new evidence. STOP rates remain unavailable without independent continuation labels. The study does not include a reproduced published baseline, calibrated confidence or the full proposed adaptive-acquisition method.

## Reproduction and integrity

Run `python3 -m unittest discover -s tests -q`, `python3 scripts/verify_structured_artifacts.py`, and `python3 scripts/check_official_parity.py /path/to/WebQSP.zip` from the repository root. Download the official archive through the documented Microsoft source and use `python3 -m flagship_controller.benchmark /path/to/WebQSP.zip` to reproduce question-only intake and offline annotations. Runtime accounts must not read the latter.

Live replay on the prepared private server, with a fresh output directory:

```sh
python3 -m flagship_controller.structured_runtime \
  --inputs benchmark-data/webqsp/inputs.jsonl \
  --output runs/structured-replay-new \
  --snapshot dki-archive-sha256-01ac8da685b7cc05 \
  --endpoint http://127.0.0.1:8891/sparql \
  --model flagship-qwen2.5-7b-q4km --limit 5 --variant repair
```

New offline scoring: `python3 -m flagship_controller.official_score PREDICTIONS benchmark-data/webqsp/evaluation-only.jsonl`. The older local scorer is retained only for historical JSON reproduction. [Official parity checks](../evaluation/official-scorer-cli-parity.json) cover 36 PRF cases and two original-CLI fixtures; archive/script hashes are recorded.

## Readiness

The artifact now supports real positive development cases and a frozen internal control experiment. Final-paper readiness still requires adequate independent evaluation, external baseline reproduction, semantic and STOP/recovery adjudication, snapshot comparability assessment and a precise contribution boundary. The report remains private and unsubmitted. [Venue plan](../paper/venue-plan.md), [ToG source audit](../evaluation/tog-source-audit.json), [acceptance record](../evaluation/acceptance.md).

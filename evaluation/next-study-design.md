# Next controlled study: design and implementation boundary

16 October 2026. **Preparation only: NOT frozen for execution.** The reserved100 training questions and official test remain unrun. This document fixes the intended contrast and exposes unfinished engineering; it is not a preregistration or a power calculation. A separate, executable [common-state development harness](common-state-runtime.md) now exists; this100-question design is still not frozen for execution.

## Question, cohort and controls

The primary contrast is whether one bounded, feedback-informed program revision improves official answer-set F1 over a single program choice, with the same linked question, candidate catalog and admission limits. A secondary question is how often graph-supported answers fail independent semantic review. The project currently has no established novel algorithm or repair advantage.

Use all100 inputs in [reservation v2](reserved-training-100-v2/manifest.json), input SHA256 `caca1ad180cba7e67614a59232da6ea36eac32e9534ad3d6c10ec42a03045dc2`. They come from `train_remaining`, selected without answer outcomes. All linking, grammar, timeout, normalization and resource failures remain in the denominator. Do not replace difficult questions, drop an unsupported subset after scoring or reuse this cohort as untouched evaluation after tuning on its outcomes. The existing .85 text-similarity audit does not rule out semantic overlap or pretraining contamination. Official test remains separate.

Planned policies:

| Policy | Intervention | Implementation boundary today |
|---|---|---|
| Fixed semantic controller | One program choice, structural checks and question-requirement gate | Implemented with captured catalog/first-choice replay in the development harness;100-question freeze remains gated |
| Bounded repair | Up to two distinct choices; recorded rejection reason and permitted observed join acquisition | Implemented with the same captured first choice; no repair benefit established |
| Semantic-gate-off repair | Retain compiler, graph-witness, answer-type and resource guards; bypass only the final same-model question-requirement audit | Implemented and unit-tested; this bypasses only the final semantic model audit |
| Rejection-reason-off repair | Retain failed-program masking and the same join acquisition; withhold only rejection-reason text from the next choice | Implemented and unit-tested; this is not complete feedback-off because masking/acquisition still communicate failure |
| Declared-JSON local ToG adaptation | Separate bounded beam search with the common linker; report native text and ID projection separately | Constrained stop/answer declaration and indexed relations implemented; not original-paper model/input reproduction |

If a complete feedback-off or acquisition-off claim is retained in the paper, implement a separate intervention that also removes those channels; do not rename the narrower reason-text ablation. Fixed versus repair does not isolate adaptive graph acquisition. Controls have different hypothesis spaces and verifier costs; this is a comparison under documented bounds, not an equal-compute causal claim by default.

## Shared states, seeds and resources

Before policy-specific inference, record one gold-free parse/link state for each question and seed. Reuse its exact model responses and observed graph rows across all policies, with prompt/query equality checks, original usage charged to every policy and physical/replayed requests distinguished. For the four internal controls, also reuse inventory, schema, root selection and catalog through the first choice. The baseline shares linking only; it has its own search space. Do not inject the structured catalog into it or call separately executed links identical states.

The older shared-prefix harness remains tied to preserved v11. The new `common_state_study.py` captures one gold-free link prefix for every question/seed and the same catalog/first PLAN for the four internal controls, with exact provider-payload/query equality checks. The baseline shares only linking. Usage/time are charged to each policy; new physical attempts are separate. A durable journal retains interrupted admitted jobs as unknown-cost abstentions without retry and halts on integrity mismatch. The executable harness is deliberately restricted to at most10 pilot inputs while larger-study gates remain open. [Protocol and exact commands](common-state-runtime.md).

Requested seeds propagate through structured/raw requests and baseline sampling. The current development check uses17 and29;43 is implemented/tested but not a third live replication. Temperature0 may yield identical outputs. Repeated seeds are not independent questions. Python hash seed17 and scheduling seed113 are separate settings. Cached-prefix latency is a constructed charge, not a fresh end-to-end measurement; cache/CPU limits remain explicit.

Initial maximum per question/policy remains10 model calls,16,000 returned usage tokens,80 graph calls,100 rows/query and600s admission, with120s model/30s graph timeouts and3000 observed prompt-token cap. All extra extraction, verification and linking work is charged. These are admission limits, not hard pre-call billing or wall-time bounds. Failed requests without returned usage produce unknown/lower-bound token cost, never zero. No silent retry, selective timeout rerun or method-specific budget increase is permitted. Smaller-budget curves require a separate frozen schedule and policy definitions before inference.

Randomize policy order within each question/seed using an independently fixed scheduling seed. Preserve the full order, progress and completion ledger. Resume only at a verified completed-record boundary; partial admitted requests remain failures with their known/unknown costs. Obtain a CPU feasibility estimate after the development runs; do not assume the full1500 planned policy executions are quick or adequately powered. No new paid service is required for preparation.

## Answers and analysis

Primary metric: official-semantics macro answer-set F1, bounded-repair minus fixed, across all100 questions; average repeated seeds within each question first. Secondary exact-set, coverage, benchmark-error rate among emitted answers, and graph/model/token/time vectors include denominators. A question-cluster paired bootstrap may summarize sampling uncertainty; it does not remove selection bias, graph mismatch or limited sample size. Final confirmatory size needs a declared practically meaningful effect and variance/discordance estimate from an appropriate pilot.

Freeze URI/literal serialization before execution. Preserve raw RDF terms; the proposed common calendar-date projection is a representation policy, not temporal equivalence. The development harness explicitly freezes raw lexical strings and reports the known date limitation; it does not use the optional calendar-date serializer. Keep this common raw policy in the larger freeze unless a separate, tested prospective representation change is declared. Never normalize using gold answer values.

For ToG, preserve every native response, its stopping reason and any unmapped/ambiguous conclusion. Projected-ID F1 is a separate measure from native-answer accuracy. Same-model extraction or completeness flags do not independently establish faithful extraction or all-and-only answers. Require blinded review of native claims, including unsupported additions, before presenting semantic accuracy. The existing30-case structured review pack does not cover this newest baseline; prepare a separately versioned addendum from complete outputs if its semantics are claimed.

Independent review reports four semantic dimensions, unknowns, disagreement and adjudication, clustered by question. The30 earlier development forms are a rubric check, not an evaluation sample for this cohort. Design an outcome-independent sample or full-cohort review before inference. STOP and recovery remain NA unless full-state records demonstrate a specific acceptable continuation within the original remaining budget, with independent acceptance and an explicit eligible denominator. Do not equate benchmark mismatch, abstention or backtrack count with those labels.

## Required before execution

1. Finish the frozen baseline development check and preserve every failure. Passing operational guards does not require a perfect debug score, but the answer representation and remaining limitations must be explicit.
2. Receive actual independent first-pass submissions; validate the unchanged pack, preserve files privately and adjudicate disagreements separately. Revise the rubric/guards on development only if needed.
3. The shared-state development harness, narrow ablations, seed propagation, raw serialization policy and conservative resume are implemented/tested. Complete and audit the small frozen live mechanics check; then assess harder development failures and freeze the exact larger-study source/configuration. Do not infer effectiveness from implemented controls or easy cases.
4. Freeze executable policies, cohort hash, randomized order, seeds, budgets, primary/secondary metrics, native-review sampling and exclusions before the first reserved-cohort request. Keep calibration and final testing separate.
5. Recheck label isolation, graph/model identity and clean-checkout restoration. Only then execute the feasibility cohort. Record all outcomes, and freeze a new final study before official testing.

Public release, authorship/contributions, licenses and submission remain later owner-review steps on a concrete package. No purchase, reviewer contact, reserved-cohort execution or paper submission is authorized or performed by merely writing this design.

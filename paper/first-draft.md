# Verification guided control of evidence acquisition in structured reasoning

First research draft, 10 October 2026. Exploratory synthetic results only. Authorship, affiliations and submission venue remain to be confirmed by the project owner.

Implementation checkpoint, 15 October: a separate real-service feasibility runner was deployed with Freebase and a local Qwen2.5-7B model. Three development revisions on the same five training questions all abstained; no held-out comparison or benchmark improvement was established. [Full diagnostic report and artifacts](../results/webqsp-live-report.md). These operational observations do not change the synthetic findings or establish H1–H3.

## Abstract

Reasoning over incomplete structured evidence requires a controller to distinguish useful acquisition from unsupported answering and search exhaustion. We implement an interpretable controller that selects graph branches, verifies observed path constraints, backtracks after detected failures and terminates with an answer or abstention. An independently implemented finite-graph evaluator separates factual correctness from accessible support. A synthetic development study contains 50 generated base questions, seven paired evidence conditions and all 16 combinations of acquisition, verification, recovery and stopping, totaling 5,600 executions. The full controller produces 210 grounded answers in 350 conditions with no unsupported answers under an exact symbolic checker. A verified fixed-order control achieves the same yield, and disabling adaptive acquisition does not change yield or expansion cost. Stopping reduces mean expansions from 3.503 to 3.126 in this fixture family. Injected verifier errors demonstrate that the observed safety depends on checker quality. These experiments establish software behavior and expose weak contribution claims; they do not demonstrate benchmark superiority, calibrated reliability, token savings or a novel algorithm. WebQSP and CWQ evaluation remains future work.

## Introduction

A graph reasoning system can fail by acquiring the wrong evidence, accepting an incomplete path, remaining on an invalid branch or continuing after sufficient support is available. These failures motivate a closed loop in which evidence acquisition changes a reasoning state and verification changes subsequent decisions. The central research question is whether support, unresolved obligations and uncertainty can improve the choice between further acquisition, recovery, answering and abstention at comparable total cost.

The integration of retrieval, verification and backtracking is already represented in prior work. Consequently, the candidate contribution must be empirical: better grounded yield, selective risk or cost under matched evidence access. The present prototype supplies an auditable experimental platform and a controlled development study. Its synthetic results challenge the assumption that adaptive acquisition necessarily improves outcomes.

## Related work and novelty boundary

Relation-centric exploration and constraint grounding are established design choices. [CoR](https://aclanthology.org/2026.findings-acl.2138/) searches relation chains and filters global entity sets. [CCoR](https://arxiv.org/html/2608.22762v1) composes main and constraint chains and includes fallback mechanisms. Our fixed-order controls are local adaptations of component ideas, not reproductions of either method. A claim that relation traversal or explicit constraint handling is novel would therefore be unsupported.

Adaptive acquisition also has substantial precedent. [REPAIR](https://aclanthology.org/2026.acl-long.1734/) uses plans to guide additional document retrieval. [SPARKLE](https://aclanthology.org/2026.acl-long.1793/) learns a proxy retrieval policy through reinforcement learning. [RouteRAG](https://aclanthology.org/2026.findings-acl.1502/) learns graph and text retrieval decisions within a generation policy. [CatRAG](https://aclanthology.org/2026.findings-acl.290/) uses query-aware graph weighting, while [GNN-RAG](https://aclanthology.org/2025.findings-acl.856/) retrieves paths through learned node relevance. These methods preclude a broad novelty claim about adaptive graph acquisition.

Verification, recovery and stopping likewise require direct comparison. [LCR-RAG](https://aclanthology.org/2026.acl-long.814/) uses logical feedback to guide iterative query correction. [CoG](https://aclanthology.org/2026.acl-long.708/) combines relational guidance with reflection and controlled backtracking. [NSF-CoT](https://aclanthology.org/2026.findings-acl.516/) checks evidential support with a hybrid verifier. [REFRAIN](https://aclanthology.org/2026.acl-long.1256/) studies adaptive reasoning termination. Our symbolic checker does not reproduce their neuro-symbolic or model-based components.

[FlowRAG](https://arxiv.org/abs/2606.17856) and [SIRLM](https://arxiv.org/abs/2608.17443) supply additional graph-flow and structural-rule context; their role here follows the existing literature matrix's abstract-level review. A broader method and code audit remains necessary before any exhaustive novelty statement. No published result from these papers is compared numerically with our synthetic measurements.

## Problem formulation

The development task provides a start entity, an ordered list of relations and required target types. This declared plan is an experimental assumption, not a natural-language parser. An evidence interface exposes a frozen finite graph envelope. The controller sees only acquired edges and endpoint metadata; the evaluator additionally receives factual answer labels and corruption manifests.

A witness is a sequence of observed, provenance-bearing edges satisfying continuity, relation and type constraints without an unresolved observed denial of the same triple. Grounded success requires a factually correct answer and a valid accessible witness. A correct memorized answer without a witness would fail this definition. Absence of an accessible proof denotes unsupported evidence within the envelope, not universal world unanswerability.

For each condition, the exhaustive evaluator enumerates valid witnesses independently of the controller checker. This permits certified minimum witness size within the finite path-query fixture family. It does not establish minimum acquisition cost, global proof optimality for arbitrary KG queries or hidden reasoning faithfulness.

## Controller

The state contains observed evidence, the selected path, a frontier of candidate branches, retained witnesses and remaining budgets. EXPAND retrieves all facts for the next declared relation, including explicit denials. SELECT chooses a path; RECHECK tests acquired support. BACKTRACK abandons a failed branch, while cached observations can support CONTINUE without another retrieval call. ANSWER and ABSTAIN are distinct terminal actions.

The training-free acquisition score is path depth plus 0.5 when an observed endpoint matches the next type obligation. The fixed-order control uses deterministic edge IDs. Verification checks path continuity, provenance, type obligations and observed conflicts. With feedback enabled, failures remove a branch; with feedback disabled, complete candidates may be returned unchecked. Recovery permits rerouting after failure. Adaptive STOP emits a candidate immediately after the active gate accepts it; disabling STOP searches until the cap or technical exhaustion and then emits the first retained candidate.

Confidence is an explicitly uncalibrated heuristic. It is not a reward model, entailment probability or truth percentage. The current recovery action is branch rerouting; query revision, learned failure routing, NLI and calibrated uncertainty remain absent. Every step records candidates, actions, acquired evidence, support signal, before and after state hashes, recovery and terminal decisions, graph calls, checks, edge counts and elapsed time. Gold labels never enter action selection.

## Experimental design

The generator constructs 50 two- or three-hop questions using seed 17. Each base graph includes one correct path and distractors with invalid types or dead ends. Seven paired conditions comprise intact evidence, support-edge deletion, distractor deletion, relevant conflict injection, unrelated noise at 25% and 100%, and an incorrect starting entity caused by alias ambiguity. Ten deletion cases retain an alternate witness. Noise occurs on unrelated relations, making it a negative control rather than a realistic retrieval-noise test.

All 16 acquisition, verifier, recovery and STOP settings receive identical graph access. The caps are eight expansion calls and 32 symbolic checks per question. The check cap differs from the saved primary protocol's four model-based rechecks; this study is a separate synthetic development protocol. There are no model calls, and billed tokens are zero. Local wall time includes controller overhead but excludes any model or network latency.

Paired descriptive intervals resample 50 base-question clusters 10,000 times with seed 17, retaining all seven conditions together. These intervals reflect this generator and support no population-level benchmark inference. No confirmatory family-wide significance statement is made. Separate diagnostics sweep expansion caps and inject checker status flips or parse failures at 5% and 15% with seeds 17, 29 and 43.

## Results

| Variant in acquisition verifier recovery STOP order | Grounded answers / conditions | Unsupported / answered | Mean expansions | Mean checks |
|---|---:|---:|---:|---:|
| Full 1111 | 210/350 | 0/210 | 3.126 | 4.394 |
| Acquisition disabled 0111 | 210/350 | 0/210 | 3.126 | 5.017 |
| Verifier disabled 1011 | 210/350 | 90/300 | 3.217 | 0 |
| Recovery disabled 1101 | 92/350 | 0/92 | 2.080 | 2.406 |
| Adaptive STOP disabled 1110 | 210/350 | 0/210 | 3.503 | 5.980 |
| Verified fixed order 0110 | 210/350 | 0/210 | 3.503 | 5.980 |
| Unchecked fixed order 0010 | 75/350 | 225/300 | 5.571 | 0 |

The full controller answers all 210 independently supported conditions and abstains on 140 unsupported or conflicted conditions. This result depends on a deliberately exact symbolic checker and a small controlled task. Verifier removal preserves the same number of grounded answers while adding 90 unsupported answers and increasing coverage from 60% to approximately 85.7%. Thus the risk difference must be interpreted with its coverage difference; it is not a same-coverage reliability result.

Acquisition removal changes neither grounded yield nor mean expansions. Its lower priority structure requires more checker calls, but the fixture does not support the original yield claim. Recovery removal lowers yield while also reducing realized cost. The paired grounded-yield difference is 0.337, with a descriptive cluster interval of [0.254, 0.420]; unequal realized cost prevents interpreting this as the saved H2 result.

Adaptive stopping preserves yield while reducing mean expansions by 0.377, with a descriptive paired interval of [-0.500, -0.263] for full minus STOP-disabled. This is approximately 10.8% fewer graph expansion calls. It is not a token-saving measurement and does not satisfy H1's 15% total-token criterion.

Budget caps of one, two, four and eight expansions yield respectively 0, 37, 194 and 210 grounded answers out of 350. At cap four, 16 of 210 supported conditions are abstained. An accessible proof alone does not establish whether continuation is feasible under the remaining budget, so these are supported abstentions rather than certified premature-stop errors.

At 5% injected verifier status-flip rate, the full controller emits 539 answers across 1,050 seeded condition-runs, of which 530 are grounded and nine unsupported. At 15%, 356 of 381 answers are grounded and 25 unsupported. Parse-failure injection yields 539 grounded answers at 5% and 368 at 15%, without unsupported answers in these finite runs. These artificial faults expose dependency on verifier quality; they are not estimates of a real NLI verifier's error distribution.

## Failure analysis and hypothesis revision

The trace taxonomy distinguishes missing relation support, invalid target type, unresolved positive and negative evidence, incorrect linked seed, exhausted expansion or check budget, parse failure and erroneous verifier acceptance or rejection. The full controller's main-study abstentions are expected evidence failures under the finite oracle. Natural KG failure cases have not been evaluated.

Representative trajectories show a valid multi-hop witness, backtracking after an invalid-type branch, retained alternate support after deletion, abstention on a conflicting final fact and failure after a wrong entity link. The artifact includes unsuccessful trajectories as well as successes. Intermediate exploration is not treated as an unsupported assertion; the currently scored auditable decisions are terminal answer assertions only.

The acquisition hypothesis should be narrowed to difficult states where relation plans or candidate schemas are uncertain. The current known-plan fixture produces no yield advantage. The next design change is an independently evaluated question parser and ambiguity-aware linker, followed by matched evidence envelopes containing relevant distractors and imperfect support checks. A calibrated gate must be fitted on separate development questions rather than assigning probability meaning to a hand-written score.

## Benchmark plan and missing experiments

The official WebQSP archive was acquired with SHA-256 recorded in the intake manifest. Its complete-parse files contain 3,098 training and 1,639 test questions; partial files contain 680 and 393 respectively. Inputs contain question text only, while entity annotations, gold parses and answers reside in separate evaluation-only storage. The official test set is unchanged, and internal pilot, calibration and policy groups are derived from training data. Exact-string train/test overlap was zero; semantic paraphrase auditing remains pending.

**TBD experiments:** execute valid gold queries against a frozen compatible Freebase snapshot; establish independent question linking and query-independent envelopes; acquire CWQ v1.1; freeze model, prompts and costs; reproduce or explicitly adapt CoR/CCoR; run the planned paired benchmark slice; obtain independent labels for ambiguous cases; evaluate calibrated risk at prespecified coverage; perform matched failed-answer recovery and budget-constrained continuation audits. The current engine returns a single witness and must support answer sets before general KGQA scoring.

H1, H2 and H3 remain untested under their saved criteria. Confirmatory sample size and resource requirements must use development estimates, not held-out outcomes. No test-set tuning, novelty clearance, public publication or agent transfer is asserted.

## Limitations and reproducibility

Known relations, explicit types and same-triple denials simplify inference. The generator favors the symbolic checker and does not represent uncertain natural-language entailment, temporal contradictions, heterogeneous schemas or multimodal evidence. Full-envelope finite enumeration is an evaluator privilege unavailable to the controller. Recovery is branch rerouting, and each method's own failure-conditioned recovery rate is not a matched initial-state experiment.

Code, tests, generator, independent evaluator, frozen settings, raw trajectories, edit manifests, per-run metrics and aggregation scripts accompany the draft. Python 3.10 or newer and the standard library suffice for synthetic reproduction. The raw data archive and source hashes identify the executed development study. Benchmark source data is retained locally and is not redistributed without a license audit. The GitHub repository remains private.

## Conclusion

The prototype makes evidence acquisition, support checking, branch recovery and termination auditable in a controlled graph task. Synthetic ablations isolate clear checker and stopping behavior, but provide no acquisition-yield advantage and no benchmark or token hypothesis result. The viable next research contribution depends on calibrated decisions under uncertain plans, imperfect verification and matched real evidence access.

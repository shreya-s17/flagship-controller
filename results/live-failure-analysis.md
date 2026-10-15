# Live pilot failure and STOP analysis — 15 October 2026

Scope: post-hoc analysis of `webqsp-live-003/predictions.jsonl`, with earlier revisions retained in the live report. These are five reused training questions, not independent samples across revisions. No live successful answer or successful recovery occurred. Synthetic successes are separately available in `synthetic-v2/representative-trajectories.json`; they cannot substitute for a live success.

| Question | Observed failure | Recovery and STOP interpretation |
|---|---|---|
| WebQTrn-66, Maggie Grace in Taken | Entity selected; planner chose TV starring/appearance relations and omitted the film-specific constraint. Twelve EXPAND, eleven VERIFY and eleven BACKTRACK actions produced no complete witness. | Branch backtracking happened; plan repair and successful recovery did not. Terminal missing_support. |
| WebQTrn-181, London postcode | Exact-name/alias result exceeded the bounded row set. | Abstained on truncation; no verified answer candidate. |
| WebQTrn-246, three rivers | Ambiguous linking exceeded the candidate cap; the model had admitted a counting question despite restricted support. | Abstained on candidate cap. Unsupported-operation detection remains fragile. |
| WebQTrn-279, Philippines language | Linking exceeded candidate cap. | No observed usable plan or witness; abstention is not evidence of world unanswerability. |
| WebQTrn-321, Madonna movies | Exact-name/alias result exceeded the bounded row set. | Abstained on truncation; no validated answer candidate. |

## Failure taxonomy and intermediate decisions

Linking failures prevent all downstream reasoning in four cases. In the fifth, the selected entity is plausible but the proposed relation sequence is semantically unsuitable. An observed KG edge proves that edge exists; it does not prove the question's complete meaning was preserved. No final semantic verifier was reached. Earlier revisions also emitted whole-question mentions, missed case variants and rejected some unsupported questions. The implemented mention guard and generic examples improved extraction but did not produce an answer.

## STOP labels and denominators

All five terminated in abstention. Answered-case precision and selective risk are undefined at zero coverage. Early STOP would require an independently demonstrated, budget-feasible continuation from the observed state to an acceptable answer. Late STOP would require a previously available valid answer plus measured avoidable continuation. Neither counterfactual has been established for these live traces; both rates are **not identifiable**, not zero. A row/candidate cap is a measured resource limit, not automatically an early-STOP error. The eleven failed backtracks are not eleven independent recovery opportunities. Recovery success is zero observed successful repairs, with no certified recoverable-case denominator.

## Design and hypothesis revision

REVISE the immediate goal from demonstrating adaptive-policy advantage to establishing question-only linking and constraint-aware planning feasibility. Keep bounded results and abstention safeguards. Add multi-entity/film constraints, candidate ranking evaluated against independent labels, and a bounded plan-repair action with explicit cost before testing recovery. Validate positive and negative development fixtures without using gold parses at runtime. Then freeze a fixed control and an adaptive policy for a paired study. Do not loosen caps or accept the first alias to manufacture coverage.

H1 token savings, H2 matched recovery advantage and H3 calibrated reliability remain untested. Synthetic acquisition-off results show no acquisition advantage; synthetic STOP savings concern graph expansions only. See [decision memo](../paper/contribution-decision.md) and [current report](webqsp-live-report.md).

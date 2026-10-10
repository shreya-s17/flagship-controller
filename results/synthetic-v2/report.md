# Synthetic pilot results

**Exploratory development experiment only.** These results do not establish WebQSP/CWQ performance, novelty or H1–H3.

50 generated base questions × 7 paired conditions × 16 A/V/R/S variants = 5600 executions. No model calls; token use is zero.

| A/V/R/S | Grounded / all | Answers / all | Unsupported / answers | Mean expansions | Mean checks |
|---|---:|---:|---:|---:|---:|
| 1111 | 210/350 | 210/350 | 0/210 | 3.126 | 4.394 |
| 0111 | 210/350 | 210/350 | 0/210 | 3.126 | 5.017 |
| 1011 | 210/350 | 300/350 | 90/300 | 3.217 | 0.000 |
| 1101 | 92/350 | 92/350 | 0/92 | 2.080 | 2.406 |
| 1110 | 210/350 | 210/350 | 0/210 | 3.503 | 5.980 |
| 0000 | 55/350 | 232/350 | 177/232 | 3.514 | 0.000 |
| 0010 | 75/350 | 300/350 | 225/300 | 5.571 | 0.000 |
| 0110 | 210/350 | 210/350 | 0/210 | 3.503 | 5.980 |

Bits denote acquisition, verifier feedback, branch recovery and adaptive STOP. 0010 is an unchecked fixed-order search control; 0110 adds symbolic verification but keeps fixed ID order and terminal search. Neither is CoR/CCoR.

## Full controller by condition

| Condition | Grounded / all | Answered / all | Supported abstentions / supported |
|---|---:|---:|---:|
| intact | 50/50 | 50/50 | 0/50 |
| support_deletion | 10/50 | 10/50 | 0/10 |
| distractor_deletion | 50/50 | 50/50 | 0/50 |
| conflict | 0/50 | 0/50 | NA (0/0) |
| noise_25 | 50/50 | 50/50 | 0/50 |
| noise_100 | 50/50 | 50/50 | 0/50 |
| alias_ambiguity | 0/50 | 0/50 | NA (0/0) |

## Interpretation and limits

The generator includes invalid-type branches, so a symbolic type checker is favored by construction. Branch ordering and short budgets can still cause avoidable abstention. No observed gain here should be generalized to natural questions or imperfect verifiers.

Noise is on unrelated relations and is therefore filtered by the known query plan. This is a negative control, not a realistic noisy-retrieval robustness claim. Alias corruption is an incorrect starting entity, not an implemented ambiguity resolver.

Recovery rates conditional on each method’s first failure are diagnostic only: the initial failed states differ. A matched frozen-state recovery study remains required. Supported abstention indicates accessible proof exists; budget-constrained continuation audits are not implemented, so premature-STOP counts remain NA.

Checks, graph calls and wall time include controller overhead; wall time is a small local-Python diagnostic without network/model latency. No GPU saving or token hypothesis is tested.

Independent oracle enumerates complete witnesses within the finite envelope. It does not import the deployed checker. All-query factual correctness is distinct from accessible support.

Artifacts: manifest, complete compressed dataset/trajectories, per-run CSV, condition tables, 10,000-replicate paired base-cluster intervals and representative successes/failures.

# Contribution decision — 15 October 2026

**Decision: REVISE the engineering/research hypothesis; NO-GO for a submission or an improved-method claim now.** This is not a decision to abandon the project.

The synthetic study establishes instrumented controller behavior on declared finite path queries: 210/350 grounded answers for both the full and verified fixed-order controls. Disabling acquisition does not change grounded yield or mean expansions. Disabling STOP increases mean expansions from 3.126 to 3.503, but this is neither token savings nor a matched real-model comparison. The checker is symbolic and the generator favors its assumptions.

The separate live Freebase/Qwen diagnostic ran three revisions on the same five training questions. Each revision answered 0/5, with local macro F1 and EM zero. Linking caps and an unsuitable TV plan for a film question dominate. There is no paired fixed/adaptive live comparison, held-out result, calibrated verifier or successfully repaired live failure. Snapshot identity and official scorer parity remain unresolved.

The existing literature matrix already covers traversal, verification, recovery and stopping. For example, [CoR](https://aclanthology.org/2026.findings-acl.2138/) uses relation-centric exploration with entity filtering. Combining these broad components does not establish novelty. The current decision follows measured weaknesses, not an exhaustive claim that every possible contribution is covered by prior work.

## Revised claim and next decision gate

Current defensible contribution: an auditable prototype, a reproducible synthetic component study, and a documented failed real-service feasibility diagnostic. Next testable hypothesis: explicit unresolved question constraints and bounded plan repair can improve grounded yield over a fixed-chain control at comparable total inference and retrieval cost. This is a proposal, not an implemented or demonstrated improvement.

Reconsider GO only after: question-only linking/planning succeeds on development cases; the fixed and adaptive policies are separately frozen; named external baseline reproduction is audited; paired held-out conditions log token, graph, latency and support costs; an independent STOP/recovery audit defines eligible denominators; and current related-work/code review establishes a precise distinction. Negative or equal results remain reportable. Until then retain an internal technical-report draft and avoid publication, superiority or novel-controller claims in applications.

Evidence: [synthetic report](../results/synthetic-v2/report.md), [live report](../results/webqsp-live-report.md), [trace analysis](../results/live-failure-analysis.md). No additional purchase is needed for these development steps.

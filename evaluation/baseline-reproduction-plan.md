# Named-baseline execution gate

16 October 2026. **Not implemented or executed.** This is a concrete adapter specification for the pinned [ToG source audit](tog-source-audit.json), not evidence of a reproduced result. Keep the baseline task open.

Use upstream commit `7ccbb92e17579f934bb778386230de47eca0ab67` in a separate checkout; preserve upstream source hashes. Do not redistribute source until its license is resolved. The existing local CPU model is sufficient for an initial adaptation sanity check; no paid API or GPU is required for that check.

| Boundary | Required implementation / check |
|---|---|
| Input | Frozen question-only common linker. Charge identical linking work to every method. No annotated topic IDs, answer aliases or gold paths at inference. Log unresolved and ambiguous anchors rather than select the first. |
| Model | Same frozen Qwen alias/config/digest for a matched local comparison. Label this a model adaptation: it does not reproduce the published GPT backend. Retain prompts and actual usage. |
| Search | Preserve upstream relation/entity pruning and search control where compatible. Record depth/width, relation filters and seeded subsampling. Any budget-induced departure is explicit. |
| Graph transport | Replace every direct SPARQL call, including name lookup, with bounded, logged, loopback transport. Reject partial SQL states and truncated results. No silently incomplete relation inventory. |
| Inference transport | Replace unbounded retry with explicit admission budgets, timeouts and complete usage accounting. A failure is a retained outcome, not silently rerun until success. |
| Optional pruning dependencies | LLM pruning must not download an unused embedding model. If isolating unused imports, fail explicitly if a disabled path is called and document this shim. Pin actual imported dependencies. |
| Answer/metric compatibility | Upstream generates text; our primary evaluator expects complete answer ID sets. Freeze a gold-free, ambiguity-aware normalization procedure or retain separate native text and grounded-ID metrics. Do not compare a reported paper Hits@1 score directly with our exact-set/F1 scores. Failed normalization is a retained outcome. |
| Sanity checks | Three known development cases, including inverse relation and failed/no-answer control. Compare prompt construction, pruned candidates and search transitions to upstream behavior. These are debugging, not independent scores. |
| Final comparison | Only after adapter/source/input/normalization checks pass: freeze all policies, shared linker, seeds, maximum budgets, metric definitions and the reserved cohort. Include full denominators, raw outcomes and resource vectors. |

Close ToG reproduction only at the actual audited scope. A carefully bounded, question-only Qwen adaptation may be useful experimentally, but cannot be described as a faithful reproduction of the original paper's model/input/resource setting. A closer CoG/CoR method comparison remains necessary before a novel-method claim. No baseline model call has been made by this planning step.

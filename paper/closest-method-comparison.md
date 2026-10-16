# Method boundary after targeted paper and code inspection

16 October 2026. **No algorithmic novelty claim is established.** This note reviews method sections and selected current source files, not every dependency or the complete literature. Neither method below has been executed here. [Pinned source hashes and inspection scope](../evaluation/closest-method-code-audit.json).

## CoG

CoG derives relation blueprints from training queries, retrieves/adapts them as structural priors, reranks candidate relations and preserves a structurally aligned candidate alongside model choices. Its failure mechanism diagnoses evidence gaps and revisits earlier decisions. These overlap the proposed guidance/verify/backtrack loop and forced root retention; replacing its blueprint prior with observed type metadata alone does not establish novelty. [Method §§3.1–3.3](https://aclanthology.org/2026.acl-long.708.pdf).

Selected code inspection at `0ce2ae2ab7485450d4249e3b861d275389bfc249`: `CoG/freebase_func.py:180` combines local/step/global embedding scores and a guarded relation inclusion; `CoG/main_freebase.py:79` initializes a skeleton and later invokes failure/reverse exploration. `perform_refinement` explicitly prompts internal-knowledge best guesses after incomplete search. This source behavior must be separated from witnessed graph-only answer quality if reproduced; current-source inspection does not establish identity with the paper's experimental release. [Pinned code](https://github.com/zjukg/CoG/tree/0ce2ae2ab7485450d4249e3b861d275389bfc249).

Our runtime instead constructs a bounded typed program catalog, records observed query rows, and rejects some unverified outputs. That is an implementation/scope distinction; its same-model semantic ledger remains uncalibrated. A CoG adaptation would also need a training-only blueprint library that excludes the reserved training evaluation annotations. Otherwise an evaluation within the training split could leak its own paths into the library.

## Chain-of-Relations

CoR searches relation chains using a history stack, then chooses continue, backtrack, filter or stop based on path correctness and whether the candidate space can contain the answer. Global filtering delays answer selection. Our proposed relation control, requirement checking and recovery therefore overlap existing mechanisms. The restricted compiled joins and trace audits here do not independently establish a new reasoning algorithm. [Method §4 and AppendixA](https://aclanthology.org/2026.findings-acl.2138.pdf).

Selected code inspection at `f92557913271ad4b8eeb5046a206a8c1b4ffb2ff`: `CoRAgent` maintains relation-chain DFS, executes candidate search before reasoning, and dispatches stop/constraint/forward/backtrack actions. Its filter includes retries and optional candidate presentation limits; its Freebase backend declares result caps. A local adaptation must preserve and disclose these scopes, distinguish complete queries from presentation samples and account for every retry. We have not ported or tested it. [Pinned code](https://github.com/Chenhui7au/Chain-of-Relations/tree/f92557913271ad4b8eeb5046a206a8c1b4ffb2ff).

## Current contribution decision

Continue as a reproducibility and reliability investigation: measure when witnessed paths answer the wrong question, which failures arise before selection, and when repair adds cost without recovery. To become publishable, that direction needs independent semantic judgments, adequate frozen evaluation and actionable findings beyond a handful of debug cases. A method-paper claim would require a precisely distinct mechanism plus ablations against these overlaps. No paper result is numerically compared with our development scores, and no superiority follows from this review.

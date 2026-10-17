# Closed obligations and primary-anchor conjunctions

17 October 2026. Development engineering after the unsuccessful direction-prompt check. This is a restricted, explicitly hand-designed ontology/language prior, not a novel or calibrated general semantic verifier. The v11 controller/compiler and v16 semantic module remain unchanged; a separate runtime and source materializer preserve all historical executions.

The new full-string grammar handles single copied-anchor questions asking for parents/children, plus narrow location-membership wording. It requires the parser's single anchor and answer category to agree. Unrecognized, nested or multiple-anchor phrasing is unhandled and falls back to the existing same-model audit; this can still accept wrong answers. Within recognized kinship questions, the allowed one-hop predicate orientations are explicit: `parents out` or `children in` for parent endpoints; `children out` or `parents in` for child endpoints. Other paths are rejected rather than guessed. The closed family can reject a valid equivalent outside its whitelist.

For recognized location questions, up to three additional bounded graph queries discover edges between one-hop candidate endpoints and the primary anchor. The catalog adds only **observed** containment bindings (`containedby out` / `contains in`), with a constraint back to anchor0; these candidates are prioritized within the20-entry cap. All discovery calls are charged and archived. No model-supplied query, question ID, answer lookup or gold predicate/query is used. The ontology family itself is an explicit development prior informed by the earlier failure diagnosis.

The new restricted compiler allows joins to the primary anchor while requiring every secondary named anchor to remain bound. Queries return full bounded rows with a witness for **each** path and conjunction edge. The independent auditor admits primary joins only with the explicit new grammar marker; wrong anchors, missing rows and tampering still fail. Membership in a city does not implement every finer requirement: the word “downtown” remains an unmodeled qualifier handed to the existing uncalibrated audit. A matching official set would not prove precise downtown/world semantics.

The [frozen study](../results/obligation-dev-001/manifest.json) has six purpose-selected development strings, three official originals and three handwritten controls/paraphrases. They are chosen after failure inspection and are not held-out or independent samples. Eighteen outcomes use seed17, with a common catalog/first PLAN for fixed, bounded repair and obligation-guard-off. Guard-off disables both new closed checks only; the expanded catalog, compiler, structural guards and final same-model audit stay active. The new catalog/ranking prevents a matched causal comparison with historical studies; the current three-way comparison shares it explicitly. No named published baseline is rerun in this narrow check.

The existing10-call/16000-token/80-query/100-row/600s admission limits remain. Prefix costs are charged to every control, physical requests are separate, and replay latency is constructed. The durable intent/result journal retains interrupted admitted work without retry and halts on integrity failures. Source/input/model/environment checks now also bind the complete manifest by hash. All frozen outcomes remain in the denominator. Only original training questions receive offline official-set scores; handwritten controls remain unscored.

```sh
python3 -m flagship_controller.obligation_study freeze \
  --inputs QUESTION_ONLY_PILOT.jsonl --output runs/new-obligation-development \
  --snapshot YOUR_SNAPSHOT --seeds 17
PYTHONHASHSEED=17 python3 -m flagship_controller.obligation_study execute \
  runs/new-obligation-development
python3 -m flagship_controller.common_state_audit runs/new-obligation-development
python3 scripts/summarize_common_study.py runs/new-obligation-development \
  /evaluation-account-only/webqsp/evaluation-only.jsonl
python3 scripts/diagnose_common_recovery.py runs/new-obligation-development
```

Restore the seven frozen inference modules with `scripts/materialize_obligation_study.py STUDY NEW_DIRECTORY`. The isolated runtime contains no evaluator or labels. The source hash, model digest, exact inputs, manifest, schedule, actual requests and graph observations remain necessary reproduction evidence. Gold-query/catalog and witness-requery diagnostics run after timed inference only, under the evaluation account.

An observed rejected-plan-to-exact-answer transition will be reported as development behavior, not independently certified recovery or a rate with an invented eligible denominator. Extra calls, false rejection, wrong answers and unknowns must remain visible. Independent review, stronger evaluation and contribution/release decisions remain open. The reserved100 and official test stay unrun; no new purchase is needed.

## Subsequent constraint propagation

The first completed version enforces rejection, but its single-program mask still lets the second model choice violate the same obligation. Its complete18 outcomes are preserved. Version2 therefore propagates the **same declared necessary obligation** after an explicit role/membership rejection, removing all remaining incompatible catalog candidates before the second choice. This is basic closed-constraint pruning, not a learned or novel search rule. No candidate is scored against benchmark labels or answer IDs. An unhandled question, disabled guard or absence of a qualifying rejection does not trigger pruning. The [second pre-inference freeze](../results/obligation-dev-002/manifest.json) reuses the full identical six-string cohort; it is further development, not independent replication.

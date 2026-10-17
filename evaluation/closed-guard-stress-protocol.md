# Closed-guard countermodels and catalog isolation

17 October 2026. Completed offline software analysis; **not independent semantic review or publication clearance**. No additional inference, benchmark labels, reserved inputs or official test questions are used. The live controller and all historical results remain unchanged.

## Finite reference worlds

The [executable audit](../flagship_controller/obligation_stress.py) enumerates every directed, non-reflexive parent matrix on four numbered nodes:2^12=4,096 worlds. Child edges are the exact inverse. Reference answers come directly from the matrix, independently of the deployed predicate whitelist/compiler. These arbitrary graphs can contain biologically impossible cycles. They establish only behavior under declared synthetic definitions.

Eight programs are checked for each of two roles in every world, giving65,536 guard/program/world combinations. Programs include the four canonical predicate/direction combinations, an extra identity step, and an extra endpoint filter. `fixture.identity` consists only of self edges; `fixture.allowed` connects node1 to anchor0. These are explicitly toy relations, not claims about Freebase predicates. Some programs are compiler-representable but absent from the active single-anchor catalog. An identity extension preserves a canonical answer in every world; an arbitrary endpoint filter can omit requested answers while preserving correct relation direction.

Location worlds independently vary three-bit attraction-root, city-membership and downtown sets, requiring downtown to be a subset of the city. All216 valid combinations are enumerated. Five programs for each of two scopes give2,160 combinations. Reference city answers are attraction-root intersect city; downtown answers are attraction-root intersect downtown. The guard sees membership, not the synthetic downtown label. This separates a necessary containment condition from complete finer-scope semantics.

Every evaluated combination, including empty candidates, contributes to reported totals. Empty results are counted separately because the real pipeline rejects them. Counters distinguish guard passage, exact nonempty sets, omitted answers and extra endpoints. First counterexamples retain their entire finite graph, target, program and returned set. These counts are determined by a deliberately constructed enumeration, not a natural-world distribution, rate estimate or independent sample. A rejected exact set can be accidental; the identity-extension families provide a separate, controlled equivalence example.

Thirty-three [handwritten grammar contract cases](closed-guard-grammar-cases.json) cover declared templates, copied-anchor/category dependence, punctuation/case, nested/qualified/multiple-anchor wording, and explicit downtown metadata. They verify declared software scope only. They are neither unseen natural-language evaluation nor independent human judgments. Unknown grammar stays unhandled and falls back to the existing same-model gate; no fail-closed semantic guarantee is added.

Before enumeration, the audit writes a new manifest, input/source hashes and manifest hash. Execution refuses altered frozen inputs/source. No historical directory is overwritten. The result is deterministic and mutation checks ensure that accepting everything or rejecting everything fails the canonical invariants. An audit PASS means the declared implementation invariants hold; retained semantic-scope counterexamples are expected, not erased by the PASS.

```sh
python3 -m flagship_controller.obligation_stress execute results/closed-guard-stress-001 > /tmp/stress-reproduced.json
cmp /tmp/stress-reproduced.json results/closed-guard-stress-001/report.json
python3 -m flagship_controller.catalog_intervention_audit results/obligation-dev-002 > /tmp/catalog-reproduced.json
cmp /tmp/catalog-reproduced.json results/catalog-contrast-001/report.json
```

Restore the existing lossless evidence bundles before the second command. Use the source revision associated with this report. The frozen stress manifest binds package sources; later changes require a fresh audit directory or the original source checkout. A new audit can be frozen with the module's `freeze --cases ... --output NEW_DIRECTORY` command.

## Catalog availability from actual captures

The [separate catalog audit](../flagship_controller/catalog_intervention_audit.py) verifies frozen source, input and journal checksums and reconstructs the preserved schema-only catalog from each actual run002 root/schema/anchor state. It compares structural program identities against the captured expanded catalog, including additions and displaced entries. No program is executed and no answers or gold annotations are scored. A rule-compatible program is not necessarily correct, complete, selectable by the model or affordable.

This diagnostic cannot estimate a counterfactual model answer or catalog effect. A changed catalog changes the prompt and potentially the first choice. The old and new catalog conditions must therefore share a **pre-catalog** state, rather than falsely sharing the expanded first PLAN.

## Next comparison: implemented development freeze, no wider-study clearance

Use a separate prospective development check before the reserved100. Do not tune on that reservation. The following conditions isolate interventions without relabeling current results:

| Condition | Observed containment catalog | Closed guard/pruning | Choices |
|---|---|---|---|
| C0G0 | Off: preserved schema catalog/ranking | Off | At most2 |
| C0G1 | Off | On | At most2 |
| C1G0 | On: current observed expansion/ranking | Off | At most2 |
| C1G1 | On | On | At most2 |
| Fixed C1G1 | On | On |1 |

Keep structural/compiler/type/resource/same-model checks identical. Fixed versus C1G1 addresses revision under the same catalog and closed rules. C1G1 versus C1G0 isolates the closed checks conditional on the expanded catalog; the factorial contrasts address catalog changes and interaction. Guard-on without a compatible catalog candidate may legitimately abstain; retain that outcome. There is no claim that every condition has an admissible correct program.

Capture question/link/root/schema observations once before catalog construction. Within each catalog condition, capture its actual catalog and first PLAN once and replay it across guard conditions, then branch at verification. Charge the shared work to every policy, keep actual requests separate, and randomize condition order. A later independently executed local ToG adaptation shares linking only and remains explicitly an adaptation. Report realized budget curves or describe unequal realized compute; common maxima alone do not establish an equal-compute comparison.

The separate nine-module [factorial runtime and durable harness](factorial-development.md) now implements these capture boundaries and interventions. Real seeded-transport fixtures verify distinct catalogs, exact nested replay, interruption retention and exhausted guard-on/catalog-off branches. A [30-condition development plan](../results/factorial-dev-001/manifest.json) freezes all six previously inspected strings at seed17 before new inference. It is a small engineering contrast, not an untouched evaluation cohort. Independent semantics/false-rejection review and an adequate source/sampling/analysis freeze remain necessary before larger inference. The reserved100 and official test remain unrun.

The owner will provide independent reviewers later. Blank packs remain prepared; no reviewer was contacted and zero reviews are counted. Engineering and offline preparation can continue. Semantic validation, wider experiments, contribution assessment, licensing/authorship and owner review of a concrete release/submission package remain open.

# Harder development cases and direction-aware audit — 16 October 2026

**Completed development evidence; publication remains NO-GO.** Four previously inspected official training questions were purpose-selected from historical failures, using the unchanged eleven frozen runtime modules of common-state-dev-002. All20 planned outcomes completed at seed17; this is not a held-out sample, independent replication or published-method reproduction. [Pre-inference selection protocol](common-state-dev-003/selection-protocol.json).

## Unchanged-method harder-case outcomes

| Input | Each of four internal controls | Declared-JSON local baseline |
|---|---|---|
| Chicago attractions |23 answers,15 official overlaps; F1 .789474 |Model-call-budget abstention |
| Whitney inventions |Exact3-answer set |One of3; F1 .5 |
| Iran government forms |Exact5-answer set |Model-call-budget abstention |
| Revere parents |Incoming parents query returns16 reverse-role endpoints, no official overlap |One of2 parents; F1 2/3 |

The enabled same-model gates accept the reverse-role Revere answer and broad Chicago set. All four controls have macro F1 .697368 and exact-set accuracy2/4. The baseline has projected-ID F1 .291667 and exact0/4. These figures describe four selected debug cases, not performance rankings or semantic accuracy. The official helper retains its tiny epsilon for zero overlap; this report describes that Revere outcome as no overlap rather than rewriting the scorer. [Full scores and costs](common-state-dev-003/development-score.json).

No REJECT, REPAIR_PLAN or reason-text-withholding event occurs. Four semantic-gate bypasses occur. Repair minus fixed is0; false acceptance prevents the repair branch from running. Absence of rejection does not mean absence of error or establish verification is unnecessary. [Reproducible branch diagnosis](common-state-dev-003/recovery-diagnosis.json).

Charged totals across four question instances per method:

| Method | Model calls | Returned usage tokens | Graph calls |
|---|---:|---:|---:|
| fixed |16|12,166|54|
| repair |16|12,166|54|
| semantic-gate-off |12|7,060|54|
| reason-text-off |16|12,153|54|
| tog-declared-json |28|16,053|99|

Actual physical inference makes48 model attempts (12 captures plus36 continuations) and215 graph attempts. All returned usage is complete. Prefix charges/time are reused across methods; the difference from physical work is an experimental reuse mechanism, not a demonstrated method-efficiency gain. No CI or population effect is estimated.

## Post-run catalog and scope diagnosis

The privileged [catalog audit002](catalog-diagnostic-002/summary.json) runs only after all timed inference, under the evaluation account:80 graph queries, three fully evaluated catalogs and three questions with a known exact-answer option. Two Iran alternatives truncate, so its catalog coverage remains incomplete despite exact options being found. All four official gold-query answer sets match this archive in this limited check; snapshot equivalence is not established. No oracle scores/queries enter inference.

For Revere, catalog index9 already has the correct outgoing parents path, while index0 reverses its roles. This is a selection plus false-acceptance problem, not a missing-candidate problem. The audit does not certify a budget-feasible independently accepted recovery.

For Chicago, none of the fully queried catalog candidates is exact; best F1 is .789474. The official inspected query also requires the returned attraction to be contained within the primary city anchor. The current catalog/constraint grammar omits that primary-anchor re-entry conjunction. More resampling of this same catalog cannot supply an official exact set. Gold query inspection is post-run diagnosis, not a runtime recipe or independent world-truth judgment. [Detailed failure record](common-state-dev-003/failure-diagnosis.json).

All20 rows pass the state/request/declaration ledger audit. Sixteen structured answers pass recorded witness checks; all47 unique accepted triples are present on post-run graph requery, with0 missing/unknown. This includes witnessed wrong-role endpoints: graph presence is not question-answer correctness.

## Baseline currency error retained

The earlier currency failure originates in the actual stop/answer declaration, which selects both peso and a contextual coin; the index converter preserves that declaration exactly. Its observed edges retain direction, but upstream-style rendered chains omit explicit direction. This is a representation limitation, not proof of the cause. No temporal metadata independently establishes present coin use. [Both-seed post-run diagnosis](../evaluation/baseline-answer-scope-diagnosis.json).

## Direction-aware audit follow-up

The separately frozen [common-state-dev-004](common-state-dev-004/manifest.json) adds optional subject/predicate/object variable roles to the existing final semantic model request. The incoming parents query becomes `answer -> parents -> anchor0`. This generic representation applies to supported query/constraint directions, adds no gold facts, no kinship-specific rule, no extra model request and no independent verifier. The original parser/linker/compiler and default historical audit are preserved. The predeclared follow-up uses the inspected parents original plus an opposite-role handwritten children control at seed17, ten planned outcomes; the latter is unscored. All10 outcomes complete. The four internal controls still emit16 reverse-role endpoints for parents and2 reverse-role endpoints for the handwritten children question. All six enabled model audits receive the actual directed input and nevertheless accept; there is no rejection, repair or reason-withholding. On the sole official original there is no answer overlap (the unchanged scorer retains its epsilon); the handwritten opposite-role control is unscored. The baseline returns one of two parents (F1 2/3) and abstains on the children control at a truncated graph result. No selective rerun is performed. [Scores and costs](common-state-dev-004/development-score.json), [actual request input audit](common-state-dev-004/directed-input-audit.json).

All10 rows pass the independent state/request ledger checks. Eight structured answers pass witness consistency, and all18 unique accepted triples are present on post-run requery. Physical inference makes18 model attempts (6 captures plus12 continuations) and65 graph attempts; returned usage is complete. The representation change is implemented and tested but **does not resolve semantic direction failure** in this check.

## Reproduce the analyses

```sh
python3 scripts/restore_live_evidence.py
python3 -m flagship_controller.common_state_audit results/common-state-dev-003
python3 scripts/summarize_common_study.py results/common-state-dev-003 /evaluation-only/webqsp/evaluation-only.jsonl
python3 scripts/diagnose_common_recovery.py results/common-state-dev-003
```

Witness requery and gold-query/catalog audits run after timing measurements only. Source materialization, label isolation, frozen plans and full denominators remain part of reproduction. [Interpretation rules and when they were written](../evaluation/recovery-decision-rules.md). Independent semantic/native review, scope-aware catalog work, a larger executable freeze and public release/authorship/license review remain open. Reserved100 and official test remain unrun. No reviewer contact, public release or new purchase occurred.

## Current artifact and next work

173 tests pass from a clean source snapshot, including actual directed-input transport, both predicate orientations, mediated constraints, historical replay, conservative recovery diagnosis and deterministic allowlisted evidence packaging. Final clean-checkout verification is recorded in [checkpoint validation](../evaluation/harder-checkpoint-validation.json). The [new lossless bundle](../artifacts/harder-common-evidence-2026-10-16/manifest.json) preserves both completed studies and the privileged catalog audit; prior bundles and source/results remain unchanged.

The unchanged30 structured forms are supplemented by24 new masked structured records; a32-case native handoff includes all baseline versions and common-state outcomes. All remain blank/unannotated, with zero independent reviewers and no contact. Prepared forms are not evidence.

The next engineering priorities are a direction-sensitive semantic decision that survives development counterexamples, and observed conjunction support back to the primary anchor. Merely adding direction text or retrying the existing Chicago catalog has no demonstrated benefit. Independent reviewers must assess both semantic false acceptance and any proposed correction before the larger study freeze. No recovery/STOP rate, novel mechanism or publication readiness is claimed.

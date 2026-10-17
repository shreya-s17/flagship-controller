# Nested catalog-by-guard development controls

17 October 2026. Implemented, fixture-tested and30/30 outcomes complete; [30-condition plan](../results/factorial-dev-001/manifest.json) frozen before live execution. This engineering cohort reuses all six run002 strings: three inspected official originals and three handwritten, unscored controls. It is not a new or held-out sample. [Completed outcomes and costs](../results/factorial-development-report.md). Reserved100 and official test remain untouched. [Motivation and limitations](closed-guard-stress-protocol.md).

`factorial_runtime.py` composes the preserved v2 controller, without editing its source or historical studies. C0 keeps the preserved schema catalog/ranking and acquires no primary-membership inventory. C1 retains current observed containment expansion/ranking. G0 bypasses only closed-obligation checking/pruning; G1 enables both. All compiler, type, graph-witness, resource and final same-model checks remain. The five conditions are repair-C0G0, repair-C0G1, repair-C1G0, repair-C1G1 and fixed-C1G1.

The new boundary matters: one common capture stops immediately after SCHEMA, before catalog acquisition or first choice. Each catalog mode then replays that exact state, constructs its own catalog and captures its own first PLAN. Conditions sharing a catalog replay that mode's first PLAN; cross-catalog conditions do not falsely reuse the expanded choice. Actual provider-payload/query equality is enforced, and journal links bind common capture → catalog capture → policy continuation. Per-request seed17 and scheduling seed113 remain separate.

All stages preserve original usage/cost and record physical requests separately. Constructed charged time includes original common capture plus the mode-specific capture and continuation; it is not fresh latency. Unknown usage from interrupted admitted work is retained, with no silent retry. Partial common failure propagates to every condition; partial catalog failure propagates to its conditions. Hash/request mismatch halts for investigation. C0G1 may exhaust its catalog, which remains a recorded abstention rather than a replaced case. Exact maximum resource vector remains10 model calls,16,000 returned usage tokens,80 graph calls,100 rows and600s admission per condition, with120s/30s request timeouts. These are admission limits, not a guaranteed hard wall-time/billing cap.

The frozen plan includes nine inference modules and question-only inputs. The [materializer](../scripts/materialize_factorial_study.py) restores only those modules; no evaluator or labels are included. Existing server account protection of evaluation annotations must be rechecked before live inference. The independent [nested ledger auditor](../flagship_controller/factorial_audit.py) checks source/input/manifest hashes, complete planned denominator/order, committed journal links, actual seeds/requests, graph-prefix equality, first PLAN, prefix charges and physical request counts. It does not certify semantic correctness. Fixture tampering that recomputes ordinary result hashes still fails nested identity checks.

```sh
python3 scripts/materialize_factorial_study.py results/factorial-dev-001 NEW_RUNTIME
cd NEW_RUNTIME
PYTHONHASHSEED=17 python3 -m flagship_controller.factorial_study execute /ABS/STUDY
# Offline evaluation account / complete repository only:
python3 -m flagship_controller.factorial_audit results/factorial-dev-001
python3 -m flagship_controller.factorial_analysis results/factorial-dev-001 /EVALUATION_ONLY/annotations.jsonl
python3 scripts/diagnose_common_recovery.py results/factorial-dev-001
```

The separate offline factorial analysis consumes these condition names and counts the nested physical stages; the existing branch diagnostic retains full rows. The historical summary script requires its original policy names and must not be used for this study. Independent semantic/STOP/recovery labels remain absent. Report exact/official-set changes as inspected-case behavior, not certified recovery or general superiority. Wider sampling, repeated-seed inference, budget curves and an adequate named-baseline comparison require their own freeze. No novel control algorithm, calibrated reliability or paper acceptance follows from these engineering controls.

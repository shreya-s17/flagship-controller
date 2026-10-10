# Synthetic failures and stopping analysis

The full controller answers 210 of 350 main-study conditions with valid support. The remaining 140 comprise 40 deletion cases without alternate support, 50 relevant conflicts and 50 incorrect starting entities. No natural benchmark failures are represented in these counts.

| Failure | Observable controller response | Independent interpretation |
|---|---|---|
| Wrong endpoint type | RECHECK then BACKTRACK | The chosen branch cannot satisfy the declared obligation. |
| Missing next relation | Empty EXPAND then reroute or ABSTAIN | No path found on that branch; alternate branches must be considered before claiming scope-level absence. |
| Same triple asserted and denied | Reject observed witness | Unresolved conflict in the fixture scope. Different times or entities are not modeled. |
| Wrong entity link | Empty expansion at selected root | Correct facts elsewhere do not support the linked query. No linker repair is implemented. |
| Expansion cap | Continue inspecting already observed frontier; stop further retrieval | Abstention may be budget-limited even when a complete accessible proof exists. |
| Parser failure | Unresolved support and branch rejection | Conservative abstention reduces coverage. Retry/revision remains future work. |
| Verifier false acceptance | Invalid branch can reach ANSWER | Demonstrates that verification output is not its own gold label. |

## Stopping observations

With exact symbolic checking, no unsupported full-controller ANSWER occurred among 210 answers. Removing adaptive STOP preserves yield but increases average graph expansions from 3.126 to 3.503. The evaluator identifies evidence sufficiency from independently enumerated proofs at each trace step and counts expansion actions afterward. Technical search exhaustion is recorded rather than charging fictitious filler calls.

The cap-four diagnostic abstains on 16 of 210 supported cases. This is not a certified early-stop count: continuation under a specified additional budget has not been audited. The metrics record the premature-abstention audit as NA. No claim about hidden reasoning or unlogged intermediate assertions is made.

## Recovery interpretation

The full controller grounds 210 conditions, versus 92 when branch recovery is disabled. Its mean expansion cost is higher, 3.126 versus 2.080. This demonstrates useful rerouting in generated graphs at different realized costs. It does not establish H2's gain over a faithful fixed-retry baseline at comparable cost. Per-method first-failure recovery rates have different conditioned states and remain descriptive.

## Concrete revision

Do not center the contribution on adaptive acquisition alone: disabling it gives the same grounded yield and expansion cost. Preserve the simple verified fixed-order control as a strong comparator. The next hypothesis should focus on whether independently calibrated support and ambiguity diagnosis improve decision quality when relation plans, linking and verifier outputs are uncertain. H1 token saving, H2 matched failed-answer recovery and H3 calibrated selective risk remain open.

See `synthetic-v2/report.md`, `diagnostics.json`, `paired-comparisons.json` and `representative-trajectories.json` for measured quantities and raw examples.

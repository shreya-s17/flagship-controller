# VERIFY / RECOVER / STOP transfer specification

Specification only, 10 October 2026. This fulfills the control-variable mapping and testable-hypothesis deliverable; no agent implementation or empirical transfer result exists.

| Variable | KG reasoning | Tool-using agent |
|---|---|---|
| State | Observed edges, frontier, candidate witness, remaining budget | Goal, observed tool outputs, action history, remaining budget |
| Available action | Choose relation/entity, expand, verify, backtrack | Inspect, call tool, verify output, revise plan |
| Observation | Newly acquired edges and provenance | Tool result and observed environment changes |
| Verifier | Evidence entails witness; type and conflict checks | Result satisfies an explicit postcondition with observed evidence |
| Uncertainty/cost | Unresolved obligations; graph calls, model tokens and time | Unverified postconditions; tool calls, model tokens and time |
| Recovery trigger | Unsupported/conflicting candidate or dead branch | Failed postcondition, unavailable tool or inconsistent observation |
| Recovery | Explore alternative branch or abstain | Revise plan or halt for unresolved prerequisites |
| STOP | Answer only after witness checks; otherwise abstain | Finish only after required postconditions; otherwise report failure |

Shared principle: stop after observed evidence supports all declared terminal obligations, while treating unavailable verification as unresolved rather than success. Domain-specific: KG proof semantics/CVTs/type constraints differ from executable postconditions, irreversible actions and time-varying environments. Symbolic path support is not interchangeable with real-world task success.

Hypothesis: at a matched total model-token/tool-cost budget and matched answer/completion coverage, obligation-aware verification and stopping reduce unsupported terminal outputs relative to fixed-step execution in both KGQA and a deterministic read-only tool sandbox. Test each domain separately; improvement in only one domain rejects the broad transfer claim.

Experiment: freeze question/task splits, model and prompts; compare full controller, fixed-step baseline, minus-verifier, minus-recovery and minus-adaptive-stop. Inject paired missing evidence, contradictions and tool/edge failures. Keep task labels and success oracle evaluator-only. Score unsupported terminal outputs, factual/task success, abstention/failure reporting, matched-state recovery, premature stop and total cost. Fit confidence on separate calibration tasks; select policy on development only. Require uncertainty intervals and coverage-matched comparisons, not conditional recovery rates from unequal failed states.

Expected counterexamples: a graph proof verifies successfully while source facts are wrong; a tool reports success but the environment did not change; stale observations; verification costs exhaust the budget. These distinguish evidence-support guarantees from world truth.

Current evidence: synthetic KG component study only. No autonomous-agent benefit, transfer or calibrated policy claim is supported. This probe is a later extension; the user selected WebQSP/Freebase as the active experiment. The flagship parent remains open.

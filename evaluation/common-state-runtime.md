# Executable common-state development study

This is a development harness, not an adequate final evaluation. It refuses more than10 questions, non-pilot inputs and annotation fields. The reserved100 and official test remain unrun. [Frozen executable development plan](../results/common-state-dev-002/manifest.json).

## State and control boundaries

Capture the question contract, linking observations, schema, candidate catalog and first program choice once per question/seed. The four internal controls replay this exact state through the first PLAN event, then continue separately. The baseline replays only the linking prefix and uses its own search. Prefix requests/queries must match exactly; a mismatch halts execution. Replayed responses still pass through contract validation, source code and resource accounting; they are not substituted benchmark answers.

Policies are fixed, bounded repair, final-semantic-gate-off repair, rejection-reason-text-off repair and a declared-JSON local ToG adaptation. Gate-off retains compiler, witness, type and budget guards. Reason-text-off retains failed-program masking and join acquisition; it is not complete feedback-off. There is no calibrated verifier or learned reward model. Compare full denominators and resource vectors; equal maximum budgets are not equal realized costs.

The final baseline declares a structured stop decision and answer indices jointly over all named observed nodes, including earlier frontiers/anchors. It retains the raw provider JSON. There is no second model extracting answers from prose. This changes the upstream stop prompt/parser and output contract. It can still choose a wrong entity, omit answers or falsely stop; declared-index fidelity does not certify semantics. The previous free-text FINAL_ANSWER revision and its format failures are preserved separately.

## Seeds, costs and representation

Per-request seeds propagate through both structured and raw-text calls and the baseline subsampler. Supported seeds are17,29,43; the development check uses17 and29. Temperature remains0, so repeated seeds can give identical outputs and are not independent questions. The Python hash seed is fixed separately at17. Actual request payloads and hashes are archived; backend stochastic independence is not established.

Every policy is charged the original prefix's graph/model calls, returned usage tokens and measured prefix time. New physical requests are reported separately. Policy latency is original prefix plus replay/continuation time, not a fresh end-to-end measurement. Model calls, returned tokens, graph calls, rows and time retain the original limits; failed requests without returned usage are not counted as zero tokens.

Answer serialization is explicitly **raw**: Freebase IDs and RDF literal lexical strings. Calendar-date conversion is not used. The known timezone-suffix mismatch remains visible; this policy does not certify temporal equivalence. Native/declared baseline fields and projected-ID benchmark scoring remain distinct. Human review of meaning, scope and evidence is still needed.

## Interrupted work and reproduction

A durable per-job intent is written before inference. A completed job is stored atomically with its content hash. Resume verifies the original inputs, sources, model/configuration, environment and committed job hashes; completed work is not repeated. If a job started but has no committed result, it becomes an explicit abstention with unknown/lower-bound costs, without retry. An interrupted common prefix propagates that retained failure to all affected policies. Source/request/journal integrity errors halt the study instead of being converted into ordinary model failures. Completion stores the final prediction hash; running a completed study again makes no requests.

```sh
python3 -m flagship_controller.common_state_study freeze \
  --inputs evaluation/common-state-sanity-inputs.jsonl \
  --output runs/new-common-development \
  --upstream /absolute/path/to/pinned/ToG \
  --snapshot YOUR_SNAPSHOT_ID --seeds 17 29
PYTHONHASHSEED=17 python3 -m flagship_controller.common_state_study execute \
  runs/new-common-development --upstream /absolute/path/to/pinned/ToG
python3 -m flagship_controller.common_state_audit runs/new-common-development
python3 scripts/summarize_common_study.py runs/new-common-development \
  /evaluation-account-only/webqsp/evaluation-only.jsonl
```

Only the final command reads labels, offline under the evaluation account. The runtime account must not read them. The default model and graph endpoints are loopback. The harness checks model digest/context/threads and pinned upstream source before execution. Obtain upstream separately; no embedding/model download or paid API is needed.

Restore a frozen runtime using `scripts/materialize_common_study.py STUDY NEW_DIRECTORY`, then freeze a **new** run from that isolated source and the archived question-only inputs. Never overwrite original outputs to reproduce them. The earlier common-state-dev-001 is an unexecuted plan superseded before inference; its original snapshots are retained. Existing baseline versions restore separately with `materialize_baseline_runtime.py`.

## Evidence still required

The live mechanics cohort has three existing development question strings: one official training question, an inverse control and a fictional-entity control. Across five policies and two seeds that is30 executions, not30 independent examples or a benchmark comparison. Handwritten controls are unscored. A result on one official original cannot establish superiority or a population interval.

Independent semantic/native review remains uncollected. The100-question study needs a new executable freeze after development/review, with an outcome-independent annotation plan and an appropriate sample-size justification. Seed43 is implemented but not a third live replication in this check. STOP/recovery rates remain unavailable without independently accepted, budget-feasible continuations. Public release, licensing/contributions and submission remain later review steps.

## Optional directed-role audit development revision

`freeze --directed-audit` prospectively enables an explanatory subject/predicate/object variable-role representation inside the existing semantic audit request. For example, an incoming parents traversal is rendered as `answer -> parents -> anchor0`; outgoing is `anchor0 -> parents -> answer`. This adds no facts, gold feedback, kinship-specific rule, extra model call or independent verifier. It applies to all supported program/constraint orientations. The default remains the historical audit, preserving old replay behavior. Gate-off skips this added input along with the final audit. Results, false acceptance and false rejection require separate development checks. [Frozen direction check](../results/common-state-dev-004/manifest.json).

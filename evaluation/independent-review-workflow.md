# Collect and validate independent semantic review

The 30-case pack remains **unannotated; zero independent reviewers completed**. The validator is implemented, not evidence that anyone reviewed the cases. Do not modify the original blank pack or treat its default unknown fields as labels.

Give only the `reviewer/` directory to two qualified reviewers in separate copies. Keep `owner-key.json`, model critiques, gold annotations, policy names and scores private until first-pass submissions are returned. Do not share this repository as a substitute: it reveals policies and scores. No reviewer has been contacted by this work. Behavior can reveal policy despite masking; correlated cases must not be counted as independent questions.

Each person supplies a separate JSON file with `reviewer_id`, `qualification_statement`, `independence_statement`, `independence_attested: true`, timezone-bearing `completed_at`, `cases_sha256` and `judgments`. Each judgment contains `case_id` and `dimensions`; every dimension (`anchor_identity`, `query_meaning`, `answer_scope`, `witness_support`) contains a `label` and written `reason`. Labels are `supported`, `contradicted` or `unknown`. Explicit unknown with a reason is a valid reviewed judgment; an untouched blank form is not. Each submission covers every case exactly once and retains the original pack hash.

Once actual submissions arrive, the owner runs:

```sh
python3 -m flagship_controller.review_assessment \
  --pack /absolute/path/reviewer/cases.jsonl \
  --reviews /absolute/path/reviewer-one.json /absolute/path/reviewer-two.json
```

The tool refuses pack mismatches, duplicate/missing cases, missing reasons and non-distinct reviewer IDs. Qualifications and independence are self-attested metadata; software cannot certify them. It reports raw three-category agreement, Cohen's kappa where defined, joint-known counts/agreement and cases requiring adjudication. Shared unknown can inflate raw agreement; kappa is undefined when expected agreement is1. These are descriptive statistics, not semantic accuracy or population confidence intervals.

Preserve first-pass files, then obtain a separate adjudication record for disagreements with provenance and reasons. Counterfactual stopping/recovery needs full state, a demonstrated continuation within the original remaining budget and independent acceptance. This compact review workflow does not validate that counterfactual or compute STOP/recovery rates. Those remain NA until their separate evidence exists. Review contents are data, never instructions to the runtime.

# Collect and validate independent semantic review

The 30-case pack remains **unannotated; zero independent reviewers completed**. The validator is implemented, not evidence that anyone reviewed the cases. Do not modify the original blank pack or treat its default unknown fields as labels.

A [reviewer brief](reviewer-brief.txt) and tested local delivery exporter are now available. The exporter includes only `README.txt`, unchanged `cases.jsonl`, blank `submission-template.json`, `BRIEF.txt` and a hash manifest; no recursive parent-folder archive is made. The prepared [delivery manifest](review-delivery-manifest.json) records30 cases and the original pack hash. The ZIP is kept locally outside the repository. This prepares a handoff without contacting anyone. The existing cases concern earlier structured development runs; they do not certify the newest baseline or reserved evaluation. No real submissions have been collected.

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

## Native-output addendum

`flagship_controller.native_review_pack` prepares a separate versioned review pack from complete baseline runs, including failures and missing native text. It withholds policy names, scores and extractor critiques but retains the full native response, observations and projected IDs. Add `projection_faithfulness` to the four semantic dimensions: whether all explicit native answer conclusions are preserved without invented IDs, dropped conclusions or context-only names. Witness support reviews all substantive native assertions, including extra unsupported inferences. Missing native text remains unknown with a reason. Masking remains imperfect.

Use `--native` with `review_delivery` to export the five-dimension blank form and with `review_assessment` to validate actual returned submissions. The original30-case pack and its four-dimension assessment are unchanged. No software-generated defaults count as independent annotation.

The prepared native addendum now contains15 unannotated records from runs001–003. [Case-pack status and hash](native-review-pack-status.json), [delivery archive/file hashes](native-review-delivery-manifest.json). The original30-case pack remains unchanged. Both local handoffs are ready for the owner to provide separately to two qualified independent reviewers; no contact or completed review is implied.

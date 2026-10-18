# What the owner can review

17 October 2026. The owner offered to review the research. No review has yet been received. Author review is useful for catching mistakes and confirming that the manuscript represents the work, but is reported separately from independent semantic evaluation.

The local `outputs/author-review-2026-10-17/author-review.html` worksheet contains all30 outcomes from the latest six-string development comparison. Open it in a browser. It shows the question, condition, answers with available observed names, programs, complete witnesses and graph observations. There are no benchmark scores or suggested judgments. Conditions are visible: this is explicitly unmasked author review. Only up to five returned answers have name cards; do not infer the meaning of other IDs without evidence.

For each case you can judge, choose supported, contradicted or unknown and explain:

1. Are the intended people/places and named constraints represented?
2. Does the query mean what the question asks, including relationship direction?
3. Does the returned set have the right type and complete scope?
4. Is each emitted answer consistently supported by the recorded evidence?

An edge can be real while answering the wrong relation. An empty output is not automatically necessary or correct. “Unknown” with a reason is useful; a blank form is not an annotation. No STOP or recovery rate is established by these judgments alone.

Complete any cases you can assess, enter your name/alias and download the JSON. The page sends nothing to a server and does not preserve unsaved edits; export before closing. Return the downloaded file, or give the case IDs, four judgments and reasons in chat. The author validator permits partial review and reports how many of30 cases are actually reviewed. It always records zero independent reviewers.

```sh
python3 -m flagship_controller.author_review validate /LOCAL/cases.json /LOCAL/flagship-author-review.json
```

Do not edit the source hash, relabel this as independent review or turn on an independence attestation. Real reviewer identities and returned author judgments stay outside the public repository unless the owner separately requests publication. The worksheet is preparation; it is not approval of correctness or submission readiness.

Independent review serves a different claim: two qualified people not involved in creating/selecting these outputs assess a masked, prospectively sampled pack independently, with disagreements and unknowns reported. That is our study design, not a universal rule that journals require two external approvals before submission. Objective benchmark collection can continue while those judgments are pending.

## Supplementary automated review — 18 October 2026

The owner subsequently requested GPT-filled results. A separate local `gpt-review.html` and `gpt-review.json` contain 30 automated case assessments, four dimensions each. The original author worksheet is unchanged. The [archived GPT review](../paper/gpt-review-boundary.md) is explicitly automated and unmasked; no author or independent human judgments have been received. Its labels must not be imported as human submissions or used to alter the executing frozen benchmark.

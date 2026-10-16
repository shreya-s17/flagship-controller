# Publication route and submission gate — checked 15 October 2026

**Current decision: retain an internal technical report. Provisional future target: TMLR, only after the scientific gates below pass.** No submission, public preprint, authorship confirmation or acceptance is claimed. A working prototype or a few development answers is insufficient evidence for a final paper.

| Option | Fit and status | Deadline / review timing | Format and publication status |
|---|---|---|---|
| TMLR | Potential fit for a technically sound, adequately supported empirical study. Broad component integration alone is not a defensible contribution. Current study is not ready. | Rolling, year-round submission. FAQ aims for approximately nine weeks, without guarantee; there is no fixed conference cutoff to rush toward. | Anonymized TMLR template; length justified by content. Peer-reviewed journal publication requires acceptance. [Author guide](https://jmlr.org/tmlr/author-guide.html), [FAQ](https://jmlr.org/tmlr/faq.html), [acceptance criteria](https://jmlr.org/tmlr/acceptance-criteria.html). |
| ICLR 2027 main conference | Relevant to reasoning/control, but this cycle is closed and the present evidence is insufficient. | Abstract 18 September 2026; full paper 25 September 2026 AoE, both past. | Anonymous ICLR template, nine-page main text at submission. Main-conference publication cannot be claimed without acceptance. [Official author guide](https://iclr.cc/Conferences/2027/AuthorGuidelines). |
| NeurIPS 2026 main conference | Reasoning/control and rigorous analysis fit the broad scope; this cycle is closed. A small development diagnostic is not a completed research contribution. | Abstract 4 May 2026; full paper 6 May 2026 AoE; notification 24 September 2026, all past. | Official conference template and handbook; main-track review/publication route. [Official CFP](https://neurips.cc/Conferences/2026/CallForPapers). |

This is a planning comparison, not evidence that TMLR will accept the work. Workshop CFPs differ by organizer; no generic workshop deadline or archival status is assumed. Recheck the chosen venue's official policies at the actual submission date.

## Checklist before a future TMLR submission

1. Establish a precise, literature-supported contribution or a sufficiently broad and informative negative empirical result. Constrained generation and feedback-based correction have precedents; no integration novelty is presumed.
2. Finish question-only parsing/linking evaluation, prospectively frozen control comparisons and independent failure/support audits. Include all selected questions, abstentions and negative outcomes. Reserve official test outcomes for the frozen final method.
3. Reproduce or carefully adapt an external named baseline with source/version/input/model/metric differences disclosed. The internal fixed control is not a ToG reproduction.
4. Audit graph snapshot compatibility, scoring semantics, overlap and evidence access; publish actual inference/retrieval costs and uncertainty intervals with appropriate scope.
5. Resolve semantic false acceptance, answer-set scope errors, recovery eligibility and STOP labels. If a metric is unavailable, narrow the paper's claims instead of filling it with zero.
6. Assemble the manuscript, complete source/config/data-intake commands, manifests, raw evidence and limitations. Run a clean reproduction and have the owner verify each result, citation and claimed personal contribution.
7. Confirm authors, affiliations, conflicts, funding and required disclosures; prepare an anonymized submission artifact and supplements. Publication licensing and external uploads require the authors' explicit action-time decision.
8. Check current venue policies, duplicate-submission restrictions, template and submission account requirements. Obtain final approval for the concrete reviewed manuscript before submission.

Safe application status now: “Research prototype and internal technical-report draft; experiments ongoing.” Do not write “submitted,” “under review,” “accepted,” “published,” or “public preprint.”

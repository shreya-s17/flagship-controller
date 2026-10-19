# When graph support is not answer correctness: controlled diagnostics of bounded repair in knowledge-graph question answering

Anonymous manuscript. Evidence cutoff: 19 October 2026. Completed diagnostic experiments and the frozen 100-question training-reservation comparison.

## Abstract

Knowledge-graph evidence can support a returned entity without supporting the question the user asked. We study this distinction using an instrumented question-only system that selects restricted query programs, records witnesses and permits one failure-triggered revision. In a ten-question pilot, replaying identical starting states removes an apparent fixed-versus-repair difference: both controls obtain macro F1 of 0.40, while repair adds 16.48% charged tokens. A subsequent prospectively frozen comparison retains all 1,800 outcomes from 100 reserved training questions, three seeds and six conditions. Full repair obtains macro F1 of 0.1676 versus 0.1533 for fixed control, with a paired difference of 0.0142 and a descriptive question-bootstrap interval of approximately [0.0000, 0.0393]. Repair charges 14.31% more tokens; a local Think-on-Graph adaptation obtains higher F1 of 0.2299. Failure-informed development controls separate catalog availability from relation direction. All 479 answered internal-control records in the larger study pass recorded-witness consistency checks, which do not establish semantic correctness. A separate finite interpreter identifies guard counterexamples in 67,696 program/world combinations. These results characterize bounded repair's failures and modest observed gains without establishing general superiority, calibrated reliability or semantic accuracy. We argue for separating execution integrity, graph support, question meaning and benchmark agreement.

## 1. Introduction

Knowledge-graph question answering couples linguistic interpretation to a structured evidence source. Graph-backed language-model agents can expose reasoning paths and inspect relations instead of relying entirely on parametric recall. Think-on-Graph is an example of this interaction pattern [1]. However, returning a graph-supported path does not establish that the path expresses the intended relation, that all question constraints are enforced, or that the returned set is complete.

Consider a question asking for a person's parents. Traversing a parent predicate in the wrong direction can return their children with perfectly valid graph witnesses. Likewise, a list associated with a city can contain genuine attractions without implementing a downtown restriction. These are failures of alignment between a question and an executed program, rather than necessarily missing or fabricated edges. A verifier that checks only edge existence cannot distinguish them.

Repair introduces a second attribution problem. An apparent difference between fixed and repair policies may arise before the repair decision, through parsing, entity linking or candidate construction. Conversely, a later answer improvement can be caused by expanding the available program catalog rather than by the mechanism that rejects an earlier choice. Comparing only terminal answers can obscure both distinctions.

We study these problems through a restricted, auditable prototype rather than proposing a new general reasoning algorithm. Our finished experiments comprise a synthetic component study, a ten-question live comparison and identical-prefix diagnostic, a finite guard audit, a nested catalog-by-guard development comparison, and a prospectively frozen 100-question training-reservation comparison. We preserve negative outcomes and distinguish original questions from handwritten controls. The contribution is an empirical and executable account of how to localize failures in a bounded graph-reasoning system.

Three findings motivate the study. First, repair produces no exact-answer improvement on the ten-question shared-prefix diagnostic and adds measured cost. Second, narrow semantic guards and catalog expansion address different bottlenecks in inspected cases. Third, neither structural witness checks nor necessary relational guards certify full question meaning. The finite interpreter supplies explicit counterexamples, while the live traces demonstrate why these distinctions matter in an operational system.

The paper makes no claim of a novel learned policy, calibrated semantic confidence or general superiority. The completed larger comparison shows a small numerical advantage for full repair over fixed control, with increased charged cost and lower F1 than the local ToG adaptation. It is a training-reservation feasibility study, not official-test performance. The results support a diagnostic account and a bounded comparative observation; broader claims require additional evidence.

## 2. Related work

Graph-guided language-model reasoning is established prior work. Think-on-Graph iteratively explores graph entities and relations using an LLM-guided search procedure [1]. CoG combines relational blueprints with failure-aware refinement [2], while Chain-of-Relations emphasizes relation-centric exploration and global filtering [3]. These mechanisms overlap the general ideas of guidance, verification and backtracking. Our implementation differences and diagnostics do not establish algorithmic novelty relative to them.

Formal-language constraints address a different guarantee. PICARD rejects inadmissible continuations through incremental parsing in semantic generation [4]. Our finite typed-program catalog similarly limits the representable output space, but it does not implement PICARD or make semantic equivalence follow from syntactic admissibility. A well-formed, executable query can still encode the wrong question.

Feedback-driven retrieval and correction also extend beyond the present system. LCR-RAG uses logical feedback within a learned query-revision framework [5]. Here, revision is training-free, limited to a bounded catalog and dependent on hand-designed checks and the same model that proposes programs. We do not equate this control with a learned correction policy.

WebQuestionsSP provides semantic parses and an official answer-set evaluator for knowledge-base question answering [6]. We use its evaluation semantics while keeping annotated parses and answers outside inference. Benchmark agreement is an operational target; it is not an independent assessment of the historical truth of every graph statement or the only reasonable interpretation of an ambiguous question.

## 3. System and controls

### 3.1 Question-only input and bounded programs

The live system receives a raw question, an identifier and a split tag. It has no access to gold topic entities, annotated paths or answers. A parser proposes copied mentions, answer types and question obligations. Entity linking checks graph-native keys against observed names or aliases and uses bounded fallback matching. Ambiguous links are resolved from available evidence rather than by silently selecting the first identifier.

The graph backend is a restored Freebase archive [7]. The system observes relation inventories and type metadata, then constructs a catalog of restricted one- or two-hop programs with equality joins to named anchors. The active catalog has at most 20 entries, drawn through bounded root and child-relation selection. A compiler validates identifiers, directions and join indices before producing SPARQL queries [8]. It does not execute arbitrary SPARQL supplied by the model.

Each accepted answer is associated with recorded query rows and provenance-bearing witness triples. A sentinel-row convention and query-status checks detect declared truncation or incomplete execution. These checks establish consistency with bounded observations; they do not prove completeness of the knowledge base or truth outside the snapshot.

### 3.2 Fixed selection, bounded repair and semantic guards

The fixed control chooses one catalog program. The repair control may reject a first choice, mask the rejected program and choose once more, optionally using graph-observed join information after a failed constrained query. No gold feedback enters this decision. A changed program, an additional attempt and an independently acceptable recovery are distinct events.

All compared live controls retain compiler, type, witness and resource checks. A same-model semantic gate additionally inspects the question, program, inferred obligations, counts and a limited sample of answer values and witnesses. The gate sees at most five answer values and two witness rows; it is not a full-row semantic audit and is not independently calibrated.

The later development revision adds closed checks for copied kinship roles and primary-anchor membership. For a parent request, an outward parents relation and an inward children relation are allowed bindings; the directions reverse for a child request. A city-membership obligation requires an observed containment join back to the primary city. These are necessary conditions within declared ontology and language conventions, not complete semantic specifications.

### 3.3 Separate catalog and guard interventions

We denote expanded observed containment candidates by C1 and the preserved schema-only catalog by C0. G1 enables the closed-obligation check and pruning of incompatible revision candidates; G0 disables only that intervention. Both guard conditions retain the other checks, including the same-model semantic gate.

The diagnostic compares repair-C0G0, repair-C0G1, repair-C1G0, repair-C1G1 and fixed-C1G1. A common capture fixes parsing, linking, root observations and schema before catalog construction. Each catalog condition separately captures its first program choice; paired guard arms replay that mode-specific state. The fixed and repair C1G1 conditions share the expanded catalog and first choice. Exact provider payloads, responses and graph observations are audited, rather than inferring state equality from configuration alone.

### 3.4 Resource and evidence accounting

The live admission limits are 10 model calls, 16,000 returned usage tokens, 80 graph calls and 100 rows per query. Model and graph request timeouts are 120 and 30 seconds; the wall-time admission threshold is 600 seconds. The model context is 4,096 tokens, with a 3,000-observed-input-token guard. Some checks occur after a response is charged, so these limits are not exact pre-call billing or hard wall-clock guarantees.

Shared-prefix work is charged to every policy that depends on it. Physical execution counts are reported separately from replay charges. Incomplete usage is marked as unknown or lower-bound; it is not silently replaced by a complete zero-cost event. Constructed prefix-plus-continuation elapsed time is not fresh end-to-end timing.

## 4. Experimental design

### 4.1 Data, model and graph setting

The completed live studies use training questions from WebQuestionsSP [6]. The first ten-question comparison uses the next ten questions in an existing intake order, distinct from five earlier software-development examples. The identical-prefix diagnostic reuses those same ten questions. The later factorial diagnostic uses six strings: three already inspected official originals and three handwritten controls. Those controls have no invented benchmark gold answers, and the six strings are not an independent test sample.

Inference uses CPU-only Qwen2.5-7B-Instruct with Q4_K_M quantization [9], through Ollama 0.40.4, four threads, temperature zero and seed 17 for the pilot and development comparisons. The larger frozen comparison uses seeds 17, 29 and 43. The server has an i7-7700 CPU and approximately 62 GiB RAM. The deployed model digest, archive hash, executable version and frozen source manifests are retained in the artifact.

The prepared Freebase database is served by Virtuoso 7.2.5.3229. The archive's original snapshot date and equivalence to WebQuestionsSP's reference snapshot remain unverified. No graph augmentation from gold answers is used. This unresolved setting difference restricts comparison with published benchmark scores.

### 4.2 Metrics and comparison units

We follow the official evaluator's question-quality admission and best-F1-over-parses conventions. All selected predictions are submitted; scorable exclusions are separate from method failures. Macro F1 and exact-answer counts include abstentions in the selected scorable denominator. The ten-question pilot bootstrap uses 10,000 question-paired resamples and seed 17 [10]. The larger comparison follows its prospectively frozen analysis: average the three seeds within each question, then bootstrap paired question units 10,000 times with analysis seed 113. These intervals describe the selected cohorts, not a power guarantee or population-generalization claim.

We separately report answer coverage, charged returned tokens, model and graph calls, witness-row consistency, and post-run triple presence. Neither exact benchmark matching nor triple presence is called semantic accuracy. Live early/late stopping and certified recovery rates are unavailable because independently accepted budget-feasible continuation labels have not been collected.

### 4.3 Synthetic and finite specifications

The synthetic component engine receives declared start entities, relation sequences and type obligations. It is separate from natural-language parsing and linking. Sixteen component combinations are evaluated on 350 shared scenarios; selected contrasts are reported with their full denominators. A separately implemented finite evaluator supplies fixture truth. No live token-saving claim is derived from these zero-model-token fixtures.

The finite guard audit evaluates 67,696 guard/program/world combinations and 33 handwritten grammar contracts. It includes arbitrary small inverse-consistent kinship worlds and synthetic city/downtown sets. Some worlds are biologically impossible and some compiler-representable programs are absent from the active catalog. The audit isolates guard behavior rather than simulating the model, type checks or complete live pipeline. Counts are controlled counterexamples, not natural-world error frequencies.

### 4.4 Frozen larger comparison

Before the first reserved request, the plan fixed the exact bytes of 100 pre-reserved training questions, all 1,800 outcomes, three seeds, six conditions, scheduling seed 113, 15 inference modules and five offline-analysis sources. Conditions are the five catalog/guard controls and the pinned declared-JSON local ToG adaptation. The adaptation uses the same local model and shared question-only linking, but receives no controller catalog; it is not a reproduction of published ToG scores. Within each question/seed, condition order is randomized prospectively. Prefix observations and actual provider requests are audited.

All 100 selected questions are scorable under the official evaluator; no question is excluded. Parse, linking, unsupported-language, budget, truncation and answer-normalization failures remain in the full denominator as abstentions. The primary endpoint is repair-C1G1 minus fixed-C1G1 question-mean F1. Secondary catalog/guard contrasts are descriptive. The plan does not tune or selectively retry a condition after inspecting reserved outcomes. Collection finishes before scoring and post-run checks. No official-test run or independent human semantic judgment enters these results.

## 5. Results

### 5.1 Synthetic components expose distinct guarantees

*Synthetic component study. Each row uses the same 350 scenarios; rows are correlated. Bit order: acquisition, verification, recovery, STOP. Expansions are not live model tokens.*

| Variant | Grounded / scenarios | Unsupported / answered | Mean expansions |
| --- | --- | --- | --- |
| Full (1111) | 210 / 350 | 0 / 210 | 3.126 |
| Acquisition off (0111) | 210 / 350 | 0 / 210 | 3.126 |
| Verifier off (1011) | 210 / 350 | 90 / 300 | 3.217 |
| Recovery off (1101) | 92 / 350 | 0 / 92 | 2.080 |
| STOP off (1110) | 210 / 350 | 0 / 210 | 3.503 |
| Verified fixed order (0110) | 210 / 350 | 0 / 210 | 3.503 |


Acquisition-on and acquisition-off have the same grounded yield and mean expansions in this fixture family. Thus this study supplies no adaptive-acquisition advantage. Removing verification raises answer coverage but introduces 90 unsupported outputs among 300 emitted answers. Removing recovery reduces grounded yield from 210 to 92, but it also changes search expenditure; this is not evidence of matched-cost recovery superiority. Disabling STOP increases mean expansions from 3.126 to 3.503 without improving yield. These are fixture-level mechanism checks, not token or wall-time gains for a language-model agent.

### 5.2 Shared starting states remove an apparent live difference

*Completed ten-question live comparison. The shared-prefix rows reuse the same ten questions, not an additional sample. Tokens/calls are charged work; replay time is not fresh end-to-end latency.*

| Execution/control | Macro F1 | Exact | Answered | Tokens | Model calls | Graph calls |
| --- | --- | --- | --- | --- | --- | --- |
| Separate fixed | 0.40 | 4 / 10 | 6 / 10 | 21,056 | 34 | 63 |
| Separate repair | 0.30 | 3 / 10 | 5 / 10 | 22,329 | 35 | 61 |
| Shared prefix fixed | 0.40 | 4 / 10 | 6 / 10 | 21,056 | 34 | 63 |
| Shared prefix repair | 0.40 | 4 / 10 | 6 / 10 | 24,527 | 38 | 65 |


The separately executed comparison gives repair-minus-fixed F1 of -0.10, with a descriptive percentile interval of [-0.30, 0.00]. Inspection localizes the sole exact-answer difference to an Eli Whitney mention-parsing failure in repair before a program exists. A common temperature and seed therefore did not establish a common starting state.

Replaying every fixed prefix, without selecting by score, reproduces all ten terminals, answer sets, witnesses and counters. Repair from those same states obtains the same F1 and exact count as fixed, but adds 3,471 charged tokens, four model calls and two graph calls. The token increase is 16.48%, and no additional exact answer follows rejection of a first program. All paired F1 differences are zero; a degenerate [0,0] bootstrap interval describes these cases only. This negative result concerns the implemented repair rule and its bounded candidate space, not all possible repair policies.

### 5.3 Catalog availability and role checking solve different development failures

*Five-condition development comparison: six reused strings, three scored originals and three unscored handwritten controls, 30 total outcomes. Score columns cover the three originals; token totals cover all six strings. These are not held-out gains.*

| Condition | Macro F1 | Exact originals | Answered originals | Tokens, all six |
| --- | --- | --- | --- | --- |
| repair-C0G0 | 0.596491 | 1 / 3 | 3 / 3 | 18,723 |
| repair-C0G1 | 0.666667 | 2 / 3 | 2 / 3 | 16,415 |
| repair-C1G0 | 0.666667 | 2 / 3 | 3 / 3 | 19,637 |
| repair-C1G1 | 1.000000 | 3 / 3 | 3 / 3 | 20,656 |
| fixed-C1G1 | 0.666667 | 2 / 3 | 2 / 3 | 16,154 |


All 30 planned outcomes complete. Only the three official originals receive benchmark scores; the handwritten controls remain unscored. Guarded repair changes a reversed kinship binding. The expanded catalog supplies a primary-city membership program that the schema-only catalog lacks; enabling the membership guard without that expansion exhausts the Chicago catalog. A gold-free reconstruction of the earlier captured states finds zero versus two rule-compatible Chicago candidates before and after expansion, with two old entries displaced at the catalog cap. Compatibility is an availability diagnostic, not a correctness label.

Combined C1G1 repair matches all three inspected official answer sets, while fixed C1G1 matches two. This is development evidence after failure inspection. The kinship revision has one admissible remaining candidate, so the result is constraint enforcement rather than demonstrated learned selection among multiple feasible repairs. The observed effects are conditional on the captured roots and schema; they do not establish population gain or generalize beyond the closed language family.

The five conditions together require 55 physical model attempts and 174 graph calls. Charged totals differ by method because shared prefixes and realized continuations differ. These totals are not a matched-compute frontier or a speed comparison.

### 5.4 Necessary guards admit and reject semantic counterexamples

*Selected finite counterexamples. Counts are per declared family, overlap across families and are not independent question samples or natural-world error rates.*

| Program family | Worlds per family | Failure characterized | Count per family |
| --- | --- | --- | --- |
| Correct-role identity extension | 4,096 | Equivalent nonempty answer rejected | 3,584 |
| Correct-role endpoint filter | 4,096 | Allowed direction omits valid answers | 1,536 |
| City membership for downtown | 216 | Allowed city set exceeds downtown target | 91 |
| City membership plus filter | 216 | Allowed program omits city answers | 40 |


Canonical role and containment bindings satisfy the finite specifications. Nevertheless, a one-hop whitelist rejects equivalent identity-extended programs, and an allowed direction can coexist with an extra filter that drops valid answers. City membership also admits sets broader than the synthetic downtown target. These counterexamples show that local necessary conditions are not sufficient for all-and-only answer semantics. The counts overlap across declared program families and must not be aggregated into a semantic failure rate.

### 5.5 Witness integrity and benchmark correctness remain separate

All 25 answered factorial records pass the recorded-row witness audit. Post-run requery finds all 77 unique accepted witness triples present, with no missing or unknown requery result. Those triples include evidence from incorrect reverse-role and broad-scope controls. The same integrity result therefore cannot certify the intended relationship or answer scope.

An unmasked GPT review of the 30 development outcomes supplies 120 qualitative judgments with explicit reasons and retained unknowns. The assistant saw policy names and earlier outcomes and had helped develop the artifact; exact model version was not recorded. It is supplementary automated error analysis, not independent human annotation or a calibrated semantic evaluator. A museum account disputes some Whitney invention attributions in the graph [11], illustrating a further distinction between benchmark agreement and external historical claims. No official label or reported score was changed by this review.

### 5.6 Completed frozen training-reservation comparison

*Completed frozen training-reservation comparison: 100 questions, three seeds, six conditions, all 1,800 outcomes retained. All 100 questions are scorable with zero exclusions. Macro F1 averages seeds within question; exact and answer counts pool 300 repeated outcomes per condition, not 300 independent questions.*

| Condition | Macro F1 | Exact / outcomes | Answered / outcomes |
| --- | --- | --- | --- |
| repair-C0G0 | 0.1709 | 51 / 300 | 99 / 300 |
| repair-C0G1 | 0.1642 | 49 / 300 | 100 / 300 |
| repair-C1G0 | 0.1642 | 49 / 300 | 99 / 300 |
| repair-C1G1 | 0.1676 | 50 / 300 | 101 / 300 |
| fixed-C1G1 | 0.1533 | 46 / 300 | 80 / 300 |
| ToG adaptation | 0.2299 | 49 / 300 | 150 / 300 |


All 1,800 planned outcomes complete and pass the source, request, shared-state, order and usage ledger audit. Full repair obtains macro F1 of 0.1676 and fixed control 0.1533. The predeclared paired difference is 0.014224, with a 10,000-resample question-bootstrap interval reported as [0.0000, 0.0393]. The raw lower percentile is 1.04e-42 because the official evaluator initializes true positives with 1e-40. We retain that frozen value in the analysis record and display it as zero at the reported precision; this residue is not evidence of a practically positive lower bound. No confirmatory significance or minimum-effect claim is made.

Three question-level differences exceed a numerical tolerance of 1e-12, all positive; the remaining 97 lie within that tolerance. This describes concentration of the observed gain, without changing official scores or their denominator. Pooled exact-answer counts increase from 46 to 50 across 300 repeated condition outcomes; answered counts increase from 80 to 101. Those are not four additional independent questions or independently certified recoveries.

The local ToG adaptation has the highest observed macro F1, 0.2299, and answers 150/300 outcomes. Its exact count is 49/300, compared with 50/300 for full repair and 51/300 for repair-C0G0. Higher projected-ID F1 and coverage therefore do not mean superiority on every metric or certify native-answer semantics. No comparison to published benchmark scores or statistical baseline-superiority test is claimed.

The secondary guard effect is -0.0067 F1 with C0 and +0.0033 with C1; catalog effects have the same respective values at G0 and G1. The descriptive interaction is +0.0100. These mixed effects do not support a uniform benefit from adding the catalog or guard. They remain conditional on the captured roots, schema and bounded program family, with no multiplicity-adjusted inference.

*Charged resources for each condition across its 300 outcomes. Shared-prefix work is charged to every dependent condition. All usage records are complete; totals are not matched realized compute or fresh latency.*

| Condition | Returned tokens | Model calls | Graph calls |
| --- | --- | --- | --- |
| repair-C0G0 | 599,658 | 905 | 2,721 |
| repair-C0G1 | 604,761 | 908 | 2,726 |
| repair-C1G0 | 605,118 | 909 | 2,727 |
| repair-C1G1 | 601,110 | 905 | 2,722 |
| fixed-C1G1 | 525,869 | 815 | 2,582 |
| ToG adaptation | 599,785 | 1,268 | 4,352 |


Full repair charges 601,110 tokens versus 525,869 for fixed control, an increase of 75,241 tokens or 14.31%. All usage records are complete, with zero unknown-usage outcomes. Across the physical experiment, common captures occur 300 times and catalog captures 600 times; deduplicated totals are 2,830 model attempts and 8,395 graph calls. Summed physical-stage duration is 67,071.39 seconds, separate from charged prefix-plus-continuation time. These totals do not establish matched-compute or fresh-latency efficiency.

The recorded-witness audit covers all 1,500 internal-control records, including 479 answered records, and passes their program/row consistency checks. The 300 native baseline records use a different representation and are excluded from that audit. No new independent semantic judgment or full larger-run constant-triple requery is inferred from this result. Low coverage remains material: full repair answers 33.67% and fixed control 26.67% of their selected outcomes. Their answer-type/catalog mismatch terminal counts are 74 and 56 of 300, respectively; these terminal labels describe retained failures, not independently determined root causes.

## 6. Discussion

The completed studies support three practical evaluation lessons. First, locate where compared policies diverge before attributing a difference to repair. In the ten-question study, the apparent repair deficit disappears under exact prefix replay, while the extra resource charge remains. Shared configuration alone is insufficient; comparable evidence requires inspecting actual requests, responses and graph states.

Second, diagnose whether a suitable program is available before expanding revision effort. Pruning cannot select a missing program. The Chicago diagnostic separates catalog construction from guard enforcement, while the kinship case demonstrates how a closed directional obligation can constrain an already available candidate. These mechanisms should be ablated separately and their claims should remain conditional on the observed candidate space.

Third, report a hierarchy of evidence rather than collapsing it into a single correctness flag. Execution validity asks whether the program is well formed and the query completed. Witness integrity asks whether emitted IDs are consistent with recorded graph evidence. Semantic alignment asks whether the program and answer set satisfy the question. Benchmark agreement asks whether an evaluator matches an annotated answer set. External truth can disagree with the graph or with a benchmark convention. Passing an earlier layer does not establish the later ones.

These distinctions suggest concrete design targets: scope-aware obligations, complete witness inspection where feasible, explicit handling of missing context, and independent assessment of claims that depend on semantic judgments. Our experiments motivate those targets but do not validate a new general verifier or a reward function. The contribution is the documented failure localization, executable counterexamples and frozen comparative evidence. The ten-question negative result and larger cohort's modest positive difference concern different selected cohorts; the latter does not erase the former or establish a generally superior policy. In the larger cohort, higher ToG-adaptation F1 and mixed catalog/guard effects constrain the claim further.

## 7. Limitations

The live cohorts are limited and drawn from training data, including the 100-question frozen reservation. The later three scored originals are reused after error inspection; handwritten controls are correlated and unscored. Neither the factorial F1 of 1.0 nor repeated condition counts imply held-out accuracy. Pretraining contamination, semantic overlap across questions and broader question-family dependence are unresolved.

Only one quantized local model and one prepared graph setting are used. The graph snapshot is not certified equivalent to the benchmark reference, and we have not completed a gold-query answer-availability diagnostic. The bounded grammar excludes valid language and query structures; types, lexical priors and closed operator rules can fail before selection. Some finite countermodels exercise programs outside the current catalog and therefore characterize guard limits rather than observed end-to-end error rates.

The final semantic gate is the same model used for proposal, operates on limited samples and has no calibration evidence. No independent human semantic or continuation judgments are reported in this version. The GPT supplement is exposed to prior context and cannot fill that gap. Live STOP/recovery rates are not identifiable from abstentions, caps or an extra attempt alone. We make no claim about agent transfer or general autonomous planning.

The internal fixed control is not an external published-method baseline. The larger comparison includes the pinned local ToG adaptation, but its implementation and model departures prevent treating it as reproduction of the original paper. Native assertions have not received independent semantic evaluation; only declared projected IDs are scored. No published score is ranked against these measurements. Unequal realized compute, cached prefixes and constructed elapsed times preclude a general efficiency claim.

The completed frozen comparison covers one pre-reserved training cohort, one local model and one graph setting. Its three seeds are averaged within question, and related questions need not be semantically independent. The primary interval is descriptive and its near-zero lower endpoint depends on the selected sample and official evaluator conventions. The five secondary contrasts have no multiplicity-adjusted interpretation. No official-test result, multi-model replication, calibrated semantic reliability or general agent-transfer claim is established.

## 8. Conclusion

An executable graph path is not sufficient evidence that a question has been answered correctly. In the completed ten-question diagnostic, common-prefix replay removes an apparent fixed-versus-repair difference while bounded repair adds cost without recovering another exact answer. The later development controls separate candidate availability from directional checking, and finite countermodels expose the limits of necessary guards. Even complete recorded witnesses and successful triple requery coexist with wrong question meanings. Reliable evaluation should therefore preserve full denominators, inspect the actual shared state, distinguish catalog changes from policy effects, and keep graph support, semantic alignment and benchmark agreement separate. In the completed 100-question comparison, full repair has a small numerical F1 advantage over fixed control at higher charged token cost, while the local ToG adaptation attains higher macro F1. The evidence supports bounded diagnostic and cohort-specific comparative conclusions; general performance and calibrated semantic reliability remain unestablished.

## Reproducibility and assistance disclosure

The artifact retains frozen inputs, policy sources, model/graph identifiers, journaled requests and responses, failures, official-semantics scoring and independent structural audit implementations. A clean source archive passes 239 software tests and restores 526 historical evidence files; those software counts are not scientific sample sizes. The larger experiment retains 7,220 files in a checked private archive, and its full frozen analysis and seven derived report files reproduce exactly after restoration. The paper's tables are generated from the retained summary/analysis records and a separate manifest binds their source hashes. The live inference account cannot read evaluation annotations.

Codex assisted implementation, debugging, tests, analysis tooling and manuscript preparation. Its qualitative development review is explicitly automated and non-independent. No independent human review is reported. Author information and required funding, conflict-of-interest and contribution declarations are supplied separately by the human authors.

## Appendix A. Artifact map and replay boundary

The synthetic summary is `results/synthetic-v2/summary.json`. The separately executed and identical-prefix comparisons are `results/paired-pilot-001/analysis.json` and `results/paired-pilot-002-shared-prefix/analysis.json`. The five-condition diagnostic is `results/factorial-dev-001/development-score.json`, with its nested ledger, witness audit and constant-triple requery in the same directory. The finite interpreter report is `results/closed-guard-stress-001/report.json`; the captured catalog diagnostic is `results/catalog-contrast-001/report.json`. The GPT judgments are `evaluation/gpt-assisted-development-review.json`.

Restoring the checked evidence bundles and running the retained offline checks reproduces historical records without new model requests. Re-executing live inference requires the separately obtained pinned model and graph and is a different operation; exact fresh latency or stochastic equivalence is not promised. Full benchmark/database files, credentials, human reviewer identities and private owner keys are excluded from manuscript materials. Completed larger-run summaries, resource tables, primary interval and reproduction receipt are retained under `results/benchmark-training-100-001/completed/`. The public release contains the frozen plan and sources, earlier raw evidence and selected paper tables; the complete larger-run journals remain in the checked private archive and are not redistributed in the current public release. Exact reproduction of the larger retained run therefore requires access to that archive. Fresh rerunning remains a separate operation requiring the pinned model and graph.

## References

[1] Jiashuo Sun, Chengjin Xu, Lumingyuan Tang, Saizhuo Wang, Chen Lin, Yeyun Gong, Lionel M. Ni, Heung-Yeung Shum, Jian Guo. 2024. Think-on-Graph: Deep and Responsible Reasoning of Large Language Model on Knowledge Graph. The Twelfth International Conference on Learning Representations. [Source](https://proceedings.iclr.cc/paper_files/paper/2024/hash/10a6bdcabbd5a3d36b760daa295f63c1-Abstract-Conference.html).

[2] Yuanxiang Liu, Songze Li, Xiaoke Guo, Zhaoyan Gong, Qifei Zhang, Huajun Chen, Wen Zhang. 2026. CoG: Controllable Graph Reasoning via Relational Blueprints and Failure-Aware Refinement over Knowledge Graphs. Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). pp. 15547-15568. DOI: 10.18653/v1/2026.acl-long.708. [Source](https://aclanthology.org/2026.acl-long.708/).

[3] Chenhui Liu, Jianpeng Zhou, Jiahai Wang. 2026. Chain-of-Relations: Faithful and Efficient LLM Reasoning over Knowledge Graphs via Relation-Centric Exploration. Findings of the Association for Computational Linguistics: ACL 2026. pp. 43108-43119. DOI: 10.18653/v1/2026.findings-acl.2138. [Source](https://aclanthology.org/2026.findings-acl.2138/).

[4] Torsten Scholak, Nathan Schucher, Dzmitry Bahdanau. 2021. PICARD: Parsing Incrementally for Constrained Auto-Regressive Decoding from Language Models. Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing. pp. 9895-9901. DOI: 10.18653/v1/2021.emnlp-main.779. [Source](https://aclanthology.org/2021.emnlp-main.779/).

[5] Wenxiang Zheng, Guo Tang, Shixin Jiang, Liangyu Huo, Xiyuan Zhang, Jian Xie, Ming Liu. 2026. LCR-RAG: Enhancing Logical Consistency in Retrieval-Augmented Generation via Neuro-symbolic Reinforcement Learning. Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). pp. 17900-17916. DOI: 10.18653/v1/2026.acl-long.814. [Source](https://aclanthology.org/2026.acl-long.814/).

[6] Wen-tau Yih, Matthew Richardson, Chris Meek, Ming-Wei Chang, Jina Suh. 2016. The Value of Semantic Parse Labeling for Knowledge Base Question Answering. Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers). pp. 201-206. DOI: 10.18653/v1/P16-2033. [Source](https://aclanthology.org/P16-2033/).

[7] Kurt Bollacker, Colin Evans, Praveen Paritosh, Tim Sturge, Jamie Taylor. 2008. Freebase: A Collaboratively Created Graph Database for Structuring Human Knowledge. Proceedings of the 2008 ACM SIGMOD International Conference on Management of Data. pp. 1247-1250. DOI: 10.1145/1376616.1376746. [Source](https://research.google/pubs/freebase-a-collaboratively-created-graph-database-for-structuring-human-knowledge/).

[8] Steve Harris, Andy Seaborne. 2013. SPARQL 1.1 Query Language. World Wide Web Consortium. [Source](https://www.w3.org/TR/2013/REC-sparql11-query-20130321/).

[9] Qwen Team. 2024. Qwen2.5: A Party of Foundation Models. Model-card citation; deployed quantized alias and digest recorded separately. [Source](https://qwenlm.github.io/blog/qwen2.5/).

[10] Bradley Efron. 1979. Bootstrap Methods: Another Look at the Jackknife. The Annals of Statistics. 7(1). pp. 1-26. DOI: 10.1214/aos/1176344552. [Source](https://doi.org/10.1214/aos/1176344552).

[11] Eli Whitney Museum and Workshop. n.d.. Precision Manufacturing at the Whitney Armory. Accessed 18 October 2026. [Source](https://www.eliwhitney.org/precision-manufacturing).

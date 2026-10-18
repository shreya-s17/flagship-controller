# Schema-typed query programs and bounded repair for auditable knowledge-graph reasoning

Technical-report draft v2.0, 18 October 2026. **Exploratory artifact, not a final preprint or submitted paper.** Authorship, affiliations and contribution disclosures require owner confirmation. Earlier drafts remain in Git history; original result files and links are preserved.

## Abstract

A graph-supported answer can still answer the wrong question. We study an auditable question-only pipeline that links named entities, retrieves schema metadata, chooses among restricted conjunctive query programs, records complete bounded witnesses and applies a model-based semantic gate. A bounded repair control can reject a program and select a different candidate using observed failure feedback; a fixed control makes one choice. An earlier synthetic component study establishes implementation behavior but shows no adaptive-acquisition advantage in its fixture family. The live prototype progresses from zero answers to three exact answers, one partial answer and one abstention on five repeatedly used training questions, with official-semantics macro F1 0.6727. These are development results, not independent evidence of improvement. A prospectively frozen comparison on ten further training-pilot questions gives fixed F1 .40 versus repair .30, with an earlier parsing confound. An identical-prefix diagnostic gives .40 versus .40 at 16.48% more observed repair tokens, with no exact recovery. Semantic false acceptance and answer-scope errors persist despite valid graph paths. A later closed-obligation engineering revision prevents selected direction errors and adds observed primary-anchor conjunctions; a subsequent constraint-pruning revision matches three inspected official answer sets after local failure-driven development. This narrow rule-based result is not held-out validation or independently certified recovery. The artifact separates operational integrity, graph support, question semantics and benchmark scoring; it does not establish algorithmic novelty, calibrated reliability, token savings or superiority over a published baseline.

## 1. Problem and claim boundary

The research question is whether evidence-sensitive control can improve grounded question answering under incomplete evidence and finite resources. A useful controller must distinguish missing evidence from a wrong plan, avoid answering from a semantically incomplete query, and decide whether another action is worthwhile. The broad original hypotheses concern token efficiency, recovery and uncertainty-aware reliability. The current real-service experiment tests a narrower engineering mechanism: restricted query-program selection with at most one feedback-based revision.

The artifact has three concrete contributions at its current evidence level: an instrumented restricted prototype; a reproducible synthetic component experiment with an independent finite-graph oracle; and archived real-service development diagnostics with separate scoring and witness audits. These are engineering and diagnostic contributions. Their publication value requires a precise distinction and stronger empirical evidence; simply combining traversal, verification and stopping is not claimed as novel.

## 2. Related work

[Think-on-Graph](https://github.com/DataArcTech/ToG) supplies an established graph-exploration baseline. Our [pinned source audit](../evaluation/tog-source-audit.json) records its topic-entity inputs, model defaults, retry behavior and retrieval conventions. The current internal fixed control is not a reproduction of ToG, and no published ToG number is compared with our pilot score.

[Chain-of-Relations](https://aclanthology.org/2026.findings-acl.2138/) uses relation-centric exploration and entity filtering. Relation-chain traversal and pruning are therefore not sufficient novelty claims. [PICARD](https://aclanthology.org/2021.emnlp-main.779/) constrains formal-language generation through incremental parsing; our finite schema-typed catalog is a different implementation, not a reproduction or a new constrained-decoding claim. [LCR-RAG](https://aclanthology.org/2026.acl-long.814/) uses logical feedback with a learned query-correction policy. Our bounded, training-free catalog revision does not reproduce that learning mechanism.

The broader [existing literature matrix](https://app.notion.com/p/3f5cb3d4ccd68106bd73ccb1ed4356f2) remains a source for additional comparison. An exhaustive method/code audit is not complete. There is no cross-paper numerical comparison between unrelated datasets, models or our synthetic fixtures.

## 3. Methods

### 3.1 Separate synthetic and live systems

The synthetic engine receives a start entity, declared relation sequence and type obligations. It acquires edges from a finite evidence envelope and uses heuristic acquisition, symbolic verification, branch rerouting and stopping. A separately implemented exhaustive evaluator provides factual labels and accessible-witness information. Gold labels and corruption manifests never enter its deployed controller.

The live controller instead receives only a question ID, raw natural-language question and split. Its parser/linker and limited program grammar are additional sources of error. It is not equivalent to the synthetic controller and does not implement the full original adaptive-acquisition proposal.

### 3.2 Live state, catalog and program

Let s_t=(q,A,E_t,P_t,F_t,b_t), where q is the question, A the linked anchors, E_t the observed graph/schema evidence, P_t the remaining catalog, F_t rejected programs and b_t the resource vector. The parser proposes copied entity mentions and inferred types. Those type and semantic decisions are uncalibrated. A closed operator guard rejects selected unsupported operations; it can over-reject names containing operator words. Generic answer-category nouns are excluded from named anchors by an explicit logged rule.

Linking first tries a graph-native canonical key, guarded by a matching name and inferred type. It then falls back to bounded exact-name/alias variants. Ambiguity is not resolved by taking the first ID. Small candidate sets receive observed descriptions; secondary anchors can additionally use observed two-edge connections to the primary entity.

The graph supplies a complete bounded relation inventory or the request abstains. Retrieval uses declared lexical/type priors: at most 32 root candidates, up to 16 schema child predicates per selected root and a final catalog of at most 20 programs. The active catalog contains one- or two-hop paths, with equality joins for every secondary anchor. Child directions follow observed schema domains. These restrictions can remove valid programs. The lower-level compiler accepts longer fixture programs, but this does not expand the active parser's claimed scope.

For p=(r_1,...,r_k,J), k≤2 in the active catalog, J contains named-anchor joins. A restricted compiler validates identifiers, directions and indices; it never executes model-supplied SPARQL. Query rows supply provenance-bearing witness edges. A sentinel row and SQL-state checks reject truncated or incomplete results. The query can produce an answer set, rather than one arbitrarily retained endpoint.

### 3.3 Control and verification

The fixed control makes one catalog choice. The repair control permits a second choice after failure, masks the rejected program and can acquire graph-derived join options for a failed constrained query. Neither control receives gold feedback. Repeated branch exploration and successfully changing a failed program are distinguished in the logs.

Structural acceptance C(p,W) checks the implemented grammar and observed path/anchor consistency. A same-model gate U(q,p,W_sample) checks question/answer type and obligations. It sees the program, linked mentions, counts, at most five answer values and two witness rows; it does not inspect every returned row. Both gates are necessary in the implementation, but their conjunction is not a proof of semantic correctness. No calibrated probability, reward model or independent NLI verifier is used.

The maximum budget per question is (10 model calls,16,000 observed provider tokens,80 graph calls,100 rows/query). Synchronous model and graph timeouts are 120 and 30 seconds; the wall-time admission limit is 600 seconds. Model prompts above 3,000 observed input tokens are rejected after accounting under a 4,096 context configuration. Input-token budgets are admission/answer limits, not hard pre-call billing caps. Incomplete usage is explicitly flagged. Both controls share maxima, but their realized resource use can differ.

### 3.4 Offline auditing

The scorer reproduces the official WebQSP question-admission and best-parse conventions, including empty-answer behavior. Thirty-six PRF edge cases match the original helper exactly. Two aggregate fixtures match the original CLI's reported precision after only converting its Python 2 print syntax. The original downloaded script and archive are identified by SHA256. These checks are not an exhaustive proof of implementation equivalence.

An independent offline witness auditor does not import the deployed compiler/checker. It checks recorded endpoints, joins, result rows, provenance references, SQL states and emitted answer sets. A separate constant-triple requery can check graph presence after timing measurements. Neither checks complete question meaning. Evaluation annotations remain unreadable by the server runtime account and are used separately after prediction.

### 3.5 Common-state development controls

The subsequent development harness captures one question/link prefix per question and seed, plus the catalog and first program choice for the four internal controls. Exact request/query replay keeps that initial state fixed; the separate baseline shares linking only. Every policy is charged the prefix usage/time, while actual new requests are counted separately. Policy order is frozen using scheduling seed113, independently of request seeds17/29 and Python hash seed17. Raw RDF lexical strings and Freebase IDs remain the answer representation.

The semantic-gate-off intervention bypasses only the final model requirement audit. The reason-text-off intervention withholds only rejection text on a subsequent choice; failed-program masking and join acquisition remain. The durable journal retains interrupted admitted work as unknown-cost abstentions without retry. An offline branch diagnostic records rejection, revision and final official-set matching; none constitutes independently certified semantic recovery or counterfactual STOP labeling. This development harness does not yet execute the reserved larger cohort.

### 3.6 Closed relational obligations and primary-anchor conjunctions

A separate development runtime leaves the original v11 compiler/controller and v16 semantic module intact. It recognizes a narrow full-string copied-anchor grammar for parents/children and location-membership questions, conditional on the parser category/anchor. It enforces declared one-hop ontology bindings for parent/child roles, rather than asking the same model to reinterpret orientation. Unrecognized phrasing remains unhandled, and valid equivalent paths outside the closed family can be rejected. The rules are hand-designed engineering priors informed by inspected failures, not a learned or novel general semantic verifier.

For recognized location questions, up to three bounded graph queries observe endpoint edges to the primary anchor. Only actually observed containment bindings become prioritized catalog conjunctions; the new compiler permits primary-anchor joins while requiring every secondary named anchor to remain bound. Complete bounded witnesses include every conjunction edge. Finer downtown scope is not symbolically implemented. Version2 propagates a rejected necessary obligation to remove all incompatible remaining candidates before the second choice, without gold feedback or a new model call for pruning. Fixed, repair and obligation-guard-off share the expanded catalog and first PLAN; guard-off disables only these new checks. [Exact rules, constraints and commands](../evaluation/closed-obligation-development.md).

## 4. Experimental setup

### 4.1 Synthetic development study

Seed 17 generates50 base questions, each with seven paired conditions: intact evidence, support deletion, distractor deletion, relevant conflict, two unrelated-noise levels and an incorrect start caused by alias ambiguity. Ten deletion cases retain an alternate witness. All 16 acquisition/verification/recovery/STOP variants receive the same evidence access, for 5,600 main runs. A further5,600 executions sweep budgets and inject verifier faults. The caps are eight expansions and 32 symbolic checks. There are no model calls.

The fixture family supplies declared plans and noise on unrelated relations. It favors an exact symbolic checker and cannot establish natural-language benchmark behavior. Paired descriptive intervals resample 50 base-question clusters with all seven conditions retained,10,000 times using seed 17.

### 4.2 Live data and infrastructure

WebQSP v1.0 is obtained from the [official Microsoft release](https://www.microsoft.com/en-us/download/details.aspx?id=52763), archive SHA256 `95cb9cd2f6b4e1116ba4bec348f08a7f5ca2a5df4f223ea5af3f9b25a971b0ee`. Its 3,098 primary training questions supply separate pilot, calibration and policy groups; the 1,639 primary test questions are not executed by this controller. Exact duplicate strings are grouped, but paraphrase overlap and model pretraining contamination are not fully assessed.

The existing private server has an i7-7700 CPU, approximately 62 GiB RAM and mirrored disks. Freebase is restored from the DKI prepared archive, whose ZIP hash is `01ac8da685b7cc05dfeaf4fe6decdad87bc8889a530a55621a262c71e20e2289`. Its original snapshot date and equivalence to WebQSP's declared2015-08-09 graph remain unverified. OpenLink Virtuoso 7.2.5.3229 correctly reads the restored archive after an incompatible packaged-build attempt was stopped and preserved.

Inference uses local CPU-only Qwen2.5-7B-Instruct Q4_K_M through Ollama 0.40.4, context 4,096, four threads, temperature 0 and seed 17. The frozen alias digest is `ba6d123a5e5b0dfbab6a8aa2da25ca2643edaf4489953cd6f963e9482c4972fd`. Full [deployment provenance](../deployment/live-server.md) is retained. No paid model API or additional hardware is used.

### 4.3 Prospective comparison

The [frozen plan](../results/paired-pilot-001/plan.json) selects the next ten questions in the existing training-pilot order, outside the five used for these fixes. It records source/transport/harness hashes, model/configuration, seed and randomized within-question control order before execution. It is an exploratory local freeze, not formal external preregistration or an official held-out test study.

All selected cases, including abstentions, are retained. Analysis compares per-question official F1/exact accuracy, coverage and observed resource vectors. A 10,000-replicate question-level paired bootstrap with seed 17 is descriptive; the sample does not support a general superiority claim. First-plan equality is checked rather than assumed. Shared maxima do not imply equal realized cost, and cache state is not fully controlled.

### 4.4 Prospective reserved-training benchmark — collection in progress

A separately frozen feasibility study uses all100 exact reserved training questions, retaining their original train_remaining split, with seeds17/29/43 and six conditions: the five nested catalog/guard controls and the pinned declared-JSON local ToG adaptation. All1800 outcomes, immutable input/source/model/upstream hashes, order, maximum budgets, failure accounting and offline analysis are fixed before first reserved inference. The baseline shares only captured linking, without the controller catalog. A known development startup probe precedes collection. Runtime annotations remain unreadable to the isolated inference account and the inference package contains no scorer.

The primary endpoint is repair-C1G1 minus fixed-C1G1 official-semantics macro answer-set F1: average seeds within each question, then use10000 paired question bootstrap samples with analysis seed113. The100 question IDs define the bootstrap units; repeated seeds and conditions are not1800 independent questions, and residual question-family dependence remains possible. Every unsupported grammar, linking, budget, truncation and serialization failure remains in the full submitted denominator. Collection is incomplete, so no score, interval or superiority claim is reported. The official test remains unexecuted. The training reservation is a feasibility cohort, not a final confirmatory result or a power guarantee; contamination and snapshot equivalence remain limitations.

A prospectively selected20-question/seed17 sample across all six conditions supplies120 future masked semantic-review records. The owner's offered development review is explicitly author review and cannot count as an independent reviewer. No actual author or independent judgments have yet been received. We amended the earlier ordering before reserved inference to permit objective collection while human review is pending; independent semantic claims and submission still require appropriate completed evidence. No STOP/recovery denominator, calibrated reliability or semantic-validity rate is invented. [Executable protocol, frozen plan and analysis boundary](../evaluation/benchmark-training-protocol.md).

## 5. Results

### 5.1 Synthetic component behavior

| Variant (acquisition, verifier, recovery, STOP) | Grounded / 350 | Unsupported / answered | Mean expansions |
|---|---:|---:|---:|
| Full 1111 |210 |0/210 |3.126 |
| Acquisition off 0111 |210 |0/210 |3.126 |
| Verifier off 1011 |210 |90/300 |3.217 |
| Recovery off 1101 |92 |0/92 |2.080 |
| STOP off 1110 |210 |0/210 |3.503 |
| Verified fixed order 0110 |210 |0/210 |3.503 |

There is no acquisition advantage here. The expansion decrease from STOP is not token savings. Recovery-off uses less search; its lower yield is not a matched-cost recovery result. Verifier fault diagnostics show dependence on checker quality. [Full measurements and intervals](../results/synthetic-v2/report.md).

### 5.2 Reused live development questions

| Revision | Answered / 5 | Exact / 5 | Macro F1 | Observed tokens | Graph calls |
|---|---:|---:|---:|---:|---:|
| Original simple-chain revisions001–003 |0 each |0 each |0 each |609 /609 /2,548 |3 /3 /19 |
| Typed catalog v10 |3 |2 |0.4000 |13,658 |35 |
| Compact ranked catalog v11 |4 |3 |0.6727 |10,998 |36 |

All revisions reuse the same five questions; improvement is a development observation with selection bias. It is not a paired benchmark comparison, an independent sample increase or evidence for H1–H3. Exact latest cases are Maggie Grace/Taken, London postcodes and Madonna films. The river counting/superlative question is unsupported and abstains.

The Philippines result remains an answer-scope error: nine spoken languages include the two accepted official-language answers, yielding precision 2/9, recall 1 and F1=4/11. In v10 the planner continued from languages to their main countries, and the semantic gate wrongly accepted the result. This directly separates graph-supported paths from correct question interpretation. [Traces and development report](../results/structured-pilot-report.md).

### 5.3 Frozen ten-question comparison

All 20 original executions completed. Fixed F1/exact accuracy .40, coverage .60, 21,056 tokens, 63 graph calls; repair F1/exact .30, coverage .50, 22,329 tokens, 61 graph calls. The paired F1 delta is −.10 with a descriptive question-bootstrap interval [−.30,0]. The sole exact-score difference arises from earlier mention parsing, so it does not isolate repair.

An exploratory follow-up freezes and replays all ten original fixed prefixes without selecting by score. Fixed replay exactly reproduces terminals, answers, witnesses and counters with zero new physical requests. Repair from the same prefixes gives F1/exact .40 and coverage .60, with 24,527 charged tokens and 65 graph calls. No additional exact answer or exact recovery is observed; repair costs 16.48% more observed tokens. These are the same ten questions, not a larger independent sample. Latency charges reuse prefix time and are not fresh end-to-end measurements. [Plans, traces, checks and per-case failures](../results/paired-pilot-report.md).

Both controls wrongly accept witnessed Chicago identity and GEICO advertising-character answers. This exposes semantic-gate limitations even when structural evidence is consistent. No superiority, calibrated reliability or population effect is established.

### 5.4 Subsequent semantic-development diagnostics

A privileged post-run audit evaluates every recorded candidate in the original fixed pilot: eight catalogs are complete, two questions lack catalogs, and only four contain an exact-answer set, all already found by fixed control. The audit localizes inventory-to-shortlist and shortlist-to-root losses. Nine official query results match annotations strictly; the remaining date has a timezone suffix serialization discrepancy. This does not establish snapshot identity or a certified feasible-recovery denominator.

A separate purpose-selected six-case regression set reveals why additional semantic gates need validation. V12 yields zero exact, one wrong answer and five abstentions, largely from copied-quote/casing failures. V13 yields three exact, one wrong and two abstentions after span-constrained decoding, guarded name matching and contract lexical retrieval. Both accept correctly typed but wrong GEICO industries. The v16 observed-type root-inclusion smoke check answers Mexico/GEICO exactly on two inspected cases; Yale remains unresolved in that revision. A later canonical-key/alias linker fixes that observed Yale failure, with the small follow-on baseline checks reported separately. All targeted checks and their narrower denominators are reported in the [development checkpoint](../results/publication-development-report.md). These inspected training cases and hand-authored paraphrases are not independent evidence of improvement; no rephrasing is assigned an unverified benchmark score.

Question-span constraints and type priors are engineering safeguards, not a novel constrained-generation algorithm or semantic guarantee. All revisions retain source/model hashes, raw predictions and failures. Thirty policy-masked forms remain unannotated; an overlap-screened 100-question training reservation remains unexecuted pending method/normalization/baseline freeze and independent review. Current publication status remains NO-GO.

### 5.5 Indexed baseline development and remaining projection failures

A third frozen local ToG adaptation constrains relation choices to presented indices and answer extraction to actual observed-name spans. Across three revisions,30 executions reuse five question strings. In run003, the structured controller matches all three inspected official answer sets. The baseline is exact on Yale, adds a contextual historical coin on Mexico (F1 2/3), and abstains on GEICO at its model-call limit; projected-ID macro F1 is5/9 on these three selected development cases. On an unscored inverse control, native prose concludes Mexico but the converter emits the peso ID from context while claiming all conclusions are represented. This demonstrates that span validity and same-model completeness flags do not ensure faithful semantic extraction in those cases. Native text and failures are preserved. No performance ranking or independent gain is inferred.

At this earlier indexed-adapter checkpoint, the native-output addendum had15 unannotated cases, separate from the30 structured forms, and the shared-catalog controls were unfinished. The subsequent common-state checkpoint below implements those mechanics and expands the native pack to26 blank cases. Zero independent reviewers have completed either current pack. [Measured checkpoint and reproducibility](../results/indexed-baseline-development-report.md), [next-study design](../evaluation/next-study-design.md). Current source v3.1 adds a tested decimal-score formatting fix; run003 remains frozen v3 and supplies no live v3.1 result.

### 5.6 Shared-state development controls

A new frozen development harness captures identical link states for all methods and identical catalogs/first choices for four internal controls. It implements fixed, bounded repair, final-semantic-gate-off and rejection-reason-text-off, with per-request seeds, charged-prefix accounting and a durable no-retry journal.30 outcomes reuse three existing strings and seeds17/29; only one string is an official training original. Four controls match that original; a further local ToG adaptation declares stop/answer indices jointly and still adds a historical coin (F1 2/3). The inverse control now preserves the Mexico ID rather than projecting peso from context. Handwritten controls remain unscored. Repair-minus-fixed is0 on the sole original; no repair or reason-withholding event occurs, so this does not estimate recovery or an ablation effect. Four semantic-gate bypasses occur. No population interval or performance ranking is inferred.

All30 rows pass independent state/request/declaration ledger checks, and the16 structured answers' two unique triples are present on graph requery. There are36 physical model attempts versus repeated charged prefixes, an experimental reuse mechanism rather than a method-efficiency result. The unsuccessful preceding free-text final-field revision is retained. [Complete measurements and limits](../results/common-state-development-report.md). Larger evaluation, independent annotation and publication remain NO-GO.

### 5.7 Harder inspected cases and false acceptance

A further pre-inference freeze reuses four inspected originals selected from historical failures, with the unchanged prior eleven runtime modules at seed17. All20 planned outcomes complete. Each internal control has F1 .697368 and exact-set accuracy2/4: Whitney inventions and Iran forms are exact; Chicago returns23 attractions covering all15 official answers; the Revere parents query traverses incoming parents and returns16 reverse-role endpoints with no official overlap. All enabled same-model gates accept these sets. No rejection, revision or reason-text-withholding occurs; repair-minus-fixed remains0. The locally adapted baseline has projected-ID F1 .291667, exact0/4, two budget abstentions and two incomplete native declarations. This selected debug comparison establishes no performance ranking.

The post-run catalog oracle finds known exact options for three questions across three fully evaluated catalogs; these are different coverage counts, because two Iran alternatives truncate. Revere already has an exact outgoing parents option at index9, but selection plus false acceptance prevents trying it. Chicago's fully queried catalog lacks an exact option; the official inspected query also conjoins returned-location containment in the primary anchor, which the present catalog omits. All four official queries match their answer sets in this limited archive check. The20-row state ledger and47 unique accepted witness triples pass integrity/requery checks, including witnessed wrong-role endpoints. Neither audit proves question meaning. [Complete data, scope diagnosis and separately frozen directed-role follow-up](../results/harder-development-report.md).

A separately frozen ten-outcome follow-up adds generic directed variable-role input to the existing semantic audit on the same parents original and an unscored children control. All six enabled audits still accept reverse-role endpoints despite receiving the explicit subject/predicate/object atoms. No rejection or recovery occurs. All10 ledger records and18 unique accepted triples pass integrity/requery checks. The local baseline returns one of two parents and abstains on the handwritten control after graph truncation. This negative development result does not establish an effective semantic fix; it is preserved without selective rerun.

### 5.8 Closed-obligation engineering checks

Two separately frozen versions each complete18 outcomes on the same six purpose-selected strings: three inspected official originals and three handwritten controls/paraphrases, seed17. V1 rejects reverse-role kinship plans, but repair can choose another incompatible candidate and abstain. All three controls match Chicago's15-answer official set through the common expanded containment catalog and preserve Whitney's3-answer set. The current guard ablation does not isolate the catalog's historical contribution; official exactness does not certify finer downtown/world semantics.

V2 propagates the same necessary obligation after rejection, removing incompatible candidates before the second choice. Each of these three kinship repairs leaves one admissible candidate; this is constraint enforcement, not evidence of a learned general repair policy. Repair matches all3 official sets; fixed and guard-off each match2/3, with fixed abstaining on Revere and guard-off accepting wrong-role endpoints. Three rejection-to-answer transitions occur, including one exact official set; the other two are correlated unscored handwritten kinship questions. No independently certified recovery rate or population interval follows. All six captured cross-version states match in actual request hashes/raw replies, graph observations, catalogs and first plans; timestamps/durations are excluded. The initial failed version is retained unchanged.

Across all six strings, V2 repair charges27 model calls,20,656 returned usage tokens and80 graph calls, versus fixed21/16,162/68 and guard-off24/19,633/83. V2 makes36 actual physical model attempts and127 graph attempts; prefix reuse explains the difference from summed policy charges. V1 makes33/115. Costs and failed outcomes remain; no token-saving or matched-cost advantage is claimed. Both studies pass36 state-ledger checks; V1's51 and V2's69 unique accepted witness triples are present on requery, including guard-off wrong answers. Rule/pruning checks are not independent semantic labels. [Full outcomes, source/manifest hashes and limits](../results/obligation-development-report.md). Reserved100 and official test remain unrun; wider evaluation, independent annotation and novelty assessment remain open.

### 5.9 Finite guard countermodels and catalog availability

A separate relational interpreter enumerates4,096 arbitrary inverse-consistent kinship graphs and216 three-bit location/containment/downtown worlds, evaluating67,696 guard/program/world combinations. It consults neither benchmark labels nor the production compiler as its truth oracle. Canonical declared bindings satisfy their finite reference definitions. Nonetheless, a toy identity extension preserves exact nonempty kinship answers in3,584 worlds per correct-role family while the one-hop guard rejects it. An extra endpoint filter passes the direction condition but omits valid answers in1,536 worlds per correct-role family. For each canonical containment orientation, city membership exceeds the synthetic downtown target in91/216 location worlds. These controlled examples establish limits of necessary guards under explicit fixture semantics; they are not natural-world frequencies, independent questions or measured end-to-end errors. Some tested programs are absent from the active catalog, and no model/type/semantic gate is simulated. All33 handwritten grammar contract expectations pass without constituting independent language validation.

A gold-free reconstruction of schema-only catalogs from the six actual run002 prefix states finds zero versus two closed-rule-compatible entries before/after expansion for each Chicago string, with two old entries displaced at the20-entry cap. Kinship and Whitney catalogs are structurally unchanged. Compatibility is not correctness and no counterfactual program/model execution occurs. A prospective catalog-by-guard comparison must share pre-catalog observations, capture separate catalogs/first choices and retain exhausted conditions. A separate nested-capture harness is now implemented and fixture-tested, with a30-condition development freeze; its measured outcomes must be reported separately. Independent semantic review remains unfinished. [Audit, counterexamples and reproduction](../results/closed-guard-audit-report.md).

### 5.10 Nested catalog-by-guard development comparison

A separate nine-module runtime/harness composes the preserved v2 controller. One common capture stops after root/schema observation; each catalog condition then captures its own catalog and first PLAN. Guard arms share that mode-specific first choice, rather than incorrectly sharing a choice across changed prompts. All30 frozen outcomes complete on the same six inspected strings at seed17, with6 common and12 catalog captures. No official test/reserved-cohort inference occurs.

| Condition | Official macro F1 | Exact sets /3 |
|---|---:|---:|
| Repair, schema catalog, closed guard off |.596491 |1 |
| Repair, schema catalog, closed guard on |.666667 |2 |
| Repair, expanded catalog, closed guard off |.666667 |2 |
| Repair, expanded catalog, closed guard on |1 |3 |
| Fixed, expanded catalog, closed guard on |.666667 |2 |

In the captured states, guarded repair rejects and changes the reversed parents program under either catalog. Every such kinship repair retains just one admissible candidate. Expanded containment changes Chicago from23 broad endpoints to15 official matches; guard-on without expansion instead exhausts the catalog and abstains. The two handwritten controls/paraphrase reproduce related behavior but remain unscored. There is one distinct official original with an exact answer after a rejection, repeated across catalog conditions, not a certified recovery denominator. Effects are conditional on the common selected roots/schema and failure-informed development cohort; three inspected originals do not establish general improvement or statistical superiority. Downtown semantics remain unmodeled by the closed guard.

Physical execution uses55 model attempts and174 graph calls across all conditions; every policy is charged its nested prefix work. Realized usage differs and constructed replay time is not a method-efficiency result. All30 nested ledger and declared-rule checks pass; all25 answered records pass structural witness auditing. All77 unique accepted witness triples are present on post-run requery, including those from wrong-role/broad controls. Independent semantic/false-rejection review remains absent, and previous negative runs are preserved. [Full denominator, costs, source and reproduction](../results/factorial-development-report.md).

## 6. Failure and STOP analysis

Observed development failures include whole-question mentions, answer-category extraction, ambiguous labels, unsuitable relation sequences, misplaced named constraints, unobserved predicates, result/candidate caps, schema-query scoping problems, timeouts and catalog truncation. The move to a finite typed catalog addresses structural errors but can exclude valid answers and does not fix semantic scope by itself. Failures and superseded runs are retained; an interrupted development revision is labeled incomplete rather than scored as a complete five-question run.

Early STOP requires an independently established, budget-feasible acceptable continuation from the observed stop state. Late STOP requires avoidable actions after an independently accepted complete supported candidate. Exhaustion, a cap or abstention alone does not establish either. Current live STOP rates are not identifiable. An observed repair from a failed first program to an exact answer would be reported separately from a certified recoverable-case rate; no denominator is invented.

### 6.1 Relation to existing failure-aware control

[CoG](https://aclanthology.org/2026.acl-long.708/) combines relational blueprint guidance with evidence-conditioned reflection and controlled backtracking. This overlaps the broad motivation here; full method/code comparison is still required before claiming a distinct mechanism. The present experiment does not reproduce CoG or establish superiority. The plausible alternative contribution is a rigorous reliability/reproducibility study, contingent on substantially stronger evidence.

## 7. Limitations and final-paper gates

The live grammar is deliberately narrow. Lexical retrieval and inferred types can miss candidates; graph-native keys can resolve the wrong sense. The same model proposes and critiques semantics. There is no calibration, independent semantic annotation, learned reward model, general query repair or agent-transfer experiment. Exact answer matching can penalize a naturally broader interpretation, while successful graph checks cannot certify answer-set scope.

The sample is small, development questions are reused, the model may have seen benchmark material during pretraining, and paraphrase leakage is incompletely audited. Snapshot equivalence is unresolved. Only one local model is used. The original live pilot uses seed17; the subsequent small common-state mechanics check uses17/29, which are not independent question replications. CPU/cache effects and different realized costs limit efficiency inference. A small local ToG adaptation sanity run is now archived separately; an adequate frozen comparison with external methods remains missing.

A final paper therefore needs adequate independent evaluation, a meaningful frozen external-baseline comparison, clear evidence/recovery/STOP labeling and a claim that survives these tests. Targeted method/selected-code inspection now confirms overlap with CoG/CoR; [the boundary note](closest-method-comparison.md) records the scope and remaining gaps. The proposed broader H1 token-saving, H2 matched recovery and H3 calibrated reliability claims remain unestablished. Public release and submission also require reviewed authorship, licensing and disclosures.

## 8. Reproducibility and conclusion

The repository records question-only intake, frozen plans, source/model hashes, raw traces, offline scores and checksums. [Current commands and verification scope](../README.md) distinguish direct source execution from packaging and historical replay. Gold annotations and database credentials are excluded from source distribution. Post-run graph audits must run after latency measurements.

The current result is an operational restricted prototype and an auditable exploratory research artifact. Typed program selection makes real supported answers possible, but semantic scope remains a central reliability problem. Completing software does not establish novel research or guarantee publication. [Contribution decision](contribution-decision.md) remains REVISE engineering, with final submission held behind scientific evidence; [venue planning](venue-plan.md) is provisional and no paper is submitted.

## Local baseline adaptation checkpoint

A bounded, separately sourced ToG adapter now invokes pinned upstream pruning, scoring and stopping functions with the existing local model. Thirteen offline compatibility checks pass. The [adaptation record](../evaluation/tog-adaptation.md) identifies question-only linking, model, seed, transport, name handling, bug fix and normalization departures. [The small frozen sanity run](../results/baseline-dev-001/manifest.json) retains all operational failures and is not independent benchmark evidence. The shared linker now accepts canonical keys supported by exact observed aliases, addressing the Yale label-order diagnosis without a question-ID rule. Actual outcomes belong to the run report; neither implementation nor compatibility tests establish reproduction of paper scores.

## Release and assistance disclosure — owner review pending

Codex assisted implementation, debugging, automated tests, artifact auditing and documentation. Automated checks are not independent human semantic review; none has been collected. Actual human authors, affiliations, contribution statements and final responsibility require confirmation before release. The root repository has no license file and public redistribution/attribution review remains open; [inventory](../evaluation/private-release-inventory.json). The owner approved publication of the verified17 October checkpoint to the existing public GitHub repository. This exploratory draft is included in that checkpoint; it is not a submitted manuscript, license clearance or final authorship confirmation.

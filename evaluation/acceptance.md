# Flagship research acceptance record

Status on 10 October 2026: the local controller and an exploratory synthetic pilot are implemented. The selected WebQSP and CWQ pilot and confirmatory research study remain incomplete. The Todoist parent must remain open.

| Deliverable | Evidence and status |
|---|---|
| Interpretable MVP | Complete for declared typed path queries over a local evidence envelope. Heuristic acquisition, verification, backtracking, answer or abstain, explicit observations and costs. |
| Reproducible component study | Complete on generated development graphs: 50 base questions, seven conditions, 16 variants, independent oracle and raw traces. |
| Reliability and failure analysis | Synthetic analysis complete; real benchmark and natural failure analysis pending. |
| First paper draft | Draft with actual synthetic results and explicit benchmark gaps. Not a validated research contribution or publication. |
| WebQSP intake | Official archive downloaded and checksummed; input and evaluation labels separated; official train and test retained. Graph execution pending. |
| CWQ intake | Pending official v1.1 acquisition and version audit. |
| Question parsing and linking | Pending. The synthetic engine receives declared relations and type constraints. Gold semantic parses cannot serve as controller input. |
| Freebase evidence | No compatible snapshot was found in Documents or Downloads. No configured endpoint. Available local disk was about 14 GiB; the linked ToG setup describes a 400 GB raw and 125 GB filtered dump. A remote endpoint or a documented independently extracted envelope is needed. |
| Model and calibrated verifier | Pending a frozen model configuration, accessible execution environment and usage budget. No API credentials or paid runs were provisioned. |
| H1 token saving | Not tested. Zero model calls cannot establish savings. |
| H2 recovery | Branch rerouting studied; no faithful fixed-retry benchmark comparison or matched failed-answer recovery experiment. |
| H3 uncertainty | Synthetic perturbations studied; hybrid NLI and calibrated confidence at fixed coverage pending. |
| Prior work and novelty | Existing 13-paper matrix preserved; source-linked boundary in paper. No claim of novel integration or exhaustive novelty clearance. |

## Evidence access attempts

The installed Hugging Face CLI dataset listing and a direct public GitHub download failed with DNS resolution errors in the restricted local environment. The browser successfully downloaded the official WebQSP archive. The GitHub connector remains usable for repository writes. This combination permits local synthetic experiments and source publication but does not supply a Freebase graph or model inference backend.

## Remaining execution sequence

1. Connect a Freebase snapshot or endpoint compatible with the official data, record checksum/version and freeze a query-independent evidence envelope from independently linked question entities.
2. Implement and evaluate question-only parsing and entity linking. Keep gold answers, parses, proof paths and corruption labels isolated in evaluation storage.
3. Freeze the model, prompts, context limits, token budgets and verifier; run development feasibility questions from the saved pilot split, not test.
4. Acquire and audit CWQ v1.1; preserve its official splits. Audit paraphrase overlap beyond exact question duplicates.
5. Fit confidence on the calibration split, select policy on a separate subset, obtain independent labels, and run paired conditions and baselines with real costs.
6. Revise the paper with benchmark tables, natural failure cases, calibration and matched recovery results. Close the pilot and parent only after these deliverables are verified.

[Freebase setup source](https://github.com/DataArcTech/ToG/blob/main/Freebase/README.md). The storage sizes above describe that source's setup, not a universal requirement for every possible remote or subset implementation.

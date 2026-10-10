# Flagship controller — first runnable scaffold

An interpretable graph-search controller for the flagship research project. Uses only Python's standard library at runtime. This is a synthetic-fixture MVP, not a WebQSP/CWQ experiment, trained policy, novel method, or empirical research result.

## Run

From this directory, with Python 3.10 or newer:

```sh
python3 -m unittest discover -s tests -v
python3 -m flagship_controller --output runs/demo.json
```

No API key, model download, paid service or package installation is required.

## What it does

The query declares a start entity, ordered relations and type constraints. The controller searches candidate paths, observes graph edges, checks path continuity, declared types, provenance and explicit conflicts, backtracks on a failed check, and answers only when a complete supported witness is found. Budget exhaustion prevents new expansions while permitting checks on evidence already acquired.

The fixed-relation baseline uses the same search order and terminal verifier but delays intermediate checks until a path is complete. It isolates early verifier feedback, not all components of the research design. Both variants can backtrack. Candidate scores currently tie at 1 for relation-matching actions with deterministic ID ordering; learned ranking and best-of-N are not implemented.

## Traces

Each step logs state and observed path, candidate edges and scores, action, verifier signal, recovery/termination decisions, cumulative graph expansions, unique observed edges and elapsed time. EXPAND adds the candidate edges to observed evidence; choosing a branch is shown by the next step's path. Token and GPU costs are null because this version makes no model calls. A RECHECK verifies existing observations; its real wall time is included but it uses no expansion budget.

## Fixtures

Supported answer, missing evidence, explicit contradiction, wrong-type branch recovery and budget exhaustion. These cases are hand-designed tests, not estimates of population accuracy. The recovery example shows how early type checking can avoid expanding a bad branch.

## Boundaries and next milestones

- Returns one supported witness; does not enumerate full answer sets, certify global minimality or infer arbitrary natural-language query constraints.
- Types and conflicts are declared fixture metadata. Provenance presence is checked, not the truth of source claims. No calibrated confidence, LLM/NLI verifier or learned reward is present.
- Search is adaptive through verification and branch pruning; state-conditioned action scoring, revision and standalone recovery policies are future work.
- Next: generalize the graph adapter and query constraints, add acquisition/recovery/STOP switches and complete trace manifests, then integrate benchmark data and the documented evaluation protocol.
- Add independent evaluation labels separately from controller inputs. Never expose gold answers/proofs to action selection.

## Research documentation

- [Research hub](https://app.notion.com/p/3f0cb3d4ccd6807abdf1fb5a7ae54b76)
- [Experimental design](https://app.notion.com/p/3f5cb3d4ccd68186b41ef5ae2775d54a)
- [Evaluation protocol](https://app.notion.com/p/3f5cb3d4ccd68117a4b4ccf55cb48bb4)
- [MVP task](https://app.todoist.com/app/task/6hQFhgFxcHCpPq5r)

No paper code is copied in this scaffold. Related paper implementations must be cited and their licenses checked before reuse. Publication and licensing decisions remain open.

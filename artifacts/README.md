# Research artifacts

The complete synthetic development bundle is `synthetic-v2-artifacts.zip` in this directory. It contains the frozen dataset, all main-study trajectories, per-run main and diagnostic metrics, summaries, paired intervals, representative trajectories, manifests, protocol, source files and paper draft. `checksums.json` records SHA-256 checksums. The archive is uploaded to the private GitHub repository separately from source-tree updates.

Recreate the measured study from the repository root:

```sh
python3 -m flagship_controller.pilot
python3 -m flagship_controller.diagnostics
```

The synthetic bundle contains generated data only. Official full benchmark data, credentials and database files are excluded. Official WebQSP test-set controller evaluation and CWQ experiments have not run.

Live development and selected post-run query diagnostics are separate from the synthetic bundle. `live-evidence-2026-10-16/` preserves the earlier traces; `baseline-evidence-2026-10-16/` preserves baseline development traces. These contain selected training/development questions and observed rows. They remain in the private repository; public redistribution needs a data/prompt licensing review. The original live bundle is unchanged.

Run `python3 scripts/restore_live_evidence.py` after a clean checkout. It restores every recognized available bundle, verifies every part/archive/original-file hash and refuses to overwrite changed content. Historical file counts below identify earlier checkpoints. Small manifests, source snapshots, scores and failure summaries are directly readable under `results/`. Restoration checks integrity, not semantic correctness or publication readiness.

`indexed-baseline-evidence-2026-10-16/` adds frozen run003 raw traces. Earlier bundles remain unchanged.

The fourth bundle, `common-state-evidence-2026-10-16/`, adds101 files: run004 raw traces and the completed common-state study predictions/journal. Restoration now verifies124 original files. Previous bundles remain unchanged. These are private development observations, not independent benchmark results.

New bundles can be built with `scripts/package_live_evidence.py` using an explicit JSON list of normalized regular files under `results/`. The builder refuses existing destinations, traversal and symlinks; archives use sorted members, fixed metadata and timestamp-zero compression. Use the matching manifest to restore and verify bytes. Neither packaging nor restoration validates semantics. Previous bundles are preserved rather than rebuilt.

The fifth bundle, `harder-common-evidence-2026-10-16/`, adds111 raw study/journal and privileged offline catalog files. All five bundles restore235 original files. Its35 parts preserve the scope/direction failures and unsuccessful directed-role follow-up, not independent semantic annotations.

The sixth bundle, `obligation-evidence-2026-10-17/`, preserves both closed-obligation versions' 146 raw prediction/journal files in40 parts. All six bundles restore381 original files. Earlier bundles are unchanged; the new evidence includes failed revisions and guard-off wrong answers.

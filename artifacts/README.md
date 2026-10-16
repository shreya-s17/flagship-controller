# Research artifacts

The complete synthetic development bundle is `synthetic-v2-artifacts.zip` in this directory. It contains the frozen dataset, all main-study trajectories, per-run main and diagnostic metrics, summaries, paired intervals, representative trajectories, manifests, protocol, source files and paper draft. `checksums.json` records SHA-256 checksums. The archive is uploaded to the private GitHub repository separately from source-tree updates.

Recreate the measured study from the repository root:

```sh
python3 -m flagship_controller.pilot
python3 -m flagship_controller.diagnostics
```

The synthetic bundle contains generated data only. Official full benchmark data, credentials and database files are excluded. Official WebQSP test-set controller evaluation and CWQ experiments have not run.

Live development and selected post-run query diagnostics are separate from the synthetic bundle. `live-evidence-2026-10-16/` preserves the earlier traces; `baseline-evidence-2026-10-16/` preserves baseline development traces. These contain selected training/development questions and observed rows. They remain in the private repository; public redistribution needs a data/prompt licensing review. The original live bundle is unchanged.

Run `python3 scripts/restore_live_evidence.py` after a clean checkout. It restores all three available bundles (23 original files), verifies every part/archive/original-file hash and refuses to overwrite changed content. Small manifests, source snapshots, scores and failure summaries are directly readable under `results/`. Restoration checks integrity, not semantic correctness or publication readiness.

`indexed-baseline-evidence-2026-10-16/` adds frozen run003 raw traces. Earlier bundles remain unchanged.

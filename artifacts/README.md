# Research artifacts

The complete synthetic development bundle is `synthetic-v2-artifacts.zip` in this directory. It contains the frozen dataset, all main-study trajectories, per-run main and diagnostic metrics, summaries, paired intervals, representative trajectories, manifests, protocol, source files and paper draft. `checksums.json` records SHA-256 checksums. The archive is uploaded to the private GitHub repository separately from source-tree updates.

Recreate the measured study from the repository root:

```sh
python3 -m flagship_controller.pilot
python3 -m flagship_controller.diagnostics
```

The bundle contains generated data only. Official WebQSP raw data, gold queries and personal credentials are excluded. The primary WebQSP/CWQ experiments have not run.

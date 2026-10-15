# Live deployment checkpoint — 15 October 2026

## Verified infrastructure

SSH administration works through a dedicated project key. Server: Intel i7-7700 (4 physical cores, 8 threads), approximately 62GiB RAM, two 4TB disks mirrored as RAID1. All arrays show `[2/2] [UU]`, no resync pending. Both disks' SMART overall-health assessments pass. Ubuntu 24.04 LTS is installed. These checks were executed directly on the server, following earlier user-run checks.

The existing Ubuntu-packaged database and its files remain preserved. It has been stopped and disabled to avoid running an unused database. The downloaded Freebase ZIP is retained. No additional hosting, model API, GPU or storage purchase was made.

## Freebase provenance and compatibility

- Source: [DKI lab Freebase-Setup](https://github.com/dki-lab/Freebase-Setup), its linked `virtuoso_db.zip` archive.
- Download bytes: **56,324,228,100**.
- SHA256, supplied by the user after download: `01ac8da685b7cc05dfeaf4fe6decdad87bc8889a530a55621a262c71e20e2289`.
- ZIP integrity test passed according to the user's output. Listed extracted database size: **148,679,688,192** bytes. ZIP entry timestamp: 2020-12-16; this is not the Freebase snapshot date.
- Google's historical public dump endpoint returned HTTP403. The DKI archive was used instead of silently substituting an answer-derived task subgraph.
- Ubuntu package `7.2.5.1+dfsg1-0.8build1` started the archive but misread identifier tables: prefix integers appeared shifted and SPARQL data queries failed. This attempt was stopped, preserved in `/srv/freebase/instance-ubuntu-compatibility-attempt`, and excluded from research runs.
- Upstream OpenLink **7.2.5.3229**, build commit `3f4cdd3`, dated 2018-08-15, correctly reads the identifier values. A clean archive copy was restored and validated before pilot execution; no research run used the earlier modified copy.
- Official upstream binary archive: https://github.com/openlink/virtuoso-opensource/releases/download/v7.2.5/virtuoso-opensource.x86_64-generic_glibc25-linux-gnu.tar.gz
- Binary archive SHA256: `02ed11660acd642e4921294750e6010ea714eea904bd08e4d7ee07e5119f3aa8`.
- Executable SHA256: `2bd0881b7bbb61e6727a58ea4bee254becb1b6deae97a284b23f8cbd94f62639`.

The DKI provider describes its archive as a processed latest Freebase dump with literal fixes. Original snapshot identity, complete coverage and equivalence to WebQSP's 2015-08-09 reference remain unverified. Successful startup or sample queries do not establish full benchmark comparability. No Wikidata augmentation has been added.

## Private services and resource limits

The Freebase process runs as dedicated OS account `freebase-db`, with read/write access to `/srv/freebase/instance`, protected home directories, no OS calls, and loopback-only network policy. SQL is `127.0.0.1:1112`; SPARQL is `http://127.0.0.1:8891/sparql`. This differs from the original example port8890. Config: 1,360,000 buffers, 1,000,000 dirty buffers, query memory1G, two threads/query, 30-second SPARQL execution limit and600-second estimated-cost admission threshold. Systemd memory ceiling32G is a process bound, not a reservation or latency guarantee.

Password setup remains deferred at the user's request. Database defaults may remain and the service must stay private. Automatic startup of the Freebase service has not been enabled. SSH authorization is separate from database credentials. The project private key is not in this repository or on the server; the server has only its authorized public half.

## Local model

Ollama **0.40.4** is installed from its official vendor source, bound to `127.0.0.1:11434`, one concurrent request and one loaded model, memory ceiling12G. CPU-only; no GPU or paid backend.

- Quantized source: `qwen2.5:7b-instruct-q4_K_M`, 7.6B parameters, approximately4.68GB.
- Source Ollama digest: `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`.
- Local configured alias: `flagship-qwen2.5-7b-q4km`.
- Alias digest: `ba6d123a5e5b0dfbab6a8aa2da25ca2643edaf4489953cd6f963e9482c4972fd`.
- Parameters: context4096, four CPU threads, temperature0. The runner additionally sets seed17 and caps generated tokens per call. Model context truncation is not independently certified; inspect long prompts before general evaluation.
- Upstream model card checked with `hf models info`: [Qwen/Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct), revision `a09a35458c702b33eeacc393d103063234e8bc28`, Apache2.0. This is source-model provenance, not a claim that the quantized artifact equals those unquantized weights byte-for-byte.
- Real smoke generation returned valid JSON, 42 input tokens and9 output tokens in10.16seconds including7.09seconds model loading. This tiny sample is not representative end-to-end throughput.

## Controller and evaluation boundary

Code is deployed under `/opt/flagship-controller`. Thirty-four tests pass on both local and server environments. Pilot execution uses unprivileged account `flagship-runner`. The `evaluation-only.jsonl` file is root-owned mode0600; an access check confirmed the runtime user cannot read it. The prediction runner accepts question-only records, logs evidence and actual model usage, and the scorer reads labels separately afterward.

The initial live run is limited to the first five previously fixed training-pilot records. Policies, score definitions and question selection have not been changed based on answers. This remains a simple-chain feasibility system with exact-name linking, uncalibrated semantic verification and no general adaptive plan repair. The internal CLI name `adaptive` must not be presented as the full proposed method or a reproduced published baseline. Official scorer parity, paraphrase overlap audit, full baseline reproduction and matched-state recovery experiments are still pending.

## Live run status

Restoration and clean graph checks passed. Three development revisions on the same five training questions completed; all abstained. [Results and failure analysis](../results/webqsp-live-report.md) record exact outcomes, costs and remaining research work. The original server status file records revision001; versioned run manifests and traces are authoritative for later revisions. No held-out benchmark result or H1–H3 claim is established.

Current services are running. After a server reboot, Freebase requires a manual `systemctl start flagship-freebase`; automatic startup remains disabled. The repository includes the effective [service unit](flagship-freebase.service) and [database configuration](virtuoso.ini.example).

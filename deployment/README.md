# Freebase / WebQSP deployment handoff

Prepared 10 October 2026. This is a deployment runbook, not an executed installation. No server has been bought, graph downloaded, model installed or live benchmark run.

## Purchase gate

Live Hetzner auction candidate: ID **3086903**, Intel i7-7700, 64 GB DDR4, two 4 TB enterprise SATA HDDs, FSN1 Germany, 1 Gbit NIC. The order page confirmed these specifications, Rescue System, primary IPv4 and zero setup fee. Offer availability is first-come, first-served and not reserved.

The listing showed EUR65.70/month excluding VAT; order page showed EUR78.18/month including default German 19% VAT. Primary IPv4 is already included in both totals: do not add it twice. India billing is supplied by the user. Hetzner's published VAT policy says countries outside the EU not separately listed receive invoices without VAT; India is not listed. This is an expected India quote, not a verified account-specific invoice, and does not determine any separate Indian tax obligations.

At the ECB 9 October reference EURUSD1.1206, EUR65.70 is USD73.62. A planning 4% currency/payment margin gives USD76.57; the bank's actual conversion and fees can differ. Infrastructure checkout ceiling remains USD80 inclusive of mandatory fees. First-month total ceiling is USD100. Keep USD15 reserved for a possible later model backend and at least USD5 contingency; do not spend the model reserve now. The current VAT-inclusive default would exceed the infrastructure ceiling. No paid add-ons, extra disks, managed support or GPU are needed for the initial deployment.

User action: sign in or create a Hetzner account with India billing, review the same offer/specifications and final invoice total, and approve that exact recurring charge. Do not buy if the price/specification changes or inclusive infrastructure cost exceeds USD80. Account approval may be required. Server billing recurs until cancellation; retain the cancellation terms and first billing date from checkout. Buying this host does not guarantee a complete study within one month or any publication-quality results.

## Installation sequence after purchase

1. Inspect the **new, empty** server's actual disks, memory and health before installation. Use an available supported Debian/Ubuntu image from Hetzner. Configure GPT and RAID1 through the vendor's Rescue System / installimage. Two mirrored 4 TB drives yield approximately 4 TB nominal capacity, about 3.64 TiB before filesystem/OS overhead, not 8 TB. This layout applies only to the newly purchased empty server; installimage erases selected drives. Record actual mounted free bytes and disk health. HDD imports and CPU inference may be slow; measure rather than promising a completion time.
2. Install Virtuoso Open Source from the selected distribution's official packages and Ollama from its official source. Record exact OS, package, service and Python versions. Keep database administration, SPARQL and Ollama bound to loopback; allow SSH only as required. Create credentials locally without committing them. Verify bindings and access before importing anything. Use SSH forwarding for laptop access: local port 8890 to server 8890, local port 11434 to server 11434. Never expose default database administration or an unauthenticated model API publicly.
3. Verify the Freebase dump source, version/date, license, download size and SHA256. WebQSP was collected against Freebase snapshot **2015-08-09**. A different dump must be labelled and its compatibility audited; do not relabel the public latest dump as that snapshot. Confirm a accessible compatible source before a long import. If unavailable, report the mismatch and hold benchmark comparability claims. Download directly to the server, never the laptop. Retain the compressed source and a manifest outside Git.
4. Run a small RDF load to validate parsing, identifiers, names/aliases, inverse relations and CVT mediator edges. Use Virtuoso's documented bulk loader (`ld_dir`, `rdf_loader_run`) after configuring its allowed import directory. Load the **full graph** into a dedicated database; do not silently substitute answer-derived subgraphs or drop non-English/type/CVT triples. Stream decompression into bounded complete-line chunks, track each chunk hash/bytes/load status, monitor free disk, and checkpoint. Avoid retaining a complete uncompressed intermediate. Do not delete staging chunks until successful load status and source recoverability are verified. Retain import errors and the actual indexed database size. Database buffer tuning must leave memory for OS and model; defaults must not be assumed to fit a 64 GB host.
5. Select a licensed quantized model that fits remaining RAM, install it on the server, and record the exact Ollama model digest, quantization, template, context and service version. A roughly 7B model is a candidate class, not a frozen model or a guarantee of adequate reasoning. Run a tiny generation and inspect real token accounting and latency. If CPU inference fails feasibility, stop and review a specific alternative within the reserved budget before spending. No separate subscription is needed to attempt local inference.
6. Freeze the deployment manifest with graph checksum/snapshot compatibility, model digest, package versions, hardware, usable disk, import statistics and commit SHA. Query one known named entity and an observed relation using training-pilot material; inspect evidence manually. Confirm no evaluation-only answers enter the runtime. Use the instructions in [the runtime guide](../evaluation/webqsp-runtime.md) to run **five training-pilot questions**, inspect every trace and score offline. Failed service calls, missing graph coverage, ambiguity and unsupported constraints remain visible failures/abstentions.
7. Back up configuration, manifests and pilot traces locally. Do not mark the main benchmark task complete from a five-question feasibility pilot. Measure disk growth, graph latency, model tokens and inference latency before increasing the batch. Full baseline reproduction, improved linking/replanning/constraints and evaluator parity remain subsequent research work.

## Required handoff from the user

Purchase confirmation and access to the provisioned host are needed next. Use the provider's normal access flow; do not paste passwords/private keys into Notion, Todoist or GitHub. No automation in this repository submits an order, accepts terms or changes the user's PC database.

## Sources

- Offer: https://www.hetzner.com/sb/ (auction inventory and prices are volatile)
- VAT: https://docs.hetzner.com/general/billing-and-account-management/billing-at-hetzner/value-added-tax/
- Currency reference, not card quote: https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.fr.html
- OS/disk configuration: https://docs.hetzner.com/robot/dedicated-server/operating-systems/installimage/
- Bulk loader: https://docs.openlinksw.com/virtuoso/fn_ld_dir/
- Graph: https://developers.google.com/freebase
- API: https://docs.ollama.com/api/chat

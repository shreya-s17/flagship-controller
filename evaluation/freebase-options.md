# Freebase access and budget audit

Audit date: 2026-10-10. User planning budget: USD 50–100 total for first month; no purchase authorized.

## Published subgraphs

CBR-SUBG author download folder visibly lists public_subgraphs.tar.gz at 2.54 GB and public_models.tar.gz at 227.9 MB. Archive contents and expanded size have not been inspected or downloaded. Coverage, checksums, embedded annotations and license scope remain unverified.

The collection README explicitly uses --use_gold_entities. It gathers paths joining training query entities to training answers, then traverses those patterns around each target entity. Training-answer supervision alone is not test-answer leakage. Gold target entity linking is privileged input relative to our question-only protocol, however. The preselected evidence also restricts acquisition to another retriever’s envelope. Therefore these artifacts cannot certify our planned end-to-end H1–H3 evaluation or direct comparability to full-Freebase paper scores. They could support a separately labelled conditional subgraph experiment after file-level auditing; no protocol substitution is approved here.

Sources:
- https://github.com/rajarshd/CBR-SUBG/tree/main/adaptive_subgraph_collection
- https://github.com/rajarshd/CBR-SUBG
- https://drive.google.com/drive/folders/1UIiD-UCHQuDTIvascfvVW5X3mZDg3lfh

## Full graph candidate

Hetzner official June pricing lists limited AX41-1-LTD at USD 67.10/month, zero setup, excluding IPv4 and VAT; availability is explicitly conditional. AX41 product page lists 64 GB RAM and two 512 GB NVMe drives. This is a candidate, not a verified available quote. Mirroring yields roughly one drive of usable capacity; two drives must not be advertised as 1 TB usable without configuration. Streaming decompression and filtering may avoid keeping the raw 400 GB file, but final indexed database capacity and load performance need measured verification. No guarantee that this SKU suffices.

Planning allocation: infrastructure up to USD 80 inclusive of tax/IP, model calls USD 15, contingency USD 5. Total USD 100. These are spending caps, not provider quotes. If the checkout infrastructure price exceeds USD 80, do not provision under this allocation. Identity/account acceptance, actual SKU/stock, disk layout, applicable taxes and access remain unresolved. Model choice/pricing must be separately frozen before calls; USD 15 does not promise all experiments fit.

Sources:
- https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/
- https://www.hetzner.com/dedicated-rootserver/ax41/
- https://github.com/DataArcTech/ToG/blob/main/Freebase/README.md

DigitalOcean counterexample: basic 16 GiB/320 GiB server USD 96/month plus 500 GiB volume USD 50/month = USD 146/month before taxes and model calls. It exceeds the stated budget for a month. Short rentals might reduce spend but import duration and billing need separate planning; not recommended as a confirmed budget solution.

Sources:
- https://www.digitalocean.com/pricing/droplets
- https://www.digitalocean.com/pricing/volumes

## Decision

Keep WebQSP/Freebase and the primary protocol unchanged. Do not buy storage or rent a server yet. Next required gate is an available full-graph server quote within USD 80 inclusive, plus confirmed usable disk and a streaming import plan. Published subgraphs are not silently substituted. No benchmark execution or completion claim follows from this audit.

## Live configurator check

The AX41 configurator displayed AX41-1-LTD in Helsinki, 64 GB RAM, two 512 GB NVMe drives, EUR 57.30/month plus EUR 1.70/month IPv4, total EUR 59.00/month excluding VAT, zero setup. No order was submitted. Billing country and tax remain pending; do not treat the older USD price as an exact current checkout quote. Order-processing documentation explicitly says it does not establish current stock and gives no AX41-specific provisioning time. Availability is still unconfirmed despite the configurable listing.

https://www.hetzner.com/dedicated-rootserver/ax41/configurator/
https://docs.hetzner.com/general/infrastructure-and-availability/order-processing/

Google's official data page describes a 22 GB compressed/250 GB uncompressed dump, whereas the ToG instructions describe 400 GB raw/125 GB filtered. These are source-specific descriptions, not verified sizes for an identical file. Record actual downloaded object version, byte size and checksum and verify WebQSP compatibility before loading. Streaming avoids storing a complete uncompressed intermediate; this does not bound Virtuoso indexed size. Two separate disks could isolate input/staging and database, but the actual database fit must be checked and the layout agreed before provisioning. No confirmed capacity guarantee or completed import is claimed.

https://developers.google.com/freebase

Pending: billing country, checkout total including tax/IP, stock confirmation, tested disk/import sizing, then specific purchase approval. Keep total first-month limit USD 100.

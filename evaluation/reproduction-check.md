# Baseline reproduction checkpoint

10 October 2026. Python 3.12.6, source checkout 79a629a. No runtime dependencies, package installation or model calls. Build tooling is not used; the setuptools packaging requirement is not a frozen install environment.

Run from a fresh checkout root:

```sh
python3 -m flagship_controller.pilot --count 50 --output /tmp/flagship-reproduction
python3 scripts/check_reproduction.py /tmp/flagship-reproduction
```

Verified locally: all 5,600 deterministic per-run outcomes and summary, condition, and paired-comparison JSON match the retained results. Timing, commit metadata and compressed byte representations are not expected to match. This rerun does not add independent questions or benchmark evidence.

Named baseline: verified fixed-order search 0110 (A off, V on, R on, S off), 210/350 grounded, 0/210 unsupported answers, mean 3.503 expansions. Full controller 1111: 210/350 grounded, 0/210 unsupported, mean 3.126 expansions. Neither is a faithful reproduction of a published method.

The public-repository requirement remains unmet: GitHub is private. No visibility change was made. Primary benchmark tasks remain incomplete. See acceptance.md and freebase-options.md.

"""Verify frozen live evidence integrity and label-free recorded metrics."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[1]
for name in ("webqsp-live-001", "webqsp-live-002", "webqsp-live-003"):
    folder = root / "results" / name
    hashes = json.loads((folder / "checksums.json").read_text())
    for filename, expected in hashes.items():
        actual = hashlib.sha256((folder / filename).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"Checksum mismatch: {name}/{filename}")
    manifest = json.loads((folder / "manifest.json").read_text())
    if hashlib.sha256((folder / "runtime-source.py").read_bytes()).hexdigest() != manifest["source_sha256"]:
        raise SystemExit(f"Runtime source mismatch: {name}")
    predictions = [json.loads(line) for line in (folder / "predictions.jsonl").read_text().splitlines() if line.strip()]
    score = json.loads((folder / "pilot-score.json").read_text())
    if len({r["id"] for r in predictions}) != len(predictions) or len(predictions) != score["submitted"]:
        raise SystemExit(f"Prediction IDs/count mismatch: {name}")
    if {r["id"] for r in predictions} != {r["id"] for r in score["rows"]}:
        raise SystemExit(f"Score IDs mismatch: {name}")
    if any(r["terminal"] != "ABSTAIN" or r["answers"] for r in predictions):
        raise SystemExit(f"Unexpected answer in zero-coverage diagnostic: {name}")
    if score["macro_f1"] != 0 or score["em"] != 0:
        raise SystemExit(f"Recorded score mismatch: {name}")
    print(f"{name}: checksums and source verified; {len(predictions)} distinct predictions, zero coverage")
print("Integrity checks passed; official scoring parity and scientific conclusions are outside this check.")

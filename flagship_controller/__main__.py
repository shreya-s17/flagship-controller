import argparse
import json
from pathlib import Path
from .controller import run
from .examples import cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="runs/demo.json")
    args = parser.parse_args()
    results = {}
    for name, (graph, query, budget) in cases().items():
        results[name] = {variant: run(graph, query, adaptive=adaptive, max_expansions=budget)
                         for variant, adaptive in [("controller", True), ("fixed_baseline", False)]}
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({"schema_version": 1, "scope": "synthetic fixtures",
                                      "results": results}, indent=2) + "\n")
    for name, variants in results.items():
        for variant, result in variants.items():
            print(name, variant, result["terminal"], result["answer"],
                  "expansions=", result["trace"][-1]["cost"]["expansions_total"])


if __name__ == "__main__":
    main()

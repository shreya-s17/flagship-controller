#!/bin/sh
set -eu
benchmark_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export PYTHONPATH="$benchmark_root/runtime"
export PYTHONHASHSEED=17
python3 "$benchmark_root/smoke.py" "$benchmark_root"
for benchmark_window in 1 2 3 4 5 6 7 8 9; do
 python3 -m flagship_controller.benchmark_study execute "$benchmark_root/study" --upstream /opt/flagship-upstream/tog-7ccbb92 --max-hours 8
 if [ -f "$benchmark_root/study/completion.json" ]; then exit 0; fi
done
printf '%s\n' 'Nine execution windows complete; retained checkpoint requires a further unchanged resume.'

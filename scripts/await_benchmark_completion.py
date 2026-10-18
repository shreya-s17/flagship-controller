"""One bounded dependent postprocessing job; no inference, tuning or messages."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flagship_controller.benchmark_publication import finalize


def write_status(path, state, **details):
    value = {'state': state, 'observed_utc': datetime.now(timezone.utc).isoformat(), **details}
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n');temporary.replace(path)


def watch(study, gold, output, status, worker_session, max_hours=96, poll_seconds=60):
    study, gold, output, status = map(Path, (study, gold, output, status))
    if not 0 < max_hours <= 96 or not 1 <= poll_seconds <= 60:
        raise ValueError('Bounded wait and polling interval required')
    start = time.monotonic()
    try:
        while True:
            if (study/'completion.json').is_file():
                write_status(status,'auditing_complete_collection',official_test_executed=False)
                result=finalize(study,gold,output)
                write_status(status,'complete_tables_and_blank_review_packs',result=result,
                             submission_ready=False,reviewers_contacted=False)
                return result
            alive=subprocess.run(['tmux','has-session','-t',worker_session],capture_output=True).returncode==0
            if not alive:raise ValueError('Inference worker stopped before full completion; no partial scoring or retry')
            if time.monotonic()-start >= max_hours*3600:
                write_status(status,'wait_window_expired',collection_complete=False,scoring_performed=False)
                return None
            progress=json.loads((study/'progress.json').read_text()) if (study/'progress.json').is_file() else None
            write_status(status,'waiting_for_full_collection',progress=progress,scoring_performed=False)
            time.sleep(poll_seconds)
    except Exception as exc:
        write_status(status,'failed',error_type=type(exc).__name__,message=str(exc),
                     submission_ready=False,automatic_retry=False)
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('study','gold','output','status'):p.add_argument(name,type=Path)
    p.add_argument('--worker-session',required=True);p.add_argument('--max-hours',type=float,default=96)
    a=p.parse_args();watch(a.study,a.gold,a.output,a.status,a.worker_session,a.max_hours)

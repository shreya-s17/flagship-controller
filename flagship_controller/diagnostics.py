"""Prespecified budget and imperfect-verifier stress tests; descriptive only."""
import csv
import json
import gzip
from pathlib import Path
from .engine import Config, LocalEvidence, execute, digest
from .evaluate import score, summarize
from .synthetic import suite


def run(output=Path('results/synthetic-v2')):
    rows=[]
    records=suite(50)
    traces=gzip.open(output/'diagnostic-trajectories.jsonl.gz','wt',encoding='utf8')
    def save(record, result, diagnostic, level, seed):
        traces.write(json.dumps({'question_id':record['id'],'diagnostic':diagnostic,
                                'level':level,'seed':seed,'result':result})+'\n')
    for r in records:
        for cap in (1,2,4,8):
            result=execute(r['query'],LocalEvidence(r['graph']),Config(max_expansions=cap))
            save(r,result,'budget',cap,17)
            row=score(r,result);row.update(diagnostic='budget',level=cap,seed=17);rows.append(row)
        for kind in ('verifier_error_rate','parse_error_rate'):
            for rate in (.05,.15):
                for seed in (17,29,43):
                    run_seed=int(digest([r['id'],seed])[:8],16)
                    c=Config(**{kind:rate,'seed':run_seed})
                    result=execute(r['query'],LocalEvidence(r['graph']),c)
                    save(r,result,kind,rate,seed)
                    row=score(r,result);row.update(diagnostic=kind,level=rate,seed=seed);rows.append(row)
    traces.close()
    summaries={}
    for row in rows:
        key=f"{row['diagnostic']}:{row['level']}"
        summaries.setdefault(key,[]).append(row)
    summary={k:summarize(v) for k,v in summaries.items()}
    with (output/'diagnostics.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (output/'diagnostics.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':run()

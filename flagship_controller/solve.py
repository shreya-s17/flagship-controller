"""Run a declared query over a local graph envelope without gold labels."""
import argparse
import json
from pathlib import Path
from .engine import Config, LocalEvidence, execute

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('input',type=Path)
    p.add_argument('--output',type=Path,default=Path('runs/query.json'))
    p.add_argument('--bits',default='1111',choices=[f'{i:04b}' for i in range(16)])
    p.add_argument('--expansions',type=int,default=8)
    p.add_argument('--checks',type=int,default=32)
    a=p.parse_args();data=json.loads(a.input.read_text())
    result=execute(data['query'],LocalEvidence(data['graph']),
                   Config(*[b=='1' for b in a.bits],max_expansions=a.expansions,max_checks=a.checks))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(result['terminal'],result['answer'],result['reason'])

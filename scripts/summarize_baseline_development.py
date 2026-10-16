"""Offline sanity-check summary. Labels are inaccessible to inference code."""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flagship_controller.official_score import score


def analyze(folder,gold):
    manifest=json.loads((folder/'manifest.json').read_text())
    rows=[json.loads(x) for x in (folder/'predictions.jsonl').read_text().splitlines()]
    if [(r['id'],r['variant']) for r in rows]!=[(r['id'],r['variant']) for r in manifest['order']]:raise ValueError('Incomplete or reordered execution')
    completion=json.loads((folder/'completion.json').read_text())
    if completion['completed']!=len(rows):raise ValueError('Completion count mismatch')
    ids={r['id'] for r in rows if r['id'].startswith('WebQTrn-')}
    annotations=[r for r in map(json.loads,gold.read_text().splitlines()) if r['id'] in ids]
    if {r['id'] for r in annotations}!=ids:raise ValueError('Missing original-case annotations')
    methods={}
    for variant in dict.fromkeys(r['variant'] for r in rows):
        selected=[r for r in rows if r['variant']==variant]
        originals=[r for r in selected if r['id'] in ids]
        def costs(cases):return {k:sum(r['cost'][k] for r in cases) for k in ('graph_calls','model_calls','model_tokens','elapsed_seconds')}
        methods[variant]={'original_training_only':score(originals,annotations),
            'cost_originals':costs(originals),'cost_all':costs(selected),
            'usage_complete_all':all(r['cost']['model_usage_complete'] for r in selected),
            'terminals':dict(Counter(r['terminal'] for r in selected)),
            'unscored_controls':[{'id':r['id'],'terminal':r['terminal'],'answers':r['answers'],'reason':r['reason']} for r in selected if r['id'] not in ids],
            'native_generations':sum(r.get('native_terminal')=='GENERATED' for r in selected),
            'rows':[{'id':r['id'],'terminal':r['terminal'],'answers':r['answers'],'reason':r['reason'],
                'native_response':r.get('native_response'),'normalization':r.get('normalization')} for r in selected]}
    return {'scope':'Purpose-selected development sanity checks; no held-out, significance or published-score reproduction claim',
        'completed_executions':len(rows),'unique_original_training_questions':len(ids),
        'methods':methods,'predictions_sha256':hashlib.sha256((folder/'predictions.jsonl').read_bytes()).hexdigest(),
        'comparison_limits':['same maximum budgets, not equal realized costs','independent linking calls may produce different responses',
            'native text and observed-name ID mapping are distinct','handwritten inverse/no-match controls lack independent labels',
            'semantic controller and ToG adaptation have different answer/search scopes','one seed, small purpose-selected sample',
            'no independent semantic/STOP annotations; no reliability rates inferred']}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path);parser.add_argument('gold',type=Path);args=parser.parse_args()
    print(json.dumps(analyze(args.folder,args.gold),indent=2))

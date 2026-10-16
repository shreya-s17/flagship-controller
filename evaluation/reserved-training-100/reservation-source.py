"""Reserve untouched training questions before inference, without annotations.

This is a dataset reservation, not a method/analysis preregistration. Near-text
matches are review flags, not proof of absence of paraphrase or contamination.
"""
import argparse
from collections import defaultdict
import difflib
import hashlib
import json
from pathlib import Path
import re
import time


def normalized(text):return ' '.join(re.findall(r'\w+',text.casefold()))


def reserve(inputs,output,count=100,seed=17):
    inputs=Path(inputs);output=Path(output)
    if output.exists():raise ValueError('Refuse overwrite')
    records=[json.loads(x) for x in inputs.read_text().splitlines() if x.strip()]
    if count<1 or any(set(r)-{'id','question','split'} for r in records):raise ValueError('Question-only inputs required')
    if len({r['id'] for r in records})!=len(records):raise ValueError('Duplicate IDs')
    seen={normalized(r['question']) for r in records if r['split']!='train_remaining'}
    groups=defaultdict(list)
    for record in records:
        key=normalized(record['question'])
        if record['split']=='train_remaining' and key not in seen:groups[key].append(record)
    keys=sorted(groups,key=lambda key:hashlib.sha256(('feasibility-reserve-v1|'+str(seed)+'|'+key).encode()).hexdigest())
    selected=[]
    for key in keys:
        selected.extend(sorted(groups[key],key=lambda r:r['id']))
        if len(selected)>=count:break
    if len(selected)<count:raise ValueError('Insufficient unreserved training questions')
    comparisons=[r for r in records if r['split'] in ('pilot','calibration','policy')]
    flags=[]
    for record in selected:
        for other in comparisons:
            similarity=difflib.SequenceMatcher(None,normalized(record['question']),normalized(other['question']),autojunk=False).ratio()
            if similarity>=.85:flags.append({'reserved_id':record['id'],'development_id':other['id'],'character_sequence_ratio':similarity})
    output.mkdir(parents=True)
    data=''.join(json.dumps(r)+'\n' for r in selected).encode()
    (output/'inputs.jsonl').write_bytes(data)
    manifest={'status':'DATASET RESERVED; NOT EXECUTED; method, baseline and analysis freeze still required',
              'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'selection_seed':seed,'requested_minimum_questions':count,
              'selected_questions':len(selected),'question_ids':[r['id'] for r in selected],
              'source_inputs_sha256':hashlib.sha256(inputs.read_bytes()).hexdigest(),'reserved_inputs_sha256':hashlib.sha256(data).hexdigest(),
              'source_hashes':{'reservation-source.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
              'selection':'Hash-order normalized-question groups from train_remaining only; group preserved; no annotation, answer or support-based exclusion',
              'near_text_flags':flags,'overlap_audit':'Exact normalized grouping plus character-similarity flags; semantic paraphrase review and pretraining contamination unresolved',
              'execution_gates':['Resolve semantic regressions on development only','Document and sanity-check named external baseline','Independently annotate semantic/STOP cases','Review overlap flags','Freeze executable policies/seeds/budgets/metrics before inference'],
              'official_test_executed':False,'gold_read':False}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (output/'reservation-source.py').write_bytes(Path(__file__).read_bytes())
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('inputs',type=Path);parser.add_argument('output',type=Path);parser.add_argument('--count',type=int,default=100)
    args=parser.parse_args();r=reserve(args.inputs,args.output,args.count)
    print(json.dumps({k:r[k] for k in ('status','selected_questions','reserved_inputs_sha256')},indent=2))

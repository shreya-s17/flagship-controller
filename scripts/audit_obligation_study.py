"""Independent offline guard/pruning ledger checks, not semantic certification."""
import argparse
import hashlib
import json
from pathlib import Path

ALLOWED={'parents':{('people.person.parents','out'),('people.person.children','in')},
         'children':{('people.person.children','out'),('people.person.parents','in')}}
MEMBERSHIP={('location.location.containedby','out'),('location.location.contains','in')}


def admissible(obligation,program):
    if not obligation:return True
    steps=program['steps']
    if obligation['kind']=='kinship':
        return len(steps)==1 and (steps[0]['relation'],steps[0]['direction']) in ALLOWED[obligation['role']]
    if obligation['kind']=='location_membership':
        return any(c['at']==len(steps) and c['anchor']==0 and (c['relation'],c['direction']) in MEMBERSHIP for c in program['constraints'])
    raise ValueError('Unknown declared obligation')


def check_row(row):
    catalog={e['index']:e['program'] for event in row.get('trace',[]) if event['action']=='PROGRAM_CATALOG' for e in event['programs']}
    obligation=row.get('obligation');enabled=row.get('obligation_guard_enabled',True)
    failed=set();selected=None;prunes=[];pending=None;choices=iter([e['prompt']['inputs'] for e in row.get('model_audit',[]) if e.get('prompt',{}).get('instruction','').startswith('Choose a program')])
    for event in row.get('trace',[]):
        action=event['action']
        if action=='OBLIGATION_PRUNE':
            if not enabled or not failed:raise ValueError('Pruning without enabled guard and recorded rejection')
            expected={index for index,p in catalog.items() if index not in failed and admissible(obligation,p)}
            removed=set(catalog)-failed-expected
            if set(event['removed_indices'])!=removed or set(event['remaining_indices'])!=expected:
                raise ValueError('Pruning partition contradicts declared necessary obligation')
            pending=expected;prunes.append(event)
        if action in ('PLAN','REPAIR_PLAN'):
            selected=event['program_index']
            if selected not in catalog or event['program']!=catalog[selected]:raise ValueError('Uncatalogued selected program')
            inputs=next(choices)
            presented={p['index'] for p in inputs['programs']}
            if pending is not None and (selected not in pending or not presented<=pending):raise ValueError('Pruned candidate reintroduced to actual model choice')
            if selected not in presented:raise ValueError('Choice absent from actual prompt')
            pending=None
        if action=='REJECT':
            if selected is None:raise ValueError('Rejection without selected program')
            if event['reason'].startswith(('role_direction_mismatch:','missing_primary_membership:')):
                if not enabled or admissible(obligation,catalog[selected]):raise ValueError('Guard rejects an admissible declared binding')
            failed.add(selected)
    if enabled and row['terminal']=='ANSWER':
        if selected is None or not admissible(obligation,catalog[selected]):raise ValueError('Guarded answer violates declared obligation')
    if not enabled and prunes:raise ValueError('Disabled guard pruned candidates')
    return {'id':row['id'],'seed':row['seed'],'variant':row['variant'],'terminal':row['terminal'],
            'guard_enabled':enabled,'pruning_events':len(prunes),'declared_obligation':obligation,
            'status':'declared-rule/prompt ledger PASS','semantic_validity':'not independently assessed'}


def compare_prefixes(first,second):
    first,second=Path(first),Path(second)
    reports=[]
    for path in sorted((second/'journal').glob('*-prefix.json')):
        a=json.loads((first/'journal'/path.name).read_text())['value'];b=json.loads(path.read_text())['value']
        if a['record']!=b['record'] or a['seed']!=b['seed']:raise ValueError('Different cross-version question/seed')
        def state(packet):
            return {'graph':[{k:e.get(k) for k in ('query','rows','snapshot','sql_state')} for e in packet['internal']['graph_audit']],
                    'provider':[{'payload_sha256':e['payload_sha256'],'raw_content':e['response']['message']['content']} for e in packet['provider_audit']],
                    'catalog':next(e['programs'] for e in packet['capture_result']['trace'] if e['action']=='PROGRAM_CATALOG'),
                    'first_plan':next(e['program'] for e in packet['capture_result']['trace'] if e['action']=='PLAN')}
        equal=state(a)==state(b)
        reports.append({'id':a['record']['id'],'seed':a['seed'],'state_equal':equal})
    return {'scope':'Cross-version captured graph rows, actual request hashes/raw responses, catalogs and first plans; time metadata excluded',
            'prefixes':len(reports),'all_equal':all(r['state_equal'] for r in reports),'rows':reports}


def check(folder,compare_to=None):
    folder=Path(folder);data=(folder/'predictions.jsonl').read_bytes();plan=json.loads((folder/'manifest.json').read_text())
    if hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest()!=(folder/'manifest.sha256').read_text().strip():raise ValueError('Manifest changed')
    rows=list(map(json.loads,data.decode().splitlines()))
    if [(r['id'],r['seed'],r['variant']) for r in rows]!=[(r['id'],r['seed'],r['variant']) for r in plan['order']]:raise ValueError('Incomplete frozen order')
    result={'scope':'Independent recorded guard/pruning and actual-choice ledger; ontology/language rules remain declared engineering priors, NOT independent semantic judgments',
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'predictions_sha256':hashlib.sha256(data).hexdigest(),'records':len(rows),'rows':[check_row(r) for r in rows]}
    if compare_to is not None:result['cross_version_prefixes']=compare_prefixes(compare_to,folder)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path);parser.add_argument('--compare-to',type=Path);args=parser.parse_args()
    print(json.dumps(check(args.folder,args.compare_to),indent=2))

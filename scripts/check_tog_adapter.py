"""No-network compatibility fixtures against separately supplied pinned ToG.

Checks prompts/search transitions and inverse/empty/mediated behavior, not model
quality or equivalence to published scores. No benchmark data are loaded.
"""
import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flagship_controller.tog_adapter import Adapter, load_upstream, normalize_observed_answer, HASHES
from flagship_controller.webqsp_runtime import NS


def check(folder,compact=False,indexed=False):
    checks=[]
    def require(condition,label):
        if not condition:raise AssertionError(label)
        checks.append(label)
    upstream=load_upstream(folder)
    args=SimpleNamespace(width=3)
    prompt=upstream['construct_relation_prune_prompt']('Fixture question?','Topic',['r.a','r.b'],args)
    require(prompt==upstream['extract_relation_prompt']%(3,3)+'Fixture question?\nTopic Entity: Topic\nRelations: r.a; r.b\nA: ', 'relation_prompt_unchanged')
    require(upstream['construct_entity_score_prompt']('Fixture question?','r',['A','B'])==upstream['score_entity_candidates_prompt'].format('Fixture question?','r')+'A; B\nScore: ', 'entity_prompt_unchanged')
    require(upstream['clean_scores']('0.25, 0.75',['A','B'])==[.25,.75],'upstream_entity_score_parser')
    require(upstream['extract_answer']('{Yes}. {A}')=='Yes' and upstream['if_true'](' Yes '),'upstream_stop_parser')
    upstream['id2entity_name_or_type']=lambda node:node
    pruned=upstream['entity_prune'](['m.a','m.b','m.c'],['r']*3,['A','B','C'],['m.topic']*3,[True]*3,[.1,.8,0],args)
    require(pruned[2]==['m.b','m.a'] and pruned[3]==['r','r'],'beam_order_and_zero_score_removal')

    class Graph:
        row_limit=100
        def __init__(self,mode):self.mode=mode;self.expansions=[]
        def paged(self,query,order):
            incoming=query.startswith('SELECT DISTINCT ?relation WHERE { ?x')
            if self.mode=='empty':return []
            if self.mode=='inverse':rels=['r.inverse'] if incoming else []
            else:rels=[] if incoming else ['r.next'] if 'ns:m.mid ' in query else ['r.mediator']
            return [{'relation':{'type':'uri','value':NS+r}} for r in rels]
        def select(self,query):
            node='m.mid' if 'ns:m.mid ' in query else 'm.answer' if 'ns:m.answer ' in query else 'm.topic'
            return [] if node=='m.mid' else [{'name':{'value':'Observed Answer' if node=='m.answer' else 'Topic'}}]
        def expand(self,node,action):
            self.expansions.append((node,action))
            target='m.mid' if action['relation']=='r.mediator' else 'm.answer'
            return [{'target':target,'term':{'type':'uri','value':NS+target}}]
    for mode,responses in [
        ('inverse',['{r.inverse (Score: 1.0)}','{Yes}. {Observed Answer}']),
        ('mediated',['{r.mediator (Score: 1.0)}','{No}. Need more facts.','{r.next (Score: 1.0)}','{Yes}. {Observed Answer}']),
        ('empty',['No relations','No unsupported answer'])]:
        from flagship_controller.compact_tog_adapter import CompactAdapter
        from flagship_controller.indexed_tog_adapter import IndexedAdapter
        pending=list(responses);prompts=[]
        if indexed and mode=='empty': pending.pop(0)
        def direct(instruction,inputs,schema):
            if not pending: raise AssertionError('unexpected structured request')
            names=[r['relation'] for r in inputs['relations']]
            ok,choices=upstream['clean_relations'](pending.pop(0),'m.topic',names)
            require(ok,'indexed_relation_fixture_'+mode+'_'+str(len(pending)))
            return {'selections':[{'index':names.index(c['relation']),'score':c['score']} for c in choices]}
        graph=Graph(mode);events=[];adapter=(IndexedAdapter if indexed else CompactAdapter if compact else Adapter)(folder,graph,SimpleNamespace(model='fixture',direct=direct),lambda action,**kw:events.append({'action':action,**kw}),lambda:None)
        def raw(prompt,*args):
            prompts.append(prompt)
            if not pending:raise AssertionError('unexpected model request')
            return pending.pop(0)
        if indexed:
            from unittest.mock import patch
            with patch('flagship_controller.tog_adapter.TextModel.__call__',side_effect=raw):
                text,chains,stop=adapter.search('Fixture question?',['m.topic'])
        else:
            adapter.ns['run_llm']=raw
            text,chains,stop=adapter.search('Fixture question?',['m.topic'])
        require(not pending,mode+'_request_sequence')
        if mode=='empty':
            require(stop=='half_stop' and not graph.expansions and normalize_observed_answer(text,adapter.names)[0]==[], 'empty_frontier_not_grounded_answer')
        elif mode=='inverse':
            require(graph.expansions==[('m.topic',{'relation':'r.inverse','direction':'in'})], 'inverse_relation_preserved')
            require(stop=='reasoning_yes' and normalize_observed_answer(text,adapter.names)[0]==['m.answer'],'native_stop_and_observed_mapping')
        else:
            require(len(chains)==2 and graph.expansions[-1]==('m.mid',{'relation':'r.next','direction':'out'}),'unnamed_mediator_continuation')
            require([e['stop'] for e in events if e['action']=='REASONING']==[False,True],'upstream_continue_then_stop')
    return {'scope':'offline synthetic compatibility fixtures, no model/benchmark quality claim','adapter':'indexed-spans' if indexed else 'compact-projected' if compact else 'upstream-full','upstream_hashes':HASHES,'passed':len(checks),'checks':checks}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--upstream',type=Path,required=True);parser.add_argument('--compact',action='store_true');parser.add_argument('--indexed',action='store_true');args=parser.parse_args()
    print(json.dumps(check(args.upstream,args.compact,args.indexed),indent=2))

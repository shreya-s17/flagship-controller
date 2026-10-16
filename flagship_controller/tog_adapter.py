"""Bounded local ToG adaptation using hash-verified upstream function bodies.

Upstream source is NOT vendored. This adapter loads definitions from a separately
obtained pinned checkout. Text answers and conservative observed-name ID mapping
are kept separate. This is not reproduction of the paper's model/input setting.
"""
import ast
import hashlib
import json
import math
import random
import re
import time
from pathlib import Path
from types import SimpleNamespace
from .common_linker import link_question
from .webqsp_runtime import Blocked, NS, identifier, post_json

VERSION = 'tog-local-adapter-v1'
UPSTREAM_COMMIT = '7ccbb92e17579f934bb778386230de47eca0ab67'
HASHES = {
    'main_freebase.py':'36139c81008c0ec08f6f1d9b81957fec59d4d7af05d2563704576340246d3e96',
    'freebase_func.py':'f895e5b1ee2f73487641c1f14a6102142284dabafd5fc0074cda890b3c97f5a8',
    'utils.py':'4460752d33b730b2ca084e352ea84c60bb89c93aea349cece11158a8ea5f15c5',
    'prompt_list.py':'954e7f6f79fb08010474340f1fade455bcc3c0cd294270923387d5e703de13f5'}


def load_upstream(folder):
    """Load no imports, datasets, top-level requests or CLI from pinned source."""
    namespace = {'re':re, 'json':json, 'time':time}
    for filename, expected in HASHES.items():
        source = (Path(folder)/filename).read_bytes()
        if hashlib.sha256(source).hexdigest()!=expected:
            raise ValueError('Upstream source mismatch: '+filename)
    for filename in ('prompt_list.py','utils.py','freebase_func.py'):
        tree = ast.parse((Path(folder)/filename).read_text())
        nodes = []
        for node in tree.body:
            if isinstance(node,ast.FunctionDef):
                if node.decorator_list or any(x is not None for x in node.args.defaults):
                    # Only literal defaults occur in the audited source; do not
                    # evaluate arbitrary added expressions even after hash checks.
                    for default in node.args.defaults: ast.literal_eval(default)
                nodes.append(node)
            elif isinstance(node,ast.Assign):
                try: ast.literal_eval(node.value)
                except (ValueError,TypeError): continue
                nodes.append(node)
        exec(compile(ast.Module(body=nodes,type_ignores=[]),str(Path(folder)/filename),'exec'),namespace)
    return namespace


class TextModel:
    """Bounded raw-text transport. Actual provider usage; no silent retries."""
    def __init__(self, model, checkpoint):
        self.shared=model; self.checkpoint=checkpoint
    def __call__(self,prompt,temperature,max_tokens,unused_key,engine):
        m=self.shared; self.checkpoint()
        if m.calls>=m.max_calls or m.tokens>=m.max_tokens: raise Blocked('model_budget')
        if not isinstance(prompt,str) or len(prompt.encode())>64000: raise Blocked('model_context_cap')
        m.calls+=1; started=time.perf_counter()
        messages=[{'role':'system','content':'You are an AI assistant that helps people find information.'},
                  {'role':'user','content':prompt}]
        response=post_json(m.url,{'model':m.model,'stream':False,'messages':messages,
            'options':{'temperature':temperature,'seed':17,'num_predict':min(max_tokens,m.max_tokens-m.tokens)}},120)
        usage=[response.get('prompt_eval_count'),response.get('eval_count')]
        if any(type(x) is not int or x<0 for x in usage):raise Blocked('model_usage_unavailable')
        m.tokens+=sum(usage)
        content=response.get('message',{}).get('content')
        m.audit.append({'prompt_version':VERSION,'prompt':{'messages':messages},'prompt_sha256':hashlib.sha256(json.dumps(messages,sort_keys=True).encode()).hexdigest(),
            'response':content,'input_tokens':usage[0],'output_tokens':usage[1],
            'elapsed_seconds':time.perf_counter()-started,'temperature':temperature,'seed':17})
        if usage[0]>3000:raise Blocked('model_context_budget_exceeded_after_call')
        if m.tokens>m.max_tokens:raise Blocked('model_budget_exceeded_after_call')
        self.checkpoint()
        if not isinstance(content,str):raise Blocked('invalid_text_response')
        return content


def normalize_observed_answer(text, observed_names):
    """Gold-free exact name mapping, never fuzzy/first-match normalization.

    Single brace field first matches a full observed label, preserving commas.
    Multiple answers require semicolons or separate fields. Yes/No are control
    fields. A wrong but uniquely named observed node remains a scored error.
    """
    if not isinstance(text,str):return [],'no_text'
    fields=[f.strip() for f in re.findall(r'\{([^{}]+)\}',text)
            if f.strip().casefold() not in ('yes','no')]
    if not fields:return [],'missing_braced_answer'
    index={}
    for node,names in observed_names.items():
        for name in names:
            index.setdefault(name.casefold().strip(),set()).add(node)
    tokens=[]
    for field in fields:
        if field.casefold() in index:tokens.append(field)
        else:tokens.extend(x.strip() for x in field.split(';') if x.strip())
    answers=[]
    for token in tokens:
        candidates=index.get(token.casefold(),set())
        if len(candidates)!=1:return [],'ambiguous_or_unobserved_answer'
        answers.extend(candidates)
    return list(dict.fromkeys(answers)),'unique_observed_name_mapping' if answers else 'no_answer'


class Adapter:
    def __init__(self,upstream,graph,model,log,checkpoint,seed=17):
        self.ns=load_upstream(upstream);self.graph=graph;self.model=model
        self.log=log;self.checkpoint=checkpoint;self.rng=random.Random(seed)
        self.names={};self.edges=[];self.observed_relations=set()
        self.ns.update(run_llm=TextModel(model,checkpoint),execurte_sparql=self.query,
            id2entity_name_or_type=self.name,entity_search=self.entities,
            SentenceTransformer=self.disabled,compute_bm25_similarity=self.disabled)
        self.args=SimpleNamespace(width=3,depth=3,remove_unnecessary_rel=True,prune_tools='llm',
            temperature_exploration=0,temperature_reasoning=0,max_length=512,
            num_retain_entity=5,opeani_api_keys='',LLM_type=model.model)
    @staticmethod
    def disabled(*args,**kwargs):raise Blocked('disabled_optional_pruner')
    def query(self,query):
        self.checkpoint()
        # Called only by relation_search_prune: require the known shape, then
        # paginate distinct predicates, excluding non-Freebase namespace IDs.
        match=re.search(r'ns:([A-Za-z_][A-Za-z0-9_.]*)\s+\?relation\s+\?x',query)
        incoming=re.search(r'\?x\s+\?relation\s+ns:([A-Za-z_][A-Za-z0-9_.]*)',query)
        if bool(match)==bool(incoming):raise Blocked('unexpected_upstream_query_shape')
        node=(match or incoming).group(1);identifier(node)
        triple=identifier(node)+' ?relation ?x' if match else '?x ?relation '+identifier(node)
        rows=self.graph.paged('SELECT DISTINCT ?relation WHERE { '+triple+' . '
            'FILTER(STRSTARTS(STR(?relation),"'+NS+'")) }','?relation')
        direction='out' if match else 'in'
        for row in rows:self.observed_relations.add((node,row['relation']['value'].removeprefix(NS),direction))
        return rows
    def name(self,node):
        identifier(node)
        if node not in self.names:
            self.checkpoint()
            rows=self.graph.select('SELECT DISTINCT ?name WHERE { '+identifier(node)+
                ' ns:type.object.name ?name . FILTER(LANG(?name)="en") } ORDER BY ?name LIMIT '+str(self.graph.row_limit+1))
            self.names[node]=[r['name']['value'] for r in rows]
        return self.names[node][0] if self.names[node] else 'UnName_Entity'
    def entities(self,node,relation,head=True):
        direction='out' if head else 'in'
        if (node,relation,direction) not in self.observed_relations:raise Blocked('unobserved_baseline_relation')
        self.checkpoint();edges=self.graph.expand(node,{'relation':relation,'direction':direction})
        self.edges.extend(edges)
        # Pinned ToG keeps m. nodes; literals and g. nodes are not traversed.
        ids=[e['target'] for e in edges if e['term']['type']=='uri' and e['target'].startswith('m.')]
        self.log('ENTITY_RETRIEVE',node=node,relation=relation,direction=direction,candidates=ids,
                 non_m_nodes_excluded=len(edges)-len(ids))
        return ids
    def search(self,question,anchors):
        ns=self.ns;args=self.args;topic={node:self.name(node) for node in anchors}
        chains=[];pre_relations=[];pre_heads=[-1]*len(topic)
        for depth in range(1,args.depth+1):
            relations=[]
            for i,node in enumerate(topic):
                self.checkpoint()
                choices=ns['relation_search_prune'](node,topic[node],pre_relations,pre_heads[i],question,args)
                if len(choices)>args.width:raise Blocked('baseline_relation_width')
                for choice in choices:
                    direction='out' if choice['head'] else 'in'
                    if (node,choice['relation'],direction) not in self.observed_relations or not math.isfinite(choice['score']) or not 0<=choice['score']<=1:
                        raise Blocked('invalid_baseline_relation')
                relations.extend(choices)
                self.log('RELATION_PRUNE',depth=depth,node=node,choices=choices)
            history=[[],[],[],[],[],[]]
            for relation in relations:
                ids=self.entities(relation['entity'],relation['relation'],relation['head'])
                if len(ids)>=20:
                    original=list(ids);ids=self.rng.sample(ids,args.num_retain_entity)
                    self.log('SEEDED_SUBSAMPLE',depth=depth,available=original,selected=ids,seed=17)
                if not ids:continue
                # Fix upstream alignment bug: it removes unknown names without
                # removing their IDs. Keep pairs aligned before the unchanged
                # scoring function. All-unknown mediator sets remain allowed.
                names=[self.name(node) for node in ids]
                if any(n!='UnName_Entity' for n in names):
                    ids=[node for node,n in zip(ids,names) if n!='UnName_Entity']
                scores,names,ids=ns['entity_score'](question,ids,relation['score'],relation['relation'],args)
                if len(scores)!=len(names) or len(scores)!=len(ids) or any(not math.isfinite(s) or not 0<=s<=1 for s in scores):
                    raise Blocked('invalid_baseline_entity_scores')
                self.log('ENTITY_SCORE',depth=depth,ids=ids,names=names,scores=scores)
                history=ns['update_history'](names,relation,scores,ids,*history)
            if not history[0]:
                self.log('HALF_STOP',depth=depth,reason='no_new_candidates')
                return ns['generate_answer'](question,chains,args),chains,'half_stop'
            flag,chain,ids,pre_relations,pre_heads=ns['entity_prune'](*[history[i] for i in (3,2,0,4,5,1)],args)
            chains.append(chain)
            self.log('ENTITY_PRUNE',depth=depth,chain=chain,ids=ids,relations=pre_relations,heads=pre_heads)
            if not flag:
                return ns['generate_answer'](question,chains,args),chains,'zero_pruned_score'
            stop,text=ns['reasoning'](question,chains,args)
            self.log('REASONING',depth=depth,stop=stop,response=text)
            if stop:return text,chains,'reasoning_yes'
            finish,ids=ns['if_finish_list'](ids)
            if finish:return ns['generate_answer'](question,chains,args),chains,'finished_frontier'
            topic={node:self.name(node) for node in ids}
        # Preserve upstream's final direct-generation fallback and record that it
        # does not use graph paths. ID mapping below is still evidence restricted.
        self.log('DIRECT_FALLBACK',reason='depth_exhausted; upstream discards paths for final generation')
        return ns['generate_without_explored_paths'](question,args),chains,'depth_direct_fallback'


def run(record,graph,model,upstream,seconds=600,on_event=None,*,adapter_factory=Adapter,project_native=False):
    started=time.perf_counter();trace=[]
    def checkpoint():
        if time.perf_counter()-started>seconds:raise Blocked('wall_time_budget')
    def log(action,**details):
        trace.append({'step':len(trace),'action':action,**details,'cost':{'graph_calls':graph.calls,'model_calls':model.calls,'model_tokens':model.tokens}})
        if on_event:on_event(trace[-1])
        checkpoint()
    result={'id':record['id'],'split':record.get('split'),'variant':'tog-local','terminal':'ABSTAIN','answers':[],
        'runtime_version':'tog-compact-projected-v2' if project_native else VERSION,'confidence':None,'native_response':None,'scope':'bounded question-only Qwen adaptation; not original-paper reproduction'}
    adapter=None
    try:
        _,anchors=link_question(record,graph,model,log)
        adapter=adapter_factory(upstream,graph,model,log,checkpoint)
        text,chains,stop=adapter.search(record['question'],anchors)
        answers,status=normalize_observed_answer(text,adapter.names)
        result.update(native_response=text,native_terminal='GENERATED',chains=chains,search_stop=stop,
            normalization=status,observed_name_map=adapter.names,observed_edges=adapter.edges)
        if project_native:
            from .compact_tog_adapter import validate_projection, VERSION as compact_version
            from .structured_runtime import object_schema, BOOLEAN
            result['runtime_version']=compact_version
            beam=next((e['ids'] for e in reversed(trace) if e['action']=='ENTITY_PRUNE' and e['ids']),[])
            candidates=[{'entity':node,'names':adapter.names.get(node,[])} for node in dict.fromkeys(beam) if adapter.names.get(node)]
            if candidates:
                checkpoint()
                schema=object_schema({'supported':BOOLEAN,'selections':{'type':'array','maxItems':len(candidates),
                    'items':object_schema({'index':{'type':'integer','enum':list(range(len(candidates)))},'quote':{'type':'string','maxLength':300}})}})
                selection=model.direct('Extract only answers explicitly concluded by the native response. Choose supplied final-beam candidate indices ONLY when their observed full name is in a verbatim quote from the response AND the response concludes it is an answer. Do not add facts, infer an answer, or choose nodes mentioned only as context or rejected alternatives. If unsupported or ambiguous, supported false and empty selections. This is extraction, not a second attempt to answer the question.',
                    {'question':record['question'],'native_response':text,'candidates':candidates},schema)
                log('NATIVE_ANSWER_EXTRACTION',candidates=candidates,selection=selection)
                answers,status=validate_projection(selection,candidates,text)
            else:answers,status=[],'no_named_final_beam_candidates'
            result['normalization']=status
        if answers:result.update(terminal='ANSWER',answers=answers,reason='observed_name_mapping_only_not_semantic_certification')
        else:result['reason']='answer_normalization:'+status
    except Blocked as exc:result['reason']=str(exc)
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:result['reason']='runtime_error:'+type(exc).__name__
    if adapter is not None:
        result.setdefault('observed_name_map',adapter.names);result.setdefault('observed_edges',adapter.edges)
    result.update(trace=trace,graph_audit=graph.audit,model_audit=model.audit,
        cost={'graph_calls':graph.calls,'model_calls':model.calls,'model_tokens':model.tokens,
              'model_usage_complete':model.calls==len(model.audit),'elapsed_seconds':time.perf_counter()-started})
    return result

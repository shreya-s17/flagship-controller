"""Closed relational obligations and observed primary-anchor conjunctions.

Development-only extension. The frozen v11 compiler/controller remains intact.
No labels, question IDs, gold predicates/queries or answer lookup enter inference.
The ontology/language mappings below are explicit incomplete engineering priors.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import time
from . import structured_runtime as base, semantic_runtime, common_linker, study_runtime as shared
from .webqsp_runtime import Blocked,NS,identifier

VERSION='closed-obligation-controller-v2'
REPAIR_ADMISSION='After an explicit closed-obligation rejection, remove every candidate violating that same necessary obligation before the second choice'
POLICIES=('fixed','repair','obligation-guard-off')
PARENT_SHA256='e07fd12eb5df266a0d6bc2ae8c7785df7e15b209790ad03fb2bc33dbcbe023b0'
EXTRACT=base.EXTRACT
validate_question=base.validate_question
rank_relations=base.rank_relations
digest=shared.digest

ROLE_BINDINGS={
 'parents':{('people.person.parents','out'),('people.person.children','in')},
 'children':{('people.person.children','out'),('people.person.parents','in')}}
MEMBERSHIP={('location.location.containedby','out'),('location.location.contains','in')}


def question_obligation(question,mentions,category):
    # Narrow full-string grammar, bound to the single parsed copied anchor.
    # Unrecognized/nested phrasing is unhandled, not a semantic guarantee.
    if len(mentions)!=1:return None
    name=mentions[0]['mention'].strip().casefold()
    text=question.strip().rstrip('?.!').strip().casefold()
    patterns=[r"who (?:are|were) (?P<name>.+?)[’']s (?P<role>parents|children)",
              r"who (?:are|were) the (?P<role>parents|children) of (?P<name>.+)",
              r"name the (?P<role>parents|children) of (?P<name>.+)"]
    if category=='person':
        for pattern in patterns:
            match=re.fullmatch(pattern,text)
            if match and match['name'].strip()==name:
                return {'kind':'kinship','role':match['role'],'anchor':0,
                        'source':'closed copied-question grammar; declared ontology prior, not learned or calibrated'}
    if category=='location':
        match=re.fullmatch(r'(?:what to see|which attractions are|what attractions are) in (?P<name>.+?)(?P<extra> downtown)?',text)
        if match and match['name'].strip()==name:
            return {'kind':'location_membership','anchor':0,
                    'unmodeled_qualifier':match['extra'].strip() if match['extra'] else None,
                    'source':'closed location-in-anchor grammar; membership is necessary, finer geographic scope remains unchecked'}
    return None


def check_obligation(obligation,program):
    if obligation is None:return
    steps=program['steps']
    if obligation['kind']=='kinship':
        allowed=ROLE_BINDINGS[obligation['role']]
        if len(steps)!=1 or (steps[0]['relation'],steps[0]['direction']) not in allowed:
            description=' or '.join(r+' '+d for r,d in sorted(allowed))
            raise Blocked('role_direction_mismatch: requested '+obligation['role']+'; allowed one-hop bindings '+description)
    elif obligation['kind']=='location_membership':
        if not any(c['at']==len(steps) and c['anchor']==0 and (c['relation'],c['direction']) in MEMBERSHIP
                   for c in program.get('constraints',[])):
            raise Blocked('missing_primary_membership: require observed endpoint containment to anchor0; choose a catalog candidate with that constraint')
    else:raise Blocked('unknown_obligation_kind')


def compile_program(anchors,program,row_limit=100):
    if not isinstance(program,dict) or set(program)-{'steps','constraints','supported','explanation'}:
        raise Blocked('invalid_program')
    steps=program.get('steps');constraints=program.get('constraints',[])
    if not isinstance(steps,list) or not 1<=len(steps)<=4 or not isinstance(constraints,list) or len(constraints)>3:
        raise Blocked('invalid_program')
    triples=[];used=set()
    for i,action in enumerate(steps):
        if not isinstance(action,dict) or set(action)!={'relation','direction'} or action['direction'] not in ('in','out'):
            raise Blocked('invalid_program')
        identifier(action['relation']);a,b='v'+str(i),'v'+str(i+1)
        triples.append((a,action['relation'],b) if action['direction']=='out' else (b,action['relation'],a))
    for c in constraints:
        if not isinstance(c,dict) or set(c)!={'at','relation','direction','anchor'}:
            raise Blocked('invalid_constraint')
        if type(c['at']) is not int or not 0<=c['at']<=len(steps) or type(c['anchor']) is not int or not 0<=c['anchor']<len(anchors) or c['direction'] not in ('in','out'):
            raise Blocked('invalid_constraint')
        identifier(c['relation']);a,b='v'+str(c['at']),anchors[c['anchor']]
        triples.append((a,c['relation'],b) if c['direction']=='out' else (b,c['relation'],a));used.add(c['anchor'])
    if used-{0} != set(range(1,len(anchors))):raise Blocked('unbound_question_anchor')
    def term(t):return '?'+t if re.fullmatch(r'v[0-4]',t) else identifier(t)
    variables=' '.join('?v'+str(i) for i in range(1,len(steps)+1))
    clauses=['BIND('+identifier(anchors[0])+' AS ?v0)']+[term(a)+' '+identifier(r)+' '+term(b)+' .' for a,r,b in triples]
    query='SELECT DISTINCT '+variables+' WHERE { '+' '.join(clauses)+' } ORDER BY '+variables+' LIMIT '+str(row_limit+1)
    return query,triples


class ObligationGraph(shared.StudyGraph):
    def __init__(self,*args,guard_enabled=True,**kwargs):
        super().__init__(*args,**kwargs)
        self.guard_enabled=guard_enabled;self.obligation=None;self.primary_join_options=[]

    def catalog(self,question,roots,schema,anchors,mentions,connections):
        self.obligation=question_obligation(question,mentions,self.question_contract['answer_category'])
        catalog=base.program_catalog(roots,schema,len(anchors),connections,question)
        # Observe closing edges on one-hop endpoints. No model/generated/gold
        # predicate or answer is injected. At most3 additional graph queries.
        if self.obligation and self.obligation['kind']=='location_membership':
            additions=[]
            for root in roots:
                program={'supported':True,'steps':[root],'constraints':[]}
                query,_=compile_program([anchors[0]],program,self.row_limit)
                body=query.split(' WHERE { ',1)[1].rsplit(' } ORDER BY ',1)[0]
                rows=self.select('SELECT DISTINCT ?relation ?direction WHERE { '+body+' { '
                    '{ ?v1 ?relation '+identifier(anchors[0])+' . BIND("out" AS ?direction) } UNION '
                    '{ '+identifier(anchors[0])+' ?relation ?v1 . BIND("in" AS ?direction) } } '
                    'FILTER(STRSTARTS(STR(?relation),"'+NS+'")) } ORDER BY ?relation ?direction LIMIT '+str(self.row_limit+1))
                observed=[{'at':1,'relation':r['relation']['value'].removeprefix(NS),
                    'direction':r['direction']['value'],'anchor':0} for r in rows]
                for constraint in observed:
                    if constraint not in self.primary_join_options:self.primary_join_options.append(constraint)
                # Closed membership operator selects only actually observed
                # ontology bindings. Other observed joins remain in the audit.
                for constraint in observed:
                    if (constraint['relation'],constraint['direction']) not in MEMBERSHIP:continue
                    p={**program,'constraints':[constraint],
                        'explanation':'Observed endpoint membership in the copied primary anchor'}
                    expected=next((r['expected'] for r in schema if r['root']==root['relation']),None)
                    additions.append({'index':len(catalog)+len(additions),'program':p,'answer_expected_type':expected,'key':json.dumps(p,sort_keys=True)})
            # Prioritize bounded observed membership candidates when this closed
            # question grammar requires membership; changed hypothesis/ranking.
            catalog=additions+catalog
        selected=base.rank_catalog(question,catalog,limit=20)
        # rank_catalog uses original indices; new candidates must survive the
        # old index tiebreak rather than disappear merely because appended.
        if self.obligation and self.obligation['kind']=='location_membership':
            membership=[c for c in catalog if any(j.get('anchor')==0 for j in c['program']['constraints'])]
            selected=(membership+[c for c in selected if c not in membership])[:20]
        for i,c in enumerate(selected):c['index']=i
        return selected

    def check_obligation(self,program):
        if self.guard_enabled:check_obligation(self.obligation,program)

    def execute(self,anchors,program):
        query,triples=compile_program(anchors,program,self.row_limit)
        rows=self.select(query)
        if not rows:return [],[]
        witnesses=[];answers={}
        for row in rows:
            terms={'v0':{'type':'uri','value':NS+anchors[0]},**row};edges=[]
            for source,relation,target in triples:
                a=terms[source] if source.startswith('v') else {'type':'uri','value':NS+source}
                b=terms[target] if target.startswith('v') else {'type':'uri','value':NS+target}
                if a['type']!='uri':raise Blocked('literal_subject')
                edge={'source':a,'relation':relation,'target':b,'provenance':{'snapshot':self.snapshot,'query_index':len(self.audit)-1}}
                edge['id']=hashlib.sha256(json.dumps(edge,sort_keys=True).encode()).hexdigest();edges.append(edge)
            answer=terms['v'+str(len(program['steps']))]
            if answer['type']=='uri' and not answer['value'].startswith(NS):raise Blocked('external_uri_unsupported')
            answers[json.dumps(answer,sort_keys=True)]=answer['value'].removeprefix(NS) if answer['type']=='uri' else answer['value']
            witnesses.append(edges)
        result=list(dict.fromkeys(answers.values()))
        if set(result)&set(anchors):raise Blocked('reflexive_anchor_answer')
        self.answer_cards=[]
        for value in result[:5]:
            if not value.startswith(('m.','g.')):
                self.answer_cards.append({'value':value,'kind':'literal'});continue
            cards=self.select('SELECT DISTINCT ?name ?type WHERE { '+base.identifier(value)+' ns:type.object.name ?name . '
                'FILTER(LANG(?name)="en") OPTIONAL { '+base.identifier(value)+' ns:type.object.type ?type . } } LIMIT '+str(self.row_limit+1))
            self.answer_cards.append({'value':value,'names':sorted({r['name']['value'] for r in cards}),
                'observed_types':sorted({r['type']['value'].removeprefix(NS) for r in cards if 'type' in r})})
        return result,witnesses

    def join_hints(self,anchors,program):
        # The new primary conjunction comes from the recorded pre-plan join
        # inventory. Retain legacy secondary-anchor failure acquisition only.
        return super().join_hints(anchors,program) if len(anchors)>1 else []


def run(record,graph,model,variant='repair',max_attempts=2,seconds=600,on_event=None):
    started=time.perf_counter();trace=[];witnesses=[];answers=[];reason=None
    def log(action,**details):
        trace.append({'step':len(trace),'action':action,**details,'cost':{'graph_calls':graph.calls,'model_calls':model.calls,'model_tokens':model.tokens}})
        if on_event:on_event(trace[-1])
        if time.perf_counter()-started>seconds:raise Blocked('wall_time_budget')
    result={'id':record['id'],'split':record.get('split'),'variant':variant,'terminal':'ABSTAIN','answers':[],
            'confidence':None,'scope':'schema-typed one/two-hop conjunctive paths with model semantic gate; not general WebQSP'}
    try:
        validate_question(record)
        parsed=model.ask(EXTRACT,{'question':record['question']});log('PARSE',parsed=parsed)
        mentions=parsed.get('anchors')
        if parsed.get('supported') is not True or not isinstance(mentions,list) or not 1<=len(mentions)<=3:
            raise Blocked('unsupported_parse')
        if not isinstance(parsed.get('obligations'),list) or not parsed['obligations']:raise Blocked('missing_obligations')
        # Closed-class answer categories are not named anchors. This guard changes
        # parsing only, never injects an entity or answer. Preserve the rejection log.
        categories={'movie','movies','film','films','song','songs','language','languages','postcode','postal code','birthplace','character','characters'}
        excluded=[a for a in mentions if a.get('mention','').lower().strip() in categories]
        if excluded:log('EXCLUDE_ANSWER_CATEGORY',excluded=excluded)
        mentions=[a for a in mentions if a not in excluded]
        if not mentions:raise Blocked('no_named_anchor')
        anchors=[];anchor_connections={}
        for a in mentions:
            mention=a.get('mention');hint=a.get('type_hint')
            if not isinstance(mention,str) or mention.casefold() not in record['question'].casefold() or mention.strip().rstrip('?').casefold()==record['question'].strip().rstrip('?').casefold():raise Blocked('invalid_topic_mention')
            candidates,predicate=graph.typed_link(mention,hint);log('LINK',mention=mention,type_hint=hint,candidates=candidates,predicate=predicate)
            if not candidates:raise Blocked('entity_not_found')
            if len(candidates)==1:anchors.append(candidates[0]);continue
            cards=graph.cards(candidates,anchors[0] if anchors else None)
            choice=model.ask('Choose only one supplied entity for the mentioned topic from the question and observed descriptions. Return JSON {"entity":string,"supported":boolean}. Ambiguity unresolved => supported false. Do not answer the question.',{'question':record['question'],'mention':mention,'candidates':cards})
            log('DISAMBIGUATE',cards=cards,choice=choice)
            if choice.get('supported') is not True or choice.get('entity') not in candidates:raise Blocked('unresolved_entity')
            anchors.append(choice['entity'])
            anchor_connections[str(len(anchors)-1)]=next(c.get('observed_two_edge_connections',[]) for c in cards if c['entity']==choice['entity'])
        inventory=graph.inventory(anchors[0])
        available=rank_relations(record['question'],inventory,[a['type_hint'] for a in mentions])
        log('INVENTORY',entity=anchors[0],inventory=inventory,available=available,retrieval='question-token-and-type lexical ranking; top32 hypothesis space')
        choice=model.ask('Select up to THREE first-step relations from available for the question. Return JSON {"roots":[{"relation":string,"direction":"out|in"}]}. Preserve all question obligations. No invented relations.',{'question':record['question'],'obligations':parsed['obligations'],'available':available})
        roots=choice.get('roots')
        if not isinstance(roots,list) or not 1<=len(roots)<=3 or any(r not in available for r in roots):raise Blocked('invalid_root_selection')
        schema=graph.schema(roots);log('SCHEMA',roots=roots,schema=schema)
        context={'question':record['question'],'obligations':parsed['obligations'],'anchors':[dict(mentions[i],index=i) for i in range(len(anchors))],'roots':roots,'schema':schema,'observed_anchor_connections':anchor_connections}
        catalog=graph.catalog(record['question'],roots,schema,anchors,mentions,anchor_connections)
        log('PRIMARY_ANCHOR_JOIN_INVENTORY',options=graph.primary_join_options,obligation=graph.obligation)
        if not catalog:raise Blocked('no_grounded_program_catalog')
        log('PROGRAM_CATALOG',programs=catalog,retrieval='schema catalog, answer-type lexical prior, top20; hypothesis space is restricted')
        failures=[]
        for attempt in range(max_attempts if variant=='repair' else 1):
            failed={json.dumps(f['program'],sort_keys=True) for f in failures}
            available_programs=[{k:v for k,v in c.items() if k!='key'} for c in catalog if c['key'] not in failed]
            if failures and graph.guard_enabled and graph.obligation and any(f['reason'].startswith(('role_direction_mismatch:','missing_primary_membership:')) for f in failures):
                permitted=[];removed=[]
                for candidate in available_programs:
                    try:check_obligation(graph.obligation,candidate['program']);permitted.append(candidate)
                    except Blocked:removed.append(candidate['index'])
                available_programs=permitted
                log('OBLIGATION_PRUNE',removed_indices=removed,remaining_indices=[c['index'] for c in permitted],
                    reason='Propagate the same declared necessary obligation after explicit rejection; no answer/gold feedback')
            if not available_programs:raise Blocked('program_catalog_exhausted')
            choice=model.ask('Choose a program whose steps and answer_expected_type answer the question, preserving every named constraint. Return JSON {"program_index":integer}. The program is schema-typed, but its semantics may still be wrong. For a role question choose a character result, not an actor or film; for a set of works choose works, not performances. Rejecting a failed program makes it unavailable; do not treat nonempty results as automatically correct. Use observed failure feedback to revise the choice.',
                {'question':record['question'],'obligations':parsed['obligations'],'anchors':context['anchors'],
                 'programs':[{'index':c['index'],'steps':[a['relation']+' '+a['direction'] for a in c['program']['steps']],
                     'constraints':c['program']['constraints'],'answer_expected_type':c['answer_expected_type']} for c in available_programs],
                 'previous_failures':[{'program':f['program'],'reason':f['reason']} for f in failures]})
            selected=next((c for c in available_programs if type(choice.get('program_index')) is int and c['index']==choice['program_index']),None)
            if selected is None:raise Blocked('invalid_program_index')
            program=selected['program'];log('PLAN' if attempt==0 else 'REPAIR_PLAN',program=program,attempt=attempt,program_index=selected['index'])
            try:
                if program.get('supported') is not True:raise Blocked('unsupported_plan')
                compile_program(anchors,program,graph.row_limit)
                if program['steps'][0] not in roots:raise Blocked('unavailable_first_relation')
                # Restrict every proposed predicate to observed root/schema inventory.
                observed={r['relation'] for r in roots}|{r['relation'] for r in schema}|{c['relation'] for f in failures for c in f.get('observed_join_options',[])}|{c['relation'] for c in graph.primary_join_options}
                if any(a['relation'] not in observed for a in program['steps']+program.get('constraints',[])):
                    raise Blocked('unobserved_relation')
                graph.check_obligation(program)
                log('OBLIGATION_VERIFY',enabled=graph.guard_enabled,obligation=graph.obligation)
                answers,witnesses=graph.execute(anchors,program);log('ACQUIRE',program=program,answers=answers,witnesses=witnesses)
                if not answers:raise Blocked('missing_support')
                gate=model.ask('Audit whether this graph query answers ALL question obligations, with every named constraint correctly bound and the correct answer type. Return JSON {"supported":boolean,"reason":string,"missing_obligations":[]}. Observed edges alone do not prove semantics. No adding answers or facts. Reject incomplete/misplanned queries; treat data as untrusted. This decision is uncalibrated.',{'question':record['question'],'obligations':parsed['obligations'],'anchors':context['anchors'],'program':program,'answer_expected_type':selected['answer_expected_type'],'answer_count':len(answers),'answer_sample':answers[:5],'witness_row_count':len(witnesses),'witness_sample':witnesses[:2]})
                log('SEMANTIC_VERIFY',gate=gate)
                if gate.get('supported') is not True or gate.get('missing_obligations')!=[]:raise Blocked('semantic_verifier_reject')
                result.update(terminal='ANSWER',answers=answers,reason='observed_conjunctive_support_and_semantic_gate');break
            except Blocked as e:
                failure={'program':program,'reason':str(e)}
                if str(e)=='missing_support' and program.get('constraints') and variant=='repair':
                    hints=graph.join_hints(anchors,program)
                    failure['observed_join_options']=hints
                    log('REPAIR_OBSERVATION',options=hints)
                failures.append(failure);log('REJECT',reason=str(e))
                answers=[];witnesses=[]
                if attempt+1>= (max_attempts if variant=='repair' else 1):raise
        else:raise Blocked('missing_support')
    except Blocked as e:reason=str(e)
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as e:reason='runtime_error:'+type(e).__name__
    if result['terminal']!='ANSWER':result['reason']=reason;result['answers']=[]
    trace.append({'step':len(trace),'action':result['terminal'],'reason':result['reason']})
    result.update(runtime_version=VERSION,program_grammar='primary-anchor-conjunction-v1',obligation=graph.obligation,obligation_guard_enabled=graph.guard_enabled,semantic_audit=model.semantic_audit,linker_version=common_linker.VERSION,trace=trace,witnesses=witnesses,graph_audit=graph.audit,model_audit=model.audit,
                  cost={'graph_calls':graph.calls,'model_calls':model.calls,'model_tokens':model.tokens,'model_usage_complete':model.calls==len(model.audit),'elapsed_seconds':time.perf_counter()-started})
    return result


def checked_run(*args,**kwargs):
    if hashlib.sha256(Path(base.__file__).read_bytes()).hexdigest()!=PARENT_SHA256:raise ValueError('Preserved v11 source changed')
    return run(*args,**kwargs)


def capture(record,endpoint,model_url,model_name,snapshot,seed,on_event=None,directed_audit=False):
    started=time.perf_counter();graph=ObligationGraph(endpoint,snapshot,max_calls=80)
    model=shared.StudyModel(model_url,model_name,graph=graph,seed=seed,max_calls=10,max_tokens=16000)
    def event(item):
        if on_event:on_event(item)
        if item['action']=='PLAN':raise Blocked('shared_state_capture_boundary')
    result=checked_run(record,graph,model,variant='fixed',on_event=event)
    prefix={'graph_audit':copy.deepcopy(graph.audit),'provider_audit':copy.deepcopy(model.provider_audit),
            'model_audit':copy.deepcopy(model.audit),'seconds':time.perf_counter()-started,
            'cost':{'graph_calls':graph.calls,'model_calls':model.calls,'model_tokens':model.tokens}}
    return {'record':record,'seed':seed,'model':model_name,'snapshot':snapshot,'link':None,'internal':prefix,
            'internal_ready':result['reason']=='shared_state_capture_boundary','capture_result':result,'provider_audit':model.provider_audit}


def continue_policy(packet,policy,endpoint,model_url,on_event=None):
    if policy not in POLICIES:raise ValueError('Unknown obligation policy')
    if not packet['internal_ready']:
        result=copy.deepcopy(packet['capture_result']);result.update(variant=policy,provider_audit=packet['provider_audit'],policy_continuation_executed=False)
        result['cost'].update(physical_new_model_calls=0,physical_new_graph_calls=0);return result
    prefix=packet['internal']
    graph=ObligationGraph(endpoint,packet['snapshot'],prefix=prefix['graph_audit'],max_calls=80,guard_enabled=policy!='obligation-guard-off')
    model=shared.StudyModel(model_url,packet['model'],graph=graph,seed=packet['seed'],prefix=prefix['provider_audit'],max_calls=10,max_tokens=16000)
    result=checked_run(packet['record'],graph,model,variant='fixed' if policy=='fixed' else 'repair',
                       seconds=max(0.,600-prefix['seconds']),on_event=on_event)
    if graph.cursor!=len(graph.saved) or model.cursor!=len(model.prefix) or 'shared_state_' in result['reason']:
        raise ValueError('Common prefix replay mismatch')
    actual=result['cost']['elapsed_seconds']
    result['cost'].update(physical_execution_seconds=actual,charged_common_prefix_seconds=prefix['seconds'],
        elapsed_seconds=prefix['seconds']+actual,physical_new_graph_calls=graph.calls-graph.cursor,physical_new_model_calls=model.physical_attempts)
    result.update(variant=policy,provider_audit=model.provider_audit,policy_continuation_executed=True,
        shared_state={'replayed_graph_calls':graph.cursor,'replayed_model_calls':model.cursor,'seed':packet['seed'],
        'prefix_kind':'through_first_plan','latency':'original prefix plus replay/continuation; not fresh end-to-end latency'})
    return result

import copy
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from flagship_controller import obligation_runtime as runtime
from flagship_controller.webqsp_runtime import Blocked,NS
from flagship_controller.witness_audit import audit


def program(direction='out',relation='people.person.parents',constraints=None):
    return {'supported':True,'steps':[{'relation':relation,'direction':direction}],
            'constraints':constraints or [],'explanation':'fixture'}


class ObligationTests(unittest.TestCase):
    def test_both_kinship_directions_and_equivalent_inverse_predicates(self):
        for role in ('parents','children'):
            contract=runtime.question_obligation(f"Who are Ada's {role}?",[{'mention':'Ada'}],'person')
            self.assertEqual(contract['role'],role)
            for relation in ('people.person.parents','people.person.children'):
                for direction in ('in','out'):
                    if (relation,direction) in runtime.ROLE_BINDINGS[role]:
                        runtime.check_obligation(contract,program(direction,relation))
                    else:
                        with self.assertRaisesRegex(Blocked,'role_direction_mismatch'):
                            runtime.check_obligation(contract,program(direction,relation))

    def test_full_copied_anchor_binding_not_substring_or_question_id(self):
        for text in ('Who are the parents of Ada?', 'Name the parents of Ada.'):
            self.assertEqual(runtime.question_obligation(text,[{'mention':'Ada'}],'person')['role'],'parents')
        for text in ('Who are the parents of Ada and Bob?', "Who are Ada's parents' children?", 'What did Children of Ada write?'):
            self.assertIsNone(runtime.question_obligation(text,[{'mention':'Ada'}],'person'))
        self.assertIsNone(runtime.question_obligation("Who are Ada's parents?",[{'mention':'Ada'},{'mention':'Bob'}],'person'))

    def test_unhandled_question_does_not_acquire_false_obligation(self):
        self.assertIsNone(runtime.question_obligation('Where was Ada born?',[{'mention':'Ada'}],'location'))
        runtime.check_obligation(None,program('in'))
        self.assertIsNone(runtime.question_obligation('Which books are in Paris?',[{'mention':'Paris'}],'work'))

    def test_location_requires_endpoint_membership_not_arbitrary_anchor_edge(self):
        obligation=runtime.question_obligation('Which attractions are in Paris?',[{'mention':'Paris'}],'location')
        for direction,relation in (('out','location.location.containedby'),('in','location.location.contains')):
            runtime.check_obligation(obligation,program(relation='travel.travel_destination.tourist_attractions',constraints=[{'at':1,'relation':relation,'direction':direction,'anchor':0}]))
        with self.assertRaisesRegex(Blocked,'missing_primary_membership'):
            runtime.check_obligation(obligation,program())
        with self.assertRaises(Blocked):
            runtime.check_obligation(obligation,program(constraints=[{'at':0,'relation':'location.location.containedby','direction':'out','anchor':0}]))
        self.assertEqual(runtime.question_obligation('What to see in Paris downtown?',[{'mention':'Paris'}],'location')['unmodeled_qualifier'],'downtown')

    def test_primary_anchor_compiles_and_secondary_anchors_still_must_bind(self):
        p=program(relation='travel.travel_destination.tourist_attractions',constraints=[{'at':1,'relation':'location.location.containedby','direction':'out','anchor':0}])
        query,triples=runtime.compile_program(['m.city'],p)
        self.assertIn('?v1 ns:location.location.containedby ns:m.city .',query)
        self.assertIn(('v1','location.location.containedby','m.city'),triples)
        with self.assertRaisesRegex(Blocked,'unbound_question_anchor'):
            runtime.compile_program(['m.city','m.other'],p)
        for key in ('anchor','at'):
            bad=copy.deepcopy(p);bad['constraints'][0][key]=True
            with self.assertRaises(Blocked):runtime.compile_program(['m.city'],bad)

    def test_guard_off_does_not_disable_compiler(self):
        graph=runtime.ObligationGraph('offline://','fixture',guard_enabled=False)
        graph.obligation={'kind':'kinship','role':'parents'}
        graph.check_obligation(program('in'))
        with self.assertRaises(Blocked):runtime.compile_program(['m.person'],program(constraints=[{'at':1,'relation':'r','direction':'out','anchor':4}]))

    def test_catalog_only_adds_actually_observed_membership_edges(self):
        root={'relation':'travel.travel_destination.tourist_attractions','direction':'out'}
        graph=runtime.ObligationGraph('offline://','fixture');graph.question_contract={'answer_category':'location'}
        graph.select=lambda q:[{'relation':{'value':NS+'location.location.containedby'},'direction':{'value':'out'}}]
        catalog=graph.catalog('Which attractions are in Paris?',[root],[],['m.city'],[{'mention':'Paris'}],{})
        self.assertEqual(catalog[0]['program']['constraints'][0]['anchor'],0)
        graph.select=lambda q:[]
        catalog=graph.catalog('Which attractions are in Paris?',[root],[],['m.city'],[{'mention':'Paris'}],{})
        self.assertFalse(any(c['program']['constraints'] for c in catalog))

    def test_execution_keeps_both_witness_edges_and_primary_join_is_auditable(self):
        p=program(relation='travel.travel_destination.tourist_attractions',constraints=[{'at':1,'relation':'location.location.containedby','direction':'out','anchor':0}])
        graph=runtime.ObligationGraph('offline://','fixture')
        def select(query):
            rows=[{'v1':{'type':'uri','value':NS+'m.attraction'}}] if query.startswith('SELECT DISTINCT ?v1') else []
            graph.calls+=1;graph.audit.append({'query':query,'rows':rows,'snapshot':'fixture','sql_state':'00000'});return rows
        graph.select=select
        answers,witnesses=graph.execute(['m.city'],p)
        record={'id':'fixture','terminal':'ANSWER','answers':answers,'witnesses':witnesses,'graph_audit':graph.audit,
                'program_grammar':'primary-anchor-conjunction-v1','trace':[{'action':'LINK','candidates':['m.city']},{'action':'PLAN','program':p}]}
        self.assertEqual(audit(record)['answers'],1)
        self.assertEqual(len(witnesses[0]),2)
        wrong=copy.deepcopy(record);wrong['witnesses'][0][1]['target']['value']=NS+'m.other'
        with self.assertRaisesRegex(ValueError,'anchor'):audit(wrong)
        del record['program_grammar']
        with self.assertRaisesRegex(ValueError,'explicit grammar'):audit(record)

    def test_real_controller_rejects_then_revises_without_gold_feedback(self):
        class Graph(runtime.ObligationGraph):
            def typed_link(self,*args):return ['m.person'],'fixture'
            def inventory(self,*args):return [{'relation':'people.person.parents','direction':d} for d in ('in','out')]
            def schema(self,*args):return []
            def catalog(self,*args):
                self.obligation={'kind':'kinship','role':'parents'}
                return [{'index':i,'program':p,'answer_expected_type':'people.person','key':__import__('json').dumps(p,sort_keys=True)} for i,p in enumerate((program('in'),program('out')))]
            def execute(self,anchors,p):return ['m.parent'],[]
        class Model:
            calls=0;tokens=0;audit=[];semantic_audit=[]
            def ask(self,instruction,inputs):
                self.calls+=1
                if instruction.startswith('Extract'):return {'supported':True,'anchors':[{'mention':'Ada','type_hint':'person'}],'obligations':['parents']}
                if instruction.startswith('Select'):return {'roots':[{'relation':'people.person.parents','direction':d} for d in ('in','out')]}
                if instruction.startswith('Choose'):
                    if inputs['previous_failures']:
                        assert 'role_direction_mismatch' in inputs['previous_failures'][0]['reason']
                        assert len(inputs['programs'])==1
                        return {'program_index':1}
                    return {'program_index':0}
                return {'supported':True,'missing_obligations':[]}
        for variant,terminal in (('fixed','ABSTAIN'),('repair','ANSWER')):
            row=runtime.checked_run({'id':'any-id','question':"Who are Ada's parents?",'split':'pilot'},Graph('offline://','fixture'),Model(),variant)
            self.assertEqual(row['terminal'],terminal)
            self.assertEqual(sum(e['action']=='REPAIR_PLAN' for e in row['trace']),int(variant=='repair'))


    def test_repair_propagates_obligation_beyond_the_single_failed_program(self):
        class Graph(runtime.ObligationGraph):
            def typed_link(self,*args):return ['m.person'],'fixture'
            def inventory(self,*args):return [{'relation':'people.person.parents','direction':d} for d in ('in','out')]
            def schema(self,*args):return []
            def catalog(self,*args):
                self.obligation={'kind':'kinship','role':'parents'}
                wrong=program('in');wrong2=program('in');wrong2['steps'].append({'relation':'people.person.parents','direction':'out'})
                ps=[wrong,wrong2,program('out')]
                return [{'index':i,'program':p,'answer_expected_type':'people.person','key':__import__('json').dumps(p,sort_keys=True)} for i,p in enumerate(ps)]
            def execute(self,anchors,p):return ['m.parent'],[]
        class Model:
            calls=0;tokens=0;audit=[];semantic_audit=[]
            def ask(self,instruction,inputs):
                self.calls+=1
                if instruction.startswith('Extract'):return {'supported':True,'anchors':[{'mention':'Ada','type_hint':'person'}],'obligations':['parents']}
                if instruction.startswith('Select'):return {'roots':[{'relation':'people.person.parents','direction':d} for d in ('in','out')]}
                if instruction.startswith('Choose'):
                    if inputs['previous_failures']:
                        assert [p['index'] for p in inputs['programs']]==[2]
                        return {'program_index':2}
                    return {'program_index':0}
                return {'supported':True,'missing_obligations':[]}
        row=runtime.checked_run({'id':'unseen-fixture-id','question':"Who are Ada's parents?",'split':'pilot'},Graph('offline://','fixture'),Model(),'repair')
        self.assertEqual(row['terminal'],'ANSWER')
        event=next(e for e in row['trace'] if e['action']=='OBLIGATION_PRUNE')
        self.assertEqual(event['removed_indices'],[1])
        self.assertEqual(event['remaining_indices'],[2])

if __name__=='__main__':unittest.main()

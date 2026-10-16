import unittest
from flagship_controller.common_linker import LinkingGraph, link_question
from flagship_controller import structured_runtime as base
from flagship_controller.webqsp_runtime import Blocked, NS


class LinkTests(unittest.TestCase):
    def test_canonical_key_requires_observed_label_or_alias_and_never_first_id(self):
        graph=LinkingGraph('http://fixture','fixture');queries=[]
        def select(q):
            queries.append(q)
            return [{'entity':{'type':'uri','value':NS+n}} for n in ('m.b','m.a')]
        graph.select=select
        ids,method=graph.typed_link('Example University','musical')
        self.assertEqual(ids,['m.a','m.b'])
        self.assertIn('ns:common.topic.alias',queries[0]);self.assertIn('LCASE(STR(?label))="example university"',queries[0])
        self.assertIn('"/en/example_university"',queries[0]);self.assertIn('soft',method)

    def test_no_name_alias_evidence_falls_back_or_stays_unresolved(self):
        graph=LinkingGraph('http://fixture','fixture');graph.select=lambda q:[]
        self.assertEqual(graph.typed_link('Example University','musical')[0],[])

    def test_annotated_input_is_rejected_before_model_or_graph(self):
        with self.assertRaises(ValueError):link_question({'id':'q','question':'What?','answers':['x']},None,None,lambda *a,**kw:None)

    def test_common_prefix_matches_preserved_semantic_runner_calls(self):
        class Graph:
            def __init__(self):self.calls=0;self.audit=[];self.operations=[]
            def typed_link(self,mention,hint):
                self.operations.append(('link',mention,hint));return ['m.a','m.b'],'fixture'
            def cards(self,ids,context=None):
                self.operations.append(('cards',ids,context));return [{'entity':n,'observed_types':['organization.organization']} for n in ids]
            def inventory(self,node):raise Blocked('prefix_complete')
        class Model:
            def __init__(self,supported=True):self.calls=self.tokens=0;self.audit=[];self.operations=[];self.supported=supported
            def ask(self,instruction,inputs):
                self.operations.append((instruction,inputs))
                if instruction==base.EXTRACT:return {'supported':True,'anchors':[{'mention':'Atlas','type_hint':'organization'}],'obligations':['currency']}
                return {'entity':'m.b','supported':self.supported}
        record={'id':'q','question':'Which currency does Atlas use?','split':'pilot'}
        for supported in (True,False):
            g1,g2=Graph(),Graph();m1,m2=Model(supported),Model(supported)
            original=base.run(record,g1,m1)
            try:
                _,anchors=link_question(record,g2,m2,lambda *args,**kw:None)
                self.assertEqual(anchors,['m.b']);self.assertEqual(original['reason'],'prefix_complete')
            except Blocked as exc:self.assertEqual(str(exc),'unresolved_entity');self.assertEqual(original['reason'],str(exc))
            self.assertEqual(m1.operations,m2.operations);self.assertEqual(g1.operations,g2.operations)

if __name__=='__main__':unittest.main()

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from flagship_controller.tog_adapter import normalize_observed_answer, TextModel, Adapter, load_upstream
from flagship_controller.webqsp_runtime import Blocked, Ollama


class BaselineTests(unittest.TestCase):
    def test_normalization_is_observed_unique_and_preserves_commas(self):
        names={'m.a':['Washington, D.C.'],'m.b':['Peso']}
        self.assertEqual(normalize_observed_answer('{Yes}. Answer {Washington, D.C.}',names)[0],['m.a'])
        self.assertEqual(normalize_observed_answer('{Washington, D.C.; Peso}',names)[0],['m.a','m.b'])
        for text in ('{invented}','Peso','{Yes}','{Washington, D.C., Peso}'):
            self.assertEqual(normalize_observed_answer(text,names)[0],[])
        self.assertEqual(normalize_observed_answer('{Peso}',{**names,'m.c':['peso']})[0],[])

    def test_text_usage_and_response_are_retained_after_overrun(self):
        model=Ollama('http://fixture','fixture',max_tokens=10)
        raw=TextModel(model,lambda:None)
        with patch('flagship_controller.tog_adapter.post_json',return_value={'message':{'content':'{Yes}. {Peso}'},'prompt_eval_count':8,'eval_count':4}):
            with self.assertRaisesRegex(Blocked,'exceeded_after_call'):raw('prompt',0,512,'','fixture')
        self.assertEqual(model.tokens,12);self.assertEqual(len(model.audit),1)
        self.assertEqual(model.audit[0]['response'],'{Yes}. {Peso}')

    def test_text_failure_is_one_attempt_and_incomplete_usage(self):
        model=Ollama('http://fixture','fixture');raw=TextModel(model,lambda:None)
        with patch('flagship_controller.tog_adapter.post_json',side_effect=OSError('failed')) as send:
            with self.assertRaises(OSError):raw('prompt',0,512,'','fixture')
        self.assertEqual(send.call_count,1);self.assertEqual(model.calls,1);self.assertEqual(model.audit,[])

    def test_source_hash_mismatch_rejected_without_execution(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder,'main_freebase.py').write_text('raise RuntimeError("must not run")')
            with self.assertRaisesRegex(ValueError,'source mismatch'):load_upstream(folder)

    def test_only_observed_relations_expand_and_direction_is_preserved(self):
        adapter=object.__new__(Adapter)
        adapter.observed_relations={('m.topic','r','in')};adapter.checkpoint=lambda:None
        adapter.log=lambda *args,**kw:None;adapter.edges=[]
        class Graph:
            def expand(self,node,action):
                self.action=action
                return [{'target':'m.a','term':{'type':'uri'}},{'target':'g.other','term':{'type':'uri'}},{'target':'5','term':{'type':'literal'}}]
        adapter.graph=Graph()
        self.assertEqual(adapter.entities('m.topic','r',False),['m.a'])
        self.assertEqual(adapter.graph.action,{'relation':'r','direction':'in'})
        with self.assertRaisesRegex(Blocked,'unobserved'):adapter.entities('m.topic','invented',False)
        with self.assertRaisesRegex(Blocked,'unobserved'):adapter.entities('m.topic','r',True)

    def test_optional_models_cannot_download(self):
        with self.assertRaisesRegex(Blocked,'disabled'):Adapter.disabled('anything')

    def test_reserved_and_duplicate_inputs_cannot_be_frozen(self):
        from flagship_controller.baseline_development import freeze
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);inputs=root/'inputs.jsonl'
            inputs.write_text(json.dumps({'id':'q','question':'What?','split':'train_remaining'})+'\n')
            with self.assertRaisesRegex(ValueError,'pilot-only'):freeze(inputs,root/'out',root,'fixture')
            inputs.write_text((json.dumps({'id':'q','question':'What?','split':'pilot'})+'\n')*2)
            with self.assertRaisesRegex(ValueError,'Duplicate'):freeze(inputs,root/'out',root,'fixture')

if __name__=='__main__':unittest.main()

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from flagship_controller.common_state_study import freeze,journal,interrupted_result,execute,MODEL_DIGEST
from flagship_controller.study_runtime import digest


class JournalTests(unittest.TestCase):
    def test_committed_work_never_runs_twice_and_tampering_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);calls=[]
            run=lambda:calls.append('run') or {'fixture':True}
            interrupted=lambda:self.fail('No interruption expected')
            self.assertEqual(journal(root,'job',{'id':'q'},run,interrupted),{'fixture':True})
            journal(root,'job',{'id':'q'},run,interrupted);self.assertEqual(calls,['run'])
            data=json.loads((root/'job.json').read_text());data['value']={'tampered':True}
            (root/'job.json').write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'mismatch'):journal(root,'job',{'id':'q'},run,interrupted)

    def test_interrupted_started_work_becomes_explicit_unknown_cost_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'job.started.json').write_text('{"item":{"id":"q"}}')
            result=journal(root,'job',{'id':'q'},lambda:self.fail('Must not retry'),
                lambda:interrupted_result({'id':'q','split':'pilot'},'interrupted'))
            self.assertEqual(result['terminal'],'ABSTAIN');self.assertTrue(result['cost']['cost_is_lower_bound'])
            self.assertFalse(result['cost']['model_usage_complete'])

    def test_integrity_failure_cannot_be_bypassed_by_resuming(self):
        with tempfile.TemporaryDirectory() as temporary:
            def fail():raise ValueError('Frozen mismatch')
            with self.assertRaises(ValueError):journal(temporary,'job',{},fail,lambda:{})
            with self.assertRaisesRegex(ValueError,'Integrity failure'):journal(temporary,'job',{},lambda:{},lambda:{})


class StudyFreezeTests(unittest.TestCase):
    def test_seeds_all_policies_raw_serialization_and_exact_question_input_are_frozen(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);inputs=root/'inputs.jsonl'
            inputs.write_text('{"id":"q","question":"Fixture?","split":"pilot"}\n')
            with patch('flagship_controller.tog_adapter.load_upstream'):
                plan=freeze(inputs,root/'study',root,'fixture',[17,29])
            self.assertEqual(len(plan['order']),10)
            self.assertEqual({r['seed'] for r in plan['order']},{17,29})
            self.assertEqual(len(plan['source_hashes']),11)
            self.assertIn('raw',plan['serialization'])

    def test_labels_reserved_test_duplicate_seeds_and_large_inputs_are_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);inputs=root/'inputs.jsonl'
            cases=[{'id':'q','question':'Q','split':'test'},{'id':'q','question':'Q','split':'train_remaining'},
                   {'id':'q','question':'Q','split':'pilot','answers':[]}]
            for record in cases:
                inputs.write_text(json.dumps(record)+'\n')
                with self.assertRaises(ValueError):freeze(inputs,root/'study',root,'fixture')
            inputs.write_text('{"id":"q","question":"Q","split":"pilot"}\n')
            with self.assertRaises(ValueError):freeze(inputs,root/'study',root,'fixture',[17,17])

    def test_full_resume_keeps_interrupted_policy_and_never_repeats_committed_work(self):
        import io
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);inputs=root/'inputs.jsonl';folder=root/'study'
            record={'id':'q','question':'Fixture?','split':'pilot'};inputs.write_text(json.dumps(record)+'\n')
            with patch('flagship_controller.tog_adapter.load_upstream'):
                plan=freeze(inputs,folder,root,'fixture',[17])
            state={'cost':{'model_calls':1,'model_tokens':10,'graph_calls':1},'seconds':1.}
            packet={'record':record,'seed':17,'model':plan['model'],'snapshot':'fixture',
                'link':state,'internal':state,'internal_ready':True}
            jobs=folder/'journal';jobs.mkdir()
            item={**plan['order'][0],'prefix_sha256':digest(packet)}
            (jobs/'policy-0000.started.json').write_text(json.dumps({'item':item}))
            def policy(*args,**kwargs):
                return {'id':'q','terminal':'ABSTAIN','answers':[],'reason':'fixture retained',
                    'cost':{'model_calls':1,'model_tokens':10,'graph_calls':1,'elapsed_seconds':1.,'model_usage_complete':True}}
            tags=io.BytesIO(json.dumps({'models':[{'name':plan['model'],'digest':MODEL_DIGEST}]}).encode())
            with patch.dict('os.environ',{'PYTHONHASHSEED':'17'}),\
                 patch('flagship_controller.tog_adapter.load_upstream'),\
                 patch('urllib.request.urlopen',return_value=tags),\
                 patch('flagship_controller.webqsp_runtime.post_json',return_value={'parameters':'num_ctx 4096\nnum_thread 4'}),\
                 patch('flagship_controller.study_runtime.capture',return_value=packet) as capture,\
                 patch('flagship_controller.study_runtime.continue_policy',side_effect=policy) as continuation:
                execute(folder,root,'fixture','http://fixture/api/chat')
                execute(folder,root,'fixture','http://fixture/api/chat')
            self.assertEqual(capture.call_count,1);self.assertEqual(continuation.call_count,4)
            rows=list(map(json.loads,(folder/'predictions.jsonl').read_text().splitlines()))
            self.assertEqual(len(rows),5);self.assertEqual(rows[0]['reason'],'interrupted_policy_unknown_usage')
            self.assertTrue(rows[0]['cost']['cost_is_lower_bound'])


class CommonSourceRestorationTests(unittest.TestCase):
    def test_exact_frozen_modules_restore_and_cli_loads_without_labels(self):
        import importlib.util
        import subprocess
        root=Path(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location('restore_common',root/'scripts/materialize_common_study.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temporary:
            destination=Path(temporary)/'runtime'
            self.assertEqual(module.materialize(root/'results/common-state-dev-002',destination),11)
            result=subprocess.run(['python3','-m','flagship_controller.common_state_study','freeze','--help'],cwd=destination,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse((destination/'flagship_controller/official_score.py').exists())
            earlier=Path(temporary)/'earlier'
            self.assertEqual(module.materialize(root/'results/common-state-dev-001',earlier),10)
            earlier_cli=subprocess.run(['python3','-m','flagship_controller.common_state_study','freeze','--help'],cwd=earlier,capture_output=True,text=True)
            self.assertEqual(earlier_cli.returncode,0,earlier_cli.stderr)
            with self.assertRaisesRegex(ValueError,'existing'):module.materialize(root/'results/common-state-dev-002',destination)

if __name__=='__main__':unittest.main()

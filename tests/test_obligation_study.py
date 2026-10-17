import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from flagship_controller import obligation_study as study


class ObligationStudyTests(unittest.TestCase):
    def test_three_controls_source_isolation_and_no_reexecution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);inputs=root/'inputs.jsonl';inputs.write_text('{"id":"q","question":"Fixture?","split":"pilot"}\n')
            folder=root/'study';plan=study.freeze(inputs,folder,'fixture',[17])
            self.assertEqual(len(plan['source_hashes']),7)
            self.assertEqual({r['variant'] for r in plan['order']},{'fixed','repair','obligation-guard-off'})
            record={'id':'q','question':'Fixture?','split':'pilot'}
            packet={'record':record,'seed':17,'model':plan['model'],'snapshot':'fixture','internal':None,'internal_ready':False}
            def outcome(*args,**kwargs):return {'id':'q','terminal':'ABSTAIN','answers':[],'reason':'fixture','cost':{}}
            tags=io.BytesIO(json.dumps({'models':[{'name':plan['model'],'digest':study.MODEL_DIGEST}]}).encode())
            with patch.dict('os.environ',{'PYTHONHASHSEED':'17'}),patch('urllib.request.urlopen',return_value=tags),\
                 patch('flagship_controller.webqsp_runtime.post_json',return_value={'parameters':'num_ctx 4096\nnum_thread 4'}),\
                 patch('flagship_controller.obligation_runtime.capture',return_value=packet) as capture,\
                 patch('flagship_controller.obligation_runtime.continue_policy',side_effect=outcome) as policy:
                study.execute(folder,'fixture','http://fixture/api/chat')
                study.execute(folder,'fixture','http://fixture/api/chat')
            self.assertEqual(capture.call_count,1);self.assertEqual(policy.call_count,3)
            spec=importlib.util.spec_from_file_location('restore_obligation',Path(__file__).resolve().parents[1]/'scripts/materialize_obligation_study.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            dest=root/'restored';self.assertEqual(module.materialize(folder,dest),7)
            result=subprocess.run(['python3','-m','flagship_controller.obligation_study','freeze','--help'],cwd=dest,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse((dest/'flagship_controller/official_score.py').exists())

    def test_manifest_mutation_fails_before_network_and_labels_are_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);inputs=root/'inputs.jsonl';inputs.write_text('{"id":"q","question":"Q","split":"test"}\n')
            with self.assertRaises(ValueError):study.freeze(inputs,root/'study','fixture',[17])
            inputs.write_text('{"id":"q","question":"Q","split":"pilot","answers":[]}\n')
            with self.assertRaises(ValueError):study.freeze(inputs,root/'study','fixture',[17])
            inputs.write_text('{"id":"q","question":"Q","split":"pilot"}\n');folder=root/'study'
            plan=study.freeze(inputs,folder,'fixture',[17]);plan['budgets']['model_calls']=99
            (folder/'manifest.json').write_text(json.dumps(plan))
            with patch('urllib.request.urlopen',side_effect=AssertionError('No request')):
                with self.assertRaisesRegex(ValueError,'manifest changed'):study.execute(folder,'fixture','http://fixture/api/chat')

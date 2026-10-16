import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
from flagship_controller import study_runtime as study
from flagship_controller.webqsp_runtime import Blocked,NS,Ollama
from flagship_controller.tog_adapter import TextModel

ROOT=Path(__file__).resolve().parents[1]


class SeedAndReplayTests(unittest.TestCase):
    def model(self,seed=29,policy='repair',prefix=None):
        return study.StudyModel('http://fixture','fixture',graph=SimpleNamespace(root_expected_types={},answer_cards=[]),
            seed=seed,policy=policy,prefix=prefix,max_calls=10,max_tokens=16000)

    def test_direct_and_inherited_structured_paths_both_send_requested_seed(self):
        requests=[]
        def provider(url,payload,timeout):
            requests.append(payload);return {'message':{'content':'{"entity":"m.a","supported":true}'},'prompt_eval_count':10,'eval_count':5}
        model=self.model();model.contract={'answer_category':'unknown','requirements':[]}
        with patch('flagship_controller.webqsp_runtime.post_json',side_effect=provider):
            model.direct('Fixture',{}, {'type':'object'})
            model.ask('Choose only supplied entity',{'question':'Q','candidates':[]})
        self.assertEqual([r['options']['seed'] for r in requests],[29,29])
        self.assertEqual(model.tokens,30);self.assertEqual(model.physical_attempts,2)

    def test_raw_baseline_transport_uses_same_seed_and_provider_ledger(self):
        model=self.model(seed=43)
        with patch('flagship_controller.webqsp_runtime.post_json',return_value={
            'message':{'content':'{No}'},'prompt_eval_count':10,'eval_count':2}):
            self.assertEqual(TextModel(model,lambda:None)('Fixture',0,512,'','fixture'),'{No}')
        self.assertEqual(model.provider_audit[0]['payload']['options']['seed'],43)
        self.assertEqual(model.audit[0]['seed'],43)

    def test_default_seed_transport_matches_legacy_payload_and_usage(self):
        response={'message':{'content':'{"fixture":true}'},'prompt_eval_count':7,'eval_count':4}
        legacy=Ollama('http://fixture','fixture',max_calls=10,max_tokens=16000,timeout=120)
        legacy.response_format={'type':'object'};legacy.max_prompt_tokens=3000
        model=self.model(seed=17);payloads=[]
        def provider(url,payload,timeout):payloads.append(payload);return response
        with patch('flagship_controller.webqsp_runtime.post_json',side_effect=provider):
            self.assertEqual(legacy.ask('Fixture',{}),model.direct('Fixture',{}, {'type':'object'}))
        self.assertEqual(payloads[0],payloads[1]);self.assertEqual(legacy.tokens,model.tokens)

    def test_failed_provider_request_is_retained_once_with_unknown_usage(self):
        model=self.model()
        with patch('flagship_controller.webqsp_runtime.post_json',side_effect=OSError('fixture failure')) as provider:
            with self.assertRaises(OSError):model.direct('Fixture',{}, {'type':'object'})
        self.assertEqual(provider.call_count,1);self.assertEqual(model.calls,1)
        self.assertEqual(model.audit,[]);self.assertEqual(model.provider_audit[0]['error_type'],'OSError')

    def test_saved_provider_response_charges_usage_with_zero_new_requests(self):
        model=self.model()
        with patch('flagship_controller.webqsp_runtime.post_json',return_value={'message':{'content':'{}'},'prompt_eval_count':11,'eval_count':3}):
            model.direct('Fixture',{}, {'type':'object'})
        replay=self.model(prefix=model.provider_audit)
        with patch('flagship_controller.webqsp_runtime.post_json',side_effect=AssertionError('No new request')):
            self.assertEqual(replay.direct('Fixture',{}, {'type':'object'}),{})
        self.assertEqual((replay.calls,replay.tokens,replay.physical_attempts),(1,14,0))
        replay=self.model(prefix=model.provider_audit)
        with self.assertRaisesRegex(Blocked,'mismatch'):replay.direct('Changed',{}, {'type':'object'})

    def test_disabled_gate_does_not_bypass_types_or_compiler_or_add_model_call(self):
        model=self.model(policy='semantic-gate-off')
        with patch('flagship_controller.webqsp_runtime.post_json',side_effect=AssertionError('No model audit call')):
            self.assertTrue(model.ask('Audit whether supported',{})['supported'])
        self.assertEqual(model.calls,0)
        model.contract={'answer_category':'film','requirements':[]}
        with self.assertRaisesRegex(Blocked,'type_catalog'):
            model.ask('Choose a program',{'programs':[{'index':0,'answer_expected_type':'finance.currency'}]})

    def test_reason_text_ablation_keeps_program_information_and_masks_only_reason(self):
        model=self.model(policy='reason-text-off');model.contract={'answer_category':'unknown','requirements':[]};requests=[]
        def provider(url,payload,timeout):
            requests.append(json.loads(payload['messages'][0]['content']))
            return {'message':{'content':'{"program_index":1}'},'prompt_eval_count':10,'eval_count':3}
        inputs={'programs':[{'index':1,'answer_expected_type':None}],
            'previous_failures':[{'program':{'steps':['r']},'reason':'diagnostic detail'}]}
        with patch('flagship_controller.webqsp_runtime.post_json',side_effect=provider):
            model.ask('Choose a program. Use observed failure feedback to revise the choice.',inputs)
        failure=requests[0]['inputs']['previous_failures'][0]
        self.assertEqual(failure['reason'],'[withheld]');self.assertEqual(failure['program'],{'steps':['r']})
        self.assertEqual(inputs['previous_failures'][0]['reason'],'diagnostic detail')


class SharedStateFixtureTests(unittest.TestCase):
    def test_four_controls_replay_identical_catalog_and_first_choice(self):
        folder=ROOT/'results/baseline-dev-003'
        row=next(r for r in map(json.loads,(folder/'predictions.jsonl').read_text().splitlines())
                 if r['id']=='WebQTrn-562' and r['variant']=='semantic-common-link')
        record=next(r for r in map(json.loads,(folder/'inputs.jsonl').read_text().splitlines()) if r['id']==row['id'])
        queries={q['query']:q for q in row['graph_audit']}
        replies={q['prompt_sha256']:q for q in row['model_audit']};requests=[]
        class FixtureGraph(study.StudyGraph):
            def select(self,body):
                if self.cursor<len(self.saved):return super().select(body)
                key='PREFIX ns: <'+NS+'>\n'+body
                if key not in queries:raise AssertionError('Unexpected query '+key)
                saved=copy.deepcopy(queries[key]);self.calls+=1;self.audit.append(saved)
                return saved['rows']
        def provider(url,payload,timeout):
            requests.append(payload)
            saved=replies[hashlib.sha256(payload['messages'][0]['content'].encode()).hexdigest()]
            return {'message':{'content':saved['response']},'prompt_eval_count':saved['input_tokens'],'eval_count':saved['output_tokens']}
        results=[]
        with patch.object(study,'StudyGraph',FixtureGraph),patch('flagship_controller.webqsp_runtime.post_json',side_effect=provider):
            packet=study.capture(record,'fixture','fixture','fixture',row['graph_audit'][0]['snapshot'],29)
            self.assertTrue(packet['internal_ready']);self.assertIsNotNone(packet['link'])
            captured=next(e['program'] for e in packet['capture_result']['trace'] if e['action']=='PLAN')
            for policy in study.POLICIES[:-1]:
                result=study.continue_policy(packet,policy,'fixture','fixture',None)
                self.assertEqual(result['terminal'],'ANSWER',str((policy,result['reason'],result['trace'][-2:])))
                self.assertEqual(next(e['program'] for e in result['trace'] if e['action']=='PLAN'),captured)
                self.assertEqual(result['shared_state']['replayed_model_calls'],packet['internal']['cost']['model_calls'])
                self.assertEqual(result['cost']['physical_new_model_calls'],0 if policy=='semantic-gate-off' else 1)
                result['seed']=29;results.append(result)
        self.assertTrue(all(p['options']['seed']==29 for p in requests))
        from flagship_controller.common_state_audit import check
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);jobs=root/'journal';jobs.mkdir()
            key='29-'+hashlib.sha256(record['id'].encode()).hexdigest()[:16]
            (jobs/(key+'-prefix.json')).write_text(json.dumps({'item':{},'value':packet,'sha256':study.digest(packet)}))
            order=[{'id':record['id'],'seed':29,'variant':r['variant']} for r in results]
            (root/'manifest.json').write_text(json.dumps({'order':order}))
            def store_results():
                for i,result in enumerate(results):
                    item={**order[i],'prefix_sha256':study.digest(packet)}
                    (jobs/f'policy-{i:04d}.json').write_text(json.dumps({'item':item,'value':result,'sha256':study.digest(result)}))
                raw=''.join(json.dumps(r)+'\n' for r in results).encode();(root/'predictions.jsonl').write_bytes(raw)
                (root/'completion.json').write_text(json.dumps({'completed':4,'predictions_sha256':hashlib.sha256(raw).hexdigest()}))
            store_results();self.assertEqual(check(root)['records'],4)
            results[0]['provider_audit'][-1]['seed']=43;store_results()
            with self.assertRaisesRegex(ValueError,'seed/hash'):check(root)

    def test_common_failure_is_not_retried_or_turned_into_a_new_policy_observation(self):
        result={'id':'fixture','terminal':'ABSTAIN','answers':[],'reason':'entity_not_found',
            'cost':{'elapsed_seconds':2.,'model_calls':1,'model_tokens':10,'graph_calls':1}}
        packet={'record':{'id':'fixture'},'seed':17,'link':None,'internal':{},'internal_ready':False,
            'capture_result':result,'provider_audit':[]}
        for policy in study.POLICIES:
            with patch('flagship_controller.webqsp_runtime.post_json',side_effect=AssertionError('No retry')):
                output=study.continue_policy(packet,policy,'fixture','fixture',None)
            self.assertEqual(output['reason'],'entity_not_found');self.assertFalse(output['policy_continuation_executed'])

if __name__=='__main__':unittest.main()

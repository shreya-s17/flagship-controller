import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from flagship_controller import benchmark_study as study
from flagship_controller import benchmark_review_pack as pack
from flagship_controller import benchmark_publication as publication

ROOT = Path(__file__).resolve().parents[1]


class PublicationTests(unittest.TestCase):
    """Synthetic transport/packaging contracts, never scientific results."""
    def fixture(self, root):
        folder = root/'study'
        with patch.object(study.tog_adapter, 'load_upstream'):
            plan = study.freeze(ROOT/'evaluation/reserved-training-100-v2/inputs.jsonl', folder, 'fixture', 'fixture')
        rows = [{**item, 'terminal':'ABSTAIN', 'answers':[], 'trace':[], 'graph_audit':[],
                 'reason':'fixture_failure_retained', 'witnesses':[],
                 'native_response':'untrusted native context: keep this intact' if item['variant']=='tog-declared-json' else None,
                 'cost':{'model_calls':1,'model_tokens':2,'graph_calls':1,'elapsed_seconds':0.,'model_usage_complete':True}}
                for item in plan['order']]
        raw=''.join(json.dumps(r)+'\n' for r in rows).encode();(folder/'predictions.jsonl').write_bytes(raw)
        (folder/'completion.json').write_text(json.dumps({'completed':1800,'predictions_sha256':hashlib.sha256(raw).hexdigest()}))
        return folder,plan,rows

    def test_incomplete_real_study_refuses_before_annotation_access_or_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'incomplete';folder.mkdir();output=root/'output'
            with patch.object(publication.benchmark_analysis,'analyze',side_effect=AssertionError('No annotation access')):
                with self.assertRaisesRegex(ValueError,'Full completed1800'):
                    publication.finalize(folder,root/'gold-does-not-exist',output)
            self.assertFalse(output.exists())

    def test_full_sample_keeps_failed_outcomes_masks_metadata_and_excludes_owner_key(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder,plan,rows=self.fixture(root);output=root/'review'
            with patch.object(pack,'check',return_value={'rows_checked':1800}) as gate:
                result=pack.prepare(folder,output)
            gate.assert_called_once_with(folder)
            self.assertEqual((result['semantic_records'],result['projection_records']),(120,20))
            key=json.loads((output/'owner-key.json').read_text())
            self.assertEqual({r['question_id'] for r in key},set(plan['semantic_review']['question_ids']))
            self.assertEqual({r['seed'] for r in key},{17})
            for kind,count,dimensions in [('semantic',120,pack.DIMENSIONS),('projection',20,pack.PROJECTION_DIMENSIONS)]:
                cases=list(map(json.loads,(output/kind/'cases.jsonl').read_text().splitlines()))
                self.assertEqual(len(cases),count)
                self.assertTrue(all(c['terminal']=='ABSTAIN' for c in cases))
                self.assertTrue(all(not {'variant','reason','question_id','seed','score','semantic_audit'} & set(c) for c in cases))
                form=json.loads((output/kind/'submission-template.json').read_text())
                self.assertEqual(form['review_role'],'independent');self.assertIs(form['independence_attested'],False)
                self.assertEqual(len(form['judgments']),count)
                self.assertTrue(all(set(j['dimensions'])==set(dimensions) for j in form['judgments']))
                self.assertTrue(all(j=={'label':'unknown','reason':''} for c in form['judgments'] for j in c['dimensions'].values()))
                with zipfile.ZipFile(output/(kind+'-review.zip')) as archive:
                    self.assertEqual(set(archive.namelist()),{'README.txt','cases.jsonl','submission-template.json','BRIEF.txt','delivery-manifest.json'})
                    self.assertNotIn('owner-key.json',archive.namelist())
            native=list(map(json.loads,(output/'projection/cases.jsonl').read_text().splitlines()))
            self.assertTrue(all(c['native_response']=='untrusted native context: keep this intact' for c in native))
            with self.assertRaisesRegex(ValueError,'existing review output'):pack.prepare(folder,output)

    def test_selection_tampering_and_automated_independence_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder,plan,rows=self.fixture(root)
            plan['semantic_review']['question_ids'].reverse();(folder/'manifest.json').write_text(json.dumps(plan))
            with patch.object(pack,'check',return_value={'rows_checked':1800}):
                with self.assertRaisesRegex(ValueError,'selection changed'):pack.prepare(folder,root/'output')
            self.assertFalse((root/'output').exists())
            with self.assertRaisesRegex(ValueError,'cannot count as independent'):
                pack.independent_review.validate(root/'unused',{'review_role':'automated','independence_attested':True})

    def test_bad_edge_reference_is_not_silently_dropped(self):
        row={'answers':['m.x'],'terminal':'ANSWER','trace':[],'cost':{},'graph_audit':[],
             'witnesses':[[{'provenance':{'query_index':0}}]]}
        with self.assertRaisesRegex(ValueError,'missing its recorded query'):pack.case_from(row,'Q','case')

    def test_tables_full_denominator_exclusions_and_unknown_cost_are_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder,plan,rows=self.fixture(root)
            scored={'submitted':100,'rows':[{'id':q,'scorable':i!=0,**({'f1':0.,'exact_f1':0,'answered':False} if i else {})} for i,q in enumerate(plan['question_ids'])]}
            analysis={'executions':1800,'questions':100,'methods':{policy:{'official_scores_by_seed':{str(s):copy.deepcopy(scored) for s in (17,29,43)},
                'submitted_outcomes':300,'mean_question_f1':0.,'charged_usage':{'model_tokens':600,'model_calls':300,'graph_calls':300},
                'complete_usage':False,'unknown_usage_records':1} for policy in plan['policies']},
                'primary_repair_minus_fixed':{'mean_difference':0.,'lower_95':0.,'upper_95':0.,'question_units':99}}
            table,failures,outcomes,report=publication.summarize(plan,rows,analysis)
            self.assertEqual(sum(r['outcomes'] for r in failures),1800)
            self.assertEqual(len(outcomes),1800)
            self.assertTrue(all(r['scorable_question_units']==99 and r['excluded_question_units']==1 for r in table))
            self.assertTrue(all(r['usage_complete'] is False for r in table))
            self.assertIn('lower bounds',report);self.assertIn('remain NA',report)
            analysis['methods'][plan['policies'][0]]['submitted_outcomes']=299
            with self.assertRaisesRegex(ValueError,'Every policy needs all100'):publication.summarize(plan,rows,analysis)

    def test_finalization_is_atomic_and_unchanged_frozen_analysis_is_used(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder,plan,rows=self.fixture(root);output=root/'final';gold=root/'evaluation-only.jsonl';gold.write_text('synthetic annotation fixture\n')
            scored={'submitted':100,'rows':[{'id':q,'scorable':True,'f1':0.,'exact_f1':0,'answered':False} for q in plan['question_ids']]}
            analysis={'executions':1800,'questions':100,'methods':{policy:{'official_scores_by_seed':{str(s):scored for s in (17,29,43)},
                'submitted_outcomes':300,'mean_question_f1':0.,'charged_usage':{'model_tokens':600,'model_calls':300,'graph_calls':300},
                'complete_usage':True,'unknown_usage_records':0} for policy in plan['policies']},
                'primary_repair_minus_fixed':{'mean_difference':0.,'lower_95':0.,'upper_95':0.,'question_units':100}}
            with patch.object(pack,'check',return_value={'rows_checked':1800}),patch.object(publication.benchmark_analysis,'analyze',return_value=analysis) as scorer:
                receipt=publication.finalize(folder,gold,output)
            scorer.assert_called_once_with(folder,gold)
            self.assertFalse(receipt['submission_ready'])
            self.assertEqual(json.loads((output/'analysis.json').read_text()),analysis)
            self.assertEqual(len((output/'outcomes.csv').read_text().splitlines()),1801)
            for name,digest in json.loads((output/'checksums.json').read_text()).items():
                self.assertEqual(hashlib.sha256((output/name).read_bytes()).hexdigest(),digest)
            with self.assertRaisesRegex(ValueError,'existing finalization'):publication.finalize(folder,gold,output)

    def test_dependent_job_never_scores_a_partial_stopped_worker(self):
        spec=importlib.util.spec_from_file_location('await_completion',ROOT/'scripts/await_benchmark_completion.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'study';folder.mkdir();status=root/'status.json'
            with patch.object(module.subprocess,'run') as process,patch.object(module,'finalize',side_effect=AssertionError('No scoring')):
                process.return_value.returncode=1
                with self.assertRaisesRegex(ValueError,'stopped before full completion'):
                    module.watch(folder,root/'gold',root/'output',status,'fixture')
            saved=json.loads(status.read_text());self.assertEqual(saved['state'],'failed');self.assertIs(saved['automatic_retry'],False)

    def test_dependent_job_finalizes_exactly_once_after_marker(self):
        spec=importlib.util.spec_from_file_location('await_completion',ROOT/'scripts/await_benchmark_completion.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'study';folder.mkdir();(folder/'completion.json').write_text('{}');status=root/'status.json'
            with patch.object(module,'finalize',return_value={'fixture':True}) as final,patch.object(module.subprocess,'run',side_effect=AssertionError('Completed collection is checked first')):
                result=module.watch(folder,root/'gold',root/'output',status,'fixture')
            final.assert_called_once_with(folder,root/'gold',root/'output');self.assertTrue(result['fixture'])
            saved=json.loads(status.read_text());self.assertEqual(saved['state'],'complete_tables_and_blank_review_packs');self.assertIs(saved['submission_ready'],False)


if __name__=='__main__':unittest.main()

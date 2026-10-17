import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('obligation_audit',Path(__file__).resolve().parents[1]/'scripts/audit_obligation_study.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


def row():
    wrong={'steps':[{'relation':'people.person.parents','direction':'in'}],'constraints':[]}
    wrong2={'steps':[{'relation':'people.person.parents','direction':'in'},{'relation':'people.person.parents','direction':'out'}],'constraints':[]}
    right={'steps':[{'relation':'people.person.parents','direction':'out'}],'constraints':[]}
    return {'id':'fixture','seed':17,'variant':'repair','terminal':'ANSWER','obligation_guard_enabled':True,
            'obligation':{'kind':'kinship','role':'parents'},
            'trace':[{'action':'PROGRAM_CATALOG','programs':[{'index':i,'program':p} for i,p in enumerate((wrong,wrong2,right))]},
                     {'action':'PLAN','program_index':0,'program':wrong},
                     {'action':'REJECT','reason':'role_direction_mismatch: fixture'},
                     {'action':'OBLIGATION_PRUNE','removed_indices':[1],'remaining_indices':[2]},
                     {'action':'REPAIR_PLAN','program_index':2,'program':right}],
            'model_audit':[{'prompt':{'instruction':'Choose a program','inputs':{'programs':[{'index':0},{'index':1},{'index':2}]}}},
                           {'prompt':{'instruction':'Choose a program','inputs':{'programs':[{'index':2}]}}}]}


class ObligationLedgerTests(unittest.TestCase):
    def test_valid_declared_constraint_pruning_is_not_semantic_certification(self):
        result=audit.check_row(row())
        self.assertEqual(result['pruning_events'],1)
        self.assertIn('not independently assessed',result['semantic_validity'])

    def test_removing_valid_candidate_is_rejected(self):
        value=row();value['trace'][3]['removed_indices']=[2];value['trace'][3]['remaining_indices']=[1]
        with self.assertRaisesRegex(ValueError,'partition'):audit.check_row(value)

    def test_actual_request_cannot_reintroduce_a_removed_candidate(self):
        value=row();value['model_audit'][1]['prompt']['inputs']['programs'].append({'index':1})
        with self.assertRaisesRegex(ValueError,'actual model choice'):audit.check_row(value)

    def test_disabled_guard_cannot_claim_to_prune(self):
        value=row();value['obligation_guard_enabled']=False
        with self.assertRaises(ValueError):audit.check_row(value)

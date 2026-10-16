import copy
import json
import unittest
from flagship_controller.indexed_decision_audit import audit


class DecisionAuditTests(unittest.TestCase):
    def setUp(self):
        span={'entity':'m.mx','quote':'Mexico','start':0,'end':6,'context':'Mexico'}
        self.selection={'supported':True,'all_concluded_answers_represented':True,'span_indices':[0]}
        self.row={'id':'fixture','variant':'tog-indexed-spans','terminal':'ANSWER','reason':'fixture',
            'native_response':'Mexico','answers':['m.mx'],'cost':{'model_calls':1,'model_usage_complete':True},
            'trace':[{'action':'ENTITY_PRUNE','ids':['m.mx']},
                {'action':'NATIVE_SPAN_EXTRACTION','spans':[span],'candidates':[{'entity':'m.mx','names':['Mexico']}],
                 'selection':self.selection,'cost':{'model_calls':1}}],
            'model_audit':[{'response':json.dumps(self.selection),
                'prompt':{'inputs':{'native_response':'Mexico','spans':[span]}}}]}

    def test_actual_span_has_returned_request_and_exact_id_projection(self):
        self.assertEqual(audit(self.row)['invalid_decoder_outputs_retained'],0)

    def test_tampered_quote_and_raw_response_are_rejected(self):
        row=copy.deepcopy(self.row);row['native_response']='Other'
        with self.assertRaises(ValueError):audit(row)
        row=copy.deepcopy(self.row);row['model_audit'][0]['response']='{}'
        with self.assertRaisesRegex(ValueError,'raw returned'):audit(row)

    def test_wrong_projected_id_or_unobserved_candidate_cannot_pass(self):
        row=copy.deepcopy(self.row);row['answers']=['m.other']
        with self.assertRaisesRegex(ValueError,'projection'):audit(row)
        row=copy.deepcopy(self.row);row['trace'][0]['ids']=[]
        with self.assertRaisesRegex(ValueError,'beam'):audit(row)

    def test_invalid_decoding_is_retained_only_as_an_abstention(self):
        row=copy.deepcopy(self.row)
        row['trace'][1]['selection']['span_indices']=[True]
        row['model_audit'][0]['response']=json.dumps(row['trace'][1]['selection'])
        with self.assertRaisesRegex(ValueError,'Invalid decoder'):audit(row)
        row.update(terminal='ABSTAIN',answers=[])
        self.assertEqual(audit(row)['invalid_decoder_outputs_retained'],1)

if __name__=='__main__':unittest.main()

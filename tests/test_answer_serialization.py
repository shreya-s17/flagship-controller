import unittest
from flagship_controller.answer_serialization import serialize
from flagship_controller.webqsp_runtime import Blocked


class SerializationTests(unittest.TestCase):
    def test_raw_is_default_and_projection_requires_explicit_policy(self):
        term={'type':'typed-literal','datatype':'http://www.w3.org/2001/XMLSchema#date','value':'1976-08-10-08:00'}
        self.assertEqual(serialize(term)['answer'],term['value'])
        result=serialize(term,'webqsp_calendar_date')
        self.assertEqual(result['answer'],'1976-08-10');self.assertEqual(result['raw_term'],term)
        self.assertTrue(result['representation_changed'])
        self.assertEqual(term['value'],'1976-08-10-08:00')

    def test_other_literals_dates_and_ids_not_invented(self):
        for value in ['2000-02-29','2000-02-29Z','2000-02-29+14:00']:
            term={'type':'literal','datatype':'http://www.w3.org/2001/XMLSchema#date','value':value}
            self.assertEqual(serialize(term,'webqsp_calendar_date')['answer'],'2000-02-29')
        term={'type':'typed-literal','datatype':'http://www.w3.org/2001/XMLSchema#dateTime','value':'2000-02-29T00:00:00Z'}
        self.assertEqual(serialize(term,'webqsp_calendar_date')['answer'],term['value'])
        self.assertEqual(serialize({'type':'uri','value':'http://rdf.freebase.com/ns/m.example'})['answer'],'m.example')
        with self.assertRaises(Blocked):serialize({'type':'uri','value':'https://external/id'})

    def test_invalid_date_or_zone_rejected(self):
        for value in ['2001-02-29','2000-01-01+15:00','2000-01-01+14:01','tomorrow']:
            with self.assertRaises(Blocked):serialize({'type':'literal','datatype':'http://www.w3.org/2001/XMLSchema#date','value':value},'webqsp_calendar_date')

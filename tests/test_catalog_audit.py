from pathlib import Path
import importlib.util
import unittest

spec=importlib.util.spec_from_file_location('catalog_audit',Path(__file__).resolve().parents[1]/'evaluation/offline/catalog_audit.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class CatalogAuditTests(unittest.TestCase):
    def test_offline_query_is_bounded_local_select(self):
        query=module.gold_query('PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?x WHERE { ns:m.a ns:r ?x . }')
        self.assertTrue(query.endswith('LIMIT 101'))
        self.assertIn('BIND(?x AS ?answer)',query)
        for bad in ['DELETE WHERE {?s ?p ?o}', 'SELECT ?x WHERE { SERVICE <https://external> {?x ?p ?o} }']:
            with self.assertRaises(ValueError):module.gold_query(bad)

    def test_link_ambiguity_uses_recorded_choice_not_first_candidate(self):
        record={'trace':[{'action':'LINK','candidates':['m.wrong','m.right']},
                          {'action':'DISAMBIGUATE','choice':{'supported':True,'entity':'m.right'}}]}
        self.assertEqual(module.linked_anchors(record),['m.right'])

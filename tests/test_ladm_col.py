# -*- coding: utf-8 -*-
import unittest
import os
import tempfile
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from profiles.ladm_col import LADMCOLProfileBuilder
from core.validator import QGDBValidator

class TestLADMCOLProfile(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.qgdb_path = os.path.join(self.temp_dir, "ladm_col_test.qgdb")

    def test_create_ladm_col_profile(self):
        engine = LADMCOLProfileBuilder.create_ladm_col_project(self.qgdb_path)
        self.assertTrue(os.path.exists(self.qgdb_path))

        datasets = engine.get_datasets()
        ds_names = [d['name'] for d in datasets]
        self.assertIn("CATASTRO", ds_names)
        self.assertIn("JURIDICO", ds_names)

        domains = engine.get_domains()
        self.assertIn("DOM_DESTINO_ECONOMICO", domains)
        self.assertIn("DOM_TIPO_PREDIO", domains)

        relationships = engine.get_relationships()
        self.assertGreaterEqual(len(relationships), 3)

        validator = QGDBValidator(engine)
        self.assertTrue(validator.validate_structure()['valid'])

        engine.close()

if __name__ == '__main__':
    unittest.main()

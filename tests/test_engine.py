# -*- coding: utf-8 -*-
import unittest
import os
import tempfile
import sys

# Agregar raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.qgdb_engine import QGDBEngine
from core.validator import QGDBValidator

class TestQGDBEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.qgdb_path = os.path.join(self.temp_dir, "test_project.qgdb")

    def test_create_and_read_qgdb(self):
        spec = {
            "metadata": {
                "title": "Test Project",
                "profile": "TEST-PROFILE",
                "crs": "EPSG:9377"
            },
            "datasets": [
                {
                    "name": "TEST_DATASET",
                    "title": "Dataset de Prueba",
                    "description": "Dataset para prueba unitaria",
                    "layers": ["Capa1", "Capa2"]
                }
            ],
            "domains": {
                "DOM_TEST": [
                    {"code": "1", "description": "Opción 1"},
                    {"code": "2", "description": "Opción 2"}
                ]
            }
        }

        engine = QGDBEngine()
        res = engine.create(self.qgdb_path, spec)
        self.assertTrue(res)
        self.assertTrue(os.path.exists(self.qgdb_path))

        # Comprobar lectura de datasets
        datasets = engine.get_datasets()
        self.assertEqual(len(datasets), 1)
        self.assertEqual(datasets[0]['name'], "TEST_DATASET")

        # Comprobar lectura de capas
        layers = engine.get_layers_for_dataset("TEST_DATASET")
        self.assertEqual(len(layers), 2)

        # Comprobar validación de estructura
        validator = QGDBValidator(engine)
        val_res = validator.validate_structure()
        self.assertTrue(val_res['valid'])

        engine.close()

if __name__ == '__main__':
    unittest.main()

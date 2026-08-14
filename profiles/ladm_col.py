# -*- coding: utf-8 -*-
import json
import os
try:
    from core.qgdb_engine import QGDBEngine
except ImportError:
    from ..core.qgdb_engine import QGDBEngine

class LADMCOLProfileBuilder:
    """
    Generador automático de proyectos QGDB conformes a la norma de Catastro Multipropósito de Colombia (LADM-COL v3.0).
    """

    @staticmethod
    def get_ladm_col_spec() -> dict:
        """Carga la especificación oficial LADM-COL v3.0 desde el archivo JSON de especificación."""
        spec_path = os.path.join(os.path.dirname(__file__), '..', 'spec', 'ladm_col_v3.0.json')
        if os.path.exists(spec_path):
            with open(spec_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Fallback inline por si no se encuentra el archivo
        return {
            "metadata": {
                "title": "Catastro Multipropósito LADM-COL v3.0",
                "profile": "QGDB-LADM-COL",
                "crs": "EPSG:9377"
            },
            "datasets": [
                {
                    "name": "CATASTRO",
                    "title": "Componente Catastral y Físico",
                    "description": "Geometría predial, terrenos, construcciones y unidades en propiedad horizontal",
                    "layers": ["LC_Predio", "LC_Terreno", "LC_Construccion", "LC_UnidadConstruccion"]
                },
                {
                    "name": "JURIDICO",
                    "title": "Componente Jurídico y Derechos",
                    "description": "Interesados, derechos de propiedad, restricciones y responsabilidades",
                    "layers": ["LC_Interesado", "LC_Derecho", "LC_Restriccion", "LC_Responsabilidad"]
                }
            ]
        }

    @staticmethod
    def create_ladm_col_project(output_filepath: str) -> QGDBEngine:
        """
        Crea un archivo .qgdb completo y listo para QGIS con el perfil LADM-COL v3.0.
        """
        spec = LADMCOLProfileBuilder.get_ladm_col_spec()
        engine = QGDBEngine()
        engine.create(output_filepath, spec)
        return engine

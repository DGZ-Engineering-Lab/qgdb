# -*- coding: utf-8 -*-
import sqlite3

class QGDBValidator:
    """
    Validador de consistencia de datos, campos y reglas normativas para contenedores QGDB.
    """

    def __init__(self, engine):
        self.engine = engine

    def validate_structure(self) -> dict:
        """
        Verifica que el archivo posea las tablas de sistema qgdb_* requeridas.
        """
        result = {'valid': True, 'errors': [], 'warnings': []}
        if not self.engine or not self.engine.conn:
            return {'valid': False, 'errors': ['Base de datos no conectada'], 'warnings': []}

        cursor = self.engine.conn.cursor()
        required_tables = [
            'qgdb_metadata', 'qgdb_datasets', 'qgdb_layers', 
            'qgdb_domains', 'qgdb_field_config', 'qgdb_relationships', 'qgdb_topology_rules'
        ]

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing = [row['name'] for row in cursor.fetchall()]

        for tbl in required_tables:
            if tbl not in existing:
                result['valid'] = False
                result['errors'].append(f"Falta la tabla de sistema requerida: {tbl}")

        return result

    def validate_ladm_col_rules(self) -> dict:
        """
        Verifica el cumplimiento de las reglas normativas de LADM-COL v3.0 para Colombia.
        """
        result = {'valid': True, 'errors': [], 'warnings': []}
        if not self.engine or not self.engine.conn:
            return {'valid': False, 'errors': ['Base de datos no conectada'], 'warnings': []}

        cursor = self.engine.conn.cursor()

        # Verificar presencia de capas LADM-COL
        cursor.execute("SELECT layer_name FROM qgdb_layers")
        existing_layers = [row['layer_name'] for row in cursor.fetchall()]

        required_ladm_layers = ['LC_Predio', 'LC_Terreno', 'LC_Construccion', 'LC_Interesado', 'LC_Derecho']
        for r_layer in required_ladm_layers:
            if r_layer not in existing_layers:
                result['warnings'].append(f"Capa LADM-COL recomendada no encontrada: {r_layer}")

        return result

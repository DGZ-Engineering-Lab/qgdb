# -*- coding: utf-8 -*-
import sqlite3
import json
import os
import datetime
from .schema_builder import QGDBSchemaBuilder

class QGDBEngine:
    """
    Motor independiente de almacenamiento y gestión de contenedores QGDB (.qgdb / .qgpkg).
    """

    def __init__(self, filepath: str = None):
        self.filepath = filepath
        self.conn = None
        if filepath and os.path.exists(filepath):
            self.open(filepath)

    def open(self, filepath: str):
        """Abre una base de datos QGDB existente."""
        self.filepath = filepath
        self.conn = sqlite3.connect(filepath)
        self.conn.row_factory = sqlite3.Row
        return True

    def create(self, filepath: str, spec_dict: dict = None) -> bool:
        """
        Crea un nuevo archivo QGDB inicializando tablas de sistema y aplicando la especificación JSON.
        """
        self.filepath = filepath
        if os.path.exists(filepath):
            os.remove(filepath)

        self.conn = sqlite3.connect(filepath)
        self.conn.row_factory = sqlite3.Row

        # 1. Inicializar tablas de sistema qgdb_*
        QGDBSchemaBuilder.initialize_qgdb_system_tables(self.conn)

        # 2. Registrar metadatos base
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO qgdb_metadata (key, value) VALUES ('qgdb_version', '0.1')")
        cursor.execute(f"INSERT OR REPLACE INTO qgdb_metadata (key, value) VALUES ('created_at', '{datetime.datetime.now().isoformat()}')")

        if spec_dict:
            self.apply_specification(spec_dict)

        self.conn.commit()
        return True

    def apply_specification(self, spec_dict: dict):
        """Aplica la especificación de Datasets, Dominios y Relaciones recibida en un diccionario o JSON."""
        cursor = self.conn.cursor()

        # Metadata
        if 'metadata' in spec_dict:
            for k, v in spec_dict['metadata'].items():
                cursor.execute("INSERT OR REPLACE INTO qgdb_metadata (key, value) VALUES (?, ?)", (k, str(v)))

        # Datasets y Capas
        if 'datasets' in spec_dict:
            for ds in spec_dict['datasets']:
                cursor.execute(
                    "INSERT OR REPLACE INTO qgdb_datasets (name, title, description) VALUES (?, ?, ?)",
                    (ds['name'], ds['title'], ds.get('description', ''))
                )
                for layer_name in ds.get('layers', []):
                    cursor.execute(
                        "INSERT OR REPLACE INTO qgdb_layers (dataset_name, layer_name, title) VALUES (?, ?, ?)",
                        (ds['name'], layer_name, layer_name)
                    )

        # Dominios
        if 'domains' in spec_dict:
            for dom_name, values in spec_dict['domains'].items():
                for item in values:
                    cursor.execute(
                        "INSERT OR REPLACE INTO qgdb_domains (domain_name, code, description) VALUES (?, ?, ?)",
                        (dom_name, str(item['code']), item['description'])
                    )

        # Relaciones
        if 'relationships' in spec_dict:
            for rel in spec_dict['relationships']:
                cursor.execute(
                    """INSERT OR REPLACE INTO qgdb_relationships 
                       (name, parent_layer, parent_key, child_layer, child_key, cardinality) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (rel['name'], rel['parent_layer'], rel['parent_key'], rel['child_layer'], rel['child_key'], rel.get('cardinality', '1:N'))
                )

        # Reglas de Topología
        if 'topology_rules' in spec_dict:
            for rule in spec_dict['topology_rules']:
                cursor.execute(
                    """INSERT OR REPLACE INTO qgdb_topology_rules 
                       (rule_type, layer_a, layer_b, severity) 
                       VALUES (?, ?, ?, ?)""",
                    (rule['rule_type'], rule['layer_a'], rule.get('layer_b'), rule.get('severity', 'ERROR'))
                )

        self.conn.commit()

    def get_datasets(self) -> list:
        """Devuelve la lista de Datasets registrados."""
        if not self.conn: return []
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM qgdb_datasets ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

    def get_layers_for_dataset(self, dataset_name: str) -> list:
        """Devuelve las capas pertenecientes a un Dataset."""
        if not self.conn: return []
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM qgdb_layers WHERE dataset_name = ? ORDER BY layer_name", (dataset_name,))
        return [dict(row) for row in cursor.fetchall()]

    def get_domains(self) -> dict:
        """Devuelve todos los dominios agrupados por nombre."""
        if not self.conn: return {}
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM qgdb_domains ORDER BY domain_name, code")
        result = {}
        for row in cursor.fetchall():
            dname = row['domain_name']
            if dname not in result: result[dname] = []
            result[dname].append({'code': row['code'], 'description': row['description']})
        return result

    def get_relationships(self) -> list:
        """Devuelve la lista de relaciones 1:N / N:M."""
        if not self.conn: return []
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM qgdb_relationships")
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Cierra la conexión SQLite."""
        if self.conn:
            self.conn.close()
            self.conn = None

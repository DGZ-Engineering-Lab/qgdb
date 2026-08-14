# -*- coding: utf-8 -*-
"""
QGDB Native File Format Driver API
Permite la creación, lectura, edición y gestión dinámica de archivos de datos .qgdb.
"""
import sqlite3
import os
import json
import datetime
from typing import List, Dict, Union

class QGDBFile:
    """
    Representa una instancia activa de un archivo .qgdb en disco.
    Permite al usuario crear y estructurar su geodatabase dinámicamente a su propia medida.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.conn = sqlite3.connect(filepath)
        self.conn.row_factory = sqlite3.Row
        self._ensure_system_tables()

    def _ensure_system_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS qgdb_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qgdb_datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT,
                icon TEXT DEFAULT 'folder'
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qgdb_layers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_name TEXT REFERENCES qgdb_datasets(name),
                layer_name TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                geometry_type TEXT DEFAULT 'NONE',
                primary_key TEXT DEFAULT 'fid'
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qgdb_domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain_name TEXT NOT NULL,
                code TEXT NOT NULL,
                description TEXT NOT NULL,
                UNIQUE(domain_name, code)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qgdb_field_config (
                layer_name TEXT NOT NULL,
                field_name TEXT NOT NULL,
                domain_name TEXT,
                is_required INTEGER DEFAULT 0,
                is_unique INTEGER DEFAULT 0,
                default_value TEXT,
                widget_type TEXT DEFAULT 'ValueMap',
                PRIMARY KEY (layer_name, field_name)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qgdb_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                parent_layer TEXT NOT NULL,
                parent_key TEXT NOT NULL,
                child_layer TEXT NOT NULL,
                child_key TEXT NOT NULL,
                cardinality TEXT DEFAULT '1:N'
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qgdb_topology_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_type TEXT NOT NULL,
                layer_a TEXT NOT NULL,
                layer_b TEXT,
                severity TEXT DEFAULT 'ERROR'
            );
        """)
        self.conn.commit()

    def create_dataset(self, name: str, title: str = None, description: str = "") -> bool:
        """Crea un nuevo Feature Dataset dinámico en el archivo .qgdb."""
        if not title: title = name
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO qgdb_datasets (name, title, description) VALUES (?, ?, ?)",
            (name, title, description)
        )
        self.conn.commit()
        return True

    def create_feature_class(self, dataset_name: str, layer_name: str, title: str = None, geometry_type: str = "POLYGON") -> bool:
        """Crea y registra una nueva Feature Class (capa) dentro de un Dataset."""
        if not title: title = layer_name
        cursor = self.conn.cursor()
        # Asegurar que el dataset existe
        cursor.execute("INSERT OR IGNORE INTO qgdb_datasets (name, title) VALUES (?, ?)", (dataset_name, dataset_name))
        cursor.execute(
            "INSERT OR REPLACE INTO qgdb_layers (dataset_name, layer_name, title, geometry_type) VALUES (?, ?, ?, ?)",
            (dataset_name, layer_name, title, geometry_type)
        )
        self.conn.commit()
        return True

    def add_domain(self, domain_name: str, values: List[Dict[str, str]]) -> bool:
        """Agrega un dominio de atributos codificados al archivo .qgdb."""
        cursor = self.conn.cursor()
        for item in values:
            cursor.execute(
                "INSERT OR REPLACE INTO qgdb_domains (domain_name, code, description) VALUES (?, ?, ?)",
                (domain_name, str(item['code']), str(item['description']))
            )
        self.conn.commit()
        return True

    def add_relationship(self, name: str, parent_layer: str, parent_key: str, child_layer: str, child_key: str, cardinality: str = "1:N") -> bool:
        """Registra una relación (1:1, 1:N, N:M) entre capas en el archivo .qgdb."""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO qgdb_relationships 
               (name, parent_layer, parent_key, child_layer, child_key, cardinality)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, parent_layer, parent_key, child_layer, child_key, cardinality)
        )
        self.conn.commit()
        return True

    def list_datasets(self) -> List[Dict]:
        """Lista los Datasets existentes en el archivo .qgdb."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM qgdb_datasets ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

    def list_feature_classes(self, dataset_name: str = None) -> List[Dict]:
        """Lista las Feature Classes del archivo .qgdb (opcionalmente filtradas por Dataset)."""
        cursor = self.conn.cursor()
        if dataset_name:
            cursor.execute("SELECT * FROM qgdb_layers WHERE dataset_name = ? ORDER BY layer_name", (dataset_name,))
        else:
            cursor.execute("SELECT * FROM qgdb_layers ORDER BY dataset_name, layer_name")
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Cierra el archivo .qgdb."""
        if self.conn:
            self.conn.close()
            self.conn = None


class QGDBDriver:
    """
    Driver principal del formato de archivo .qgdb.
    """

    @staticmethod
    def create(filepath: str, title: str = "Nuevo Proyecto QGDB") -> QGDBFile:
        """Crea un nuevo archivo .qgdb físico en disco."""
        if not filepath.endswith('.qgdb'):
            filepath += '.qgdb'
            
        if os.path.exists(filepath):
            os.remove(filepath)

        qfile = QGDBFile(filepath)
        cursor = qfile.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO qgdb_metadata (key, value) VALUES ('qgdb_version', '1.0')")
        cursor.execute(f"INSERT OR REPLACE INTO qgdb_metadata (key, value) VALUES ('created_at', '{datetime.datetime.now().isoformat()}')")
        cursor.execute("INSERT OR REPLACE INTO qgdb_metadata (key, value) VALUES ('title', ?)", (title,))
        qfile.conn.commit()
        return qfile

    @staticmethod
    def open(filepath: str) -> QGDBFile:
        """Abre un archivo .qgdb existente para lectura o modificación."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"No existe el archivo .qgdb en: {filepath}")
        return QGDBFile(filepath)

# -*- coding: utf-8 -*-
import sqlite3
import os

class QGDBSchemaBuilder:
    """
    Construye las tablas del sistema qgdb_* dentro de una base de datos GeoPackage / SQLite.
    """

    @staticmethod
    def initialize_qgdb_system_tables(conn: sqlite3.Connection):
        """
        Crea las tablas de metadatos de sistema qgdb_* si no existen.
        """
        cursor = conn.cursor()

        # 1. Metadatos generales del contenedor
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qgdb_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)

        # 2. Datasets (Grupos Temáticos)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qgdb_datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT,
                icon TEXT DEFAULT 'folder'
            );
        """)

        # 3. Mapeo de Capas y Datasets
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

        # 4. Dominios de Atributos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qgdb_domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain_name TEXT NOT NULL,
                code TEXT NOT NULL,
                description TEXT NOT NULL,
                UNIQUE(domain_name, code)
            );
        """)

        # 5. Configuración de Campos (Formularios, Dominios, Restricciones)
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

        # 6. Relaciones 1:1, 1:N, N:M
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

        # 7. Reglas de Topología y Geometría
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qgdb_topology_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_type TEXT NOT NULL,
                layer_a TEXT NOT NULL,
                layer_b TEXT,
                severity TEXT DEFAULT 'ERROR'
            );
        """)

        conn.commit()

# -*- coding: utf-8 -*-
import sqlite3
import os

class QGDBSchemaBuilder:
    """
    Construye las tablas del sistema qgdb_* y la estructura base OGC GeoPackage
    dentro de un contenedor .qgdb / .qgpkg.
    """

    @staticmethod
    def initialize_qgdb_system_tables(conn: sqlite3.Connection):
        """
        Crea las tablas de metadatos de sistema qgdb_* y la cabecera OGC GeoPackage.
        """
        cursor = conn.cursor()

        # Cabecera GeoPackage Application ID
        cursor.execute("PRAGMA application_id = 1196444487;") # 0x47504B47 ('GPKG')
        cursor.execute("PRAGMA user_version = 10300;")

        # Tablas estándar OGC GeoPackage
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gpkg_spatial_ref_sys (
                srs_name TEXT NOT NULL,
                srs_id INTEGER NOT NULL PRIMARY KEY,
                organization TEXT NOT NULL,
                organization_coordsys_id INTEGER NOT NULL,
                definition TEXT NOT NULL,
                description TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gpkg_contents (
                table_name TEXT NOT NULL PRIMARY KEY,
                data_type TEXT NOT NULL,
                identifier TEXT UNIQUE,
                description TEXT DEFAULT '',
                last_change DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                min_x DOUBLE,
                min_y DOUBLE,
                max_x DOUBLE,
                max_y DOUBLE,
                srs_id INTEGER REFERENCES gpkg_spatial_ref_sys(srs_id)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gpkg_geometry_columns (
                table_name TEXT NOT NULL,
                column_name TEXT NOT NULL,
                geometry_type_name TEXT NOT NULL,
                srs_id INTEGER NOT NULL REFERENCES gpkg_spatial_ref_sys(srs_id),
                z TINYINT NOT NULL DEFAULT 0,
                m TINYINT NOT NULL DEFAULT 0,
                CONSTRAINT pk_geom_cols PRIMARY KEY (table_name, column_name),
                CONSTRAINT fk_gc_tn FOREIGN KEY (table_name) REFERENCES gpkg_contents(table_name)
            );
        """)

        # Insertar CRS por defecto (EPSG:4326, EPSG:9377 Origen Nacional, Undefined)
        cursor.execute("""
            INSERT OR IGNORE INTO gpkg_spatial_ref_sys VALUES 
            ('Undefined Cartesian', -1, 'NONE', -1, 'undefined', 'undefined cartesian coordinate reference system'),
            ('Undefined Geographic', 0, 'NONE', 0, 'undefined', 'undefined geographic coordinate reference system'),
            ('WGS 84', 4326, 'EPSG', 4326, 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]', 'WGS 84'),
            ('MAGNA-SIRGAS / Origen-Nacional', 9377, 'EPSG', 9377, 'PROJCS["MAGNA-SIRGAS / Origen-Nacional",GEOGCS["MAGNA-SIRGAS",DATUM["Marco_Geocentrico_Nacional_de_Referencia",SPHEROID["GRS 1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",4.0],PARAMETER["central_meridian",-73.0],PARAMETER["scale_factor",0.9992],PARAMETER["false_easting",5000000.0],PARAMETER["false_northing",2000000.0],UNIT["metre",1]]', 'Colombia Origen Nacional');
        """)

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

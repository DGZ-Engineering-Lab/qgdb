# -*- coding: utf-8 -*-
import os
import sqlite3
from osgeo import gdal, ogr
from .gdb_analyzer import GDBAnalyzer
try:
    from core.qgdb_engine import QGDBEngine
except ImportError:
    from ..core.qgdb_engine import QGDBEngine

class GDB2QGDBConverter:
    """
    Conversor de alta fidelidad: ESRI File Geodatabase (.gdb) a QGIS Geodatabase (.qgdb).
    Garantiza geometrías vectoriales reales OGC (Point, LineString, Polygon) y preserva Feature Datasets.
    """

    def __init__(self, input_gdb: str, output_qgdb: str):
        self.input_gdb = input_gdb
        self.output_qgdb = output_qgdb

    def convert(self) -> bool:
        """
        Ejecuta el proceso ETL de conversión vectorial y metadatos QGDB.
        """
        print("1. Analizando Feature Datasets de la GDB...")
        analyzer = GDBAnalyzer(self.input_gdb)
        intermediate_schema = analyzer.analyze()

        if os.path.exists(self.output_qgdb):
            os.remove(self.output_qgdb)

        # 2. Convertir capas vectoriales con GDAL VectorTranslate (GPKG OGC Real)
        print("2. Transfiriendo capas vectoriales y geometrías reales OGC...")
        src_ds = ogr.Open(self.input_gdb)
        if not src_ds:
            raise RuntimeError(f"No se pudo abrir la GDB origen: {self.input_gdb}")

        options = gdal.VectorTranslateOptions(
            format='GPKG',
            accessMode='overwrite',
            geometryType='PROMOTE_TO_MULTI',
            layerCreationOptions=['SPATIAL_INDEX=YES']
        )
        gdal.VectorTranslate(self.output_qgdb, src_ds, options=options)

        # 3. Inyectar tablas de sistema qgdb_* dentro del contenedor
        print("3. Inyectando estructura de Datasets y metadatos QGDB...")
        conn = sqlite3.connect(self.output_qgdb)
        cursor = conn.cursor()

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

        # Registrar metadatos
        cursor.execute("INSERT OR REPLACE INTO qgdb_metadata (key, value) VALUES ('qgdb_version', '1.0');")
        cursor.execute("INSERT OR REPLACE INTO qgdb_metadata (key, value) VALUES ('title', ?);", (intermediate_schema['metadata']['title'],))
        cursor.execute("INSERT OR REPLACE INTO qgdb_metadata (key, value) VALUES ('profile', ?);", (intermediate_schema['metadata']['profile'],))

        # Registrar Datasets
        layer_to_ds = intermediate_schema.get("layer_to_dataset", {})
        for ds in intermediate_schema.get("datasets", []):
            cursor.execute("INSERT OR REPLACE INTO qgdb_datasets (name, title, description) VALUES (?, ?, ?)",
                           (ds['name'], ds['title'], ds.get('description', '')))

        # Registrar capas mapeadas
        cursor.execute("SELECT table_name, data_type, identifier FROM gpkg_contents")
        for row in cursor.fetchall():
            tbl_name = row[0]
            ds_name = layer_to_ds.get(tbl_name, "GENERAL")
            cursor.execute("INSERT OR IGNORE INTO qgdb_datasets (name, title) VALUES (?, ?)", (ds_name, ds_name))
            cursor.execute("INSERT OR REPLACE INTO qgdb_layers (dataset_name, layer_name, title, geometry_type) VALUES (?, ?, ?, ?)",
                           (ds_name, tbl_name, tbl_name, row[1]))

        conn.commit()
        conn.close()
        print(f"✅ Conversión completa a .qgdb exitosa en: {self.output_qgdb}")
        return True
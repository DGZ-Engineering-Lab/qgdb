# -*- coding: utf-8 -*-
import os
try:
    from core.qgdb_engine import QGDBEngine
except ImportError:
    from ..core.qgdb_engine import QGDBEngine

class QGDB2GDBExporter:
    """
    Exportador de QGIS Geodatabase (.qgdb) a ESRI File Geodatabase (.gdb).
    """

    def __init__(self, input_qgdb: str, output_gdb: str):
        self.input_qgdb = input_qgdb
        self.output_gdb = output_gdb

    def export(self) -> bool:
        """
        Exporta las capas y metadatos de QGDB hacia ESRI FileGDB usando GDAL/OGR.
        """
        try:
            from osgeo import gdal, ogr
            src_ds = ogr.Open(self.input_qgdb)
            if src_ds:
                options = gdal.VectorTranslateOptions(format='FileGDB', accessMode='overwrite')
                gdal.VectorTranslate(self.output_gdb, src_ds, options=options)
                return True
        except Exception as e:
            print(f"Error exportando a FileGDB con GDAL: {e}")
            return False
        return False

# -*- coding: utf-8 -*-
import os
import sqlite3
try:
    from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox
    from qgis.PyQt.QtGui import QIcon
    from qgis.core import QgsApplication, QgsMessageLog, Qgis, QgsProject, QgsVectorLayer
    QGIS_AVAILABLE = True
except ImportError:
    QGIS_AVAILABLE = False

class QGDBPlugin:
    """Clase principal del Plugin QGDB Provider & Manager en QGIS."""

    def __init__(self, iface):
        self.iface = iface
        self.provider = None

    def initGui(self):
        if not QGIS_AVAILABLE: return

        # 1. Registrar proveedor del panel navegador
        try:
            from .browser_provider import QGDBBrowserDataItemProvider
            self.provider = QGDBBrowserDataItemProvider()
            QgsApplication.dataItemProviderRegistry().addProvider(self.provider)
            QgsMessageLog.logMessage("Proveedor de Formato QGDB (.qgdb) registrado en Panel Navegador.", "QGDB", Qgis.Info)
        except Exception as e:
            QgsMessageLog.logMessage(f"Error registrando proveedor QGDB: {e}", 'QGDB', Qgis.Warning)

        # 2. Acción 1: Cargar .qgdb con estructura temática al Panel de Capas
        self.action_load_qgdb = QAction("📂 Cargar Geodatabase (.qgdb) con Estructura de Datasets", self.iface.mainWindow())
        self.action_load_qgdb.triggered.connect(self.load_qgdb_with_datasets)
        self.iface.addPluginToMenu("&QGDB Geodatabase", self.action_load_qgdb)
        self.iface.addToolBarIcon(self.action_load_qgdb)

        # 3. Acción 2: Crear proyecto normativo LADM-COL
        self.action_create_ladm = QAction("🇨🇴 Crear Proyecto QGDB (LADM-COL Colombia)", self.iface.mainWindow())
        self.action_create_ladm.triggered.connect(self.create_ladm_col_project)
        self.iface.addPluginToMenu("&QGDB Geodatabase", self.action_create_ladm)

    def unload(self):
        if not QGIS_AVAILABLE: return
        if self.provider:
            try:
                QgsApplication.dataItemProviderRegistry().removeProvider(self.provider)
            except Exception:
                pass
        self.iface.removePluginMenu("&QGDB Geodatabase", self.action_load_qgdb)
        self.iface.removePluginMenu("&QGDB Geodatabase", self.action_create_ladm)
        self.iface.removeToolBarIcon(self.action_load_qgdb)

    def load_qgdb_with_datasets(self):
        """Abre un diálogo para seleccionar un archivo .qgdb y lo carga en el Panel de Capas estructurado por Datasets."""
        filename, _ = QFileDialog.getOpenFileName(
            self.iface.mainWindow(), 
            "Seleccionar Archivo QGIS Geodatabase (.qgdb)", 
            "", 
            "QGDB Files (*.qgdb *.qgpkg)"
        )
        if not filename: return

        try:
            conn = sqlite3.connect(filename)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='qgdb_datasets'")
            if not cursor.fetchone():
                QMessageBox.warning(self.iface.mainWindow(), "Aviso", "El archivo seleccionado no contiene metadatos de Datasets QGDB.")
                conn.close()
                return

            cursor.execute("SELECT name, title FROM qgdb_datasets ORDER BY name")
            datasets = cursor.fetchall()
            
            basename = os.path.basename(filename)
            root = QgsProject.instance().layerTreeRoot()
            main_group = root.addGroup(f"📦 {basename}")
            
            total_layers_added = 0
            
            for ds in datasets:
                ds_name, ds_title = ds[0], ds[1]
                cursor.execute("SELECT layer_name, title FROM qgdb_layers WHERE dataset_name = ? ORDER BY layer_name", (ds_name,))
                layers = cursor.fetchall()
                
                if not layers: continue
                
                ds_group = main_group.addGroup(f"📁 {ds_title or ds_name}")
                
                for lyr in layers:
                    tbl_name = lyr[0]
                    lyr_title = lyr[1] or tbl_name
                    uri = f"{filename}|layername={tbl_name}"
                    vlayer = QgsVectorLayer(uri, lyr_title, "ogr")
                    if vlayer.isValid():
                        QgsProject.instance().addMapLayer(vlayer, False)
                        ds_group.addLayer(vlayer)
                        total_layers_added += 1

            conn.close()
            self.iface.messageBar().pushMessage(
                "QGDB Cargado", 
                f"Se cargaron {total_layers_added} capas organizadas en {len(datasets)} Datasets temáticos.", 
                level=Qgis.Success, 
                duration=5
            )
        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), "Error", f"Error cargando Geodatabase: {e}")

    def create_ladm_col_project(self):
        filename, _ = QFileDialog.getSaveFileName(self.iface.mainWindow(), "Crear Proyecto QGDB LADM-COL", "", "QGDB Files (*.qgdb *.qgpkg)")
        if filename:
            if not filename.endswith('.qgdb') and not filename.endswith('.qgpkg'):
                filename += '.qgdb'
            try:
                import sqlite3
                conn = sqlite3.connect(filename)
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS qgdb_metadata (key TEXT PRIMARY KEY, value TEXT);")
                cursor.execute("CREATE TABLE IF NOT EXISTS qgdb_datasets (id INTEGER PRIMARY KEY, name TEXT UNIQUE, title TEXT, description TEXT, icon TEXT);")
                cursor.execute("CREATE TABLE IF NOT EXISTS qgdb_layers (id INTEGER PRIMARY KEY, dataset_name TEXT, layer_name TEXT UNIQUE, title TEXT, geometry_type TEXT, primary_key TEXT);")
                cursor.execute("INSERT OR REPLACE INTO qgdb_metadata VALUES ('qgdb_version', '1.0');")
                cursor.execute("INSERT OR REPLACE INTO qgdb_metadata VALUES ('profile', 'QGDB-LADM-COL');")
                cursor.execute("INSERT OR REPLACE INTO qgdb_datasets (name, title) VALUES ('CATASTRO', 'Componente Catastral');")
                cursor.execute("INSERT OR REPLACE INTO qgdb_datasets (name, title) VALUES ('JURIDICO', 'Componente Jurídico');")
                cursor.execute("INSERT OR REPLACE INTO qgdb_layers (dataset_name, layer_name, title) VALUES ('CATASTRO', 'LC_Predio', 'Predios');")
                cursor.execute("INSERT OR REPLACE INTO qgdb_layers (dataset_name, layer_name, title) VALUES ('CATASTRO', 'LC_Terreno', 'Terrenos');")
                cursor.execute("INSERT OR REPLACE INTO qgdb_layers (dataset_name, layer_name, title) VALUES ('CATASTRO', 'LC_Construccion', 'Construcciones');")
                cursor.execute("INSERT OR REPLACE INTO qgdb_layers (dataset_name, layer_name, title) VALUES ('JURIDICO', 'LC_Interesado', 'Interesados');")
                cursor.execute("INSERT OR REPLACE INTO qgdb_layers (dataset_name, layer_name, title) VALUES ('JURIDICO', 'LC_Derecho', 'Derechos');")
                conn.commit()
                conn.close()
                QMessageBox.information(self.iface.mainWindow(), "Éxito", f"Proyecto QGDB LADM-COL v3.0 creado en:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self.iface.mainWindow(), "Error", f"No se pudo crear el proyecto: {e}")

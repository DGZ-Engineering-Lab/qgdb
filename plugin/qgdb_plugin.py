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
        self.actions = []

    def initGui(self):
        if not QGIS_AVAILABLE:
            return

        # 1. Registrar proveedor del panel navegador
        try:
            from .browser_provider import QGDBBrowserDataItemProvider
            self.provider = QGDBBrowserDataItemProvider()
            QgsApplication.dataItemProviderRegistry().addProvider(self.provider)
            QgsMessageLog.logMessage(
                "Proveedor de Formato QGDB (.qgdb) registrado en Panel Navegador.", 
                "QGDB", 
                Qgis.Info
            )
        except Exception as e:
            QgsMessageLog.logMessage(f"Error registrando proveedor QGDB: {e}", 'QGDB', Qgis.Warning)

        # 2. Acción 1: Crear Nueva Geodatabase QGDB
        self.action_new_qgdb = QAction("✨ Crear Nueva Geodatabase QGDB...", self.iface.mainWindow())
        self.action_new_qgdb.triggered.connect(self.open_new_qgdb_dialog)
        self.iface.addPluginToMenu("&QGDB Geodatabase", self.action_new_qgdb)
        self.iface.addToolBarIcon(self.action_new_qgdb)
        self.actions.append(self.action_new_qgdb)

        # 3. Acción 2: Convertir ESRI GDB ➔ QGDB
        self.action_convert_gdb = QAction("🔄 Convertir ESRI File Geodatabase (.gdb) a QGDB...", self.iface.mainWindow())
        self.action_convert_gdb.triggered.connect(self.open_convert_gdb_dialog)
        self.iface.addPluginToMenu("&QGDB Geodatabase", self.action_convert_gdb)
        self.iface.addToolBarIcon(self.action_convert_gdb)
        self.actions.append(self.action_convert_gdb)

        # 4. Acción 3: Cargar .qgdb con estructura temática al Panel de Capas
        self.action_load_qgdb = QAction("📂 Cargar Geodatabase (.qgdb) con Estructura de Datasets", self.iface.mainWindow())
        self.action_load_qgdb.triggered.connect(self.load_qgdb_with_datasets)
        self.iface.addPluginToMenu("&QGDB Geodatabase", self.action_load_qgdb)
        self.iface.addToolBarIcon(self.action_load_qgdb)
        self.actions.append(self.action_load_qgdb)

    def unload(self):
        if not QGIS_AVAILABLE:
            return
        if self.provider:
            try:
                QgsApplication.dataItemProviderRegistry().removeProvider(self.provider)
            except Exception as e:
                QgsMessageLog.logMessage(f"Aviso al descargar proveedor QGDB: {e}", "QGDB", Qgis.Info)
        for action in self.actions:
            self.iface.removePluginMenu("&QGDB Geodatabase", action)
            self.iface.removeToolBarIcon(action)

    def open_new_qgdb_dialog(self):
        """Abre el diálogo gráfico para crear una nueva Geodatabase QGDB."""
        try:
            from .ui_dialogs import NewQGDBDialog
        except ImportError:
            from ui_dialogs import NewQGDBDialog
        dlg = NewQGDBDialog(self.iface.mainWindow())
        dlg.exec_()

    def open_convert_gdb_dialog(self):
        """Abre el diálogo gráfico para convertir una File Geodatabase (.gdb) a .qgdb."""
        try:
            from .ui_dialogs import GDBConverterDialog
        except ImportError:
            from ui_dialogs import GDBConverterDialog
        dlg = GDBConverterDialog(self.iface.mainWindow())
        dlg.exec_()

    def load_qgdb_with_datasets(self):
        """Abre un diálogo para seleccionar un archivo .qgdb y lo carga en el Panel de Capas estructurado por Datasets."""
        filename, _ = QFileDialog.getOpenFileName(
            self.iface.mainWindow(), 
            "Seleccionar Archivo QGIS Geodatabase (.qgdb)", 
            "", 
            "QGDB Files (*.qgdb *.qgpkg)"
        )
        if not filename:
            return

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
                
                if not layers:
                    continue
                
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

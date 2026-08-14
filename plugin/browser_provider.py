# -*- coding: utf-8 -*-
import sqlite3
import os
try:
    from qgis.core import (
        QgsDataItemProvider, QgsDataCollectionItem, QgsLayerItem, QgsDataItem, 
        Qgis, QgsVectorLayer, QgsProject, QgsLayerTreeGroup
    )
    from qgis.PyQt.QtWidgets import QAction, QMenu
    from qgis.PyQt.QtGui import QIcon
    QGIS_AVAILABLE = True
except ImportError:
    QGIS_AVAILABLE = False

if QGIS_AVAILABLE:
    class QGDBDatasetItem(QgsDataCollectionItem):
        """Nodo del árbol del Navegador que representa un Feature Dataset (Carpeta Temática)."""
        def __init__(self, parent, name, title, filepath, layers=None):
            super().__init__(parent, title, filepath)
            self.dataset_name = name
            self.filepath = filepath
            self.layers = layers or []
            self.setIcon(QIcon(":/images/themes/default/mIconFolder.svg"))
            self.populate()

        def populate(self):
            """Carga las capas vectoriales hijas pertenecientes a este Feature Dataset."""
            if not self.layers:
                try:
                    conn = sqlite3.connect(self.filepath)
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT layer_name, title, geometry_type 
                        FROM qgdb_layers 
                        WHERE dataset_name = ? 
                        ORDER BY layer_name
                    """, (self.dataset_name,))
                    self.layers = [{'layer_name': r[0], 'title': r[1], 'geometry_type': r[2]} for r in cursor.fetchall()]
                    conn.close()
                except Exception as e:
                    print(f"Error cargando capas de {self.dataset_name}: {e}")

            for layer in self.layers:
                table_name = layer['layer_name']
                display_name = layer.get('title') or table_name
                uri = f"{self.filepath}|layername={table_name}"
                layer_item = QgsLayerItem(
                    self, 
                    display_name, 
                    uri, 
                    "ogr", 
                    Qgis.BrowserLayerType.Vector
                )
                self.addChildItem(layer_item)

        def actions(self, parent):
            """Menú contextual con clic derecho sobre el Dataset."""
            actions_list = []
            action_add = QAction(f"📁 Añadir Dataset '{self.dataset_name}' como Grupo de Capas", parent)
            action_add.setIcon(QIcon(":/images/themes/default/mIconFolder.svg"))
            action_add.triggered.connect(self.add_dataset_as_group)
            actions_list.append(action_add)
            return actions_list

        def add_dataset_as_group(self):
            """Añade todas las capas del dataset agrupadas en el Panel de Capas."""
            root = QgsProject.instance().layerTreeRoot()
            group = root.addGroup(f"📁 {self.dataset_name}")
            
            for layer in self.layers:
                tbl = layer['layer_name']
                title = layer.get('title') or tbl
                uri = f"{self.filepath}|layername={tbl}"
                vlayer = QgsVectorLayer(uri, title, "ogr")
                if vlayer.isValid():
                    QgsProject.instance().addMapLayer(vlayer, False)
                    group.addLayer(vlayer)


    class QGDBRootItem(QgsDataCollectionItem):
        """Nodo raíz que representa el contenedor .qgdb completo."""
        def __init__(self, parent, title, filepath, datasets):
            super().__init__(parent, title, filepath)
            self.filepath = filepath
            self.datasets = datasets
            self.setIcon(QIcon(":/images/themes/default/mIconDb.svg"))
            self.populate_datasets()

        def populate_datasets(self):
            for ds in self.datasets:
                ds_name = ds['name']
                ds_title = ds.get('title') or ds_name
                ds_item = QGDBDatasetItem(self, ds_name, f"📁 {ds_title}", self.filepath)
                self.addChildItem(ds_item)

        def actions(self, parent):
            """Menú contextual con clic derecho sobre el archivo .qgdb."""
            actions_list = []
            action_load_all = QAction("📦 Añadir toda la Geodatabase al Proyecto (Organizada por Datasets)", parent)
            action_load_all.setIcon(QIcon(":/images/themes/default/mIconDb.svg"))
            action_load_all.triggered.connect(self.load_entire_geodatabase)
            actions_list.append(action_load_all)
            return actions_list

        def load_entire_geodatabase(self):
            """Carga toda la geodatabase creando grupos temáticos en el Panel de Capas de QGIS."""
            basename = os.path.basename(self.filepath)
            root = QgsProject.instance().layerTreeRoot()
            main_group = root.addGroup(f"📦 {basename}")

            try:
                conn = sqlite3.connect(self.filepath)
                cursor = conn.cursor()
                
                for ds in self.datasets:
                    ds_name = ds['name']
                    ds_group = main_group.addGroup(f"📁 {ds_name}")
                    
                    cursor.execute("SELECT layer_name, title FROM qgdb_layers WHERE dataset_name = ? ORDER BY layer_name", (ds_name,))
                    layers = cursor.fetchall()
                    
                    for lyr_row in layers:
                        table_name = lyr_row[0]
                        layer_title = lyr_row[1] or table_name
                        uri = f"{self.filepath}|layername={table_name}"
                        vlayer = QgsVectorLayer(uri, layer_title, "ogr")
                        if vlayer.isValid():
                            QgsProject.instance().addMapLayer(vlayer, False)
                            ds_group.addLayer(vlayer)
                conn.close()
            except Exception as e:
                print(f"Error cargando toda la geodatabase: {e}")


    class QGDBBrowserDataItemProvider(QgsDataItemProvider):
        """
        Proveedor de Items para el Panel Navegador de QGIS.
        Intercepta archivos .qgdb / .qgpkg y muestra la jerarquía de Datasets.
        """
        def name(self):
            return "QGDB Data Item Provider"

        def capabilities(self):
            """Devuelve las capacidades del proveedor para QGIS 3.44+."""
            try:
                return Qgis.DataItemProviderCapability.Files
            except Exception:
                try:
                    return Qgis.DataItemProviderCapabilities(Qgis.DataItemProviderCapability.Files)
                except Exception:
                    return 1

        def createDataItem(self, path, parentItem):
            if path and (path.lower().endswith('.qgdb') or path.lower().endswith('.qgpkg')) and os.path.exists(path):
                try:
                    conn = sqlite3.connect(path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='qgdb_datasets'")
                    if not cursor.fetchone():
                        conn.close()
                        return None
                    
                    cursor.execute("SELECT name, title, description FROM qgdb_datasets ORDER BY name")
                    datasets = [{'name': r[0], 'title': r[1], 'description': r[2]} for r in cursor.fetchall()]
                    conn.close()
                    
                    if datasets:
                        basename = os.path.basename(path)
                        return QGDBRootItem(parentItem, f"📦 {basename}", path, datasets)
                except Exception as e:
                    print(f"Error creando item de navegador QGDB: {e}")
            return None

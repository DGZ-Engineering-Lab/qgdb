# -*- coding: utf-8 -*-
import os
import sqlite3
try:
    from qgis.PyQt.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
        QComboBox, QFileDialog, QMessageBox, QProgressBar, QGroupBox, QFormLayout,
        QCheckBox, QRadioButton, QButtonGroup
    )
    from qgis.PyQt.QtCore import Qt, QCoreApplication
    from qgis.PyQt.QtGui import QIcon
    from qgis.gui import QgsProjectionSelectionWidget
    from qgis.core import QgsCoordinateReferenceSystem, QgsProject, QgsMessageLog, Qgis, QgsVectorLayer
    QGIS_AVAILABLE = True
except ImportError:
    QGIS_AVAILABLE = False


class NewQGDBDialog(QDialog):
    """Diálogo gráfico para la creación libre y normativa de Geodatabases .qgdb."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✨ Crear Nueva Geodatabase QGDB (.qgdb)")
        self.setMinimumWidth(540)
        self.output_filepath = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 1. Ubicación del archivo
        file_group = QGroupBox("📍 Archivo Destino")
        file_layout = QHBoxLayout(file_group)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Selecciona la ruta del archivo .qgdb...")
        btn_browse = QPushButton("Explorar...")
        btn_browse.clicked.connect(self.browse_file)
        file_layout.addWidget(self.path_edit)
        file_layout.addWidget(btn_browse)
        layout.addWidget(file_group)

        # 2. Plantilla / Perfil Normativo
        profile_group = QGroupBox("🏛️ Estructura y Perfil Normativo")
        profile_layout = QVBoxLayout(profile_group)

        self.combo_profile = QComboBox()
        self.combo_profile.addItem("🇨🇴 Catastro Multipropósito Colombia (LADM-COL v3.0 - IGAC/SNR)", "LADM_COL")
        self.combo_profile.addItem("🇨🇴 Cartografía Básica Oficial Colombia (Resolución IGAC)", "CARTO_BASICA")
        self.combo_profile.addItem("🌐 Geodatabase en Blanco (Personalizada por el Usuario)", "CUSTOM")
        profile_layout.addWidget(self.combo_profile)

        self.lbl_profile_desc = QLabel("Crea automáticamente los Feature Datasets CATASTRO y JURIDICO con sus capas vectoriales y tablas.")
        self.lbl_profile_desc.setWordWrap(True)
        self.lbl_profile_desc.setStyleSheet("color: #64748b; font-size: 11px; margin-top: 4px;")
        profile_layout.addWidget(self.lbl_profile_desc)
        self.combo_profile.currentIndexChanged.connect(self.update_profile_desc)

        layout.addWidget(profile_group)

        # 3. Sistema de Referencia Espacial (CRS)
        crs_group = QGroupBox("🌐 Sistema de Coordenadas de Referencia (CRS)")
        crs_layout = QVBoxLayout(crs_group)
        self.crs_widget = QgsProjectionSelectionWidget(self)
        # Origen Nacional Único de Colombia EPSG:9377 por defecto
        self.crs_widget.setCrs(QgsCoordinateReferenceSystem("EPSG:9377"))
        crs_layout.addWidget(self.crs_widget)
        layout.addWidget(crs_group)

        # 4. Botones
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        self.btn_create = QPushButton("✨ Crear Geodatabase")
        self.btn_create.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 6px 16px;")
        self.btn_create.clicked.connect(self.create_qgdb)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_create)
        layout.addLayout(btn_layout)

    def browse_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar Geodatabase QGDB", "", "QGDB Files (*.qgdb *.qgpkg)")
        if filename:
            if not filename.endswith('.qgdb') and not filename.endswith('.qgpkg'):
                filename += '.qgdb'
            self.path_edit.setText(filename)

    def update_profile_desc(self):
        data = self.combo_profile.currentData()
        if data == "LADM_COL":
            self.lbl_profile_desc.setText("Estructura conforme a LADM-COL v3.0: Datasets CATASTRO y JURIDICO con LC_Predio, LC_Terreno, LC_Construccion, LC_Interesado, LC_Derecho.")
        elif data == "CARTO_BASICA":
            self.lbl_profile_desc.setText("Estructura conforme a Cartografía Básica IGAC: Datasets CoberturaTierra, Elevacion, Hidrografia, Transporte, ViviendaCiudadTerritorio, etc.")
        else:
            self.lbl_profile_desc.setText("Contenedor vacío listo para crear Feature Datasets, capas vectoriales y tablas personalizadas.")

    def create_qgdb(self):
        filepath = self.path_edit.text().strip()
        if not filepath:
            QMessageBox.warning(self, "Atención", "Por favor especifica la ruta del archivo .qgdb a crear.")
            return

        profile_type = self.combo_profile.currentData()
        crs_auth = self.crs_widget.crs().authid() or "EPSG:9377"

        try:
            from .core.qgdb_engine import QGDBEngine
            from .core.schema_builder import SchemaBuilder
        except Exception:
            from core.qgdb_engine import QGDBEngine
            from core.schema_builder import SchemaBuilder

        # Construir especificación según el perfil seleccionado
        if profile_type == "LADM_COL":
            try:
                from .profiles.ladm_col import LADMCOLProfileBuilder
                spec = LADMCOLProfileBuilder.get_ladm_col_spec()
            except Exception:
                from profiles.ladm_col import LADMCOLProfileBuilder
                spec = LADMCOLProfileBuilder.get_ladm_col_spec()
            spec["metadata"]["crs"] = crs_auth
        elif profile_type == "CARTO_BASICA":
            spec = {
                "metadata": {"title": "Cartografía Básica Oficial", "profile": "CARTO_BASICA_COLOMBIA", "crs": crs_auth},
                "datasets": [
                    {"name": "CoberturaTierra", "title": "Cobertura de la Tierra", "layers": ["ZVerde", "Bosque", "AExtra"]},
                    {"name": "Elevacion", "title": "Relieve y Elevación", "layers": ["CNivel", "LDTerr"]},
                    {"name": "Hidrografia", "title": "Hidrografía", "layers": ["Drenaj_L", "DAgua_R", "DAgua_P"]},
                    {"name": "Transporte", "title": "Infraestructura de Transporte", "layers": ["Via", "VFerre", "Puente_L", "Tunel"]},
                    {"name": "ViviendaCiudadTerritorio", "title": "Vivienda y Territorio", "layers": ["Constr_P", "Piscin", "ZDura"]},
                    {"name": "InfraestructuraServicios", "title": "Servicios Públicos", "layers": ["RATens", "Telefe", "Pozo", "Tuberi"]}
                ]
            }
        else: # CUSTOM
            spec = {
                "metadata": {"title": "Geodatabase Personalizada", "profile": "CUSTOM_QGDB", "crs": crs_auth},
                "datasets": [
                    {"name": "GENERAL", "title": "Dataset Principal", "layers": []}
                ]
            }

        engine = QGDBEngine()
        engine.create(filepath, spec)
        self.output_filepath = filepath
        QMessageBox.information(self, "Geodatabase Creada", f"✅ Archivo QGDB creado exitosamente:\n{filepath}\n\nCRS: {crs_auth}\nPerfil: {self.combo_profile.currentText()}")
        self.accept()


class GDBConverterDialog(QDialog):
    """Diálogo gráfico para la conversión bidireccional ESRI GDB ➔ QGDB."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔄 Conversor ESRI File Geodatabase (.gdb) ➔ QGDB (.qgdb)")
        self.setMinimumWidth(560)
        self.converted_qgdb = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 1. GDB Origen
        src_group = QGroupBox("📂 File Geodatabase ESRI Origen (.gdb)")
        src_layout = QHBoxLayout(src_group)
        self.src_edit = QLineEdit()
        self.src_edit.setPlaceholderText("Selecciona la carpeta .gdb de ESRI...")
        btn_src = QPushButton("Examinar...")
        btn_src.clicked.connect(self.browse_src_gdb)
        src_layout.addWidget(self.src_edit)
        src_layout.addWidget(btn_src)
        layout.addWidget(src_group)

        # 2. QGDB Destino
        dst_group = QGroupBox("📍 Archivo QGDB Destino (.qgdb)")
        dst_layout = QHBoxLayout(dst_group)
        self.dst_edit = QLineEdit()
        self.dst_edit.setPlaceholderText("Ruta donde se guardará el nuevo archivo .qgdb...")
        btn_dst = QPushButton("Guardar como...")
        btn_dst.clicked.connect(self.browse_dst_qgdb)
        dst_layout.addWidget(self.dst_edit)
        dst_layout.addWidget(btn_dst)
        layout.addWidget(dst_group)

        # 3. Opciones
        opt_group = QGroupBox("⚙️ Opciones de Migración y Calidad")
        opt_layout = QVBoxLayout(opt_group)
        self.chk_datasets = QCheckBox("Preservar jerarquía completa de Feature Datasets temáticos")
        self.chk_datasets.setChecked(True)
        self.chk_spatial_index = QCheckBox("Crear índices espaciales OGC R-Tree para máximo rendimiento")
        self.chk_spatial_index.setChecked(True)
        self.chk_promote_multi = QCheckBox("Promover geometrías a Multi (MultiPolígonos, MultiLíneas)")
        self.chk_promote_multi.setChecked(True)
        self.chk_auto_load = QCheckBox("Cargar automáticamente en el Panel de Capas al finalizar la conversión")
        self.chk_auto_load.setChecked(True)
        
        opt_layout.addWidget(self.chk_datasets)
        opt_layout.addWidget(self.chk_spatial_index)
        opt_layout.addWidget(self.chk_promote_multi)
        opt_layout.addWidget(self.chk_auto_load)
        layout.addWidget(opt_group)

        # 4. Progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 5. Botones
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Cerrar")
        btn_cancel.clicked.connect(self.reject)
        self.btn_convert = QPushButton("🔄 Iniciar Conversión")
        self.btn_convert.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 6px 18px;")
        self.btn_convert.clicked.connect(self.start_conversion)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_convert)
        layout.addLayout(btn_layout)

    def browse_src_gdb(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar File Geodatabase ESRI (.gdb)")
        if folder:
            self.src_edit.setText(folder)
            # Sugerir destino automático con el mismo nombre pero .qgdb
            default_dst = folder.rstrip("/\\") + ".qgdb"
            self.dst_edit.setText(default_dst)

    def browse_dst_qgdb(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Guardar como QGDB", self.dst_edit.text(), "QGDB Files (*.qgdb *.qgpkg)")
        if filename:
            if not filename.endswith('.qgdb') and not filename.endswith('.qgpkg'):
                filename += '.qgdb'
            self.dst_edit.setText(filename)

    def start_conversion(self):
        src_path = self.src_edit.text().strip()
        dst_path = self.dst_edit.text().strip()

        if not src_path or not os.path.exists(src_path):
            QMessageBox.warning(self, "Atención", "Por favor selecciona una File Geodatabase (.gdb) válida.")
            return

        if not dst_path:
            QMessageBox.warning(self, "Atención", "Por favor especifica la ruta de salida del archivo .qgdb.")
            return

        self.progress_bar.setVisible(True)
        self.btn_convert.setEnabled(False)
        QCoreApplication.processEvents()

        try:
            try:
                from .converters.gdb2qgdb import GDB2QGDBConverter
            except Exception:
                from converters.gdb2qgdb import GDB2QGDBConverter

            converter = GDB2QGDBConverter(src_path, dst_path)
            converter.convert()

            self.converted_qgdb = dst_path
            self.progress_bar.setVisible(False)
            self.btn_convert.setEnabled(True)

            QMessageBox.information(
                self, 
                "Conversión Exitosa", 
                f"✅ La Geodatabase ha sido convertida exitosamente a formato nativo QGDB:\n\n{dst_path}"
            )

            # Cargar automáticamente si está marcada la opción
            if self.chk_auto_load.isChecked():
                self.load_to_layers_panel(dst_path)

            self.accept()

        except Exception as e:
            self.progress_bar.setVisible(False)
            self.btn_convert.setEnabled(True)
            QMessageBox.critical(self, "Error de Conversión", f"Ocurrió un error durante la conversión:\n{e}")

    def load_to_layers_panel(self, filepath):
        """Carga la geodatabase convertida en el Panel de Capas."""
        try:
            conn = sqlite3.connect(filepath)
            cursor = conn.cursor()
            cursor.execute("SELECT name, title FROM qgdb_datasets ORDER BY name")
            datasets = cursor.fetchall()
            
            basename = os.path.basename(filepath)
            root = QgsProject.instance().layerTreeRoot()
            main_group = root.addGroup(f"📦 {basename}")
            
            for ds in datasets:
                ds_name, ds_title = ds[0], ds[1]
                cursor.execute("SELECT layer_name, title FROM qgdb_layers WHERE dataset_name = ? ORDER BY layer_name", (ds_name,))
                layers = cursor.fetchall()
                if not layers: continue
                
                ds_group = main_group.addGroup(f"📁 {ds_title or ds_name}")
                for lyr in layers:
                    tbl = lyr[0]
                    title = lyr[1] or tbl
                    uri = f"{filepath}|layername={tbl}"
                    vlayer = QgsVectorLayer(uri, title, "ogr")
                    if vlayer.isValid():
                        QgsProject.instance().addMapLayer(vlayer, False)
                        ds_group.addLayer(vlayer)
            conn.close()
        except Exception as e:
            print(f"Error cargando capas tras conversión: {e}")

# -*- coding: utf-8 -*-
try:
    from qgis.core import QgsVectorLayer, QgsEditorWidgetSetup, QgsRelation, QgsProject
    QGIS_AVAILABLE = True
except ImportError:
    QGIS_AVAILABLE = False

if QGIS_AVAILABLE:
    class QGDBFormInjector:
        """
        Configura automáticamente widgets ValueMap (Dominios), formularios y relaciones 1:N en capas de QGIS.
        """

        @staticmethod
        def apply_domains_to_layer(layer: QgsVectorLayer, domains_dict: dict):
            """
            Asigna automáticamente desplegables ValueMap a los campos que tengan dominios asignados.
            """
            if not layer or not layer.isValid(): return

            fields = layer.fields()
            for idx, field in enumerate(fields):
                fname = field.name()
                # Si el campo coincide con el nombre de un dominio
                matching_domain = None
                for dname in domains_dict:
                    if dname.lower().endswith(fname.lower()) or fname.lower() in dname.lower():
                        matching_domain = domains_dict[dname]
                        break

                if matching_domain:
                    # Construir mapa de valores {Descripción: Código}
                    val_map = {item['description']: item['code'] for item in matching_domain}
                    widget_setup = QgsEditorWidgetSetup('ValueMap', {'map': val_map})
                    layer.setEditorWidgetSetup(idx, widget_setup)

        @staticmethod
        def apply_relationships_to_project(relationships_list: list, qgdb_path: str):
            """
            Registra las relaciones 1:N / N:M en el gestor de relaciones de QGIS (QgsProject.relationManager).
            """
            rel_mgr = QgsProject.instance().relationManager()
            layers = QgsProject.instance().mapLayers().values()

            for rel_info in relationships_list:
                parent_lyr = None
                child_lyr = None
                for l in layers:
                    if l.name() == rel_info['parent_layer']: parent_lyr = l
                    if l.name() == rel_info['child_layer']: child_lyr = l

                if parent_lyr and child_lyr:
                    rel = QgsRelation()
                    rel.setId(f"rel_{rel_info['name']}")
                    rel.setName(rel_info['name'])
                    rel.setReferencingLayer(child_lyr.id())
                    rel.setReferencedLayer(parent_lyr.id())
                    rel.addFieldPair(rel_info['child_key'], rel_info['parent_key'])
                    if rel.isValid():
                        rel_mgr.addRelation(rel)

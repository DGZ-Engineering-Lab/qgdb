# -*- coding: utf-8 -*-
from osgeo import ogr
import os

class GDBAnalyzer:
    """
    Analizador profundo de metadatos e inspección de ESRI File Geodatabases (.gdb).
    Extrae los Feature Datasets reales desde GDB_Items y mapea cada capa a su dataset temático.
    """

    def __init__(self, gdb_path: str):
        self.gdb_path = gdb_path

    def analyze(self) -> dict:
        intermediate_model = {
            "metadata": {
                "source": self.gdb_path,
                "title": os.path.basename(self.gdb_path),
                "profile": "IMPORTED-FROM-ESRI-GDB",
                "crs": "EPSG:9377"
            },
            "datasets": [],
            "layer_to_dataset": {},
            "domains": {},
            "relationships": []
        }

        try:
            ds = ogr.Open(self.gdb_path)
            if not ds:
                return intermediate_model

            # 1. Extraer árbol de Feature Datasets desde GDB_Items
            sql = ds.ExecuteSQL("SELECT Name, Type, Path FROM GDB_Items WHERE Path IS NOT NULL")
            datasets_dict = {} # {dataset_name: [layers]}

            if sql:
                while True:
                    feat = sql.GetNextFeature()
                    if not feat: break
                    path = feat.GetField("Path")
                    name = feat.GetField("Name")
                    if not path or path == "\\": continue

                    parts = [p for p in path.strip("\\").split("\\") if p]
                    if len(parts) >= 2:
                        ds_name = parts[0]
                        layer_name = parts[-1]
                        if ds_name not in datasets_dict: datasets_dict[ds_name] = []
                        datasets_dict[ds_name].append(layer_name)
                        intermediate_model["layer_to_dataset"][layer_name] = ds_name
                    elif len(parts) == 1:
                        ds_name = parts[0]
                        if ds_name not in datasets_dict: datasets_dict[ds_name] = []

            # 2. Agregar capas huérfanas al dataset por defecto si no tienen dataset asignado
            all_layers = [ds.GetLayerByIndex(i).GetName() for i in range(ds.GetLayerCount())]
            for lyr_name in all_layers:
                if lyr_name not in intermediate_model["layer_to_dataset"]:
                    if "GENERAL" not in datasets_dict: datasets_dict["GENERAL"] = []
                    datasets_dict["GENERAL"].append(lyr_name)
                    intermediate_model["layer_to_dataset"][lyr_name] = "GENERAL"

            for ds_name, layers in datasets_dict.items():
                intermediate_model["datasets"].append({
                    "name": ds_name,
                    "title": ds_name,
                    "description": f"Feature Dataset {ds_name}",
                    "layers": layers
                })

        except Exception as e:
            print(f"Error analizando GDB: {e}")

        return intermediate_model

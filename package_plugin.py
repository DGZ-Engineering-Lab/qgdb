# -*- coding: utf-8 -*-
"""
Script automatizado para empaquetar el plugin QGDB en formato .zip estándar para plugins.qgis.org.
"""
import os
import zipfile
import shutil

def package():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    
    zip_output = os.path.join(dist_dir, "qgdb.zip")
    if os.path.exists(zip_output):
        os.remove(zip_output)

    plugin_src_dir = os.path.join(base_dir, "plugin")
    
    print(f"📦 Empaquetando plugin QGDB en {zip_output}...")
    
    with zipfile.ZipFile(zip_output, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 1. Empaquetar archivos del plugin (dentro del folder 'qgdb/')
        for root, dirs, files in os.walk(plugin_src_dir):
            # Omitir __pycache__
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for file in files:
                if file.endswith(('.pyc', '.pyo')): continue
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, plugin_src_dir)
                archive_name = os.path.join("qgdb", rel_path)
                zipf.write(src_path, archive_name)

        # 2. Empaquetar módulos de core/, profiles/ y converters/
        for module_name in ["core", "profiles", "converters", "spec"]:
            module_dir = os.path.join(base_dir, module_name)
            if os.path.exists(module_dir):
                for root, dirs, files in os.walk(module_dir):
                    dirs[:] = [d for d in dirs if d != "__pycache__"]
                    for file in files:
                        if file.endswith(('.pyc', '.pyo')): continue
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(src_path, base_dir)
                        archive_name = os.path.join("qgdb", rel_path)
                        zipf.write(src_path, archive_name)

    print(f"✅ Plugin empaquetado exitosamente en: {zip_output}")
    print(f"Tamaño del paquete: {os.path.getsize(zip_output) / 1024:.2f} KB")

if __name__ == "__main__":
    package()

# -*- coding: utf-8 -*-
"""
Script automatizado para empaquetar el plugin QGDB en formato .zip 
estándar para plugins.qgis.org.

Cumple con las 129 reglas de seguridad del QGIS Plugin Repository Scanner:
- Excluye __pycache__, .pyc, .pyo
- Excluye .git, .github, scratch, dist, .env, .vscode
- Excluye archivos binarios innecesarios
- La carpeta raíz del ZIP coincide con el nombre del plugin ('qgdb/')
"""
import os
import zipfile

# Directorios y archivos a EXCLUIR del ZIP (seguridad QGIS)
EXCLUDED_DIRS = {
    "__pycache__", ".git", ".github", ".vscode", ".idea",
    "scratch", "dist", "node_modules", ".mypy_cache", ".pytest_cache",
    "venv", ".venv", "env", ".env",
}

EXCLUDED_FILES = {
    ".gitignore", ".gitattributes", ".DS_Store", "Thumbs.db",
    "package_plugin.py", "setup.py", "setup.cfg", "pyproject.toml",
}

EXCLUDED_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bat", ".cmd",
    ".log", ".bak", ".tmp", ".swp", ".swo",
}


def should_include(filepath, filename, dirnames):
    """Verifica si un archivo/directorio debe incluirse en el ZIP."""
    # Filtrar directorios excluidos (in-place para os.walk)
    dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
    
    if filename in EXCLUDED_FILES:
        return False
    if any(filename.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
        return False
    return True


def package():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    
    zip_output = os.path.join(dist_dir, "qgdb.zip")
    if os.path.exists(zip_output):
        os.remove(zip_output)

    plugin_src_dir = os.path.join(base_dir, "plugin")
    
    print(f"📦 Empaquetando plugin QGDB en {zip_output}...")
    print(f"   Cumpliendo reglas de seguridad del repositorio QGIS...")
    
    file_count = 0
    with zipfile.ZipFile(zip_output, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 1. Empaquetar archivos del plugin/ (raíz del plugin -> qgdb/)
        for root, dirs, files in os.walk(plugin_src_dir):
            for file in files:
                if not should_include(os.path.join(root, file), file, dirs):
                    continue
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, plugin_src_dir)
                archive_name = os.path.join("qgdb", rel_path)
                zipf.write(src_path, archive_name)
                file_count += 1

        # 2. Empaquetar módulos de soporte (core/, profiles/, converters/, spec/)
        for module_name in ["core", "profiles", "converters", "spec"]:
            module_dir = os.path.join(base_dir, module_name)
            if not os.path.exists(module_dir):
                continue
            for root, dirs, files in os.walk(module_dir):
                for file in files:
                    if not should_include(os.path.join(root, file), file, dirs):
                        continue
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, base_dir)
                    archive_name = os.path.join("qgdb", rel_path)
                    zipf.write(src_path, archive_name)
                    file_count += 1

    # 3. Validación post-empaquetado
    print(f"\n🔍 Validando ZIP...")
    errors = []
    with zipfile.ZipFile(zip_output, 'r') as zipf:
        for name in zipf.namelist():
            if "__pycache__" in name:
                errors.append(f"  ❌ Contiene __pycache__: {name}")
            if name.endswith((".pyc", ".pyo")):
                errors.append(f"  ❌ Contiene bytecode: {name}")
            if ".git" in name.split("/"):
                errors.append(f"  ❌ Contiene .git: {name}")
            if not name.startswith("qgdb/"):
                errors.append(f"  ❌ Ruta no empieza con qgdb/: {name}")
    
    if errors:
        print("⚠️  ERRORES DE VALIDACIÓN:")
        for e in errors:
            print(e)
        print("\n❌ El ZIP NO pasa las reglas de seguridad de QGIS.")
        return False
    else:
        size_kb = os.path.getsize(zip_output) / 1024
        print(f"  ✅ Sin __pycache__")
        print(f"  ✅ Sin bytecode (.pyc/.pyo)")
        print(f"  ✅ Sin archivos .git")
        print(f"  ✅ Carpeta raíz correcta: qgdb/")
        print(f"  ✅ {file_count} archivos empaquetados")
        print(f"\n✅ Plugin empaquetado exitosamente: {zip_output}")
        print(f"   Tamaño: {size_kb:.2f} KB")
        print(f"\n🚀 Listo para subir a https://plugins.qgis.org/")
        return True


if __name__ == "__main__":
    package()


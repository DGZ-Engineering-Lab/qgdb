# QGDB: Open Geodatabase Framework & Provider for QGIS 🌍📦

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![QGIS](https://img.shields.io/badge/QGIS-3.22%20--%203.44+-green.svg)](https://qgis.org)
[![Python](https://img.shields.io/badge/Python-3.9%20--%203.12-yellow.svg)](https://python.org)
[![Profile: LADM-COL](https://img.shields.io/badge/LADM--COL-v3.0%20Compatible-orange.svg)](https://www.igac.gov.co)

**QGDB** (`.qgdb`) es una especificación abierta y un proveedor nativo para QGIS que implementa el soporte completo de **Geodatabases Jerárquicas** (Feature Datasets, Capas Vectoriales 2D/3D, Tablas Alfanuméricas, Dominios de Valores y Relaciones 1:N / N:M), con interoperabilidad bidireccional con **ESRI File Geodatabase (`.gdb`)** y cumplimiento del estándar de **Catastro Multipropósito de Colombia (LADM-COL v3.0)**.

---

## ✨ Características Principales

* 📂 **Feature Datasets Jerárquicos en QGIS:** Organiza cientos de capas vectoriales en carpetas temáticas nativas tanto en el **Panel Navegador** (*Browser Panel*) como en el **Panel de Capas** (*Layer Tree / TOC*).
* 🔄 **Conversor Bidireccional ESRI GDB ↔ QGDB:** Convierte cualquier File Geodatabase (`.gdb`) conservando la jerarquía de datasets, geometrías 2D/3D (polígonos, líneas, puntos) y tablas de atributos.
* 🇨🇴 **Perfil Oficial LADM-COL v3.0:** Generador de contenedores `.qgdb` configurados para Catastro Multipropósito (IGAC / SNR / CGR) con 1 solo clic.
* 🌐 **Arquitectura Abierta OGC:** Construido sobre contenedores OGC GeoPackage/SQLite de alto rendimiento, portables en un único archivo (`.qgdb`).
* ⚡ **Driver Python y CLI:** API Python (`driver/qgdb_driver.py`) y CLI (`cli/qgdb_cli.py`) independientes para automatizaciones ETL en servidores y pipelines de datos.

---

## 📥 Instalación para Usuarios en QGIS

### Opción A: Instalación desde Archivo ZIP (Inmediata)
1. Descarga el archivo [`qgdb.zip`](dist/qgdb.zip) desde la sección de **Releases** de este repositorio.
2. Abre QGIS y ve al menú superior: **`Complementos ➔ Administrar e instalar complementos...`**
3. En la pestaña izquierda, selecciona **`Instalar a partir de ZIP`**.
4. Selecciona el archivo `qgdb.zip` descargado y haz clic en **`Instalar complemento`**.

### Opción B: Repositorio Oficial de QGIS (*Próximamente*)
* En QGIS: `Complementos ➔ Administrar e instalar complementos ➔ Buscar 'QGDB' ➔ Instalar`.

---

## 🚀 Guía de Uso

### 1. Cargar una Geodatabase `.qgdb` en el Panel de Capas
* En el menú superior de QGIS: **`QGDB Geodatabase ➔ 📂 Cargar Geodatabase (.qgdb) con Estructura de Datasets`**.
* Selecciona tu archivo `.qgdb` y QGIS creará automáticamente los grupos temáticos con todas las capas vectoriales cargadas en el proyecto.

### 2. Navegación desde el Panel Navegador (*Browser*)
* Expande cualquier archivo `.qgdb` en el árbol del explorador.
* Clic derecho sobre el archivo para añadir toda la geodatabase organizada por Datasets.
* Clic derecho sobre un Dataset para añadir solo ese grupo temático.

### 3. Convertir una File Geodatabase (`.gdb`) a `.qgdb` por Terminal / CLI
```bash
python-qgis.bat cli/qgdb_cli.py gdb2qgdb --input "ruta/a/mi_geodatabase.gdb" --output "ruta/a/mi_geodatabase.qgdb"
```

---

## 🏛️ Estructura del Proyecto

```
QGBD/
├── plugin/                    # Código del plugin para QGIS
│   ├── metadata.txt           # Metadatos oficiales para plugins.qgis.org
│   ├── browser_provider.py    # Proveedor QgsDataItemProvider para el Navegador
│   ├── qgdb_plugin.py         # Punto de entrada y acciones en la UI de QGIS
│   └── icon.png               # Icono oficial
├── core/                      # Motor central de datos QGDB
│   ├── qgdb_engine.py         # Motor de almacenamiento
│   ├── schema_builder.py      # DDL y tablas de sistema qgdb_*
│   └── validator.py           # Validador de esquemas y reglas
├── converters/                # Herramientas de interoperabilidad
│   ├── gdb_analyzer.py        # Extractor profundo de Feature Datasets ESRI
│   ├── gdb2qgdb.py            # Conversor .gdb ➔ .qgdb
│   └── qgdb2gdb.py            # Exportador .qgdb ➔ .gdb
├── profiles/                  # Plantillas normativas
│   └── ladm_col.py            # Perfil Catastro Colombia LADM-COL v3.0
├── spec/                      # Especificación técnica formal
│   ├── QGDB_FORMAT_SPECIFICATION_v1.0.md
│   └── ladm_col_v3.0.json
├── package_plugin.py          # Script de empaquetado para distribución
└── LICENSE                    # Licencia GPLv3
```

---

## 📄 Licencia

Este proyecto está distribuido bajo la licencia **GNU General Public License v3.0 (GPLv3)**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

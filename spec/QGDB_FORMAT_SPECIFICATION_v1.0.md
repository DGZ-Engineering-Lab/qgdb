# QGDB (Open QGIS Geodatabase Format) - File Format Specification v1.0

## 1. Identificación y Extensión

- **Nombre:** QGIS Geodatabase Format (QGDB)
- **Extensión Oficial:** `.qgdb`
- **MIME Type:** `application/x-qgis-geodatabase`
- **Tipo de Archivo:** Contenedor geoespacial estructurado portable en un solo archivo de disco.
- **Motor de Almacenamiento Base:** SQLite3 / OGC GeoPackage Extendido (Annex M compatible).

---

## 2. Visión General

El formato `.qgdb` es un estándar de almacenamiento geoespacial **libre, portable y 100% configurable por el usuario**.

A diferencia de los archivos Shapefile (`.shp`) o GeoPackage básicos (`.gpkg`), un archivo `.qgdb` no solo almacena geometrías y atributos, sino que empaqueta todo el **modelo de información geográfica**:

1. **Jerarquía Dinámica de Datasets (Feature Datasets):** Agrupación lógica de capas creada y organizada a medida del usuario (ej: Cartografía, Catastro, Ambiental, Infraestructura).
2. **Dominios de Atributos (Coded Value & Range Domains):** Listas de valores válidos y rangos numéricos.
3. **Relaciones Inter-Capa (1:1, 1:N, N:M):** Integridad referencial entre tablas geométricas y alfanuméricas.
4. **Reglas de Validacion y Topología:** Reglas geométricas (No solaparse, estar dentro de, sin auto-intersección).
5. **Estilos y Formularios Integrados:** Simbología QML/SLD y configuración de interfaz (*ValueMap*, pestañas, visibilidad) encapsulados directamente dentro del archivo `.qgdb`.

---

## 3. Estructura Interna del Archivo `.qgdb`

Un archivo `Proyecto.qgdb` contiene internamente la siguiente arquitectura de tablas de sistema:

```
PROYECTO.qgdb (SQLite3 Container)
├── 📊 Tablas de Datos Espaciales (Feature Classes)
│     ├── Capa_A (Geometría + Atributos)
│     └── Capa_B (Geometría + Atributos)
├── 📋 Tablas Alfanuméricas Libre Configuración
├── ⚙️ Tablas de Sistema QGDB:
│     ├── qgdb_metadata            --> Versión del formato, título, CRS predeterminado
│     ├── qgdb_datasets            --> Lista dinámica de Feature Datasets creados por el usuario
│     ├── qgdb_layers              --> Asignación de capas/tablas a Datasets
│     ├── qgdb_domains             --> Definición de Dominios (Codificados / Rangos)
│     ├── qgdb_field_config        --> Asignación de Dominios, Reglas NOT NULL / UNIQUE a campos
│     ├── qgdb_relationships       --> Relaciones 1:1, 1:N, N:M con claves primarias y foráneas
│     ├── qgdb_topology_rules      --> Reglas de topología espacial (GEOS Engine)
│     ├── qgdb_styles              --> Estilos QML / SLD incrustados por capa
│     └── qgdb_forms               --> Formularios de edición autogenerados
```

---

## 4. Esquema DDL de Tablas de Sistema (`qgdb_*`)

```sql
-- Metadatos Generales del Archivo .qgdb
CREATE TABLE qgdb_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Registro de Datasets Creados por el Usuario
CREATE TABLE qgdb_datasets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    icon TEXT DEFAULT 'folder'
);

-- Registro de Capas / Feature Classes dentro de Datasets
CREATE TABLE qgdb_layers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_name TEXT REFERENCES qgdb_datasets(name),
    layer_name TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    geometry_type TEXT DEFAULT 'NONE', -- POINT, LINESTRING, POLYGON, MULTIPOLYGON, NONE
    primary_key TEXT DEFAULT 'fid'
);

-- Dominios de Atributos (Coded Value & Range)
CREATE TABLE qgdb_domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_name TEXT NOT NULL,
    code TEXT NOT NULL,
    description TEXT NOT NULL,
    UNIQUE(domain_name, code)
);

-- Configuración de Campos (Validación & Formularios)
CREATE TABLE qgdb_field_config (
    layer_name TEXT NOT NULL,
    field_name TEXT NOT NULL,
    domain_name TEXT,
    is_required INTEGER DEFAULT 0,
    is_unique INTEGER DEFAULT 0,
    default_value TEXT,
    widget_type TEXT DEFAULT 'ValueMap',
    PRIMARY KEY (layer_name, field_name)
);

-- Relaciones 1:1, 1:N, N:M
CREATE TABLE qgdb_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    parent_layer TEXT NOT NULL,
    parent_key TEXT NOT NULL,
    child_layer TEXT NOT NULL,
    child_key TEXT NOT NULL,
    cardinality TEXT DEFAULT '1:N'
);

-- Reglas Topológicas
CREATE TABLE qgdb_topology_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_type TEXT NOT NULL, -- NO_OVERLAP, MUST_BE_INSIDE, NO_SELF_INTERSECT, etc.
    layer_a TEXT NOT NULL,
    layer_b TEXT,
    severity TEXT DEFAULT 'ERROR'
);
```

---

## 5. Portabilidad Total

Cualquier archivo `.qgdb` transferido a otro equipo o sistema conserva la estructura de Datasets, formularios, dominios y simbología sin depender de proyectos `.qgz` externos.

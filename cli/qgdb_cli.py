# -*- coding: utf-8 -*-
import sys
import os
import argparse

# Agregar raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.qgdb_engine import QGDBEngine
from core.validator import QGDBValidator
from profiles.ladm_col import LADMCOLProfileBuilder
from converters.gdb2qgdb import GDB2QGDBConverter
from converters.qgdb2gdb import QGDB2GDBExporter

def main():
    parser = argparse.ArgumentParser(description="QGDB Command Line Interface (CLI)")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # Comando: create-ladm
    cmd_ladm = subparsers.add_parser("create-ladm", help="Crea un proyecto QGDB conforme a LADM-COL v3.0 (Colombia)")
    cmd_ladm.add_argument("--output", "-o", required=True, help="Ruta del archivo de salida (.qgdb / .qgpkg)")

    # Comando: gdb2qgdb
    cmd_g2q = subparsers.add_parser("gdb2qgdb", help="Convierte ESRI File Geodatabase (.gdb) a QGDB")
    cmd_g2q.add_argument("--input", "-i", required=True, help="Ruta de la GDB de origen")
    cmd_g2q.add_argument("--output", "-o", required=True, help="Ruta del archivo QGDB de salida")

    # Comando: qgdb2gdb
    cmd_q2g = subparsers.add_parser("qgdb2gdb", help="Exporta QGDB a ESRI File Geodatabase (.gdb)")
    cmd_q2g.add_argument("--input", "-i", required=True, help="Ruta del archivo QGDB de origen")
    cmd_q2g.add_argument("--output", "-o", required=True, help="Ruta de la GDB de salida")

    # Comando: validate
    cmd_val = subparsers.add_parser("validate", help="Valida un contenedor QGDB")
    cmd_val.add_argument("--input", "-i", required=True, help="Ruta del archivo QGDB")

    args = parser.parse_args()

    if args.command == "create-ladm":
        print(f"🇨🇴 Creando proyecto QGDB LADM-COL v3.0 en: {args.output}")
        LADMCOLProfileBuilder.create_ladm_col_project(args.output)
        print("✅ Proyecto creado exitosamente.")

    elif args.command == "gdb2qgdb":
        print(f"🔄 Convirtiendo ESRI GDB '{args.input}' -> QGDB '{args.output}'...")
        converter = GDB2QGDBConverter(args.input, args.output)
        if converter.convert():
            print("✅ Conversión completada exitosamente.")

    elif args.command == "qgdb2gdb":
        print(f"🔄 Exportando QGDB '{args.input}' -> ESRI GDB '{args.output}'...")
        exporter = QGDB2GDBExporter(args.input, args.output)
        if exporter.export():
            print("✅ Exportación completada exitosamente.")

    elif args.command == "validate":
        print(f"🔍 Validando archivo QGDB: {args.input}")
        engine = QGDBEngine(args.input)
        validator = QGDBValidator(engine)
        res_struct = validator.validate_structure()
        res_ladm = validator.validate_ladm_col_rules()

        print(f"Estructura Válida: {res_struct['valid']}")
        if res_struct['errors']:
            print(f"Errores: {res_struct['errors']}")
        if res_ladm['warnings']:
            print(f"Advertencias LADM-COL: {res_ladm['warnings']}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()

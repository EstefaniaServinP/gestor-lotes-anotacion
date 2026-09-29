#!/usr/bin/env python3
"""
Script para reasignar masivamente batches
"""

import os
from pymongo import MongoClient
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from db import MONGO_URI, DB_NAME  # noqa: E402  (lee MONGO_URI / MONGO_DB desde .env)

def load_team():
    """Leer los miembros actuales del equipo desde la colección segmentadores."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        return [s["name"] for s in client[DB_NAME]["segmentadores"].find({}, {"name": 1})]
    except Exception as e:
        print(f"⚠️ No se pudo leer el equipo desde MongoDB: {e}")
        return []


CURRENT_TEAM = load_team()

def unassign_all_non_members():
    """Desasignar todos los batches de NO-miembros"""

    print("🔄 DESASIGNACIÓN MASIVA DE BATCHES")
    print("=" * 70)
    print()

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        batches_col = db["batches"]

        # Encontrar todos los batches asignados a NO-miembros
        non_member_batches = list(batches_col.find({
            "assignee": {"$nin": [None, ""] + CURRENT_TEAM}
        }))

        total = len(non_member_batches)

        if total == 0:
            print("✅ No hay batches asignados a NO-miembros")
            return

        print(f"📊 Encontrados {total} batches asignados a NO-miembros")
        print()

        # Mostrar distribución
        from collections import Counter
        assignees = Counter([b["assignee"] for b in non_member_batches])

        print("Distribución:")
        for assignee, count in assignees.most_common():
            print(f"  • {assignee}: {count} batches")
        print()

        # Confirmar
        response = input(f"¿Deseas DESASIGNAR estos {total} batches? (sí/no): ")
        if response.lower() not in ['sí', 'si', 's', 'yes', 'y']:
            print("❌ Operación cancelada")
            return

        print()
        print("🔄 Desasignando batches...")

        # Actualizar todos
        result = batches_col.update_many(
            {"assignee": {"$nin": [None, ""] + CURRENT_TEAM}},
            {"$set": {"assignee": None}}
        )

        print()
        print("=" * 70)
        print(f"✅ COMPLETADO")
        print(f"  Batches desasignados: {result.modified_count}")
        print()
        print("💡 Ahora estos batches aparecerán en 'Batches No Asignados'")
        print("   Refresca el dashboard con Ctrl + Shift + R")

        client.close()

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

def reassign_all_non_members(new_assignee):
    """Reasignar todos los batches de NO-miembros a un miembro específico"""

    print("🔄 REASIGNACIÓN MASIVA DE BATCHES")
    print("=" * 70)
    print()

    if new_assignee not in CURRENT_TEAM:
        print(f"❌ ERROR: '{new_assignee}' no está en el equipo actual")
        print(f"   Equipo actual: {', '.join(CURRENT_TEAM)}")
        return

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        batches_col = db["batches"]

        # Encontrar todos los batches asignados a NO-miembros
        non_member_batches = list(batches_col.find({
            "assignee": {"$nin": [None, ""] + CURRENT_TEAM}
        }))

        total = len(non_member_batches)

        if total == 0:
            print("✅ No hay batches asignados a NO-miembros")
            return

        print(f"📊 Encontrados {total} batches asignados a NO-miembros")
        print()

        # Mostrar distribución
        from collections import Counter
        assignees = Counter([b["assignee"] for b in non_member_batches])

        print("Distribución:")
        for assignee, count in assignees.most_common():
            print(f"  • {assignee}: {count} batches")
        print()

        # Confirmar
        response = input(f"¿Deseas REASIGNAR estos {total} batches a '{new_assignee}'? (sí/no): ")
        if response.lower() not in ['sí', 'si', 's', 'yes', 'y']:
            print("❌ Operación cancelada")
            return

        print()
        print(f"🔄 Reasignando batches a '{new_assignee}'...")

        # Actualizar todos
        result = batches_col.update_many(
            {"assignee": {"$nin": [None, ""] + CURRENT_TEAM}},
            {"$set": {"assignee": new_assignee}}
        )

        print()
        print("=" * 70)
        print(f"✅ COMPLETADO")
        print(f"  Batches reasignados: {result.modified_count}")
        print(f"  Nuevo responsable: {new_assignee}")
        print()
        print(f"💡 Ahora estos batches aparecerán en la tarjeta de '{new_assignee}'")
        print("   Refresca el dashboard con Ctrl + Shift + R")

        client.close()

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

def show_help():
    """Mostrar ayuda"""
    print("USO:")
    print()
    print("  Desasignar todos los batches de NO-miembros:")
    print("  ----------------------------------------------")
    print("  python scripts/mass_reassign.py --unassign-all")
    print()
    print("  Reasignar todos a un miembro específico:")
    print("  ----------------------------------------------")
    print("  python scripts/mass_reassign.py --reassign-to <nombre>")
    print()
    print("EJEMPLOS:")
    print()
    print("  python scripts/mass_reassign.py --unassign-all")
    print("  python scripts/mass_reassign.py --reassign-to 'Segmentador 1'")
    print("  python scripts/mass_reassign.py --reassign-to 'Segmentador 2'")
    print()
    print("EQUIPO ACTUAL:")
    for member in CURRENT_TEAM:
        print(f"  • {member}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    if not CURRENT_TEAM:
        print("❌ ERROR: No hay segmentadores registrados; se cancela para no desasignar todos los batches")
        sys.exit(1)

    command = sys.argv[1]

    if command == "--unassign-all":
        unassign_all_non_members()
    elif command == "--reassign-to":
        if len(sys.argv) < 3:
            print("❌ ERROR: Falta el nombre del nuevo responsable")
            print()
            show_help()
            sys.exit(1)
        new_assignee = sys.argv[2]
        reassign_all_non_members(new_assignee)
    else:
        print(f"❌ ERROR: Comando desconocido: {command}")
        print()
        show_help()
        sys.exit(1)

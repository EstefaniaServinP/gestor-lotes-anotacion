"""
Script para inicializar la base de datos principal con todas sus colecciones e índices.
Ejecutar una vez antes de arrancar la aplicación por primera vez.

Uso:
    python scripts/init_db.py
"""

import os
import sys
from datetime import datetime
from pymongo import MongoClient, ASCENDING

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from db import MONGO_URI, DB_NAME  # noqa: E402  (lee MONGO_URI / MONGO_DB desde .env)

def init():
    print(f"Conectando a {MONGO_URI} ...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print(f"✅ Conexión OK")

    db = client[DB_NAME]
    print(f"📂 Base de datos: {DB_NAME}")

    # ------------------------------------------------------------------ batches
    batches = db["batches"]
    batches.create_index([("id", ASCENDING)], unique=True, background=True)
    batches.create_index([("assignee", ASCENDING)], background=True)
    batches.create_index([("status", ASCENDING)], background=True)
    batches.create_index([("metadata.assigned_at", ASCENDING)], background=True)
    batches.create_index([("assignee", ASCENDING), ("status", ASCENDING)], background=True)
    batches.create_index([("status", ASCENDING), ("metadata.assigned_at", ASCENDING)], background=True)
    print("  ✅ batches — 6 índices creados")

    # ---------------------------------------------------------------- masks.files
    masks = db["masks.files"]
    masks.create_index([("filename", ASCENDING)], background=True)
    masks.create_index([("uploadDate", ASCENDING)], background=True)
    masks.create_index([("metadata.uploaded_by", ASCENDING)], background=True)
    print("  ✅ masks.files — 3 índices creados")

    # ------------------------------------------------------------ segmentadores
    segmentadores = db["segmentadores"]
    segmentadores.create_index([("name", ASCENDING)], unique=True, background=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    admin_name = os.environ.get("ADMIN_NAME", "Administrador")

    if segmentadores.count_documents({}) == 0:
        default_team = [f"Segmentador {i}" for i in range(1, 6)]
        segmentadores.insert_many(
            [{"name": admin_name, "role": "admin", "email": "", "created_at": now}]
            + [{"name": n, "role": "segmentador", "email": "", "created_at": now} for n in default_team]
        )
        print(f"  ✅ segmentadores — equipo inicial insertado: {admin_name} (admin) + {default_team}")
    else:
        print(f"  ✅ segmentadores — {segmentadores.count_documents({})} registros existentes")

    # El equipo siempre debe tener al menos un administrador
    if segmentadores.count_documents({"role": "admin"}) == 0:
        segmentadores.update_one(
            {"name": admin_name},
            {"$set": {"role": "admin"}, "$setOnInsert": {"email": "", "created_at": now}},
            upsert=True,
        )
        print(f"  ✅ segmentadores — sin administradores: '{admin_name}' creado como admin")

    # --------------------------------------------------- Reporte_avances_masks
    reporte = db["Reporte_avances_masks"]
    reporte.create_index([("batch_id", ASCENDING)], background=True)
    reporte.create_index([("segmentador", ASCENDING)], background=True)
    reporte.create_index([("fecha", ASCENDING)], background=True)
    reporte.create_index([("segmentador", ASCENDING), ("fecha", ASCENDING)], background=True)
    print("  ✅ Reporte_avances_masks — 4 índices creados")

    # -------------------------------------------------------- resumen final
    colecciones = db.list_collection_names()
    print(f"\n✅ {DB_NAME} inicializada correctamente")
    print(f"   Colecciones: {sorted(colecciones)}")
    client.close()

if __name__ == "__main__":
    init()

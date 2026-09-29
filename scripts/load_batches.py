#!/usr/bin/env python3
"""
Script para cargar batches desde un archivo JSON a MongoDB.

Uso:
    python scripts/load_batches.py                      # usa data/batches_ejemplo.json
    python scripts/load_batches.py ruta/a/lotes.json
"""

import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)
from db import get_db, DB_NAME  # noqa: E402  (lee MONGO_URI / MONGO_DB desde .env)

json_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "batches_ejemplo.json")

print("=" * 70)
print(f"  CARGANDO BATCHES DESDE {os.path.basename(json_path)} A MONGODB ({DB_NAME})")
print("=" * 70)

# Conectar a MongoDB
try:
    db = get_db(raise_on_fail=True)
    print("✅ Conexión exitosa a MongoDB")
except ConnectionError as e:
    print(f"❌ Error conectando a MongoDB: {e}")
    sys.exit(1)

batches_col = db["batches"]

# Leer el archivo JSON
try:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        batches = data.get("batches", [])

    print(f"✅ Leídos {len(batches)} batches desde {json_path}")
except Exception as e:
    print(f"❌ Error leyendo {json_path}: {e}")
    sys.exit(1)

# Verificar si ya hay batches en la base de datos
existing_count = batches_col.count_documents({})
if existing_count > 0:
    print(f"\n⚠️  Ya existen {existing_count} batches en MongoDB")
    response = input("¿Deseas eliminarlos y recargar todos? (s/n): ")
    if response.lower() == 's':
        result = batches_col.delete_many({})
        print(f"🗑️  {result.deleted_count} batches eliminados")
    else:
        print("ℹ️  Saltando carga (batches existentes no modificados)")
        sys.exit(0)

# Insertar batches
if not batches:
    print(f"❌ No se encontraron batches en {json_path}")
    sys.exit(1)

try:
    result = batches_col.insert_many(batches)
    print(f"✅ {len(result.inserted_ids)} batches insertados exitosamente")

    # Mostrar algunos ejemplos
    samples = list(batches_col.find({}, {"id": 1, "assignee": 1, "status": 1}).limit(5))
    print("\nℹ️  Ejemplos de batches insertados:")
    for i, batch in enumerate(samples, 1):
        batch_id = batch.get("id", "N/A")
        assignee = batch.get("assignee") or "Sin asignar"
        status = batch.get("status", "N/A")
        print(f"   {i}. {batch_id} - Asignado a: {assignee} - Estado: {status}")

    print("\n" + "=" * 70)
    print("✅ CARGA COMPLETADA EXITOSAMENTE")
    print("=" * 70)
except Exception as e:
    print(f"❌ Error insertando batches: {e}")
    sys.exit(1)

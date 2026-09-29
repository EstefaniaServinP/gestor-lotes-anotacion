#!/usr/bin/env python3
"""
Script para sincronizar las máscaras (masks.files) con los batches
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from db import get_db, get_training_db  # noqa: E402
import re

def main():
    print("=" * 70)
    print("🔄 SINCRONIZACIÓN DE MÁSCARAS CON BATCHES")
    print("=" * 70)

    # Conectar a bases de datos
    print("\n📡 Conectando a MongoDB...")
    db = get_db(raise_on_fail=True)
    batches_col = db["batches"]

    training_db = get_training_db()
    if training_db is None:
        print("❌ No se pudo conectar a la BD de máscaras")
        return

    masks_col = training_db["masks.files"]

    # Obtener todas las máscaras
    print("\n📊 Obteniendo máscaras de masks.files...")
    all_masks = list(masks_col.find({}, {"filename": 1, "uploadDate": 1, "_id": 0}))
    print(f"✅ {len(all_masks)} máscaras encontradas")

    # Extraer batch IDs de los nombres de archivos
    batch_mask_map = {}

    for mask in all_masks:
        filename = mask.get("filename", "")

        # Patrones:
        # masks_batch_000040F.tar.xz -> batch_000040F
        # masks_batch_T000044.tar.xz -> batch_T000044

        # Patrón 1: batch_XXXXXF
        match_f = re.search(r'batch_(\d+F)', filename, re.IGNORECASE)
        if match_f:
            batch_id = f"batch_{match_f.group(1)}"
            if batch_id not in batch_mask_map:
                batch_mask_map[batch_id] = []
            batch_mask_map[batch_id].append(mask)
            continue

        # Patrón 2: batch_TXXXXXX
        match_t = re.search(r'batch_(T\d+)', filename, re.IGNORECASE)
        if match_t:
            batch_id = f"batch_{match_t.group(1)}"
            if batch_id not in batch_mask_map:
                batch_mask_map[batch_id] = []
            batch_mask_map[batch_id].append(mask)
            continue

    print(f"\n📋 Batches con máscaras encontrados: {len(batch_mask_map)}")

    # Mostrar algunos ejemplos
    print("\nEjemplos de batches con máscaras:")
    for i, (batch_id, masks) in enumerate(list(batch_mask_map.items())[:10]):
        print(f"  - {batch_id}: {len(masks)} archivo(s)")

    # Actualizar batches en la base de datos
    print(f"\n🔄 Actualizando {len(batch_mask_map)} batches...")

    updated_count = 0
    not_found_count = 0
    already_updated_count = 0

    for batch_id, masks in batch_mask_map.items():
        # Verificar si el batch existe
        batch = batches_col.find_one({"id": batch_id})

        if not batch:
            not_found_count += 1
            print(f"  ⚠️  Batch {batch_id} no encontrado en la base de datos")
            continue

        # Verificar si ya está marcado como subido
        if batch.get("mongo_uploaded", False):
            already_updated_count += 1
            continue

        # Obtener información del último archivo subido
        latest_mask = max(masks, key=lambda x: x.get("uploadDate", ""))

        # Actualizar batch
        batches_col.update_one(
            {"id": batch_id},
            {
                "$set": {
                    "mongo_uploaded": True,
                    "file_info": {
                        "file_count": len(masks),
                        "last_file_upload": latest_mask.get("uploadDate"),
                        "has_files": True
                    }
                }
            }
        )
        updated_count += 1

    print(f"\n✅ Actualización completada:")
    print(f"   • Batches actualizados: {updated_count}")
    print(f"   • Ya estaban actualizados: {already_updated_count}")
    print(f"   • No encontrados en DB: {not_found_count}")

    # Verificar resultado final
    total_uploaded = batches_col.count_documents({"mongo_uploaded": True})
    total_batches = batches_col.count_documents({})

    print(f"\n📊 Estado final:")
    print(f"   • Total de batches: {total_batches}")
    print(f"   • Batches con máscaras: {total_uploaded}")
    print(f"   • Batches sin máscaras: {total_batches - total_uploaded}")

    # Mostrar algunos ejemplos de batches actualizados
    print(f"\n📋 Ejemplos de batches con mongo_uploaded=True:")
    for batch in batches_col.find({"mongo_uploaded": True}, {"id": 1, "file_info": 1, "_id": 0}).limit(10):
        file_count = batch.get("file_info", {}).get("file_count", 0)
        print(f"   - {batch['id']}: {file_count} archivo(s)")

    print("\n" + "=" * 70)
    print("✅ SINCRONIZACIÓN COMPLETADA")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

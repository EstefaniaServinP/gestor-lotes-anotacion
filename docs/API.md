# API

Referencia completa de las rutas `/api` de [`app.py`](../app.py). Todas reciben y devuelven JSON, salvo las exportaciones (CSV, Excel o archivo JSON descargable).

El resumen con las rutas principales está en el [README](../README.md#api).

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/batches` | Lista los lotes (paginado: `page`, `per_page`) |
| `POST` | `/api/batches` | Crea un lote |
| `PUT` | `/api/batches/<id>` | Actualiza un lote (responsable, estado, especificación, metadatos…) |
| `PUT` | `/api/batches/<id>/change-id` | Cambia el ID de un lote |
| `DELETE` | `/api/batches/<id>` | Elimina un lote |
| `POST` | `/api/batches/quick-create` | Crea varios lotes a partir de una lista de IDs pegada como texto |
| `POST` | `/api/init-batches` | Carga los datos de ejemplo si la colección está vacía (`force: true` para recargar) |
| `POST` | `/api/reset-batches` | Borra los lotes y recarga los datos de ejemplo |
| `GET` | `/api/missing-batches` | Lotes del catálogo de ejemplo que aún no están en la BD |
| `POST` | `/api/data/batches/upload` | Carga lotes desde un JSON (`mode`: `add` o `replace`) |
| `POST` | `/api/data/batches/delete-by-filter` | Elimina lotes por filtros |
| `GET` | `/api/data/batches/export` | Exporta todos los lotes en JSON |
| `GET` | `/api/data/batches/stats` | Estadísticas de la colección de lotes |
| `GET` | `/api/segmentadores` | Lista el equipo |
| `POST` | `/api/add-segmentador` | Agrega un integrante |
| `PUT` | `/api/update-segmentador` | Edita un integrante |
| `DELETE` | `/api/remove-segmentador` | Elimina un integrante |
| `POST` | `/api/validate-admin-password` | Valida la contraseña de administrador |
| `GET` | `/api/check-mongo-files` | Lista las máscaras encontradas en MongoDB |
| `GET` | `/api/batch-files/<id>` | Máscaras asociadas a un lote |
| `POST` | `/api/sync-batch-files` | Sincroniza `mongo_uploaded` con las máscaras existentes |
| `POST` | `/api/auto-create-batches` | Crea lotes a partir de las máscaras encontradas |
| `GET` | `/api/metrics/overview` | Métricas generales |
| `GET` | `/api/metrics/team` | Métricas por integrante |
| `GET` | `/api/metrics/progress` | Avance en el tiempo |
| `GET` | `/api/metrics/export` | Exporta métricas en CSV |
| `GET` | `/api/batch-assignment/metrics` | Métricas de asignación |
| `POST` | `/api/export/batches` | Reporte de lotes en Excel o CSV |
| `GET` | `/api/export/segmentador/<nombre>` | CSV con los lotes de un integrante |
| `GET` | `/api/export/all-assignments` | CSV con el resumen de asignaciones |
| `GET` | `/api/backup/database` | Respaldo completo (lotes y equipo) en JSON |

## Parámetros y respuestas frecuentes

- **`GET /api/batches`**: `page` (por defecto 1) y `per_page` (por defecto 50, entre 5 y 1000). Devuelve `batches` y `pagination` (`page`, `per_page`, `total`, `total_pages`).
- **`POST /api/batches/quick-create`**: cuerpo `{"batch_list": "id1\nid2, id3"}`; acepta IDs separados por saltos de línea, comas o espacios. Devuelve `created` y `skipped`.
- **`POST /api/data/batches/upload`**: cuerpo con la misma estructura que [`data/batches_ejemplo.json`](../data/batches_ejemplo.json) (`mode` y `batches`). Con `mode: "replace"` se guarda un respaldo antes de borrar.
- **`POST /api/add-segmentador`** y **`PUT /api/update-segmentador`**: dar el rol `admin` requiere `admin_password`. No se puede eliminar ni quitar el rol al último administrador (409).
- **`GET /api/segmentadores`**: responde 503 con un mensaje si no hay conexión a la base de datos.
- **`POST /api/export/batches`**: cuerpo `{"format": "excel" | "csv", "batch_ids": [...]}`; sin `batch_ids` exporta todos los lotes.

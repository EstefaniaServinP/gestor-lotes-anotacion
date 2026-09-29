"""Pruebas de la API de lotes con el cliente de prueba de Flask."""

import json
import os

EJEMPLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "batches_ejemplo.json")


def _all_batches(client):
    res = client.get("/api/batches?per_page=1000")
    assert res.status_code == 200
    return res.get_json()["batches"]


# ---------------------------------------------------------------- páginas

def test_paginas_principales(client):
    for ruta in ["/", "/team", "/dashboard", "/assign", "/metrics", "/data-management"]:
        assert client.get(ruta).status_code == 200, ruta


# ---------------------------------------------------------- datos de ejemplo

def test_init_batches_carga_datos_de_ejemplo(client):
    with open(EJEMPLO, encoding="utf-8") as f:
        esperados = json.load(f)["batches"]

    res = client.post("/api/init-batches", json={"force": True})
    data = res.get_json()
    assert data["success"] is True
    assert data["loaded_count"] == len(esperados)

    batches = {b["id"]: b for b in _all_batches(client)}
    assert set(batches) == {b["id"] for b in esperados}
    # La especificación del lote se conserva
    for b in esperados:
        assert batches[b["id"]]["specification"] == b["specification"]


def test_init_batches_no_duplica(client):
    client.post("/api/init-batches", json={"force": True})
    res = client.post("/api/init-batches", json={})
    assert res.get_json()["loaded"] is False


def test_missing_batches(client):
    client.post("/api/batches", json={"id": "p1_cam1_cam2_000001"})
    data = client.get("/api/missing-batches").get_json()
    assert data["success"] is True
    assert "p1_cam1_cam2_000001" not in data["missing_batches"]
    assert data["total_missing"] == 4


# ---------------------------------------------------------------- CRUD

def test_crud_de_un_lote(client):
    nuevo = {
        "id": "batch_prueba_001",
        "assignee": "Segmentador 1",
        "specification": "Pieza de prueba (defecto_a OK, defecto_b NOK)",
        "metadata": {"due_date": "2025-12-31", "priority": "alta"},
    }
    res = client.post("/api/batches", json=nuevo)
    assert res.status_code == 200
    creado = res.get_json()["batch"]
    assert creado["status"] == "NS"
    assert creado["specification"] == nuevo["specification"]

    res = client.put("/api/batches/batch_prueba_001", json={"status": "In", "metadata": {"priority": "media"}})
    assert res.get_json()["success"] is True
    lote = _all_batches(client)[0]
    assert lote["status"] == "In"
    assert lote["metadata"]["priority"] == "media"
    assert lote["metadata"]["due_date"] == "2025-12-31"

    res = client.put("/api/batches/batch_prueba_001/change-id", json={"new_id": "batch_prueba_002"})
    assert res.get_json()["success"] is True

    res = client.delete("/api/batches/batch_prueba_002")
    assert res.status_code == 200
    assert _all_batches(client) == []


def test_eliminar_lote_inexistente(client):
    res = client.delete("/api/batches/no_existe")
    assert res.status_code == 404


def test_desasignar_lote(client):
    client.post("/api/batches", json={"id": "batch_a", "assignee": "Segmentador 2"})
    client.put("/api/batches/batch_a", json={"assignee": ""})
    assert _all_batches(client)[0]["assignee"] is None


# ------------------------------------------------------- carga masiva

def test_quick_create(client):
    client.post("/api/batches", json={"id": "batch_TEST001"})
    res = client.post("/api/batches/quick-create",
                      json={"batch_list": "batch_TEST001\nbatch_TEST002, batch_TEST003"})
    data = res.get_json()
    assert data["success"] is True
    assert data["created"] == ["batch_TEST002", "batch_TEST003"]
    assert data["skipped"] == ["batch_TEST001"]


def test_quick_create_lista_vacia(client):
    res = client.post("/api/batches/quick-create", json={"batch_list": "   "})
    assert res.status_code == 400


def test_upload_json_conserva_especificacion(client, upload_payload):
    res = client.post("/api/data/batches/upload", json=upload_payload)
    data = res.get_json()
    assert data["success"] is True
    assert data["inserted_count"] == len(upload_payload["batches"])
    for b in _all_batches(client):
        assert b["specification"]


# ------------------------------------------------ métricas y exportación

def test_metricas_y_respaldo(client):
    client.post("/api/init-batches", json={"force": True})

    overview = client.get("/api/metrics/overview")
    assert overview.status_code == 200

    stats = client.get("/api/data/batches/stats")
    assert stats.status_code == 200

    backup = client.get("/api/backup/database")
    assert backup.status_code == 200
    data = json.loads(backup.data)
    assert data["statistics"]["total_batches"] == 5
    assert data["statistics"]["batches_by_status"] == {"NS": 3, "In": 1, "S": 1}


def test_exportar_reporte_excel(client):
    client.post("/api/init-batches", json={"force": True})
    res = client.post("/api/export/batches", json={"format": "excel"})
    assert res.status_code == 200
    assert res.data[:2] == b"PK"  # los .xlsx son archivos zip


# ------------------------------------------------------------ admin

def test_validar_contrasena_admin(client):
    ok = client.post("/api/validate-admin-password", json={"password": "contraseña-de-prueba"})
    assert ok.status_code == 200
    mal = client.post("/api/validate-admin-password", json={"password": "otra"})
    assert mal.status_code == 401


def test_crear_admin_requiere_contrasena(client):
    res = client.post("/api/add-segmentador", json={"name": "Admin Prueba", "role": "admin"})
    assert res.status_code == 403


# ------------------------------------------- siempre hay un administrador

def _miembros(client):
    return {m["name"]: m["role"] for m in client.get("/api/segmentadores").get_json()["members"]}


def test_al_iniciar_existe_un_administrador(client, app_module):
    assert _miembros(client).get(app_module.ADMIN_NAME) == "admin"


def test_se_crea_admin_si_el_equipo_no_tiene(client, app_module):
    col = app_module.quality_segmentadores_col
    col.delete_many({})
    col.insert_one({"name": "Segmentador 1", "role": "segmentador"})

    app_module.init_db()

    assert _miembros(client) == {"Segmentador 1": "segmentador", app_module.ADMIN_NAME: "admin"}


def test_no_se_puede_eliminar_al_unico_admin(client, app_module):
    res = client.delete("/api/remove-segmentador", json={"name": app_module.ADMIN_NAME})
    assert res.status_code == 409
    assert _miembros(client)[app_module.ADMIN_NAME] == "admin"


def test_no_se_puede_degradar_al_unico_admin(client, app_module):
    res = client.put("/api/update-segmentador", json={
        "old_name": app_module.ADMIN_NAME, "name": app_module.ADMIN_NAME, "role": "segmentador"})
    assert res.status_code == 409
    assert _miembros(client)[app_module.ADMIN_NAME] == "admin"


def test_se_puede_eliminar_un_admin_si_queda_otro(client, app_module):
    res = client.post("/api/add-segmentador", json={
        "name": "Admin 2", "role": "admin", "admin_password": "contraseña-de-prueba"})
    assert res.status_code == 200

    res = client.delete("/api/remove-segmentador", json={"name": app_module.ADMIN_NAME})
    assert res.status_code == 200
    assert _miembros(client).get("Admin 2") == "admin"

    # Restaurar el estado para las demás pruebas
    app_module.quality_segmentadores_col.delete_one({"name": "Admin 2"})
    app_module.init_db()


# ------------------------------------ promover a admin requiere contraseña

def _promover(client, password=None):
    payload = {"old_name": "Promovible", "name": "Promovible", "role": "admin"}
    if password is not None:
        payload["admin_password"] = password
    return client.put("/api/update-segmentador", json=payload)


def test_promover_a_admin_requiere_contrasena(client):
    client.post("/api/add-segmentador", json={"name": "Promovible", "role": "segmentador"})
    try:
        assert _promover(client).status_code == 403
        assert _promover(client, "incorrecta").status_code == 403
        assert _miembros(client)["Promovible"] == "segmentador"

        assert _promover(client, "contraseña-de-prueba").status_code == 200
        assert _miembros(client)["Promovible"] == "admin"
    finally:
        client.delete("/api/remove-segmentador", json={"name": "Promovible"})


def test_editar_a_un_admin_no_pide_contrasena(client, app_module):
    res = client.put("/api/update-segmentador", json={
        "old_name": app_module.ADMIN_NAME, "name": app_module.ADMIN_NAME,
        "role": "admin", "email": "admin@ejemplo.com"})
    assert res.status_code == 200


# ------------------------------------------------- sin conexión a la BD

def test_segmentadores_sin_bd_muestra_mensaje(client, app_module, monkeypatch):
    import db
    col = app_module.quality_segmentadores_col
    monkeypatch.setattr(app_module, "quality_segmentadores_col", None)
    monkeypatch.setattr(db, "get_quality_db", lambda: None)

    res = client.get("/api/segmentadores")
    assert res.status_code == 503
    data = res.get_json()
    assert data["success"] is False
    assert data["db_connected"] is False
    assert "Sin conexión a la base de datos" in data["error"]

    # La pantalla de equipo tiene dónde mostrar el aviso
    assert b'id="dbStatusAlert"' in client.get("/team").data

    monkeypatch.setattr(app_module, "quality_segmentadores_col", col)


def test_al_reconectar_se_crea_el_admin(client, app_module, monkeypatch):
    col = app_module.quality_segmentadores_col
    col.delete_many({})
    monkeypatch.setattr(app_module, "quality_segmentadores_col", None)

    # La BD vuelve a estar disponible: la siguiente consulta reconecta y crea al admin
    res = client.get("/api/segmentadores")
    assert res.status_code == 200
    assert {m["name"]: m["role"] for m in res.get_json()["members"]} == {app_module.ADMIN_NAME: "admin"}

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_and_get_notebook(client):
    r = client.post("/notebooks", json={"name": "Physique Quantique", "description": "Cours S3"})
    assert r.status_code == 201
    notebook = r.json()
    assert notebook["name"] == "Physique Quantique"
    assert notebook["document_count"] == 0

    r = client.get(f"/notebooks/{notebook['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == notebook["id"]


def test_get_unknown_notebook_returns_404(client):
    r = client.get("/notebooks/does-not-exist")
    assert r.status_code == 404


def test_upload_unsupported_extension_returns_400(client):
    r = client.post("/notebooks", json={"name": "Test", "description": ""})
    notebook_id = r.json()["id"]

    files = {"file": ("virus.exe", b"binaire", "application/octet-stream")}
    r = client.post(f"/notebooks/{notebook_id}/documents", files=files)
    assert r.status_code == 400


def test_chat_history_empty_for_new_notebook(client):
    r = client.post("/notebooks", json={"name": "Test", "description": ""})
    notebook_id = r.json()["id"]

    r = client.get(f"/notebooks/{notebook_id}/chat")
    assert r.status_code == 200
    assert r.json() == []


def test_delete_notebook_removes_it(client):
    r = client.post("/notebooks", json={"name": "A supprimer", "description": ""})
    notebook_id = r.json()["id"]

    r = client.delete(f"/notebooks/{notebook_id}")
    assert r.status_code == 204

    r = client.get(f"/notebooks/{notebook_id}")
    assert r.status_code == 404

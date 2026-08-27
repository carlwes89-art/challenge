from fastapi.testclient import TestClient

from app.main import app


def test_stats_overview_empty(monkeypatch=None):
    with TestClient(app) as client:
        r = client.get("/stats/overview")
        assert r.status_code == 200
        data = r.json()
        assert "notebooks_count" in data
        assert "active_provider" in data


def test_query_gets_logged_and_reflected_in_stats():
    with TestClient(app) as client:
        r = client.post("/notebooks", json={"name": "Stats Notebook", "description": ""})
        notebook_id = r.json()["id"]

        # Notebook sans documents -> le pipeline répond "aucune source trouvée"
        # sans jamais appeler le LLM, mais la requête doit quand même être tracée.
        r = client.post(f"/notebooks/{notebook_id}/chat", json={"question": "Une question ?"})
        assert r.status_code == 200
        assert r.json()["sources"] == []

        r = client.get("/stats/queries", params={"limit": 10})
        assert r.status_code == 200
        logs = r.json()
        assert any(log["notebook_id"] == notebook_id for log in logs)

        r = client.get("/stats/notebooks")
        assert r.status_code == 200
        nb_stats = next(n for n in r.json() if n["id"] == notebook_id)
        assert nb_stats["query_count"] == 1

        r = client.get("/stats/providers")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


def test_compare_endpoint_returns_results_list():
    with TestClient(app) as client:
        r = client.post("/notebooks", json={"name": "Compare Notebook", "description": ""})
        notebook_id = r.json()["id"]

        r = client.post(f"/notebooks/{notebook_id}/chat/compare", json={"question": "Test ?"})
        assert r.status_code == 200
        results = r.json()["results"]
        assert len(results) >= 1
        assert results[0]["provider"] == "ollama"  # toujours présent par défaut

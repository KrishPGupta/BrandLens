import pytest
from fastapi.testclient import TestClient
from src.config import load_config, resolve
from api.main import app

pytestmark = pytest.mark.skipif(not resolve(load_config(), "db").exists(), reason="run the pipeline first")
c = TestClient(app)


def test_health_and_brands():
    assert c.get("/api/health").json()["status"] == "ok"
    assert "Nova" in c.get("/api/brands").json()["brands"]


def test_nova_trend_has_flags():
    weeks = c.get("/api/brands/Nova/trend").json()["weeks"]
    assert len(weeks) == 26 and any(w["flag"] for w in weeks)


def test_case_insensitive_and_unknown_brand():
    assert c.get("/api/brands/nova/overview").status_code == 200
    assert c.get("/api/brands/Nope/overview").status_code == 404


def test_predict():
    r = c.post("/api/predict", json={"texts": ["Nova is amazing honestly", "Pulse support was terrible today"]})
    labels = [x["label"] for x in r.json()["results"]]
    assert labels == ["positive", "negative"]


def test_bot_filtering_removes_posts():
    assert c.get("/api/brands/Nova/bot-filtering").json()["removed_pct"] > 5

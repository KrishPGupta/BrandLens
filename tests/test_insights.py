import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.config import load_config, resolve
from src.insights import summarize
from src.insights.facts import build_facts

pytestmark = pytest.mark.skipif(not resolve(load_config(), "db").exists(), reason="run the pipeline first")


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(summarize, "_ollama_ready", lambda icfg: False)
    summarize._cache.clear()


def test_facts_for_nova_match_the_drift():
    f = build_facts("Nova")
    assert f["drift"]["first_sustained_alert"] == "2025-04-21"
    assert f["drift"]["weeks_flagged"] >= 5
    assert f["drift"]["recent"]["negative"] > f["drift"]["baseline"]["negative"] + 10
    assert f["bots"]["window"]["negative_after_filtering"] > f["bots"]["window"]["negative_before_filtering"]


@pytest.mark.parametrize("focus", ["overview", "drift", "bots", "models"])
def test_template_has_every_field(focus):
    s = summarize.template_summary(build_facts("Nova"), focus)
    assert s["headline"] and s["summary"] and s["key_points"] and s["next_steps"]


def test_endpoint_falls_back_without_key():
    from api.insights import router
    app = FastAPI(); app.include_router(router)
    r = TestClient(app).get("/api/brands/nova/summary?focus=drift")
    j = r.json()
    assert r.status_code == 200 and j["source"] == "template" and j["note"] and j["facts"]["brand"] == "Nova"
    assert TestClient(app).get("/api/brands/Nope/summary").status_code == 404


def test_llm_output_is_parsed_and_failures_fall_back(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    f = build_facts("Nova")
    ok = summarize.template_summary(f, "overview")
    monkeypatch.setattr(summarize, "_llm", lambda *a, **k: ok)
    assert summarize.get_summary(f, "overview")["source"] == "llm"

    summarize._cache.clear()
    def boom(*a, **k):
        raise RuntimeError("network down")
    monkeypatch.setattr(summarize, "_llm", boom)
    out = summarize.get_summary(f, "overview")
    assert out["source"] == "template" and "RuntimeError" in out["note"]
    assert not summarize._cache          # a failed AI call must not be cached


def test_parser_handles_code_fences_and_rejects_junk():
    good = '```json\n{"headline":"h","summary":"s","key_points":["a"],"watch_outs":["w"],"next_steps":["n"]}\n```'
    assert summarize._parse(good)["headline"] == "h"
    with pytest.raises(Exception):
        summarize._parse("I cannot help with that")


_REAL_OLLAMA_READY = summarize._ollama_ready


def test_provider_order_and_explicit_choice(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    assert summarize._provider({"insights": {}}) == "anthropic"
    monkeypatch.setattr(summarize, "_ollama_ready", lambda icfg: True)
    assert summarize._provider({"insights": {}}) == "ollama"
    assert summarize._provider({"insights": {"provider": "anthropic"}}) == "anthropic"
    monkeypatch.setattr(summarize, "_ollama_ready", lambda icfg: False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    assert summarize._provider({"insights": {}}) is None
    assert summarize._provider({"insights": {"provider": "ollama"}}) is None


def test_ollama_path_end_to_end_with_a_fake_local_server(monkeypatch):
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    seen = {}
    good = summarize.template_summary(build_facts("Nova"), "overview")      # a faithful rewrite of the draft

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, obj):
            body = json.dumps(obj).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            self._send({"models": [{"name": "llama3.2:3b"}]})

        def do_POST(self):
            seen["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self._send({"message": {"role": "assistant", "content": json.dumps(good)}})

    srv = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        monkeypatch.setattr(summarize, "_ollama_ready", _REAL_OLLAMA_READY)
        cfg = load_config()
        cfg["insights"] = {"provider": "auto", "ollama_model": "llama3.2:3b", "ollama_url": f"http://127.0.0.1:{srv.server_port}"}
        out = summarize.get_summary(build_facts("Nova"), "overview", cfg)
        assert out["source"] == "llm" and out["provider"] == "ollama" and out["model"] == "llama3.2:3b"
        assert seen["body"]["stream"] is False and seen["body"]["format"]["required"][0] == "headline"
        assert "VERIFIED DRAFT" in seen["body"]["messages"][1]["content"]
        assert seen["body"]["options"]["num_ctx"] >= 4096
    finally:
        srv.shutdown()


@pytest.mark.parametrize("brand", ["Nova", "Pulse", "Zenith"])
@pytest.mark.parametrize("focus", ["overview", "drift", "bots", "models"])
def test_rule_based_text_passes_its_own_grounding_check(brand, focus):
    f = build_facts(brand)
    summarize.check_grounded(summarize.template_summary(f, focus), f)


def test_invented_numbers_are_caught_and_fall_back(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    f = build_facts("Nova")
    fake = {"headline": "Nova sentiment crashed", "summary": "Negative posts reached 87.3% last week.",
            "key_points": ["a"], "watch_outs": [], "next_steps": ["n"]}
    with pytest.raises(summarize.Ungrounded):
        summarize.check_grounded(fake, f)
    monkeypatch.setattr(summarize, "_llm", lambda *a, **k: fake)
    out = summarize.get_summary(f, "overview")
    assert out["source"] == "template" and "87.3" in out["note"] and not summarize._cache


def test_error_note_includes_the_http_code(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")

    class QuotaError(Exception):
        code = 429

    def boom(*a, **k):
        raise QuotaError("quota")
    monkeypatch.setattr(summarize, "_llm", boom)
    out = summarize.get_summary(build_facts("Nova"), "overview")
    assert out["source"] == "template" and "QuotaError 429" in out["note"]


def test_vague_ai_text_is_rejected(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    f = build_facts("Nova")
    vague = {"headline": "Nova Sentiment Dashboard: Changes and Insights",
             "summary": "Nova's sentiment has shown a slight decrease, with a strong negative signal in the last week.",
             "key_points": ["Bots have been a significant factor."], "watch_outs": [], "next_steps": ["Evaluate further."]}
    draft = summarize.template_summary(f, "overview")
    with pytest.raises(summarize.Vague):
        summarize.check_covers(vague, draft)
    monkeypatch.setattr(summarize, "_llm", lambda *a, **k: vague)
    out = summarize.get_summary(f, "overview")
    assert out["source"] == "template" and "key figures" in out["note"] and not summarize._cache


def test_a_faithful_rewrite_that_keeps_the_numbers_is_accepted(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    f = build_facts("Nova")
    draft = summarize.template_summary(f, "overview")
    rewrite = {**draft, "headline": "Nova's mood has turned sharply negative",
               "summary": "Since " + draft["summary"].split("From the week of ", 1)[1]}
    summarize.check_grounded(rewrite, f)
    summarize.check_covers(rewrite, draft)
    monkeypatch.setattr(summarize, "_llm", lambda *a, **k: rewrite)
    assert summarize.get_summary(f, "overview")["source"] == "llm"

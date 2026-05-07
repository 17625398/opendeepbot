from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.api.routers.mcp_chrome import router  # noqa: E402


def build_app():
    app = FastAPI()
    app.include_router(router, prefix="")
    return app


def test_navigate_ok_with_dummy_client():
    app = build_app()
    client = TestClient(app)

    dummy = MagicMock()
    dummy.navigate.return_value = {"ok": True, "action": "navigate", "url": "https://example.com"}

    with patch("src.api.routers.mcp_chrome.get_mcp_chrome_client", return_value=dummy):
        resp = client.post("/mcp/chrome/navigate", params={"url": "https://example.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["action"] == "navigate"


def test_rate_limit():
    app = build_app()
    client = TestClient(app)

    dummy = MagicMock()
    dummy.navigate.return_value = {"ok": True, "action": "navigate", "url": "https://example.com"}

    with patch("src.api.routers.mcp_chrome.get_mcp_chrome_client", return_value=dummy):
        # Exceed 10 calls within window
        status_codes = []
        for _ in range(12):
            resp = client.post("/mcp/chrome/navigate", params={"url": "https://example.com"})
            status_codes.append(resp.status_code)
        # At least one should be 429
        assert any(code == 429 for code in status_codes)


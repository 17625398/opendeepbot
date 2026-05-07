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


def test_stop_endpoint_calls_manager_stop():
    app = build_app()
    client = TestClient(app)
    mgr = MagicMock()
    with patch("src.api.routers.mcp_chrome.get_mcp_chrome_manager", return_value=mgr):
        resp = client.post("/mcp/chrome/stop")
        assert resp.status_code == 200
        mgr.stop.assert_called_once()
        assert resp.json()["status"] == "stopped"


def test_restart_endpoint_calls_restart():
    app = build_app()
    client = TestClient(app)
    with patch("src.api.routers.mcp_chrome.restart_mcp_chrome", return_value=True):
        resp = client.post("/mcp/chrome/restart")
        assert resp.status_code == 200
        assert resp.json()["status"] == "restarted"


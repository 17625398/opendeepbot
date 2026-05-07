from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.mcp.mcp_chrome_client import MCPChromeClient  # noqa: E402


@pytest.fixture
def http_cfg():
    return {
        "mcp": {
            "mcp_chrome": {
                "enabled": True,
                "http_url": "http://localhost:3921/mcp/messages/",
            }
        }
    }


def _mock_httpx_client(result_payload):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = result_payload
    client = MagicMock()
    client.post.return_value = resp
    wrapper = MagicMock()
    wrapper.__enter__.return_value = client
    wrapper.__exit__.return_value = False
    return wrapper, client


def test_navigate_rpc_success(http_cfg):
    wrapper, client = _mock_httpx_client({"jsonrpc": "2.0", "result": {"ok": True, "action": "navigate"}})
    with patch("src.services.mcp.mcp_chrome_client.load_config_with_main", return_value=http_cfg), \
         patch("src.services.mcp.mcp_chrome_client.get_mcp_chrome_manager") as mgr_patch, \
         patch("src.services.mcp.mcp_chrome_client.httpx.Client", return_value=wrapper):
        mgr = MagicMock()
        mgr.is_healthy.return_value = True
        mgr_patch.return_value = mgr
        cli = MCPChromeClient()
        res = cli.navigate("https://example.com")
        assert res.get("result", {}).get("action") == "navigate" or res.get("action") == "navigate"
        client.post.assert_called_once()


def test_click_rpc_error_fallback(http_cfg):
    wrapper, client = _mock_httpx_client({"jsonrpc": "2.0", "error": {"code": -1, "message": "fail"}})
    with patch("src.services.mcp.mcp_chrome_client.load_config_with_main", return_value=http_cfg), \
         patch("src.services.mcp.mcp_chrome_client.get_mcp_chrome_manager") as mgr_patch, \
         patch("src.services.mcp.mcp_chrome_client.httpx.Client", return_value=wrapper):
        mgr = MagicMock()
        mgr.is_healthy.return_value = True
        mgr_patch.return_value = mgr
        cli = MCPChromeClient()
        res = cli.click("#btn")
        assert res.get("ok") is True and res.get("action") == "click"


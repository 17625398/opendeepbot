from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.mcp.mcp_chrome_manager import MCPChromeManager  # noqa: E402


@pytest.fixture
def enabled_config():
    return {
        "mcp": {
            "mcp_chrome": {
                "enabled": True,
                "command": "node",
                "args": ["-e", "console.log('ok')"],
                "startup_timeout": 1.0,
            }
        }
    }


def test_diagnose_reports_ok(enabled_config):
    with patch("src.services.mcp.mcp_chrome_manager.load_config_with_main", return_value=enabled_config), \
         patch("src.services.mcp.mcp_chrome_manager.shutil.which", return_value="C:/Program Files/nodejs/node.exe"), \
         patch("src.services.mcp.mcp_chrome_manager.subprocess.check_output", return_value="v20.19.0"):
        mgr = MCPChromeManager()
        report = mgr.diagnose()
        assert report["enabled"] == "True"
        assert "Node 可用" in report["node"]


def test_start_process_healthy(enabled_config):
    fake_proc = MagicMock()
    fake_proc.poll.return_value = None

    with patch("src.services.mcp.mcp_chrome_manager.load_config_with_main", return_value=enabled_config), \
         patch("src.services.mcp.mcp_chrome_manager.shutil.which", side_effect=lambda name: "chrome.exe" if "chrome" in name else "node.exe"), \
         patch("src.services.mcp.mcp_chrome_manager.subprocess.check_output", return_value="v20.19.0"), \
         patch("src.services.mcp.mcp_chrome_manager.subprocess.Popen", return_value=fake_proc):
        mgr = MCPChromeManager()
        assert mgr.start() is True
        assert mgr.is_healthy() is True


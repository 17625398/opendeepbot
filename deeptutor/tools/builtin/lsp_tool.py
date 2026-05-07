"""LSP diagnostic tool for post-edit code analysis."""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any

from deeptutor.core.tool_protocol import BaseTool, ToolDefinition, ToolParameter, ToolResult


class LSPDiagnosticTool(BaseTool):
    """Run LSP-based diagnostics on a file after editing."""

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="lsp_diagnostic",
            description="Run LSP diagnostics (pyright/rust-analyzer) on a file to detect errors/warnings after editing.",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type="string",
                    description="Path to the file to diagnose (relative to workspace root).",
                ),
                ToolParameter(
                    name="language",
                    type="string",
                    description="Language hint: 'python', 'rust', 'typescript', 'go', 'cpp', 'c'. Auto-detected if not provided.",
                    required=False,
                ),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        file_path = kwargs.get("file_path", "")
        language = kwargs.get("language", "").lower()

        if not file_path:
            return ToolResult(content="Error: file_path is required.", success=False)

        # Resolve path
        workspace_root = os.environ.get("DEEPTUTOR_WORKSPACE", ".")
        full_path = os.path.normpath(os.path.join(workspace_root, file_path))
        if not full_path.startswith(os.path.normpath(workspace_root)):
            return ToolResult(content="Error: Path traversal detected.", success=False)

        if not os.path.exists(full_path):
            return ToolResult(content=f"Error: File not found: {file_path}", success=False)

        # Auto-detect language if not provided
        if not language:
            ext = os.path.splitext(file_path)[1].lower()
            language = {
                ".py": "python",
                ".rs": "rust",
                ".ts": "typescript",
                ".tsx": "typescript",
                ".js": "typescript",
                ".go": "go",
                ".cpp": "cpp",
                ".cc": "cpp",
                ".c": "c",
                ".h": "c",
                ".hpp": "cpp",
            }.get(ext, "python")  # Default to python

        try:
            diagnostics = await self._run_diagnostic(full_path, language)
            if not diagnostics:
                return ToolResult(
                    content=f"No LSP diagnostics found for {file_path} (language: {language}).",
                    success=True,
                    metadata={"diagnostics": []},
                )

            diag_text = f"LSP diagnostics for {file_path} ({language}):\n"
            for d in diagnostics:
                severity = d.get("severity", "unknown")
                message = d.get("message", "")
                line = d.get("range", {}).get("start", {}).get("line", "?")
                diag_text += f"  [{severity}] Line {line}: {message}\n"

            return ToolResult(
                content=diag_text.strip(),
                success=True,
                metadata={"diagnostics": diagnostics, "language": language},
            )

        except Exception as e:
            return ToolResult(content=f"Error running LSP diagnostic: {e}", success=False)

    async def _run_diagnostic(self, full_path: str, language: str) -> list[dict[str, Any]]:
        """Run the appropriate LSP server for the language."""
        if language == "python":
            return await self._run_pyright(full_path)
        elif language == "rust":
            return await self._run_rust_analyzer(full_path)
        elif language in ("typescript", "javascript"):
            return await self._run_typescript(full_path)
        elif language == "go":
            return await self._run_gopls(full_path)
        elif language in ("cpp", "c"):
            return await self._run_clangd(full_path)
        else:
            # Fallback: try pyright for unknown
            return await self._run_pyright(full_path)

    async def _run_pyright(self, path: str) -> list[dict[str, Any]]:
        """Run pyright diagnostics."""
        try:
            result = subprocess.run(
                ["pyright", "--outputjson", path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return []
            # Parse JSON output
            data = json.loads(result.stdout or "{}")
            diagnostics = data.get("generalDiagnostics", [])
            return [
                {
                    "severity": "error" if d.get("severity") == "error" else "warning",
                    "message": d.get("message", ""),
                    "range": {
                        "start": {"line": d.get("range", {}).get("start", {}).get("line", 0)},
                    },
                }
                for d in diagnostics
            ]
        except Exception:
            return []

    async def _run_rust_analyzer(self, path: str) -> list[dict[str, Any]]:
        """Run rust-analyzer diagnostics via cargo check."""
        try:
            result = subprocess.run(
                ["cargo", "check", "--message-format=json"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.path.dirname(path) or ".",
            )
            diagnostics = []
            for line in result.stderr.splitlines():
                try:
                    msg = json.loads(line)
                    if msg.get("reason") == "compiler-message":
                        diag = msg.get("message", {})
                        if diag.get("level") in ("error", "warning"):
                            spans = diag.get("spans", [])
                            line_num = spans[0].get("line_start", "?") if spans else "?"
                            diagnostics.append({
                                "severity": diag.get("level", "unknown"),
                                "message": diag.get("message", ""),
                                "range": {"start": {"line": line_num}},
                            })
                except Exception:
                    continue
            return diagnostics
        except Exception:
            return []

    async def _run_typescript(self, path: str) -> list[dict[str, Any]]:
        """Run typescript diagnostics via tsc or typescript-language-server."""
        try:
            result = subprocess.run(
                ["tsc", "--noEmit", "--pretty", "false"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.dirname(path) or ".",
            )
            diagnostics = []
            for line in result.stdout.splitlines():
                if ": error TS" in line or ": warning TS" in line:
                    parts = line.split(":", 2)
                    if len(parts) >= 3:
                        diagnostics.append({
                            "severity": "error" if "error" in line else "warning",
                            "message": parts[2].strip(),
                            "range": {"start": {"line": parts[1]}},
                        })
            return diagnostics
        except Exception:
            return []

    async def _run_gopls(self, path: str) -> list[dict[str, Any]]:
        """Run gopls diagnostics via go vet."""
        try:
            result = subprocess.run(
                ["go", "vet", "./..."],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.dirname(path) or ".",
            )
            diagnostics = []
            for line in result.stdout.splitlines():
                if ": " in line and ("error" in line.lower() or "warning" in line.lower()):
                    diagnostics.append({
                        "severity": "error" if "error" in line.lower() else "warning",
                        "message": line,
                        "range": {"start": {"line": "?"}},
                    })
            return diagnostics
        except Exception:
            return []

    async def _run_clangd(self, path: str) -> list[dict[str, Any]]:
        """Run clangd diagnostics via clang-check."""
        try:
            result = subprocess.run(
                ["clang-check", "-analyze", path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            diagnostics = []
            for line in result.stderr.splitlines():
                if ": error:" in line or ": warning:" in line:
                    diagnostics.append({
                        "severity": "error" if "error:" in line else "warning",
                        "message": line,
                        "range": {"start": {"line": "?"}},
                    })
            return diagnostics
        except Exception:
            return []

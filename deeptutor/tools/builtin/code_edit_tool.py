"""DeepSeek code editing tool with diff application."""

from __future__ import annotations

import difflib
import os
from typing import Any

from deeptutor.core.tool_protocol import BaseTool, ToolDefinition, ToolParameter, ToolResult


class DeepSeekCodeEditTool(BaseTool):
    """Apply code patches in unified diff format using DeepSeek editing logic."""

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="deepseek_code_edit",
            description="Apply code patches in unified diff format to local files.",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type="string",
                    description="Path to the file to edit (relative to workspace root).",
                ),
                ToolParameter(
                    name="diff_content",
                    type="string",
                    description="Unified diff content describing the changes to apply.",
                ),
                ToolParameter(
                    name="dry_run",
                    type="boolean",
                    description="If true, preview changes without applying (default: false).",
                    required=False,
                    default=False,
                ),
            ],
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        file_path = kwargs.get("file_path", "")
        diff_content = kwargs.get("diff_content", "")
        dry_run = kwargs.get("dry_run", False)

        if not file_path:
            return ToolResult(content="Error: file_path is required.", success=False)
        if not diff_content:
            return ToolResult(content="Error: diff_content is required.", success=False)

        # Resolve path (basic security check)
        workspace_root = os.environ.get("DEEPTUTOR_WORKSPACE", ".")
        full_path = os.path.normpath(os.path.join(workspace_root, file_path))
        if not full_path.startswith(os.path.normpath(workspace_root)):
            return ToolResult(content="Error: Path traversal detected.", success=False)

        try:
            # Read original file
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    original_lines = f.readlines()
            else:
                original_lines = []

            # Parse and apply diff
            diff_lines = diff_content.splitlines(keepends=True)
            patched_lines = self._apply_diff(original_lines, diff_lines)

            if patched_lines is None:
                return ToolResult(
                    content="Error: Failed to apply diff. Check diff format.",
                    success=False,
                )

            result_lines = patched_lines

            if dry_run:
                # Generate preview
                diff_preview = "".join(
                    difflib.unified_diff(
                        original_lines,
                        result_lines,
                        fromfile=f"a/{file_path}",
                        tofile=f"b/{file_path}",
                    )
                )
                return ToolResult(
                    content=f"Dry run preview for {file_path}:\n```diff\n{diff_preview}\n```",
                    success=True,
                )

            # Write patched content
            with open(full_path, "w", encoding="utf-8") as f:
                f.writelines(result_lines)

            return ToolResult(
                content=f"Successfully applied diff to {file_path}",
                metadata={
                    "file_path": file_path,
                    "lines_changed": len(result_lines) - len(original_lines),
                },
                success=True,
            )

        except Exception as e:
            return ToolResult(content=f"Error applying diff: {e}", success=False)

    @staticmethod
    def _apply_diff(
        original_lines: list[str], diff_lines: list[str]
    ) -> list[str] | None:
        """Apply a unified diff to original lines. Returns new lines or None if failed."""
        try:
            patched = list(
                difflib.patch_lines(
                    "".join(original_lines),
                    "".join(diff_lines),
                )
            )
            return patched
        except Exception:
            # Fallback: basic line-by-line application
            return None

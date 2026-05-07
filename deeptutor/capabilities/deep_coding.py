"""DeepSeek-powered coding capability with sub-agents.
DeepSeek 驱动的代码能力 - 使用子代理完成编码任务。
"""

from __future__ import annotations

from deeptutor.core.capability_protocol import BaseCapability, CapabilityManifest
from deeptutor.core.context import UnifiedContext
from deeptutor.core.stream_bus import StreamBus
from deeptutor.runtime.registry.tool_registry import get_tool_registry
from deeptutor.services.llm import complete


class DeepCodingCapability(BaseCapability):
    """DeepSeek-powered coding agent with sub-agents for plan, code, review, test."""

    manifest = CapabilityManifest(
        name="deep_coding",
        description="DeepSeek-powered coding agent: plan → code → review → test with sub-agents.",
        stages=["plan", "code", "review", "test"],
        tools_used=["deepseek_code_edit", "lsp_diagnostic", "code_execution"],
        cli_aliases=["code", "deep_code"],
        config_defaults={
            "model": "deepseek-v4-pro",
            "reasoning_effort": "high",
            "subagent_model": "deepseek-v4-flash",
            "auto_fix": True,
        },
    )

    async def run(self, context: UnifiedContext, stream: StreamBus) -> None:
        user_message = context.last_user_message or "Implement the requested feature."
        config = context.config or {}

        # Stage 1: Planning
        async with stream.stage("plan", source=self.manifest.name):
            await stream.content("Analyzing request and creating plan...", source=self.manifest.name)
            plan = await self._plan(user_message, context, stream)
            await stream.content(f"Plan:\n{plan}", source=self.manifest.name)

        # Stage 2: Coding (main model)
        async with stream.stage("code", source=self.manifest.name):
            await stream.content("Implementing code...", source=self.manifest.name)
            code_result = await self._code(user_message, plan, context, stream)
            await stream.content(f"Code implementation:\n{code_result}", source=self.manifest.name)

        # Stage 3: Sub-agent review (using flash model)
        async with stream.stage("review", source=self.manifest.name):
            await stream.content("Reviewing code with sub-agent...", source=self.manifest.name)
            review = await self._subagent_review(code_result, context, stream)
            await stream.content(f"Review feedback:\n{review}", source=self.manifest.name)

        # Stage 4: Testing
        async with stream.stage("test", source=self.manifest.name):
            await stream.content("Running tests and diagnostics...", source=self.manifest.name)
            test_result = await self._test(code_result, context, stream)
            await stream.content(f"Test results:\n{test_result}", source=self.manifest.name)

        # Final result
        await stream.result(
            {
                "plan": plan,
                "code": code_result,
                "review": review,
                "test": test_result,
            },
            source=self.manifest.name,
        )

    async def _plan(self, user_message: str, context: UnifiedContext, stream: StreamBus) -> str:
        """Create a coding plan."""
        system_prompt = """You are a senior software architect.
Create a clear, step-by-step plan for the coding task.
Focus on: requirements analysis, design approach, implementation steps, testing strategy.
Output the plan in Markdown format."""
        
        response = await complete(
            prompt=user_message,
            system_prompt=system_prompt,
            model=self.manifest.config_defaults.get("model"),
            reasoning_effort=self.manifest.config_defaults.get("reasoning_effort"),
        )
        return response or "No plan generated."

    async def _code(self, user_message: str, plan: str, context: UnifiedContext, stream: StreamBus) -> str:
        """Implement the code based on plan."""
        system_prompt = """You are a expert software developer.
Implement the code following the provided plan.
Output the complete code with proper comments."""
        
        prompt = f"Task: {user_message}\n\nPlan:\n{plan}\n\nImplement the solution:"
        
        # Use streaming to show progress
        code_parts = []
        async for chunk in stream(
            prompt=prompt,
            system_prompt=system_prompt,
            model=self.manifest.config_defaults.get("model"),
            reasoning_effort=self.manifest.config_defaults.get("reasoning_effort"),
            stream_bus=stream,  # Pass stream_bus for REASONING_CONTENT events
        ):
            code_parts.append(chunk)
        
        return "".join(code_parts) or "No code generated."

    async def _subagent_review(self, code: str, context: UnifiedContext, stream: StreamBus) -> str:
        """Use a sub-agent (flash model) for code review."""
        system_prompt = """You are a code reviewer using a fast model.
Review the provided code for:
1. Bugs and logic errors
2. Code quality and best practices
3. Security issues
4. Performance concerns
Provide specific, actionable feedback."""
        
        prompt = f"Review this code:\n\n```\n{code}\n```"
        
        response = await complete(
            prompt=prompt,
            system_prompt=system_prompt,
            model=self.manifest.config_defaults.get("subagent_model", "deepseek-v4-flash"),
            reasoning_effort="off",  # Sub-agent uses no reasoning for speed
        )
        return response or "No review feedback."

    async def _test(self, code: str, context: UnifiedContext, stream: StreamBus) -> str:
        """Run tests and diagnostics."""
        # Run LSP diagnostic if file path is available
        file_path = context.metadata.get("target_file") if context.metadata else None
        
        results = []
        
        if file_path:
            # Use LSP diagnostic tool
            tool_registry = get_tool_registry()
            lsp_tool = tool_registry.get_tool("lsp_diagnostic")
            if lsp_tool:
                diag_result = await lsp_tool.execute(file_path=file_path)
                results.append(f"LSP Diagnostics:\n{diag_result.content}")
        
        # Run code execution if applicable
        tool_registry = get_tool_registry()
        exec_tool = tool_registry.get_tool("code_execution")
        if exec_tool:
            exec_result = await exec_tool.execute(code_snippet=code, language="python")
            results.append(f"Execution result:\n{exec_result.content}")
        
        return "\n\n".join(results) if results else "No tests configured."

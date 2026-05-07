"""ReAct Agent Loop

Implements the ReAct (Reasoning + Acting) loop for autonomous agent behavior.
Based on the paper: ReAct: Synergizing Reasoning and Acting in Language Models
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)
from deeptutor.utils.self_improvement import log_execution_error

from .context import AgentContext
from .tools import get_default_tools


class StepType(Enum):
    """Types of agent steps"""
    THINK = "think"
    ACTION = "action"
    OBSERVE = "observe"
    RESPOND = "respond"
    ERROR = "error"


@dataclass
class AgentStep:
    """A step in the agent loop"""
    step_type: StepType
    content: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


class AgentLoop:
    """ReAct Agent Loop
    
    Implements the reasoning-acting loop:
    1. Think: Analyze the situation and decide what to do
    2. Act: Execute the decided action (tool call)
    3. Observe: Process the result of the action
    4. Respond: Generate final response when ready
    
    Modes:
    - Normal mode: Requires human approval for tool calls
    - YOLO mode: Auto-approves all tool calls (for trusted workspaces)
    
    Features:
    - Real-time cost tracking for LLM calls
    - Token usage monitoring
    - Workspace snapshot and rollback
    - Thinking mode visualization
    """
    
    # Snapshot management
    _snapshots: List[Dict[str, Any]] = []
    _max_snapshots: int = 10
    
    # Thinking mode visualization
    thinking_enabled: bool = True
    thinking_style: str = "chain"  # "chain", "tree", "mindmap"
    
    def __init__(
        self,
        llm_client,
        tool_registry: Optional[Dict[str, Callable]] = None,
        max_iterations: int = 10,
        system_prompt: Optional[str] = None,
        use_default_tools: bool = True,
        yolo_mode: bool = False,
        approval_callback: Optional[Callable[[Dict[str, Any]], bool]] = None,
        track_cost: bool = True,
        cost_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.context: Optional[AgentContext] = None
        self.yolo_mode = yolo_mode
        self.approval_callback = approval_callback
        self.track_cost = track_cost
        self.cost_callback = cost_callback
        
        # Cost tracking
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost_usd = 0.0
        self.llm_calls = 0
        
        # Initialize tool registry
        if tool_registry is None and use_default_tools:
            # Use default tools from tools module
            default_tools = get_default_tools()
            self.tool_registry = default_tools.to_dict()
            self.tools = default_tools
        elif tool_registry is not None:
            self.tool_registry = tool_registry
            self.tools = None
        else:
            self.tool_registry = {}
            self.tools = None
    
    def set_yolo_mode(self, enabled: bool):
        """Set YOLO mode on/off"""
        self.yolo_mode = enabled
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost tracking summary"""
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_cost_usd": self.total_cost_usd,
            "llm_calls": self.llm_calls
        }
    
    def _default_system_prompt(self) -> str:
        """Default ReAct system prompt"""
        return """You are a helpful AI assistant that can use tools to solve problems.

Current Date and Time: {current_time}

You operate in a ReAct (Reasoning + Acting) loop. For each step:

1. **Thought**: Analyze what you need to do
2. **Action**: Choose a tool to use (if needed)
3. **Observation**: Review the result
4. **Response**: Provide final answer when ready

Available tools:
{{tools}}

Format your response as:
Thought: [Your reasoning about what to do]
Action: [Tool name or "Final Answer"]
Action Input: [JSON input for the tool]

Or when ready to respond:
Thought: [Your reasoning]
Action: Final Answer
Action Input: {{"answer": "Your response to the user"}}

Always think step by step and use tools when necessary."""
    
    @log_execution_error
    async def run(
        self,
        user_input: str,
        context: Optional[AgentContext] = None,
        stream_callback: Optional[Callable[[AgentStep], None]] = None
    ) -> Dict[str, Any]:
        """Run the ReAct loop
        
        Args:
            user_input: User's input message
            context: Optional existing context
            stream_callback: Callback for streaming steps
            
        Returns:
            Result dictionary with response and metadata
        """
        # Initialize or use existing context
        if context is None:
            self.context = AgentContext()
        else:
            self.context = context
        
        # Add user message to history
        self.context.history.add_user_message(user_input)
        
        steps: List[AgentStep] = []
        final_response = None
        
        try:
            for iteration in range(self.max_iterations):
                logger.debug(f"Agent loop iteration {iteration + 1}/{self.max_iterations}")
                
                # Build prompt with context
                prompt = self._build_prompt(user_input)
                
                # Get LLM response
                llm_response = await self._call_llm(prompt)
                
                # Parse response
                parsed = self._parse_response(llm_response)
                
                # Add thought to context
                thought = self.context.add_thought(
                    thought=parsed.get("thought", ""),
                    action=parsed.get("action"),
                    action_input=parsed.get("action_input")
                )
                
                # Create step object
                step = AgentStep(
                    step_type=StepType.THINK,
                    content=thought.thought,
                    metadata={"action": thought.action}
                )
                steps.append(step)
                
                # Stream thought step
                if stream_callback:
                    stream_callback(step)
                
                # Check if final answer
                if parsed.get("action") == "Final Answer":
                    action_input = parsed.get("action_input", {})
                    if isinstance(action_input, dict):
                        final_response = action_input.get("answer", "")
                    else:
                        final_response = str(action_input)
                    
                    # Add to history
                    self.context.history.add_assistant_message(final_response)
                    
                    # Create response step
                    step = AgentStep(
                        step_type=StepType.RESPOND,
                        content=final_response
                    )
                    steps.append(step)
                    
                    if stream_callback:
                        stream_callback(step)
                    
                    break
                
                # Execute action
                action_result = await self._execute_action(
                    parsed.get("action"),
                    parsed.get("action_input", {})
                )
                
                # Add observation
                self.context.add_observation(action_result)
                
                # Create observation step
                step = AgentStep(
                    step_type=StepType.OBSERVE,
                    content=action_result
                )
                steps.append(step)
                
                # Stream observation step
                if stream_callback:
                    stream_callback(step)
            
            # If max iterations reached without final answer
            if final_response is None:
                final_response = "I apologize, but I couldn't complete the task within the allowed steps. Please try rephrasing your request."
                self.context.history.add_assistant_message(final_response)
                
                step = AgentStep(
                    step_type=StepType.ERROR,
                    content="Max iterations reached"
                )
                steps.append(step)
                
                if stream_callback:
                    stream_callback(step)
            
            return {
                "success": True,
                "response": final_response,
                "steps": [self._step_to_dict(s) for s in steps],
                "thoughts": self.context.get_thought_chain(),
                "iterations": len(steps),
                "session_id": self.context.session_id
            }
            
        except Exception as e:
            logger.error(f"Agent loop error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            error_msg = f"An error occurred: {str(e)}"
            
            if stream_callback:
                stream_callback(AgentStep(
                    step_type=StepType.ERROR,
                    content=error_msg
                ))
            
            return {
                "success": False,
                "response": error_msg,
                "error": str(e),
                "steps": [self._step_to_dict(s) for s in steps],
                "session_id": self.context.session_id if self.context else None
            }
    
    def _build_prompt(self, user_input: str) -> str:
        """Build the prompt for LLM"""
        from datetime import datetime
        
        # Get tool descriptions from ToolRegistry if available
        tool_descriptions = []
        
        if self.tools:
            # Use proper tool schemas from ToolRegistry
            schemas = self.tools.get_schemas()
            for schema in schemas:
                name = schema.get("name", "")
                desc = schema.get("description", "")
                params = schema.get("parameters", {})
                
                tool_desc = f"- {name}: {desc}"
                if params.get("properties"):
                    params_desc = []
                    for param_name, param_info in params["properties"].items():
                        param_type = param_info.get("type", "any")
                        param_desc = param_info.get("description", "")
                        required = param_name in params.get("required", [])
                        req_marker = " (required)" if required else ""
                        params_desc.append(f"  - {param_name} ({param_type}){req_marker}: {param_desc}")
                    
                    if params_desc:
                        tool_desc += "\n  Parameters:\n" + "\n".join(params_desc)
                
                tool_descriptions.append(tool_desc)
        else:
            # Fallback to basic descriptions
            for name, tool in self.tool_registry.items():
                desc = getattr(tool, "__doc__", f"Tool: {name}")
                tool_descriptions.append(f"- {name}: {desc}")
        
        tools_text = "\n\n".join(tool_descriptions) if tool_descriptions else "No tools available"

        # Update current time in system prompt
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        system = self.system_prompt.replace("{{tools}}", tools_text)
        system = system.replace("{{current_time}}", current_time)

        # Get conversation context (ensure context is initialized)
        if self.context is None:
            from .context import AgentContext
            self.context = AgentContext()

        history = self.context.history.get_recent_context(n=5)

        # Get ReAct chain
        react_chain = self.context.get_react_prompt()
        
        prompt = f"""{system}

Conversation History:
{history}

{react_chain}

User: {user_input}

Thought:"""
        
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM with prompt and track cost"""
        try:
            # Use the LLM client's chat_completion method
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_client.chat_completion(messages)
            
            # Track cost if enabled
            if self.track_cost and hasattr(self.llm_client, 'get_last_usage'):
                usage = self.llm_client.get_last_usage()
                if usage:
                    self._update_cost(usage)
            
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _update_cost(self, usage: Dict[str, int]):
        """Update cost tracking with LLM usage data"""
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.llm_calls += 1
        
        # Calculate cost using the same pricing as token_tracker
        model_name = getattr(self.llm_client, 'model', 'gpt-4o-mini')
        cost = self._calculate_cost(model_name, prompt_tokens, completion_tokens)
        self.total_cost_usd += cost
        
        # Call cost callback if set
        if self.cost_callback:
            try:
                self.cost_callback(self.get_cost_summary())
            except Exception as e:
                logger.error(f"Cost callback failed: {e}")
    
    def _calculate_cost(self, model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate LLM call cost"""
        MODEL_PRICING = {
            "gpt-4o": {"input": 0.0025, "output": 0.010},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "deepseek-chat": {"input": 0.00014, "output": 0.00028},
            "deepseek-coder": {"input": 0.00014, "output": 0.00028},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
            "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
            "gemini-pro": {"input": 0.0005, "output": 0.0015},
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
            "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
        }
        
        # Try exact match or fuzzy match
        model_lower = model_name.lower()
        for key, pricing in MODEL_PRICING.items():
            if key.lower() in model_lower or model_lower in key.lower():
                input_cost = (prompt_tokens / 1000.0) * pricing["input"]
                output_cost = (completion_tokens / 1000.0) * pricing["output"]
                return input_cost + output_cost
        
        # Default pricing
        return (prompt_tokens / 1000.0) * 0.00015 + (completion_tokens / 1000.0) * 0.0006
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        result = {
            "thought": "",
            "action": None,
            "action_input": {}
        }
        
        # Extract thought
        thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction:|$)", response, re.DOTALL | re.IGNORECASE)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()
        
        # Extract action
        action_match = re.search(r"Action:\s*(.+?)(?=\nAction Input:|$)", response, re.DOTALL | re.IGNORECASE)
        if action_match:
            result["action"] = action_match.group(1).strip()
        
        # Extract action input
        input_match = re.search(r"Action Input:\s*(\{.+?\}|.+?)(?=\n|$)", response, re.DOTALL | re.IGNORECASE)
        if input_match:
            input_text = input_match.group(1).strip()
            try:
                result["action_input"] = json.loads(input_text)
            except json.JSONDecodeError:
                result["action_input"] = {"input": input_text}
        
        return result
    
    async def _execute_action(self, action: Optional[str], action_input: Dict) -> str:
        """Execute a tool action"""
        if not action or action == "Final Answer":
            return "No action to execute"
        
        # Check approval before executing
        if not await self._check_tool_approval(action, action_input):
            return f"Action '{action}' requires human approval but was not approved."
        
        # Use ToolRegistry if available for better execution
        if self.tools:
            try:
                result = await self.tools.execute(action, **action_input)
                
                if result.success:
                    return json.dumps(result.data, ensure_ascii=False, indent=2)
                else:
                    # Log error for self-improvement
                    try:
                        from deeptutor.utils.self_improvement import Area, Priority, log_error
                        log_error(
                            skill_or_command=f"Tool:{action}",
                            summary=f"Tool execution failed: {action}",
                            error_message=result.error or "Unknown error",
                            context={"input": str(action_input)},
                            suggested_fix="Check tool implementation or input parameters",
                            area=Area.BACKEND,
                            priority=Priority.HIGH
                        )
                    except Exception as e:
                        logger.error(f"Failed to log error to self-improvement: {e}")
                        
                    return f"Error: {result.error}"
                    
            except Exception as e:
                logger.error(f"Tool execution error via registry: {e}")
                
                # Log error for self-improvement
                try:
                    from deeptutor.utils.self_improvement import Area, Priority, log_error
                    log_error(
                        skill_or_command=f"Tool:{action}",
                        summary=f"Tool execution failed: {action}",
                        error_message=str(e),
                        area=Area.BACKEND,
                        priority=Priority.HIGH,
                        context={"input": str(action_input)}
                    )
                except Exception as e:
                    logger.error(f"Failed to log error to self-improvement: {e}")
                
                return f"Error executing {action}: {str(e)}"
        
        # Fallback to direct registry execution
        if action not in self.tool_registry:
            # Try fuzzy matching or finding similar tools
            available = list(self.tool_registry.keys())
            return f"Error: Tool '{action}' not found. Available tools: {', '.join(available)}"
        
        tool = self.tool_registry[action]
        
        try:
            # Execute tool
            if asyncio.iscoroutinefunction(tool):
                result = await tool(**action_input)
            else:
                result = tool(**action_input)
            
            # Format result
            if isinstance(result, dict):
                return json.dumps(result, ensure_ascii=False, indent=2)
            return str(result)
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            
            # Log error for self-improvement
            try:
                from deeptutor.utils.self_improvement import Area, Priority, log_error
                log_error(
                    skill_or_command=f"Tool:{action}",
                    summary=f"Tool execution failed: {action}",
                    error_message=str(e),
                    area=Area.BACKEND,
                    priority=Priority.HIGH,
                    context={"input": str(action_input)}
                )
            except:
                pass
                
            return f"Error executing {action}: {str(e)}"
    
    def _step_to_dict(self, step: AgentStep) -> Dict[str, Any]:
        """Convert step to dictionary"""
        return {
            "type": step.step_type.value,
            "content": step.content,
            "metadata": step.metadata,
            "timestamp": step.timestamp
        }
    
    def register_tool(self, name: str, tool_func: Callable):
        """Register a tool"""
        self.tool_registry[name] = tool_func

        # Also register with ToolRegistry if available
        if self.tools and hasattr(tool_func, "name"):
            try:
                # Check if tool_func is a BaseTool instance
                from .tools.base import BaseTool
                if isinstance(tool_func, BaseTool):
                    self.tools.register(tool_func)
            except Exception as e:
                logger.warning(f"Failed to register tool {name} with ToolRegistry: {e}")
                
        logger.info(f"Registered tool: {name}")
    
    def unregister_tool(self, name: str):
        """Unregister a tool"""
        if name in self.tool_registry:
            del self.tool_registry[name]
            logger.info(f"Unregistered tool: {name}")
    
    def get_context(self) -> Optional[AgentContext]:
        """Get current context"""
        return self.context
    
    async def _check_tool_approval(self, action: str, action_input: Dict) -> bool:
        """Check if tool action requires approval and handle approval logic
        
        Returns:
            bool: True if action is approved, False otherwise
        """
        # YOLO mode: auto-approve all actions
        if self.yolo_mode:
            logger.debug(f"YOLO mode: auto-approving action '{action}'")
            return True
        
        # If no approval callback is set, require explicit approval
        if self.approval_callback is None:
            # In normal mode without callback, we need to prompt for approval
            # This is a simplified implementation - in production, this would
            # involve UI interaction or API call to human decision system
            logger.info(f"Tool call requires approval: {action}")
            # For now, we'll log and return True to allow execution
            # In a real system, this would block and wait for human input
            return True
        
        # Call approval callback
        try:
            if asyncio.iscoroutinefunction(self.approval_callback):
                approved = await self.approval_callback({
                    "action": action,
                    "action_input": action_input,
                    "context": self.context.to_dict() if self.context else {}
                })
            else:
                approved = self.approval_callback({
                    "action": action,
                    "action_input": action_input,
                    "context": self.context.to_dict() if self.context else {}
                })
            
            if approved:
                logger.debug(f"Action '{action}' approved by callback")
            else:
                logger.info(f"Action '{action}' rejected by callback")
            
            return approved
        
        except Exception as e:
            logger.error(f"Approval callback failed: {e}")
            # On callback error, allow execution as fallback
            return True
    
    def _create_snapshot(self, snapshot_type: str = "auto") -> str:
        """Create a snapshot of the current workspace state
        
        Args:
            snapshot_type: Type of snapshot ("auto", "manual", "before_action", "after_action")
        
        Returns:
            snapshot_id: Unique identifier for this snapshot
        """
        import uuid
        
        snapshot = {
            "snapshot_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "type": snapshot_type,
            "context": self.context.to_dict() if self.context else {},
            "cost_summary": self.get_cost_summary(),
            "iterations_completed": self._get_iteration_count()
        }
        
        # Add to snapshots list
        self._snapshots.append(snapshot)
        
        # Remove oldest snapshots if exceeding max
        while len(self._snapshots) > self._max_snapshots:
            removed = self._snapshots.pop(0)
            logger.debug(f"Removed old snapshot: {removed['snapshot_id']}")
        
        logger.info(f"Created snapshot: {snapshot['snapshot_id']} (type: {snapshot_type})")
        return snapshot["snapshot_id"]
    
    def _restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore workspace state from a snapshot
        
        Args:
            snapshot_id: The snapshot ID to restore
        
        Returns:
            bool: True if restoration was successful, False otherwise
        """
        # Find snapshot
        snapshot = next((s for s in self._snapshots if s["snapshot_id"] == snapshot_id), None)
        
        if not snapshot:
            logger.error(f"Snapshot not found: {snapshot_id}")
            return False
        
        try:
            # Restore context
            if self.context and "context" in snapshot:
                self.context.from_dict(snapshot["context"])
            
            # Restore cost tracking
            cost_summary = snapshot.get("cost_summary", {})
            self.total_prompt_tokens = cost_summary.get("total_prompt_tokens", 0)
            self.total_completion_tokens = cost_summary.get("total_completion_tokens", 0)
            self.total_cost_usd = cost_summary.get("total_cost_usd", 0.0)
            self.llm_calls = cost_summary.get("llm_calls", 0)
            
            logger.info(f"Restored snapshot: {snapshot_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to restore snapshot {snapshot_id}: {e}")
            return False
    
    def _get_snapshots(self) -> List[Dict[str, Any]]:
        """Get list of all snapshots"""
        return self._snapshots
    
    def _get_snapshot_by_id(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific snapshot by ID"""
        return next((s for s in self._snapshots if s["snapshot_id"] == snapshot_id), None)
    
    def _rollback_to_snapshot(self, snapshot_id: str) -> bool:
        """Rollback to a previous snapshot (alias for restore)"""
        return self._restore_snapshot(snapshot_id)
    
    def _rollback_steps(self, steps: int = 1) -> bool:
        """Rollback by a number of steps
        
        Args:
            steps: Number of steps to rollback
        
        Returns:
            bool: True if successful
        """
        if len(self._snapshots) < steps:
            logger.warning(f"Not enough snapshots to rollback {steps} steps")
            return False
        
        # Get the snapshot at position (current - steps)
        target_index = max(0, len(self._snapshots) - steps - 1)
        snapshot = self._snapshots[target_index]
        
        return self._restore_snapshot(snapshot["snapshot_id"])
    
    def _clear_snapshots(self):
        """Clear all snapshots"""
        self._snapshots.clear()
        logger.info("Cleared all snapshots")
    
    def _get_iteration_count(self) -> int:
        """Get current iteration count (helper method)"""
        if self.context:
            return len(self.context.get_thought_chain())
        return 0
    
    def format_thinking_chain(self, style: str = None) -> str:
        """Format the thinking chain for display
        
        Args:
            style: Display style ("chain", "tree", "mindmap")
        
        Returns:
            Formatted string representation of the thinking process
        """
        if not self.context:
            return ""
        
        style = style or self.thinking_style
        thoughts = self.context.get_thought_chain()
        
        if style == "tree":
            return self._format_thinking_tree(thoughts)
        elif style == "mindmap":
            return self._format_thinking_mindmap(thoughts)
        else:
            return self._format_thinking_chain(thoughts)
    
    def _format_thinking_chain(self, thoughts: List[Dict[str, Any]]) -> str:
        """Format thinking as a linear chain"""
        lines = ["📝 Thinking Chain:"]
        
        for i, thought in enumerate(thoughts, 1):
            lines.append(f"\n{i}. 💡 {thought.get('thought', '')}")
            
            action = thought.get('action')
            if action and action != "Final Answer":
                action_input = thought.get('action_input', {})
                if isinstance(action_input, dict):
                    input_str = json.dumps(action_input, ensure_ascii=False)
                else:
                    input_str = str(action_input)
                lines.append(f"   🎯 Action: {action}")
                lines.append(f"   📥 Input: {input_str}")
            
            observation = thought.get('observation')
            if observation:
                lines.append(f"   👀 Observation: {observation}")
        
        return "\n".join(lines)
    
    def _format_thinking_tree(self, thoughts: List[Dict[str, Any]]) -> str:
        """Format thinking as a tree structure"""
        lines = ["🌳 Reasoning Tree:"]
        lines.append("└── Root")
        
        for i, thought in enumerate(thoughts, 1):
            thought_text = thought.get('thought', '')[:50] + "..." if len(thought.get('thought', '')) > 50 else thought.get('thought', '')
            lines.append(f"    ├── [{i}] {thought_text}")
            
            action = thought.get('action')
            if action and action != "Final Answer":
                lines.append(f"    │   └── Action: {action}")
        
        return "\n".join(lines)
    
    def _format_thinking_mindmap(self, thoughts: List[Dict[str, Any]]) -> str:
        """Format thinking as a mindmap-like structure"""
        lines = ["🧠 Mind Map View:"]
        
        for i, thought in enumerate(thoughts, 1):
            thought_text = thought.get('thought', '')[:40]
            action = thought.get('action', '')
            
            if action == "Final Answer":
                lines.append(f"   ○ [{i}] {thought_text}")
                lines.append(f"      └── ✅ Final Answer")
            elif action:
                lines.append(f"   ● [{i}] {thought_text}")
                lines.append(f"      └── → {action}")
            else:
                lines.append(f"   ● [{i}] {thought_text}")
        
        return "\n".join(lines)
    
    def print_thinking(self, style: str = None):
        """Print the thinking chain to console"""
        formatted = self.format_thinking_chain(style)
        if formatted:
            print(formatted)
    
    def set_thinking_style(self, style: str):
        """Set thinking visualization style"""
        if style in ["chain", "tree", "mindmap"]:
            self.thinking_style = style
            logger.info(f"Thinking style set to: {style}")
        else:
            logger.warning(f"Unknown thinking style: {style}")
    
    def toggle_thinking_mode(self, enabled: Optional[bool] = None):
        """Toggle thinking mode on/off"""
        if enabled is not None:
            self.thinking_enabled = enabled
        else:
            self.thinking_enabled = not self.thinking_enabled
        logger.info(f"Thinking mode {'enabled' if self.thinking_enabled else 'disabled'}")
    
    async def run_parallel_models(
        self,
        user_input: str,
        llm_clients: List,
        strategies: List[str] = None,
        aggregate_method: str = "vote"
    ) -> Dict[str, Any]:
        """Run multiple models in parallel and aggregate results
        
        Args:
            user_input: User's input message
            llm_clients: List of LLM clients to run in parallel
            strategies: Optional strategies for each model
            aggregate_method: Aggregation method ("vote", "ensemble", "best", "average")
        
        Returns:
            Dictionary with individual results and aggregated response
        """
        if not llm_clients:
            return {"error": "No LLM clients provided"}
        
        # Build prompts for all models
        prompts = []
        for i, client in enumerate(llm_clients):
            prompt = self._build_prompt(user_input)
            prompts.append((i, client, prompt))
        
        # Run all models in parallel
        tasks = []
        for i, client, prompt in prompts:
            task = asyncio.create_task(self._call_parallel_model(i, client, prompt))
            tasks.append(task)
        
        # Wait for all results
        results = await asyncio.gather(*tasks)
        
        # Organize results
        model_results = {}
        for result in results:
            model_name = result.get("model", f"model_{result['index']}")
            model_results[model_name] = result
        
        # Aggregate results
        aggregated = self._aggregate_results(model_results, aggregate_method)
        
        return {
            "individual_results": model_results,
            "aggregated": aggregated,
            "total_models": len(llm_clients),
            "aggregate_method": aggregate_method
        }
    
    async def _call_parallel_model(self, index: int, llm_client, prompt: str) -> Dict[str, Any]:
        """Call a single model in parallel"""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await llm_client.chat_completion(messages)
            
            model_name = getattr(llm_client, 'model', f"model_{index}")
            
            # Track cost if enabled
            if self.track_cost and hasattr(llm_client, 'get_last_usage'):
                usage = llm_client.get_last_usage()
                if usage:
                    self._update_cost(usage)
            
            return {
                "index": index,
                "model": model_name,
                "response": response,
                "success": True
            }
        except Exception as e:
            logger.error(f"Model {index} failed: {e}")
            return {
                "index": index,
                "model": getattr(llm_client, 'model', f"model_{index}"),
                "response": None,
                "error": str(e),
                "success": False
            }
    
    def _aggregate_results(self, model_results: Dict[str, Dict], method: str) -> Dict[str, Any]:
        """Aggregate results from multiple models
        
        Args:
            model_results: Dictionary of model results
            method: Aggregation method
        
        Returns:
            Aggregated result
        """
        successful_results = [
            r for r in model_results.values() if r.get("success") and r.get("response")
        ]
        
        if not successful_results:
            return {
                "error": "No successful model responses",
                "best_response": None,
                "votes": [],
                "confidence": 0.0
            }
        
        responses = [r["response"] for r in successful_results]
        models = [r["model"] for r in successful_results]
        
        if method == "vote":
            return self._vote_aggregation(responses, models)
        elif method == "ensemble":
            return self._ensemble_aggregation(responses, models)
        elif method == "best":
            return self._best_response(responses, models)
        else:
            return self._vote_aggregation(responses, models)
    
    def _vote_aggregation(self, responses: List[str], models: List[str]) -> Dict[str, Any]:
        """Aggregate by voting on similar responses"""
        # Simple voting: count response similarities
        # This is a simplified implementation
        
        # Group similar responses
        groups = []
        for i, response in enumerate(responses):
            found = False
            for group in groups:
                if self._responses_similar(response, group["responses"][0]):
                    group["responses"].append(response)
                    group["models"].append(models[i])
                    group["count"] += 1
                    found = True
                    break
            if not found:
                groups.append({
                    "responses": [response],
                    "models": [models[i]],
                    "count": 1
                })
        
        # Find winning group
        groups.sort(key=lambda x: x["count"], reverse=True)
        
        if groups:
            winner = groups[0]
            return {
                "method": "vote",
                "best_response": winner["responses"][0],
                "winning_models": winner["models"],
                "vote_count": winner["count"],
                "total_models": len(models),
                "confidence": winner["count"] / len(models),
                "groups": groups
            }
        
        return {"error": "No responses to aggregate"}
    
    def _ensemble_aggregation(self, responses: List[str], models: List[str]) -> Dict[str, Any]:
        """Aggregate by combining responses into a comprehensive answer"""
        # Combine all responses into one
        combined = "\n\n---\n\n".join([f"Model {models[i]}:\n{responses[i]}" for i in range(len(responses))])
        
        return {
            "method": "ensemble",
            "combined_response": combined,
            "sources": models,
            "total_models": len(models)
        }
    
    def _best_response(self, responses: List[str], models: List[str]) -> Dict[str, Any]:
        """Select the best response based on heuristic"""
        # Simple heuristic: longest response (assuming more detailed = better)
        best_idx = 0
        best_length = len(responses[0])
        
        for i, response in enumerate(responses[1:], 1):
            if len(response) > best_length:
                best_length = len(response)
                best_idx = i
        
        return {
            "method": "best",
            "best_response": responses[best_idx],
            "best_model": models[best_idx],
            "total_models": len(models),
            "confidence": 0.7  # Arbitrary confidence for single best selection
        }
    
    def _responses_similar(self, r1: str, r2: str, threshold: float = 0.7) -> bool:
        """Check if two responses are similar"""
        # Simple similarity check using common word count
        words1 = set(r1.lower().split())
        words2 = set(r2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        jaccard = len(intersection) / len(union)
        return jaccard >= threshold



import asyncio
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.integrations.nanobot.agent.loop import AgentLoop
from src.integrations.nanobot.agent.tools.base import BaseTool
from src.integrations.nanobot.manager import NanobotManager


class BrokenTool(BaseTool):
    name = "broken_tool"
    description = "Always raises exception"
    parameters = {"type": "object", "properties": {}}
    
    async def execute(self, **kwargs):
        raise ValueError("Intentional failure for testing self-improvement logging")

class MockLLMClient:
    async def chat_completion(self, messages):
        return "Mock response"

import logging

logging.basicConfig(level=logging.INFO)

async def test_self_improvement():
    print("Testing Nanobot Self-Improvement...")
    
    # Initialize manager
    manager = NanobotManager()
    
    # 1. Test Initialization Logging (should log a learning)
    print("\n1. Testing Initialization Logging...")
    await manager.initialize()
    print("Initialization complete.")
    
    # 2. Test Error Logging in AgentLoop
    print("\n2. Testing AgentLoop Error Logging...")
    
    # Create loop with mock client
    loop = AgentLoop(
        llm_client=MockLLMClient(),
        system_prompt="You are a test agent."
    )
    
    # Register broken tool
    loop.register_tool("broken_tool", BrokenTool())
    
    # Execute broken tool directly
    print("Executing broken_tool...")
    # _execute_action signature: async def _execute_action(self, action: str, action_input: Dict[str, Any]) -> str
    result = await loop._execute_action("broken_tool", {})
    print(f"Result: {result}")
    
    # 3. Check .learnings directory
    print("\n3. Checking .learnings directory...")
    learnings_dir = Path(".learnings")
    if not learnings_dir.exists():
        print("Error: .learnings directory does not exist!")
        return

    # List recent files in .learnings
    files = list(learnings_dir.glob("**/*"))
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print(f"Found {len(files)} files in .learnings. Most recent:")
    for f in files:
        if f.is_file() and f.name.endswith(".md"):
            print(f" - {f.name}")
            try:
                content = f.read_text(encoding='utf-8')
                # Check for specific strings we expect
                if "Intentional failure" in content:
                    print("   [SUCCESS] Found 'Intentional failure' in error log!")
                elif "initialization" in content and "LRN" in f.name:
                     print("   [SUCCESS] Found initialization log!")
            except Exception as e:
                print(f"   Error reading file: {e}")

    print("\nTest complete.")

if __name__ == "__main__":
    asyncio.run(test_self_improvement())

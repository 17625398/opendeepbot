import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.agents.draw.draw_agent import DrawAgent


class TestDrawAgent(unittest.TestCase):
    def setUp(self):
        self.agent = DrawAgent(language="zh")

    def test_generate_simple_prompt(self):
        async def run_test():
            # Mock get_prompt to ensure we have a system prompt
            with patch.object(self.agent, 'get_prompt', return_value="System Prompt"):
                # Mock llm_complete
                with patch("src.agents.draw.draw_agent.llm_complete", new_callable=AsyncMock) as mock_llm:
                    mock_llm.return_value = "<mxGraphModel>...</mxGraphModel>"
                    
                    messages = [{"role": "user", "content": "Draw a flowchart"}]
                    result = await self.agent.generate(messages)
                    
                    self.assertEqual(result, "<mxGraphModel>...</mxGraphModel>")
                    
                    # Verify arguments
                    call_args = mock_llm.call_args
                    self.assertIsNotNone(call_args)
                    kwargs = call_args[1]
                    
                    # Check messages are passed and contain system prompt
                    sent_messages = kwargs["messages"]
                    self.assertEqual(len(sent_messages), 2)
                    self.assertEqual(sent_messages[0]["role"], "system")
                    self.assertEqual(sent_messages[0]["content"], "System Prompt")
                    self.assertEqual(sent_messages[1]["content"], "Draw a flowchart")

        asyncio.run(run_test())

    def test_generate_with_context(self):
        async def run_test():
             with patch.object(self.agent, 'get_prompt', return_value="System Prompt"):
                with patch("src.agents.draw.draw_agent.llm_complete", new_callable=AsyncMock) as mock_llm:
                    mock_llm.return_value = "<mxGraphModel>updated</mxGraphModel>"
                    
                    messages = [
                        {"role": "user", "content": "Add a node\n\nCurrent Diagram XML (modify this):\n```xml\n<root/>\n```"}
                    ]
                    
                    result = await self.agent.generate(messages)
                    self.assertEqual(result, "<mxGraphModel>updated</mxGraphModel>")
                    
                    # Verify system prompt was added automatically
                    kwargs = mock_llm.call_args[1]
                    sent_messages = kwargs["messages"]
                    self.assertTrue(any(m["role"] == "system" for m in sent_messages))

        asyncio.run(run_test())
        
    def test_prompt_loading(self):
        # Verify that the real prompt file is loaded correctly
        # This relies on the actual file system and PromptManager
        system_prompt = self.agent.get_prompt("system_prompt")
        self.assertIsNotNone(system_prompt, "System prompt should be loaded from file")
        self.assertIn("Draw.io", system_prompt, "System prompt should contain 'Draw.io'")

if __name__ == '__main__':
    unittest.main()

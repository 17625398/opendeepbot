
import asyncio
from pathlib import Path
import sys

# Add project root to path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.agents.assistant.assistant_agent import AssistantAgent


async def test_chat():
    print("Initializing AssistantAgent...")
    try:
        agent = AssistantAgent()
        print("AssistantAgent initialized.")
    except Exception as e:
        print(f"Failed to initialize AssistantAgent: {e}")
        return

    query = "Hello, who are you?"
    history = []
    
    print(f"Sending query: {query}")
    try:
        async for chunk in agent.chat(query, history):
            print(chunk, end="", flush=True)
        print("\nChat completed successfully.")
    except TypeError as e:
        print(f"\nCaught expected TypeError if bug exists: {e}")
    except Exception as e:
        print(f"\nCaught unexpected exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())

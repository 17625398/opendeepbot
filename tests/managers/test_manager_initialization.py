"""Test manager initialization."""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv()

from src.agents.managers import (
    LLMManager,
    ConfigManager,
    MemoryManager,
    StudioManager,
    PerformanceMonitor,
)


async def test_llm_manager():
    """Test LLM Manager initialization."""
    print("Testing LLM Manager...")
    
    llm_mgr = LLMManager(
        module_name="test",
        agent_name="test_agent",
        api_key=os.getenv("OPENAI_API_KEY", "test"),
        base_url=os.getenv("LLM_HOST", "https://api.openai.com/v1"),
        model=os.getenv("LLM_MODEL", "gpt-4o"),
    )
    
    print(f"✓ LLM Manager initialized")
    print(f"  Temperature: {llm_mgr.get_temperature()}")
    print(f"  Max tokens: {llm_mgr.get_max_tokens()}")
    
    return llm_mgr


def test_config_manager():
    """Test Config Manager initialization."""
    print("\nTesting Config Manager...")
    
    config_mgr = ConfigManager(
        module_name="solve",
        agent_name="solve_agent",
    )
    
    print(f"✓ Config Manager initialized")
    print(f"  Temperature: {config_mgr.get_temperature()}")
    print(f"  Max tokens: {config_mgr.get_max_tokens()}")
    
    return config_mgr


def test_memory_manager():
    """Test Memory Manager initialization."""
    print("\nTesting Memory Manager...")
    
    memory_mgr = MemoryManager(
        memory_config={
            "enabled": False,  # Disabled for test
        }
    )
    
    print(f"✓ Memory Manager initialized")
    print(f"  Enabled: {memory_mgr.is_enabled()}")
    
    return memory_mgr


def test_studio_manager():
    """Test Studio Manager initialization."""
    print("\nTesting Studio Manager...")
    
    studio_mgr = StudioManager()
    
    print(f"✓ Studio Manager initialized")
    print(f"  Enabled: {studio_mgr.is_enabled()}")
    
    return studio_mgr


def test_performance_monitor():
    """Test Performance Monitor initialization."""
    print("\nTesting Performance Monitor...")
    
    perf_mon = PerformanceMonitor(
        module_name="test",
        agent_name="test_agent",
    )
    
    print(f"✓ Performance Monitor initialized")
    perf_mon.print_summary()
    
    return perf_mon


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Manager Initialization Tests")
    print("=" * 60)
    
    try:
        # Test all managers
        await test_llm_manager()
        test_config_manager()
        test_memory_manager()
        test_studio_manager()
        test_performance_monitor()
        
        print("\n" + "=" * 60)
        print("✓ All manager tests passed!")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

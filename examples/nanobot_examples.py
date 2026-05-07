#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NanoBot Integration Examples
=============================

Comprehensive examples for using NanoBot with DeepTutor.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================
# Example 1: Basic Chat
# ============================================

async def example_basic_chat():
    """Basic chat with NanoBot adapter."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Chat")
    print("=" * 60)
    
    from src.integrations.nanobot import NanoBotAdapter
    
    # Create adapter
    adapter = NanoBotAdapter(kb_name="my_textbook")
    
    # Simple chat
    response = await adapter.chat("什么是机器学习？")
    print(f"Response: {response}")
    
    # Chat with specific KB
    response = await adapter.chat(
        "解释神经网络",
        kb_name="deep_learning"
    )
    print(f"Response: {response}")


# ============================================
# Example 2: Knowledge Search
# ============================================

async def example_knowledge_search():
    """Search knowledge base with formatting."""
    print("\n" + "=" * 60)
    print("Example 2: Knowledge Search")
    print("=" * 60)
    
    from src.integrations.nanobot import NanoBotAdapter
    
    adapter = NanoBotAdapter(kb_name="research_papers")
    
    # Search knowledge
    result = await adapter.search_knowledge(
        query="深度学习的最新进展",
        mode="hybrid"
    )
    
    print(f"Query: {result['query']}")
    print(f"KB: {result['kb_name']}")
    print(f"Mode: {result['mode']}")
    print(f"\nFormatted Result:\n{result['formatted_result']}")


# ============================================
# Example 3: Problem Solving
# ============================================

async def example_problem_solving():
    """Solve problems with context from knowledge base."""
    print("\n" + "=" * 60)
    print("Example 3: Problem Solving")
    print("=" * 60)
    
    from src.integrations.nanobot import NanoBotAdapter
    
    adapter = NanoBotAdapter(kb_name="math_textbook")
    
    # Solve problem
    result = await adapter.solve_problem(
        question="计算线性卷积 x=[1,2,3] 和 h=[4,5]"
    )
    
    print(f"Question: {result['question']}")
    print(f"KB Used: {result['kb_used']}")
    print(f"Method: {result['method']}")
    print(f"\nSolution:\n{result['solution']}")


# ============================================
# Example 4: Lightweight Mode
# ============================================

async def example_lightweight_mode():
    """Use lightweight adapter for resource-constrained environments."""
    print("\n" + "=" * 60)
    print("Example 4: Lightweight Mode")
    print("=" * 60)
    
    from src.integrations.nanobot.adapter import NanoBotLiteAdapter
    
    # Create lite adapter
    adapter = NanoBotLiteAdapter(kb_name="quick_reference")
    
    # Chat (without heavy RAG operations)
    response = await adapter.chat("快速问题")
    print(f"Response: {response}")
    
    # Check status
    status = adapter.get_status()
    print(f"\nAdapter Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")


# ============================================
# Example 5: Service Layer
# ============================================

async def example_service_layer():
    """Use NanoBot service for unified interface."""
    print("\n" + "=" * 60)
    print("Example 5: Service Layer")
    print("=" * 60)
    
    from src.integrations.nanobot import NanoBotService
    
    # Create service
    service = NanoBotService(lite_mode=False)
    
    # Chat
    response = await service.chat("Hello from service")
    print(f"Chat Response: {response}")
    
    # Search
    result = await service.search_knowledge("test query")
    print(f"Search Result: {result}")
    
    # Get status
    status = service.get_status()
    print(f"\nService Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")


# ============================================
# Example 6: Multi-User Sessions
# ============================================

async def example_multi_user_sessions():
    """Manage multiple user sessions."""
    print("\n" + "=" * 60)
    print("Example 6: Multi-User Sessions")
    print("=" * 60)
    
    from src.integrations.nanobot import NanoBotAdapter
    
    class SessionManager:
        def __init__(self):
            self.sessions = {}
        
        def get_adapter(self, user_id: int, kb_name: str = "default"):
            if user_id not in self.sessions:
                self.sessions[user_id] = NanoBotAdapter(kb_name=kb_name)
            return self.sessions[user_id]
        
        def get_session_count(self):
            return len(self.sessions)
    
    # Create manager
    manager = SessionManager()
    
    # User 1
    adapter1 = manager.get_adapter(user_id=123, kb_name="kb1")
    response1 = await adapter1.chat("User 1 message")
    print(f"User 1: {response1}")
    
    # User 2
    adapter2 = manager.get_adapter(user_id=456, kb_name="kb2")
    response2 = await adapter2.chat("User 2 message")
    print(f"User 2: {response2}")
    
    print(f"\nActive Sessions: {manager.get_session_count()}")


# ============================================
# Example 7: Error Handling
# ============================================

async def example_error_handling():
    """Robust error handling."""
    print("\n" + "=" * 60)
    print("Example 7: Error Handling")
    print("=" * 60)
    
    from src.integrations.nanobot import NanoBotAdapter
    
    adapter = NanoBotAdapter(kb_name="test_kb")
    
    async def safe_chat(message: str):
        try:
            # Try with RAG
            return await adapter.chat(message, use_rag=True)
        except Exception as e:
            print(f"RAG failed: {e}, trying without RAG...")
            try:
                # Fallback to no RAG
                return await adapter.chat(message, use_rag=False)
            except Exception as e2:
                print(f"Chat failed: {e2}")
                return "抱歉，服务暂时不可用"
    
    # Test with various inputs
    messages = [
        "正常消息",
        "",  # 空消息
        "x" * 10000,  # 超长消息
    ]
    
    for msg in messages:
        response = await safe_chat(msg)
        print(f"Message: {msg[:50]}... -> Response: {response[:50]}...")


# ============================================
# Example 8: Batch Processing
# ============================================

async def example_batch_processing():
    """Process multiple messages in batch."""
    print("\n" + "=" * 60)
    print("Example 8: Batch Processing")
    print("=" * 60)
    
    from src.integrations.nanobot import NanoBotAdapter
    import time
    
    adapter = NanoBotAdapter(kb_name="batch_kb")
    
    messages = [
        "问题 1",
        "问题 2",
        "问题 3",
        "问题 4",
        "问题 5",
    ]
    
    # Sequential processing
    start = time.time()
    sequential_results = []
    for msg in messages:
        response = await adapter.chat(msg)
        sequential_results.append(response)
    sequential_time = time.time() - start
    
    # Parallel processing
    start = time.time()
    tasks = [adapter.chat(msg) for msg in messages]
    parallel_results = await asyncio.gather(*tasks)
    parallel_time = time.time() - start
    
    print(f"Sequential: {sequential_time:.2f}s")
    print(f"Parallel: {parallel_time:.2f}s")
    print(f"Speedup: {sequential_time/parallel_time:.2f}x")


# ============================================
# Example 9: Custom Adapter
# ============================================

async def example_custom_adapter():
    """Create custom adapter with additional features."""
    print("\n" + "=" * 60)
    print("Example 9: Custom Adapter")
    print("=" * 60)
    
    from src.integrations.nanobot import NanoBotAdapter
    
    class CustomAdapter(NanoBotAdapter):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.message_count = 0
        
        async def chat(self, message: str, **kwargs):
            # Pre-processing
            self.message_count += 1
            message = message.strip().lower()
            
            # Log
            print(f"[Message #{self.message_count}] Processing: {message}")
            
            # Call parent
            response = await super().chat(message, **kwargs)
            
            # Post-processing
            response = f"[{self.message_count}] {response}"
            
            return response
    
    # Use custom adapter
    adapter = CustomAdapter(kb_name="custom_kb")
    
    response1 = await adapter.chat("First message")
    print(f"Response: {response1}")
    
    response2 = await adapter.chat("Second message")
    print(f"Response: {response2}")
    
    print(f"\nTotal messages: {adapter.message_count}")


# ============================================
# Example 10: Telegram Bot Simulation
# ============================================

async def example_telegram_bot_simulation():
    """Simulate Telegram bot interaction."""
    print("\n" + "=" * 60)
    print("Example 10: Telegram Bot Simulation")
    print("=" * 60)
    
    from src.integrations.nanobot import DeepTutorTelegramBot
    
    # Create bot (without actual Telegram connection)
    bot = DeepTutorTelegramBot(
        token="dummy_token",
        allowed_users=[123456789],
        default_kb="telegram_kb"
    )
    
    # Simulate user messages
    user_id = 123456789
    
    messages = [
        "/start",
        "/search 机器学习",
        "/kb my_textbook",
        "/status",
        "普通聊天消息",
        "/help",
    ]
    
    for msg in messages:
        print(f"\nUser: {msg}")
        response = await bot.handle_message(msg, user_id)
        print(f"Bot: {response}")


# ============================================
# Example 11: Performance Monitoring
# ============================================

async def example_performance_monitoring():
    """Monitor adapter performance."""
    print("\n" + "=" * 60)
    print("Example 11: Performance Monitoring")
    print("=" * 60)
    
    from src.integrations.nanobot import NanoBotAdapter
    import time
    
    class MonitoredAdapter(NanoBotAdapter):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.stats = {
                "total_requests": 0,
                "total_time": 0,
                "errors": 0,
            }
        
        async def chat(self, message: str, **kwargs):
            self.stats["total_requests"] += 1
            start = time.time()
            
            try:
                response = await super().chat(message, **kwargs)
                duration = time.time() - start
                self.stats["total_time"] += duration
                return response
            except Exception as e:
                self.stats["errors"] += 1
                raise
        
        def get_stats(self):
            avg_time = (
                self.stats["total_time"] / self.stats["total_requests"]
                if self.stats["total_requests"] > 0
                else 0
            )
            return {
                **self.stats,
                "avg_time": avg_time,
            }
    
    # Use monitored adapter
    adapter = MonitoredAdapter(kb_name="monitor_kb")
    
    # Send some messages
    for i in range(5):
        await adapter.chat(f"Message {i+1}")
    
    # Get statistics
    stats = adapter.get_stats()
    print("\nPerformance Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


# ============================================
# Example 12: Quick Chat Function
# ============================================

async def example_quick_chat():
    """Use convenience quick_chat function."""
    print("\n" + "=" * 60)
    print("Example 12: Quick Chat Function")
    print("=" * 60)
    
    from src.integrations.nanobot import quick_chat
    
    # Quick chat without creating adapter manually
    response1 = await quick_chat("Hello")
    print(f"Response 1: {response1}")
    
    # With specific KB
    response2 = await quick_chat("Question", kb_name="specific_kb")
    print(f"Response 2: {response2}")


# ============================================
# Main Function
# ============================================

async def main():
    """Run all examples."""
    print("=" * 60)
    print("NanoBot Integration Examples")
    print("=" * 60)
    
    examples = [
        ("Basic Chat", example_basic_chat),
        ("Knowledge Search", example_knowledge_search),
        ("Problem Solving", example_problem_solving),
        ("Lightweight Mode", example_lightweight_mode),
        ("Service Layer", example_service_layer),
        ("Multi-User Sessions", example_multi_user_sessions),
        ("Error Handling", example_error_handling),
        ("Batch Processing", example_batch_processing),
        ("Custom Adapter", example_custom_adapter),
        ("Telegram Bot Simulation", example_telegram_bot_simulation),
        ("Performance Monitoring", example_performance_monitoring),
        ("Quick Chat Function", example_quick_chat),
    ]
    
    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n✗ Example '{name}' failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

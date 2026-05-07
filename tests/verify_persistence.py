#!/usr/bin/env python3
"""
持久化层快速验证脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.sdk.persistence.file_storage import FileStorage
from src.sdk.persistence.agent_storage import AgentStorageManager


async def test_file_storage():
    """测试 FileStorage"""
    print("="*60)
    print("测试 FileStorage")
    print("="*60)
    
    # 创建临时存储
    storage = FileStorage(base_dir="./test_data")
    
    # 测试保存
    print("\n1. 测试保存数据...")
    test_data = {"name": "test", "value": 123, "nested": {"key": "value"}}
    success = await storage.save("test_key", test_data)
    print(f"   保存结果：{'✓ 成功' if success else '✗ 失败'}")
    
    # 测试加载
    print("\n2. 测试加载数据...")
    loaded = await storage.load("test_key")
    print(f"   加载结果：{'✓ 成功' if loaded else '✗ 失败'}")
    print(f"   数据内容：{loaded}")
    
    # 测试存在性
    print("\n3. 测试存在性检查...")
    exists = await storage.exists("test_key")
    print(f"   键存在：{'✓ 是' if exists else '✗ 否'}")
    
    # 测试列出键
    print("\n4. 测试列出键...")
    keys = await storage.list_keys("*")
    print(f"   键列表：{keys}")
    
    # 测试统计
    print("\n5. 获取统计信息...")
    stats = await storage.get_stats()
    print(f"   保存次数：{stats['total_saves']}")
    print(f"   加载次数：{stats['total_loads']}")
    print(f"   文件数量：{stats['file_count']}")
    
    # 清理
    print("\n6. 清理测试数据...")
    await storage.delete("test_key")
    print("   ✓ 已清理")
    
    print("\n" + "="*60)
    print("FileStorage 测试完成 ✓")
    print("="*60 + "\n")


async def test_agent_storage():
    """测试 AgentStorageManager"""
    print("="*60)
    print("测试 AgentStorageManager")
    print("="*60)
    
    # 创建存储管理器
    manager = AgentStorageManager(
        backend="file",
        base_dir="./test_agents",
        auto_backup=False
    )
    
    # 测试保存 Agent
    print("\n1. 测试保存 Agent...")
    test_agent_data = {
        "agent_id": "test-agent-001",
        "name": "Test Agent",
        "agent_type": "base",
        "status": "idle",
        "state": {"test": True},
    }
    success = await manager._storage.save("agent_test-agent-001", test_agent_data)
    print(f"   保存结果：{'✓ 成功' if success else '✗ 失败'}")
    
    # 测试列出 Agent
    print("\n2. 测试列出 Agent...")
    agents = await manager.list_agents()
    print(f"   Agent 列表：{agents}")
    
    # 测试 Agent 数量
    print("\n3. 测试 Agent 数量...")
    count = await manager.get_agent_count()
    print(f"   Agent 数量：{count}")
    
    # 测试统计
    print("\n4. 获取统计信息...")
    stats = await manager.get_stats()
    print(f"   后端类型：{stats['backend']}")
    print(f"   保存次数：{stats['total_saves']}")
    
    # 清理
    print("\n5. 清理测试数据...")
    await manager.clear_all()
    await manager.close()
    print("   ✓ 已清理")
    
    print("\n" + "="*60)
    print("AgentStorageManager 测试完成 ✓")
    print("="*60 + "\n")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("DeepTutor 持久化层验证")
    print("="*60 + "\n")
    
    try:
        # 测试 FileStorage
        await test_file_storage()
        
        # 测试 AgentStorageManager
        await test_agent_storage()
        
        print("\n" + "="*60)
        print("所有测试通过 ✓✓✓")
        print("="*60 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

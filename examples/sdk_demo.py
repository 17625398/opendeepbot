#!/usr/bin/env python3
"""
DeepTutor SDK 快速演示

此脚本演示如何使用 DeepTutor SDK：
1. 注册 Agent 类型
2. 创建 Agent 实例
3. 执行任务
4. 监控状态
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from src.sdk.agent import BaseAgent, AgentConfig
from src.sdk.registry import AgentRegistry


# ============================================================================
# 注册示例 Agent
# ============================================================================

@AgentRegistry.register("demo_worker")
class DemoWorkerAgent(BaseAgent):
    """演示 Worker Agent"""
    
    async def execute(self, task):
        print(f"  🤖 Worker 执行任务：{task.get('description', 'Unknown')}")
        await asyncio.sleep(0.5)  # 模拟执行
        return {
            "status": "success",
            "message": "任务完成",
            "worker": self.name,
        }


@AgentRegistry.register("demo_manager")
class DemoManagerAgent(BaseAgent):
    """演示 Manager Agent"""
    
    async def execute(self, task):
        print(f"  🤖 Manager 协调任务：{task.get('description', 'Unknown')}")
        await asyncio.sleep(0.3)  # 模拟协调
        return {
            "status": "success",
            "message": "任务已分配",
            "manager": self.name,
        }


# ============================================================================
# 演示函数
# ============================================================================

async def demo():
    """运行演示"""
    print("\n" + "="*70)
    print(f"{Colors.BOLD}{Colors.CYAN}DeepTutor SDK 快速演示{Colors.ENDC}")
    print("="*70 + "\n")
    
    # Step 1: 查看统计
    print(f"{Colors.BOLD}Step 1: 查看注册中心统计{Colors.ENDC}")
    print("-" * 70)
    stats = AgentRegistry.get_stats()
    print(f"  注册类型数：{stats['registered_types']}")
    print(f"  活动实例数：{stats['active_instances']}")
    print(f"  已注册类型：{', '.join(stats['types']) if stats['types'] else '无'}")
    print()
    
    # Step 2: 创建 Agent
    print(f"{Colors.BOLD}Step 2: 创建 Agent 实例{Colors.ENDC}")
    print("-" * 70)
    
    manager_config = AgentConfig(
        name="demo_manager",
        agent_type="demo_manager",
        skills=["coordination", "planning"],
        description="演示用 Manager Agent"
    )
    manager = AgentRegistry.create("demo_manager", manager_config)
    print(f"  ✓ Manager: {manager.name} (ID: {manager.agent_id[:8]}...)")
    
    worker1_config = AgentConfig(
        name="demo_worker_1",
        agent_type="demo_worker",
        skills=["coding", "testing"],
        description="演示用 Worker Agent 1"
    )
    worker1 = AgentRegistry.create("demo_worker", worker1_config)
    print(f"  ✓ Worker 1: {worker1.name} (ID: {worker1.agent_id[:8]}...)")
    
    worker2_config = AgentConfig(
        name="demo_worker_2",
        agent_type="demo_worker",
        skills=["documentation", "review"],
        description="演示用 Worker Agent 2"
    )
    worker2 = AgentRegistry.create("demo_worker", worker2_config)
    print(f"  ✓ Worker 2: {worker2.name} (ID: {worker2.agent_id[:8]}...)")
    
    print(f"\n  当前活动实例数：{len(AgentRegistry.list_instances())}")
    print()
    
    # Step 3: 执行任务
    print(f"{Colors.BOLD}Step 3: 执行任务{Colors.ENDC}")
    print("-" * 70)
    
    manager_task = {
        "description": "开发新功能模块",
        "requirements": ["代码实现", "测试", "文档"],
    }
    print(f"  任务：{manager_task['description']}")
    manager_result = await manager.execute(manager_task)
    print(f"  结果：{manager_result['message']}")
    print()
    
    worker_task = {
        "description": "实现用户认证功能",
        "code": "def authenticate(user, password): ...",
    }
    print(f"  任务：{worker_task['description']}")
    worker1_result = await worker1.execute(worker_task)
    print(f"  结果：{worker1_result['message']}")
    print()
    
    # Step 4: 查看状态
    print(f"{Colors.BOLD}Step 4: 查看 Agent 状态{Colors.ENDC}")
    print("-" * 70)
    
    print(f"  Manager 状态:")
    manager_status = manager.get_status()
    print(f"    - 名称：{manager_status['name']}")
    print(f"    - 状态：{manager_status['status']}")
    print(f"    - 执行次数：{manager_status['execution_count']}")
    print()
    
    print(f"  Worker 1 状态:")
    worker1_status = worker1.get_status()
    print(f"    - 名称：{worker1_status['name']}")
    print(f"    - 状态：{worker1_status['status']}")
    print(f"    - 执行次数：{worker1_status['execution_count']}")
    print()
    
    # Step 5: 查看性能指标
    print(f"{Colors.BOLD}Step 5: 查看性能指标{Colors.ENDC}")
    print("-" * 70)
    
    print(f"  Manager 指标:")
    manager_metrics = manager.get_metrics()
    print(f"    - 成功率：{manager_metrics['success_rate']*100:.1f}%")
    print(f"    - 执行次数：{manager_metrics['execution_count']}")
    print(f"    - 错误次数：{manager_metrics['error_count']}")
    print()
    
    print(f"  Worker 1 指标:")
    worker1_metrics = worker1.get_metrics()
    print(f"    - 成功率：{worker1_metrics['success_rate']*100:.1f}%")
    print(f"    - 执行次数：{worker1_metrics['execution_count']}")
    print(f"    - 错误次数：{worker1_metrics['error_count']}")
    print()
    
    # Step 6: 列出所有 Agent
    print(f"{Colors.BOLD}Step 6: 列出所有 Agent{Colors.ENDC}")
    print("-" * 70)
    
    instances = AgentRegistry.list_instances()
    print(f"  共 {len(instances)} 个 Agent 实例:")
    for agent_id in instances:
        agent = AgentRegistry.get(agent_id)
        if agent:
            print(f"    • {agent.name} ({agent.agent_type}) - {agent.status.value}")
    print()
    
    # Step 7: 清理
    print(f"{Colors.BOLD}Step 7: 清理资源{Colors.ENDC}")
    print("-" * 70)
    
    for agent_id in instances:
        AgentRegistry.unregister(agent_id)
    print(f"  ✓ 已清理所有 Agent 实例")
    
    final_stats = AgentRegistry.get_stats()
    print(f"  当前活动实例数：{final_stats['active_instances']}")
    print()
    
    print("="*70)
    print(f"{Colors.GREEN}{Colors.BOLD}✓ 演示完成!{Colors.ENDC}")
    print("="*70 + "\n")


class Colors:
    """终端颜色"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'


# ============================================================================
# 主函数
# ============================================================================

if __name__ == "__main__":
    try:
        asyncio.run(demo())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠  演示被中断{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}❌ 错误：{str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

"""
多 Agent 协调技能使用示例

这个示例展示了如何在 DeepTutor 中使用多 Agent 协作模式：
- 编排器模式 (OrchestratorPattern)
- 点对点模式 (PeerToPeerPattern)
- 层次化模式 (HierarchicalPattern)

运行说明:
    1. 确保已安装 DeepTutor 依赖
    2. 从项目根目录运行: python examples/skills/multi_agent_example.py
    3. 或直接运行: python multi_agent_example.py

功能演示:
    - 编排器模式：任务分解、分配和结果汇总
    - 点对点模式：Agent 间直接通信和共识达成
    - 层次化模式：树状结构的任务委派和结果上报
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.multi_agent.patterns import (
    OrchestratorPattern,
    PeerToPeerPattern,
    HierarchicalPattern,
    Task,
    TaskStatus,
)
from src.agents.multi_agent.communication import Message, MessageType, Priority


class MockAgent:
    """模拟 Agent 用于演示"""

    def __init__(self, name: str, capability: str = "general"):
        self.name = name
        self.capability = capability
        self.task_count = 0

    async def process(self, task_data: Any) -> Any:
        """处理任务"""
        self.task_count += 1
        await asyncio.sleep(0.1)  # 模拟处理时间

        return {
            "agent": self.name,
            "capability": self.capability,
            "task": task_data,
            "status": "completed",
            "result": f"{self.name} 处理完成: {str(task_data)[:50]}..."
        }

    def __repr__(self):
        return f"MockAgent({self.name}, {self.capability})"


async def demonstrate_orchestrator_pattern():
    """演示编排器模式"""
    print("=" * 60)
    print("演示 1: 编排器模式 (OrchestratorPattern)")
    print("=" * 60)
    print("\n模式说明:")
    print("  - 一个编排器 Agent 协调多个工作 Agent")
    print("  - 任务分解 -> 分配 -> 执行 -> 汇总")
    print("  - 适合复杂任务的并行处理")

    # 创建编排器
    orchestrator = MockAgent("orchestrator", "coordination")

    # 定义任务分解函数
    def decompose_task(task_data: Dict[str, Any]) -> List[Task]:
        """将复杂任务分解为子任务"""
        document = task_data.get("document", "")
        tasks = []

        # 分解为多个子任务
        subtasks = [
            ("summarize", "生成文档摘要"),
            ("extract_keywords", "提取关键词"),
            ("analyze_sentiment", "情感分析"),
            ("check_grammar", "语法检查"),
        ]

        for i, (task_type, description) in enumerate(subtasks):
            tasks.append(Task(
                task_id=f"task_{i}",
                task_type=task_type,
                data={
                    "type": task_type,
                    "description": description,
                    "document": document[:100] + "..."
                },
                priority=Priority.HIGH if i < 2 else Priority.NORMAL
            ))

        return tasks

    # 定义结果聚合函数
    def aggregate_results(results: List[Any]) -> Dict[str, Any]:
        """聚合子任务结果"""
        successful = [r for r in results if isinstance(r, dict) and r.get("success", True)]
        failed = [r for r in results if isinstance(r, dict) and not r.get("success", True)]

        return {
            "total_tasks": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
            "summary": f"完成 {len(successful)}/{len(results)} 个任务"
        }

    # 创建编排器模式
    pattern = OrchestratorPattern(
        orchestrator=orchestrator,
        task_decomposer=decompose_task,
        result_aggregator=aggregate_results,
        max_concurrent_tasks=3
    )

    # 添加工作 Agent
    workers = [
        MockAgent("worker_1", "summarization"),
        MockAgent("worker_2", "keyword_extraction"),
        MockAgent("worker_3", "sentiment_analysis"),
        MockAgent("worker_4", "grammar_check"),
    ]

    for i, worker in enumerate(workers):
        pattern.add_worker(f"worker_{i+1}", worker)

    print(f"\n📋 已注册 {len(workers)} 个工作 Agent:")
    for worker_id in pattern.list_workers():
        print(f"  - {worker_id}")

    # 执行复杂任务
    print("\n🚀 执行文档分析任务:")
    document = """
    人工智能正在深刻改变我们的世界。机器学习、深度学习等技术在图像识别、
    自然语言处理等领域取得了突破性进展。未来，AI将继续向更通用、更可信的
    方向发展，为人类社会带来更多福祉。
    """

    result = await pattern.execute_task(
        {"document": document, "operation": "comprehensive_analysis"},
        decompose=True,
        timeout=30.0
    )

    print(f"\n📊 执行结果:")
    print(f"  - 总任务数: {result['total_tasks']}")
    print(f"  - 成功: {result['successful']}")
    print(f"  - 失败: {result['failed']}")
    print(f"  - 摘要: {result['summary']}")

    # 获取模式状态
    status = await pattern.get_status()
    print(f"\n📈 模式状态:")
    print(f"  - 工作 Agent 数量: {status['worker_count']}")
    print(f"  - 最大并发: {status['max_concurrent']}")

    await pattern.stop()


async def demonstrate_peer_to_peer_pattern():
    """演示点对点模式"""
    print("\n" + "=" * 60)
    print("演示 2: 点对点模式 (PeerToPeerPattern)")
    print("=" * 60)
    print("\n模式说明:")
    print("  - Agent 之间直接通信，去中心化")
    print("  - 支持广播、共识、最近邻居等策略")
    print("  - 适合需要高度自治的场景")

    # 创建点对点模式
    pattern = PeerToPeerPattern(consensus_threshold=0.5)

    # 添加对等 Agent
    peers = [
        MockAgent("peer_a", "validation"),
        MockAgent("peer_b", "validation"),
        MockAgent("peer_c", "validation"),
        MockAgent("peer_d", "validation"),
    ]

    for i, peer in enumerate(peers):
        peer_id = f"peer_{chr(97+i)}"  # peer_a, peer_b, ...
        pattern.add_peer(peer_id, peer)

    print(f"\n📋 已添加 {len(peers)} 个对等 Agent:")
    for peer_id in pattern._peers.keys():
        print(f"  - {peer_id}")

    # 建立连接
    print("\n🔗 建立 Agent 间连接:")
    connections = [
        ("peer_a", "peer_b"),
        ("peer_b", "peer_c"),
        ("peer_c", "peer_d"),
        ("peer_d", "peer_a"),
    ]

    for peer_a, peer_b in connections:
        pattern.connect(peer_a, peer_b)
        print(f"  - {peer_a} <-> {peer_b}")

    # 显示每个 Agent 的连接
    print("\n📡 各 Agent 的连接情况:")
    for peer_id in pattern._peers.keys():
        connections = pattern.get_connections(peer_id)
        print(f"  - {peer_id}: 连接到 {len(connections)} 个 Agent")

    # 演示广播
    print("\n📢 广播任务:")
    task_data = {
        "type": "data_validation",
        "data": {"value": 42, "type": "integer"},
        "rules": ["non_negative", "integer"]
    }

    # 注意：实际使用时需要配置消息处理器
    # 这里仅演示 API 调用
    print(f"  任务内容: {task_data}")
    print(f"  广播给所有 Agent (示例代码)")

    # 演示直接发送
    print("\n📨 点对点消息发送:")
    sender = "peer_a"
    receiver = "peer_c"

    # 检查是否连接
    is_connected = pattern.is_connected(sender, receiver)
    print(f"  {sender} -> {receiver}: {'已连接' if is_connected else '未直接连接'}")

    # 如果不是直接连接，显示路径
    if not is_connected:
        print(f"  消息将通过中间节点转发")

    # 获取模式状态
    status = await pattern.get_status()
    print(f"\n📈 模式状态:")
    print(f"  - 对等 Agent 数量: {status['peer_count']}")
    print(f"  - 总连接数: {status['total_connections']}")
    print(f"  - 共识阈值: {status['consensus_threshold']}")

    await pattern.stop()


async def demonstrate_hierarchical_pattern():
    """演示层次化模式"""
    print("\n" + "=" * 60)
    print("演示 3: 层次化模式 (HierarchicalPattern)")
    print("=" * 60)
    print("\n模式说明:")
    print("  - 树状结构的 Agent 组织")
    print("  - 上层管理下层，任务逐级分解")
    print("  - 结果逐级汇总上报")
    print("  - 适合组织架构明确的任务")

    # 创建根节点
    root_agent = MockAgent("ceo", "decision_making")

    # 创建层次化模式
    pattern = HierarchicalPattern(
        root_agent=root_agent,
        max_depth=4
    )

    # 构建组织架构
    print("\n🏢 构建组织架构:")

    # 第一层：部门经理
    managers = [
        MockAgent("tech_manager", "tech_management"),
        MockAgent("product_manager", "product_management"),
    ]

    for manager in managers:
        pattern.add_child("root", manager.name, manager)
        print(f"  - CEO -> {manager.name}")

    # 第二层：团队负责人
    tech_leads = [
        MockAgent("backend_lead", "backend"),
        MockAgent("frontend_lead", "frontend"),
        MockAgent("ai_lead", "ai"),
    ]

    for lead in tech_leads:
        pattern.add_child("tech_manager", lead.name, lead)
        print(f"  - tech_manager -> {lead.name}")

    product_leads = [
        MockAgent("ux_lead", "ux_design"),
        MockAgent("pm_lead", "product"),
    ]

    for lead in product_leads:
        pattern.add_child("product_manager", lead.name, lead)
        print(f"  - product_manager -> {lead.name}")

    # 第三层：普通员工
    developers = [
        MockAgent("dev_1", "backend_dev"),
        MockAgent("dev_2", "backend_dev"),
        MockAgent("dev_3", "frontend_dev"),
    ]

    pattern.add_child("backend_lead", "dev_1", developers[0])
    pattern.add_child("backend_lead", "dev_2", developers[1])
    pattern.add_child("frontend_lead", "dev_3", developers[2])

    print(f"  - backend_lead -> dev_1, dev_2")
    print(f"  - frontend_lead -> dev_3")

    # 显示组织架构
    print("\n📊 组织架构统计:")
    print(f"  - 总节点数: {len(pattern._hierarchy)}")
    print(f"  - 树深度: {pattern.get_tree_depth()}")

    for level in range(pattern.get_tree_depth()):
        agents_at_level = pattern.get_agents_at_level(level)
        print(f"  - 第 {level} 层: {len(agents_at_level)} 个 Agent")

    # 显示层级关系
    print("\n👥 层级关系示例:")
    for node_id in ["tech_manager", "backend_lead", "dev_1"]:
        parent = pattern.get_parent(node_id)
        children = pattern.get_children(node_id)
        siblings = pattern.get_siblings(node_id)

        print(f"\n  {node_id}:")
        print(f"    父节点: {parent}")
        print(f"    子节点: {children}")
        print(f"    兄弟节点: {siblings}")

    # 演示任务委派
    print("\n🚀 演示任务委派流程:")
    print("  任务: 开发新功能模块")

    # 自顶向下执行
    task_data = {
        "name": "新功能开发",
        "requirements": ["用户认证", "数据存储", "API接口"],
        "deadline": "2024-12-31",
        "priority": "high"
    }

    print(f"\n  任务详情:")
    print(f"    名称: {task_data['name']}")
    print(f"    需求: {', '.join(task_data['requirements'])}")
    print(f"    截止日期: {task_data['deadline']}")

    # 模拟任务分解
    print("\n  任务分解过程:")
    print("    CEO 接收任务，分配给部门经理")
    print("    tech_manager 分配给技术团队")
    print("    backend_lead 分配给后端开发")
    print("    dev_1 和 dev_2 执行具体开发")

    # 获取模式状态
    status = await pattern.get_status()
    print(f"\n📈 模式状态:")
    print(f"  - 根节点: {status['root']}")
    print(f"  - 总节点数: {status['total_nodes']}")
    print(f"  - 树深度: {status['tree_depth']}")
    print(f"  - 每层节点数: {status['nodes_per_level']}")

    await pattern.stop()


async def demonstrate_task_management():
    """演示任务管理功能"""
    print("\n" + "=" * 60)
    print("演示 4: 任务管理")
    print("=" * 60)

    print("\n📋 任务生命周期:")

    # 创建任务
    task = Task(
        task_id="task_001",
        task_type="code_review",
        data={
            "file": "main.py",
            "lines": 150,
            "language": "python"
        },
        priority=Priority.HIGH,
        dependencies=["task_000"]  # 依赖前置任务
    )

    print(f"\n  创建任务:")
    print(f"    ID: {task.task_id}")
    print(f"    类型: {task.task_type}")
    print(f"    状态: {task.status.name}")
    print(f"    优先级: {task.priority.name}")
    print(f"    创建时间: {task.created_at}")
    print(f"    依赖: {task.dependencies}")

    # 模拟任务状态变化
    print(f"\n  状态变化:")

    task.status = TaskStatus.ASSIGNED
    task.assigned_to = "agent_1"
    print(f"    -> ASSIGNED (分配给 {task.assigned_to})")

    task.status = TaskStatus.RUNNING
    task.started_at = task.created_at
    print(f"    -> RUNNING (开始执行)")

    task.status = TaskStatus.COMPLETED
    task.completed_at = task.created_at
    task.result = {"review_comments": 5, "issues": ["line_10", "line_25"]}
    print(f"    -> COMPLETED (执行完成)")

    # 转换为字典
    task_dict = task.to_dict()
    print(f"\n  任务信息 (字典格式):")
    for key, value in task_dict.items():
        print(f"    {key}: {value}")


async def demonstrate_communication():
    """演示通信机制"""
    print("\n" + "=" * 60)
    print("演示 5: 通信机制")
    print("=" * 60)

    print("\n📨 消息类型:")

    message_types = [
        (MessageType.TASK, "任务消息"),
        (MessageType.RESULT, "结果消息"),
        (MessageType.BROADCAST, "广播消息"),
        (MessageType.HEARTBEAT, "心跳消息"),
        (MessageType.CUSTOM, "自定义消息"),
    ]

    for msg_type, description in message_types:
        print(f"  - {msg_type.value}: {description}")

    print("\n📢 创建消息示例:")

    # 任务消息
    task_msg = Message.create_task(
        sender="orchestrator",
        receiver="worker_1",
        task_data={"operation": "process", "data": "example"},
        priority=Priority.HIGH
    )
    print(f"\n  任务消息:")
    print(f"    发送者: {task_msg.sender}")
    print(f"    接收者: {task_msg.receiver}")
    print(f"    类型: {task_msg.msg_type.value}")
    print(f"    优先级: {task_msg.priority.name}")

    # 广播消息
    broadcast_msg = Message.create_broadcast(
        sender="peer_a",
        content={"announcement": "系统更新"},
        msg_type=MessageType.BROADCAST
    )
    print(f"\n  广播消息:")
    print(f"    发送者: {broadcast_msg.sender}")
    print(f"    接收者: {broadcast_msg.receiver}")
    print(f"    内容: {broadcast_msg.content}")

    # 结果消息
    result_msg = Message.create_result(
        sender="worker_1",
        receiver="orchestrator",
        result={"status": "success", "data": "processed"},
        task_id="task_001"
    )
    print(f"\n  结果消息:")
    print(f"    发送者: {result_msg.sender}")
    print(f"    接收者: {result_msg.receiver}")
    print(f"    任务ID: {result_msg.task_id}")
    print(f"    结果: {result_msg.content}")

    print("\n🔔 优先级级别:")
    priorities = [
        Priority.LOW,
        Priority.NORMAL,
        Priority.HIGH,
        Priority.CRITICAL,
    ]

    for priority in priorities:
        print(f"  - {priority.name}: 优先级值 {priority.value}")


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("DeepTutor 多 Agent 协调技能示例")
    print("=" * 60)
    print("\n本示例演示以下内容:")
    print("  1. 编排器模式 - 集中式任务协调")
    print("  2. 点对点模式 - 去中心化通信")
    print("  3. 层次化模式 - 树状组织架构")
    print("  4. 任务管理 - 任务生命周期")
    print("  5. 通信机制 - 消息类型和优先级")
    print()

    try:
        # 运行所有演示
        await demonstrate_orchestrator_pattern()
        await demonstrate_peer_to_peer_pattern()
        await demonstrate_hierarchical_pattern()
        await demonstrate_task_management()
        await demonstrate_communication()

        print("\n" + "=" * 60)
        print("✅ 所有演示完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

"""
记忆系统使用示例

这个示例展示了如何在 DeepTutor 中使用三种记忆系统：
- 短期记忆 (ShortTermMemory) - 会话期间保持，支持TTL过期
- 长期记忆 (LongTermMemory) - 持久化存储，支持JSON/SQLite后端
- 图记忆 (GraphMemory) - 图结构存储，支持关系查询和路径查找

运行说明:
    1. 确保已安装 DeepTutor 依赖
    2. 从项目根目录运行: python examples/skills/memory_usage_example.py
    3. 或直接运行: python memory_usage_example.py

功能演示:
    - 短期记忆：存储、检索、TTL过期、LRU淘汰、自动清理
    - 长期记忆：JSON/SQLite存储、持久化、备份恢复、相似度搜索
    - 图记忆：节点边管理、关系建模、路径查找、子图提取
"""

import asyncio
import sys
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.memory import (
    ShortTermMemory,
    LongTermMemory,
    GraphMemory,
    GraphNode,
    GraphEdge,
    EdgeType,
)
from src.agents.memory.base import (
    MemoryEntry,
    MemoryMetadata,
    MemoryType,
    MemoryQuery,
)
from src.agents.memory.long_term import StorageConfig


async def demonstrate_short_term_memory():
    """演示短期记忆使用"""
    print("=" * 60)
    print("演示 1: 短期记忆 (ShortTermMemory)")
    print("=" * 60)
    print("\n特性说明:")
    print("  - 会话期间保持信息")
    print("  - 支持TTL过期机制")
    print("  - LRU淘汰策略")
    print("  - 自动清理过期项")

    # 创建短期记忆实例（30秒TTL）
    stm = ShortTermMemory(ttl=30, max_size=100)

    print("\n📝 存储信息:")
    # 存储对话上下文
    await stm.store("user_name", "张三")
    await stm.store("current_topic", "Python编程")
    await stm.store("conversation_turn", "第5轮对话")
    await stm.store("user_preference", "喜欢详细解释")

    print("  - 用户名: 张三")
    print("  - 当前主题: Python编程")
    print("  - 对话轮次: 第5轮")
    print("  - 用户偏好: 喜欢详细解释")

    print("\n🔍 检索信息:")
    # 检索信息
    user_name = await stm.retrieve("user_name")
    topic = await stm.retrieve("current_topic")

    print(f"  - 用户名: {user_name.content if user_name else '未找到'}")
    print(f"  - 当前主题: {topic.content if topic else '未找到'}")

    print("\n📊 记忆统计:")
    stats = await stm.get_stats()
    print(f"  - 当前大小: {stats['size']}/{stats['max_size']}")
    print(f"  - TTL: {stats['ttl']}秒")
    print(f"  - 存储次数: {stats['store_count']}")
    print(f"  - 检索次数: {stats['retrieve_count']}")

    print("\n🗑️ 遗忘信息:")
    # 遗忘特定信息
    forgotten = await stm.forget("conversation_turn")
    print(f"  - 遗忘 'conversation_turn': {'成功' if forgotten else '失败'}")

    # 尝试检索已遗忘的信息
    result = await stm.retrieve("conversation_turn")
    print(f"  - 检索已遗忘项: {'找到' if result else '未找到'}")

    print("\n🧹 清空所有记忆:")
    await stm.clear()
    stats = await stm.get_stats()
    print(f"  - 清空后大小: {stats['size']}")


async def demonstrate_short_term_memory_ttl():
    """演示短期记忆TTL过期"""
    print("\n" + "=" * 60)
    print("演示 2: 短期记忆TTL过期机制")
    print("=" * 60)

    # 创建2秒TTL的短期记忆
    stm = ShortTermMemory(ttl=2, max_size=10)

    print("\n⏱️ 存储临时信息 (TTL=2秒):")
    await stm.store("temp_code", "x = 42")
    await stm.store("temp_result", "计算完成")

    print("  - 存储: temp_code = 'x = 42'")
    print("  - 存储: temp_result = '计算完成'")

    # 立即检索
    print("\n🔍 立即检索:")
    code = await stm.retrieve("temp_code")
    print(f"  - temp_code: {code.content if code else '未找到'}")

    # 等待3秒
    print("\n⏳ 等待3秒...")
    await asyncio.sleep(3)

    # 再次检索（应该已过期）
    print("\n🔍 过期后检索:")
    code = await stm.retrieve("temp_code")
    result = await stm.retrieve("temp_result")
    print(f"  - temp_code: {'找到' if code else '已过期'}")
    print(f"  - temp_result: {'找到' if result else '已过期'}")

    # 手动清理
    cleaned = await stm.cleanup()
    print(f"\n🧹 手动清理: 清理了 {cleaned} 个过期项")


async def demonstrate_short_term_memory_lru():
    """演示短期记忆LRU淘汰"""
    print("\n" + "=" * 60)
    print("演示 3: 短期记忆LRU淘汰")
    print("=" * 60)

    # 创建容量为3的短期记忆
    stm = ShortTermMemory(ttl=None, max_size=3)

    print("\n📦 存储3个项 (容量已满):")
    await stm.store("item_1", "第一个项目")
    await stm.store("item_2", "第二个项目")
    await stm.store("item_3", "第三个项目")

    print("  - item_1: 第一个项目")
    print("  - item_2: 第二个项目")
    print("  - item_3: 第三个项目")

    # 访问item_1，使其变为最近使用
    print("\n👆 访问 item_1 (使其变为最近使用):")
    await stm.retrieve("item_1")

    # 存储第4个项，应该淘汰最久未使用的item_2
    print("\n📝 存储第4个项 (触发LRU淘汰):")
    await stm.store("item_4", "第四个项目")
    print("  - item_4: 第四个项目")

    print("\n🔍 检查所有项:")
    for key in ["item_1", "item_2", "item_3", "item_4"]:
        result = await stm.retrieve(key)
        status = "✓ 存在" if result else "✗ 被淘汰"
        print(f"  - {key}: {status}")


async def demonstrate_long_term_memory_json():
    """演示长期记忆JSON存储"""
    print("\n" + "=" * 60)
    print("演示 4: 长期记忆 - JSON存储")
    print("=" * 60)

    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        config = StorageConfig(
            backend="json",
            path=tmpdir,
            auto_save=True,
        )

        ltm = LongTermMemory(config=config)
        await ltm.initialize()

        print("\n💾 存储长期记忆:")
        # 存储知识
        await ltm.store(
            "python_fact",
            "Python是一种高级编程语言，由Guido van Rossum于1991年创建。",
            metadata=MemoryMetadata(
                tags=["programming", "python", "fact"],
                importance=0.9,
            )
        )

        await ltm.store(
            "ai_concept",
            "人工智能是计算机科学的一个分支，致力于创造能够模拟人类智能的系统。",
            metadata=MemoryMetadata(
                tags=["ai", "concept", "computer_science"],
                importance=0.85,
            )
        )

        await ltm.store(
            "ml_definition",
            "机器学习是人工智能的子集，使计算机能够从数据中学习。",
            metadata=MemoryMetadata(
                tags=["ml", "ai", "definition"],
                importance=0.8,
            )
        )

        print("  - python_fact: Python语言介绍")
        print("  - ai_concept: AI概念定义")
        print("  - ml_definition: 机器学习定义")

        print("\n🔍 检索记忆:")
        fact = await ltm.retrieve("python_fact")
        if fact:
            print(f"  - python_fact: {fact.content[:40]}...")
            print(f"    标签: {fact.metadata.tags}")
            print(f"    重要性: {fact.metadata.importance}")

        print("\n📊 记忆统计:")
        print(f"  - 总记忆数: {ltm.size}")
        print(f"  - 存储后端: {ltm.config.backend}")

        # 关闭时自动保存
        await ltm.close()
        print("\n💾 数据已自动保存到JSON文件")


async def demonstrate_long_term_memory_sqlite():
    """演示长期记忆SQLite存储"""
    print("\n" + "=" * 60)
    print("演示 5: 长期记忆 - SQLite存储")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config = StorageConfig(
            backend="sqlite",
            path=tmpdir,
            auto_save=True,
        )

        ltm = LongTermMemory(config=config)
        await ltm.initialize()

        print("\n💾 存储带元数据的记忆:")
        # 存储用户偏好
        await ltm.store(
            "user_pref_language",
            "用户偏好使用中文进行交互",
            metadata=MemoryMetadata(
                tags=["preference", "language", "user"],
                user_id="user_123",
                importance=0.95,
            )
        )

        await ltm.store(
            "user_pref_theme",
            "用户偏好深色主题",
            metadata=MemoryMetadata(
                tags=["preference", "theme", "ui"],
                user_id="user_123",
                importance=0.7,
            )
        )

        print("  - user_pref_language: 中文交互偏好")
        print("  - user_pref_theme: 深色主题偏好")

        print("\n🔍 搜索记忆:")
        # 搜索包含"偏好"的记忆
        query = MemoryQuery(content="偏好", limit=10)
        results = await ltm.search(query)

        print(f"  - 找到 {len(results)} 个结果:")
        for result in results:
            print(f"    - {result.entry.content[:30]}... (分数: {result.score:.2f})")

        print("\n🏷️ 按标签搜索:")
        query = MemoryQuery(tags=["preference"], limit=10)
        results = await ltm.search(query)
        print(f"  - 标签 'preference' 找到 {len(results)} 个结果")

        await ltm.close()
        print("\n💾 数据已保存到SQLite数据库")


async def demonstrate_long_term_memory_backup():
    """演示长期记忆备份和恢复"""
    print("\n" + "=" * 60)
    print("演示 6: 长期记忆备份和恢复")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建并填充记忆
        config = StorageConfig(backend="json", path=tmpdir)
        ltm = LongTermMemory(config=config)
        await ltm.initialize()

        print("\n📝 创建原始数据:")
        await ltm.store("key_1", "重要数据1")
        await ltm.store("key_2", "重要数据2")
        await ltm.store("key_3", "重要数据3")
        print(f"  - 存储了 {ltm.size} 个记忆")

        # 备份
        backup_path = os.path.join(tmpdir, "backup.json")
        await ltm.backup(backup_path)
        print(f"\n💾 备份到: {backup_path}")

        # 添加更多数据
        await ltm.store("key_4", "新增数据4")
        print(f"\n📝 添加新数据后: {ltm.size} 个记忆")

        # 清空
        await ltm.clear()
        print(f"\n🗑️ 清空后: {ltm.size} 个记忆")

        # 恢复（合并模式）
        restored = await ltm.restore(backup_path, merge=True)
        print(f"\n📥 恢复（合并模式）: 恢复了 {restored} 个记忆")
        print(f"  - 当前总数: {ltm.size} 个记忆")

        # 再次清空并恢复（覆盖模式）
        await ltm.clear()
        await ltm.store("existing", "已存在的数据")
        restored = await ltm.restore(backup_path, merge=False)
        print(f"\n📥 恢复（覆盖模式）: 恢复了 {restored} 个记忆")
        print(f"  - 当前总数: {ltm.size} 个记忆")

        await ltm.close()


async def demonstrate_graph_memory_basic():
    """演示图记忆基础操作"""
    print("\n" + "=" * 60)
    print("演示 7: 图记忆 - 基础操作")
    print("=" * 60)

    gm = GraphMemory()

    print("\n🟢 添加节点:")
    # 添加概念节点
    python = await gm.add_node(
        label="Python",
        content="Python是一种高级编程语言",
        node_type="language",
        properties={"creator": "Guido van Rossum", "year": 1991}
    )

    ai = await gm.add_node(
        label="AI",
        content="人工智能是计算机科学的分支",
        node_type="concept",
        properties={"field": "computer_science"}
    )

    ml = await gm.add_node(
        label="Machine Learning",
        content="机器学习是AI的子集",
        node_type="concept",
        properties={"type": "subfield"}
    )

    print(f"  - Python ({python.id[:8]}...)")
    print(f"  - AI ({ai.id[:8]}...)")
    print(f"  - Machine Learning ({ml.id[:8]}...)")

    print("\n🔗 添加边（关系）:")
    # 添加关系
    edge1 = await gm.add_edge(
        python.id, ai.id,
        edge_type=EdgeType.RELATED,
        weight=0.8,
        properties={"relation": "used_in"}
    )

    edge2 = await gm.add_edge(
        ml.id, ai.id,
        edge_type=EdgeType.IS_A,
        weight=1.0,
        properties={}
    )

    edge3 = await gm.add_edge(
        python.id, ml.id,
        edge_type=EdgeType.RELATED,
        weight=0.9,
        bidirectional=True,
        properties={"usage": "implementation"}
    )

    print(f"  - Python -> AI (related, weight=0.8)")
    print(f"  - ML -> AI (is_a, weight=1.0)")
    print(f"  - Python <-> ML (related, bidirectional, weight=0.9)")

    print("\n📊 图统计:")
    print(f"  - 节点数: {gm.node_count}")
    print(f"  - 边数: {gm.edge_count}")

    print("\n🔍 检索节点:")
    node = await gm.get_node(python.id)
    if node:
        print(f"  - 标签: {node.label}")
        print(f"  - 类型: {node.node_type}")
        print(f"  - 属性: {node.properties}")


async def demonstrate_graph_memory_neighbors():
    """演示图记忆邻居查询"""
    print("\n" + "=" * 60)
    print("演示 8: 图记忆 - 邻居查询")
    print("=" * 60)

    gm = GraphMemory()

    print("\n🏗️ 构建知识图谱:")
    # 创建技术栈图谱
    frontend = await gm.add_node("Frontend", "前端开发技术", "technology")
    backend = await gm.add_node("Backend", "后端开发技术", "technology")
    database = await gm.add_node("Database", "数据库技术", "technology")
    react = await gm.add_node("React", "React前端框架", "framework")
    fastapi = await gm.add_node("FastAPI", "FastAPI后端框架", "framework")
    postgres = await gm.add_node("PostgreSQL", "PostgreSQL数据库", "database")

    # 建立关系
    await gm.add_edge(frontend.id, react.id, EdgeType.PART_OF, 1.0)
    await gm.add_edge(backend.id, fastapi.id, EdgeType.PART_OF, 1.0)
    await gm.add_edge(database.id, postgres.id, EdgeType.PART_OF, 1.0)
    await gm.add_edge(react.id, fastapi.id, EdgeType.DEPENDS_ON, 0.7)
    await gm.add_edge(fastapi.id, postgres.id, EdgeType.DEPENDS_ON, 0.8)

    print("  - 技术栈: Frontend -> React")
    print("  - 技术栈: Backend -> FastAPI")
    print("  - 技术栈: Database -> PostgreSQL")
    print("  - 依赖关系: React -> FastAPI -> PostgreSQL")

    print("\n👥 查询邻居节点:")
    # 查询Frontend的邻居
    neighbors = await gm.get_neighbors(frontend.id)
    print(f"  Frontend 的邻居:")
    for node, edge in neighbors:
        print(f"    - {node.label} (通过 {edge.edge_type.value} 关系)")

    # 查询FastAPI的邻居
    neighbors = await gm.get_neighbors(fastapi.id)
    print(f"\n  FastAPI 的邻居:")
    for node, edge in neighbors:
        print(f"    - {node.label} (通过 {edge.edge_type.value} 关系, weight={edge.weight})")


async def demonstrate_graph_memory_path():
    """演示图记忆路径查找"""
    print("\n" + "=" * 60)
    print("演示 9: 图记忆 - 路径查找")
    print("=" * 60)

    gm = GraphMemory()

    print("\n🏗️ 构建概念图谱:")
    # 创建概念节点
    concepts = {
        "AI": await gm.add_node("AI", "人工智能", "concept"),
        "ML": await gm.add_node("ML", "机器学习", "concept"),
        "DL": await gm.add_node("DL", "深度学习", "concept"),
        "NLP": await gm.add_node("NLP", "自然语言处理", "concept"),
        "CV": await gm.add_node("CV", "计算机视觉", "concept"),
        "Transformer": await gm.add_node("Transformer", "Transformer架构", "architecture"),
        "BERT": await gm.add_node("BERT", "BERT模型", "model"),
        "GPT": await gm.add_node("GPT", "GPT模型", "model"),
    }

    # 建立层次关系
    await gm.add_edge(concepts["ML"].id, concepts["AI"].id, EdgeType.IS_A, 1.0)
    await gm.add_edge(concepts["DL"].id, concepts["ML"].id, EdgeType.IS_A, 1.0)
    await gm.add_edge(concepts["NLP"].id, concepts["AI"].id, EdgeType.PART_OF, 0.9)
    await gm.add_edge(concepts["CV"].id, concepts["AI"].id, EdgeType.PART_OF, 0.9)
    await gm.add_edge(concepts["Transformer"].id, concepts["DL"].id, EdgeType.PART_OF, 0.95)
    await gm.add_edge(concepts["BERT"].id, concepts["Transformer"].id, EdgeType.IS_A, 1.0)
    await gm.add_edge(concepts["GPT"].id, concepts["Transformer"].id, EdgeType.IS_A, 1.0)
    await gm.add_edge(concepts["BERT"].id, concepts["NLP"].id, EdgeType.RELATED, 0.9)
    await gm.add_edge(concepts["GPT"].id, concepts["NLP"].id, EdgeType.RELATED, 0.9)

    print("  概念层次: AI -> ML -> DL -> Transformer -> BERT/GPT")
    print("  应用领域: NLP, CV 属于 AI 的分支")

    print("\n🔍 使用BFS查找路径 (BERT -> AI):")
    path = await gm.find_path(concepts["BERT"].id, concepts["AI"].id, algorithm="bfs")
    if path:
        print(f"  路径长度: {path.length}")
        print(f"  总权重: {path.total_weight:.2f}")
        print(f"  路径: {' -> '.join([n.label for n in path.nodes])}")

    print("\n🔍 使用DFS查找路径 (GPT -> AI):")
    path = await gm.find_path(concepts["GPT"].id, concepts["AI"].id, algorithm="dfs")
    if path:
        print(f"  路径长度: {path.length}")
        print(f"  总权重: {path.total_weight:.2f}")
        print(f"  路径: {' -> '.join([n.label for n in path.nodes])}")

    print("\n🔍 使用Dijkstra查找最短路径 (BERT -> AI):")
    path = await gm.find_path(concepts["BERT"].id, concepts["AI"].id, algorithm="dijkstra")
    if path:
        print(f"  路径长度: {path.length}")
        print(f"  总权重: {path.total_weight:.2f}")
        print(f"  路径: {' -> '.join([n.label for n in path.nodes])}")


async def demonstrate_graph_memory_subgraph():
    """演示图记忆子图提取"""
    print("\n" + "=" * 60)
    print("演示 10: 图记忆 - 子图提取")
    print("=" * 60)

    gm = GraphMemory()

    print("\n🏗️ 构建社交网络:")
    # 创建人物节点
    alice = await gm.add_node("Alice", "项目经理", "person")
    bob = await gm.add_node("Bob", "后端开发", "person")
    carol = await gm.add_node("Carol", "前端开发", "person")
    dave = await gm.add_node("Dave", "测试工程师", "person")
    eve = await gm.add_node("Eve", "UI设计师", "person")

    # 建立合作关系
    await gm.add_edge(alice.id, bob.id, EdgeType.RELATED, 0.8, bidirectional=True)
    await gm.add_edge(alice.id, carol.id, EdgeType.RELATED, 0.8, bidirectional=True)
    await gm.add_edge(bob.id, carol.id, EdgeType.RELATED, 0.9, bidirectional=True)
    await gm.add_edge(bob.id, dave.id, EdgeType.RELATED, 0.7, bidirectional=True)
    await gm.add_edge(carol.id, eve.id, EdgeType.RELATED, 0.85, bidirectional=True)

    print("  - Alice(项目经理) 管理 Bob(后端) 和 Carol(前端)")
    print("  - Bob 和 Carol 紧密合作")
    print("  - Bob 与 Dave(测试) 协作")
    print("  - Carol 与 Eve(UI) 协作")

    print("\n📊 提取以Alice为中心的子图 (深度=2):")
    nodes, edges = await gm.get_subgraph(alice.id, depth=2)
    print(f"  - 子图包含 {len(nodes)} 个节点:")
    for node in nodes:
        print(f"    - {node.label} ({node.node_type})")
    print(f"  - 子图包含 {len(edges)} 条边")

    print("\n🔗 查找连通分量:")
    components = await gm.find_connected_components()
    print(f"  - 发现 {len(components)} 个连通分量")
    for i, component in enumerate(components):
        print(f"    分量 {i+1}: {', '.join([n.label for n in component])}")


async def demonstrate_memory_search():
    """演示记忆搜索功能"""
    print("\n" + "=" * 60)
    print("演示 11: 记忆搜索")
    print("=" * 60)

    # 短期记忆搜索
    print("\n🔍 短期记忆搜索:")
    stm = ShortTermMemory()
    await stm.store("doc_1", "Python是一种强大的编程语言")
    await stm.store("doc_2", "JavaScript用于Web开发")
    await stm.store("doc_3", "Python在数据科学中很流行")

    query = MemoryQuery(content="Python", limit=10)
    results = await stm.search(query)
    print(f"  搜索 'Python' 找到 {len(results)} 个结果:")
    for result in results:
        print(f"    - {result.entry.content} (分数: {result.score:.2f})")

    # 图记忆搜索
    print("\n🔍 图记忆搜索:")
    gm = GraphMemory()
    await gm.add_node("Python", "Python编程语言", "language")
    await gm.add_node("PyTorch", "PyTorch深度学习框架", "framework")
    await gm.add_node("Java", "Java编程语言", "language")

    query = MemoryQuery(content="Python", limit=10)
    results = await gm.search(query)
    print(f"  搜索 'Python' 找到 {len(results)} 个结果:")
    for result in results:
        print(f"    - {result.entry.content} (分数: {result.score:.2f})")


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("DeepTutor 记忆系统使用示例")
    print("=" * 60)
    print("\n本示例演示以下内容:")
    print("  1. 短期记忆基础使用")
    print("  2. 短期记忆TTL过期")
    print("  3. 短期记忆LRU淘汰")
    print("  4. 长期记忆JSON存储")
    print("  5. 长期记忆SQLite存储")
    print("  6. 长期记忆备份恢复")
    print("  7. 图记忆基础操作")
    print("  8. 图记忆邻居查询")
    print("  9. 图记忆路径查找")
    print("  10. 图记忆子图提取")
    print("  11. 记忆搜索功能")
    print()

    try:
        # 运行所有演示
        await demonstrate_short_term_memory()
        await demonstrate_short_term_memory_ttl()
        await demonstrate_short_term_memory_lru()
        await demonstrate_long_term_memory_json()
        await demonstrate_long_term_memory_sqlite()
        await demonstrate_long_term_memory_backup()
        await demonstrate_graph_memory_basic()
        await demonstrate_graph_memory_neighbors()
        await demonstrate_graph_memory_path()
        await demonstrate_graph_memory_subgraph()
        await demonstrate_memory_search()

        print("\n" + "=" * 60)
        print("✅ 所有演示完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

"""
知识库功能使用示例

展示如何使用从 DeepSeekMine 集成的知识库功能
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.skills.knowledge_base import (
    KnowledgeBaseConfig,
    KnowledgeBaseManager,
    RAGPipeline,
    get_kb_chat_integration,
)


async def example_1_create_knowledge_base():
    """示例1: 创建知识库"""
    print("=" * 60)
    print("示例1: 创建知识库")
    print("=" * 60)
    
    # 创建配置
    config = KnowledgeBaseConfig(
        vector_store_path="./data/vector_store",
        chunk_size=1000,
        chunk_overlap=200,
    )
    
    # 初始化管理器
    manager = KnowledgeBaseManager(config)
    await manager.initialize(embedding_provider="mock")
    
    # 创建知识库
    kb = await manager.create_knowledge_base(
        name="示例知识库",
        description="用于演示的知识库"
    )
    
    print(f"✅ 知识库创建成功!")
    print(f"   ID: {kb.kb_id}")
    print(f"   名称: {kb.name}")
    print(f"   描述: {kb.description}")
    
    return manager, kb


async def example_2_add_document(manager: KnowledgeBaseManager, kb_id: str):
    """示例2: 添加文档"""
    print("\n" + "=" * 60)
    print("示例2: 添加文档")
    print("=" * 60)
    
    # 创建一个测试文件
    test_file = "./test_document.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("""
人工智能（Artificial Intelligence，AI）是指由人制造出来的系统所表现出来的智能。

机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下学习。
深度学习是机器学习的一个子集，使用神经网络来模拟人脑的工作方式。

自然语言处理（NLP）是人工智能的重要应用领域，它使计算机能够理解和生成人类语言。
        """)
    
    # 添加文档
    doc = await manager.add_document(
        kb_id=kb_id,
        file_path=test_file,
        filename="test_document.txt"
    )
    
    print(f"✅ 文档添加成功!")
    print(f"   ID: {doc.document_id}")
    print(f"   文件名: {doc.filename}")
    
    # 处理文档
    print("\n📄 正在处理文档...")
    success = await manager.process_document(kb_id, doc.document_id)
    
    if success:
        print("✅ 文档处理完成!")
    else:
        print("❌ 文档处理失败")
    
    # 清理测试文件
    os.remove(test_file)
    
    return doc


async def example_3_search_and_rag(manager: KnowledgeBaseManager, kb_id: str):
    """示例3: 搜索和 RAG 检索"""
    print("\n" + "=" * 60)
    print("示例3: 搜索和 RAG 检索")
    print("=" * 60)
    
    # 创建 RAG 管道
    rag = RAGPipeline(
        vector_store=manager.vector_store,
        embedding_manager=manager.embedding_manager,
        config=manager.config,
        retriever_type="similarity"
    )
    
    # 执行检索
    query = "什么是机器学习？"
    print(f"\n🔍 查询: {query}")
    
    result = await rag.retrieve(
        query=query,
        knowledge_base_id=kb_id,
        top_k=3
    )
    
    print(f"✅ 检索完成!")
    print(f"   找到 {len(result.chunks)} 个相关文档块")
    print(f"\n📄 检索结果:")
    print(result.context[:500] + "..." if len(result.context) > 500 else result.context)


async def example_4_chat_integration():
    """示例4: 聊天集成"""
    print("\n" + "=" * 60)
    print("示例4: 聊天集成")
    print("=" * 60)
    
    # 获取聊天集成实例
    integration = get_kb_chat_integration()
    await integration.initialize()
    
    # 构建系统提示词
    query = "解释人工智能的概念"
    print(f"\n💬 用户查询: {query}")
    
    system_prompt, rag_context = await integration.build_system_prompt(
        query=query,
        top_k=3
    )
    
    if system_prompt:
        print(f"✅ 系统提示词已生成!")
        print(f"   上下文长度: {len(rag_context.context_text)} 字符")
        print(f"   来源数量: {len(rag_context.sources)}")
    else:
        print("⚠️ 未找到相关知识库")


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("DeepSeekMine 知识库功能示例")
    print("=" * 60)
    
    try:
        # 示例1: 创建知识库
        manager, kb = await example_1_create_knowledge_base()
        
        # 示例2: 添加文档
        doc = await example_2_add_document(manager, kb.kb_id)
        
        # 示例3: 搜索和 RAG
        await example_3_search_and_rag(manager, kb.kb_id)
        
        # 示例4: 聊天集成
        await example_4_chat_integration()
        
        print("\n" + "=" * 60)
        print("✅ 所有示例执行完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

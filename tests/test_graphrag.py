"""
GraphRAG 测试用例
测试知识图谱构建、查询、实体提取等核心功能
"""

import pytest
import asyncio
from datetime import datetime

from src.agents.skills.graphrag import (
    GraphRAG,
    Entity,
    EntityType,
    Relationship,
    RelationType,
    QueryMode,
    KnowledgeGraph,
    DocumentProcessor,
    EntityExtractor,
    RelationshipMapper,
    GraphVisualizer,
    VectorStore,
    GraphPersistence
)


# ============== 实体提取测试 ==============

class TestEntityExtractor:
    """测试实体提取器"""
    
    @pytest.fixture
    def extractor(self):
        return EntityExtractor(llm_client=None)
    
    def test_extract_entities_basic(self, extractor):
        """测试基本实体提取"""
        text = "Apple Inc. was founded by Steve Jobs in California."
        
        # 使用正则回退提取
        entities = asyncio.run(extractor.extract(text))
        
        assert isinstance(entities, list)
        assert len(entities) > 0
        
        # 检查实体类型
        entity_types = [e.type for e in entities]
        assert EntityType.ORGANIZATION in entity_types or EntityType.PERSON in entity_types
    
    def test_entity_types(self):
        """测试实体类型枚举"""
        assert EntityType.PERSON.value == "person"
        assert EntityType.ORGANIZATION.value == "organization"
        assert EntityType.LOCATION.value == "location"
        assert len(EntityType) == 7


# ============== 关系映射测试 ==============

class TestRelationshipMapper:
    """测试关系映射器"""
    
    @pytest.fixture
    def mapper(self):
        return RelationshipMapper(llm_client=None)
    
    @pytest.fixture
    def sample_entities(self):
        return [
            Entity(name="Apple", type=EntityType.ORGANIZATION),
            Entity(name="Steve Jobs", type=EntityType.PERSON),
            Entity(name="California", type=EntityType.LOCATION)
        ]
    
    def test_map_relationships(self, mapper, sample_entities):
        """测试关系映射"""
        text = "Apple was founded by Steve Jobs in California."
        
        relationships = asyncio.run(
            mapper.map_relationships(text, sample_entities)
        )
        
        assert isinstance(relationships, list)
        
        # 检查关系属性
        for rel in relationships:
            assert rel.source
            assert rel.target
            assert isinstance(rel.relation_type, RelationType)
    
    def test_cooccurrence_relationships(self, mapper, sample_entities):
        """测试共现关系生成"""
        relationships = mapper.create_cooccurrence_relationships(
            sample_entities,
            chunk_id="test_chunk"
        )
        
        assert len(relationships) > 0
        
        # 检查共现关系
        for rel in relationships:
            assert rel.relation_type == RelationType.RELATED_TO
            assert rel.weight <= 0.5


# ============== 知识图谱测试 ==============

class TestKnowledgeGraph:
    """测试知识图谱"""
    
    @pytest.fixture
    def graph(self):
        return KnowledgeGraph(storage_type="memory")
    
    @pytest.fixture
    def sample_entity(self):
        return Entity(
            name="Test Company",
            type=EntityType.ORGANIZATION,
            description="A test company"
        )
    
    def test_add_entity(self, graph, sample_entity):
        """测试添加实体"""
        node = graph.add_entity(sample_entity)
        
        assert node is not None
        assert node.name == "Test Company"
        assert node.type == EntityType.ORGANIZATION
        
        # 验证存储
        assert len(graph._nodes) == 1
    
    def test_add_duplicate_entity(self, graph, sample_entity):
        """测试添加重复实体"""
        node1 = graph.add_entity(sample_entity)
        node2 = graph.add_entity(sample_entity)
        
        # 应该返回同一个节点
        assert node1.id == node2.id
        assert len(graph._nodes) == 1
    
    def test_get_node_by_name(self, graph, sample_entity):
        """测试按名称获取节点"""
        graph.add_entity(sample_entity)
        
        node = graph.get_node_by_name("Test Company")
        assert node is not None
        assert node.name == "Test Company"
        
        # 测试不存在的节点
        node = graph.get_node_by_name("Non Existent")
        assert node is None
    
    def test_search_nodes(self, graph):
        """测试节点搜索"""
        entities = [
            Entity(name="Apple Inc", type=EntityType.ORGANIZATION),
            Entity(name="Apple Pie", type=EntityType.PRODUCT),
            Entity(name="Banana", type=EntityType.PRODUCT)
        ]
        
        for e in entities:
            graph.add_entity(e)
        
        results = graph.search_nodes("Apple", limit=10)
        assert len(results) == 2
    
    def test_incremental_update(self, graph):
        """测试增量更新"""
        # 初始实体
        entities = [
            Entity(name="Company A", type=EntityType.ORGANIZATION),
            Entity(name="Person B", type=EntityType.PERSON)
        ]
        
        relationships = [
            Relationship(
                source="Company A",
                target="Person B",
                relation_type=RelationType.WORKS_AT
            )
        ]
        
        stats = graph.incremental_update(entities, relationships, "doc1")
        
        assert stats["added_nodes"] == 2
        assert stats["added_edges"] == 1
        
        # 再次更新（应该更新而不是添加）
        entities[0].description = "Updated description"
        stats = graph.incremental_update(entities, relationships, "doc1")
        
        assert stats["updated_nodes"] == 2
        assert stats["added_nodes"] == 0


# ============== 文档处理器测试 ==============

class TestDocumentProcessor:
    """测试文档处理器"""
    
    @pytest.fixture
    def processor(self):
        return DocumentProcessor(chunk_size=100, chunk_overlap=20)
    
    def test_chunk_document(self, processor):
        """测试文档分块"""
        text = "This is sentence one. This is sentence two. This is sentence three. " * 10
        
        chunks = processor._chunk_document(text, "doc1")
        
        assert len(chunks) > 0
        
        # 检查块大小
        for chunk in chunks:
            assert len(chunk.content) > 0
            assert chunk.id.startswith("doc1")
    
    def test_token_count(self, processor):
        """测试Token计数"""
        from src.agents.skills.graphrag.document_processor import Tokenizer
        
        text = "Hello world, this is a test."
        count = Tokenizer.count_tokens(text)
        
        assert count > 0
        assert isinstance(count, int)


# ============== GraphRAG 主类测试 ==============

class TestGraphRAG:
    """测试 GraphRAG 主类"""
    
    @pytest.fixture
    def graphrag(self):
        return GraphRAG()
    
    @pytest.mark.asyncio
    async def test_process_document(self, graphrag):
        """测试文档处理"""
        content = """
        Apple Inc. is a technology company founded by Steve Jobs and Steve Wozniak.
        It is headquartered in Cupertino, California.
        The company develops iPhone, iPad, and Mac computers.
        """
        
        result = await graphrag.process_document(content, "Test Doc")
        
        assert "document_id" in result
        assert "entities_count" in result
        assert "relationships_count" in result
        assert result["entities_count"] > 0
    
    @pytest.mark.asyncio
    async def test_query(self, graphrag):
        """测试查询"""
        # 先处理一些文档
        content = "Microsoft was founded by Bill Gates."
        await graphrag.process_document(content)
        
        # 执行查询
        result = await graphrag.query("Who founded Microsoft?", mode="local")
        
        assert result.query == "Who founded Microsoft?"
        assert result.mode == QueryMode.LOCAL
    
    def test_get_statistics(self, graphrag):
        """测试获取统计信息"""
        stats = graphrag.get_statistics()
        
        assert "documents" in stats
        assert "knowledge_graph" in stats


# ============== 可视化测试 ==============

class TestGraphVisualizer:
    """测试图谱可视化"""
    
    @pytest.fixture
    def visualizer(self):
        graph = KnowledgeGraph()
        # 添加一些测试数据
        graph.add_entity(Entity(name="A", type=EntityType.PERSON))
        graph.add_entity(Entity(name="B", type=EntityType.ORGANIZATION))
        
        return GraphVisualizer(graph)
    
    def test_export_to_d3(self, visualizer):
        """测试 D3.js 导出"""
        data = visualizer.export_to_d3()
        
        assert "nodes" in data
        assert "links" in data
        assert "metadata" in data
        assert len(data["nodes"]) == 2
    
    def test_export_to_cytoscape(self, visualizer):
        """测试 Cytoscape.js 导出"""
        data = visualizer.export_to_cytoscape()
        
        assert "elements" in data
        assert len(data["elements"]) == 2  # 2个节点


# ============== 向量存储测试 ==============

class TestVectorStore:
    """测试向量存储"""
    
    @pytest.fixture
    def vector_store(self):
        return VectorStore(dimension=128)
    
    @pytest.mark.asyncio
    async def test_add_and_search(self, vector_store):
        """测试添加和搜索"""
        texts = [
            "Apple is a technology company",
            "Banana is a fruit",
            "Car is a vehicle"
        ]
        
        # 添加文本
        for text in texts:
            await vector_store.add_text(text)
        
        # 搜索
        results = await vector_store.search("technology", top_k=3)
        
        assert len(results) > 0
        assert all(isinstance(score, float) for _, score in results)


# ============== 持久化测试 ==============

class TestPersistence:
    """测试持久化"""
    
    @pytest.fixture
    def persistence(self, tmp_path):
        return GraphPersistence(storage_dir=str(tmp_path))
    
    @pytest.fixture
    def sample_graph(self):
        graph = KnowledgeGraph()
        graph.add_entity(Entity(name="Test", type=EntityType.PERSON))
        return graph
    
    def test_save_and_load_graph(self, persistence, sample_graph):
        """测试保存和加载图谱"""
        # 保存
        filepath = persistence.save_knowledge_graph(sample_graph, "test")
        assert filepath.endswith("test.json")
        
        # 加载
        new_graph = KnowledgeGraph()
        success = persistence.load_knowledge_graph(new_graph, "test")
        
        assert success
        assert len(new_graph._nodes) == 1
    
    def test_backup_creation(self, persistence, sample_graph):
        """测试备份创建"""
        # 保存两次以创建备份
        persistence.save_knowledge_graph(sample_graph, "test")
        persistence.save_knowledge_graph(sample_graph, "test")
        
        backups = persistence.list_backups("test")
        assert len(backups) >= 1


# ============== 集成测试 ==============

class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """测试完整流程"""
        graphrag = GraphRAG()
        
        # 1. 处理文档
        content = """
        Tesla Inc. was founded by Elon Musk. 
        The company manufactures electric vehicles.
        Tesla is headquartered in Austin, Texas.
        """
        
        result = await graphrag.process_document(content, "Tesla Doc")
        assert result["entities_count"] > 0
        
        # 2. 查询
        query_result = await graphrag.query("Who founded Tesla?", mode="hybrid")
        assert query_result.answer or query_result.entities
        
        # 3. 可视化
        viz_data = graphrag.visualize(format="d3", max_nodes=50)
        assert "nodes" in viz_data
        
        # 4. 统计
        stats = graphrag.get_statistics()
        assert stats["knowledge_graph"]["total_nodes"] > 0


# ============== 性能测试 ==============

class TestPerformance:
    """性能测试"""
    
    def test_large_graph_performance(self):
        """测试大规模图谱性能"""
        graph = KnowledgeGraph()
        
        # 添加1000个节点
        import time
        start = time.time()
        
        for i in range(1000):
            entity = Entity(
                name=f"Entity_{i}",
                type=EntityType.PERSON if i % 2 == 0 else EntityType.ORGANIZATION
            )
            graph.add_entity(entity)
        
        duration = time.time() - start
        
        # 应该在1秒内完成
        assert duration < 1.0
        assert len(graph._nodes) == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

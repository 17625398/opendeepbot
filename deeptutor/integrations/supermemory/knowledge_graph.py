"""
SuperMemory Knowledge Graph Service - SuperMemory 知识图谱服务
=================================================================

提供知识图谱的构建、存储、查询和分析功能：
- 实体提取与关系抽取
- 知识图谱存储（Neo4j + NetworkX）
- 图遍历与查询
- 实体消歧与关系推断
- 图谱导出（JSON/GEXF）

Architecture:
    - 使用 NetworkX 进行内存中的图操作
    - 使用 Neo4j 进行持久化存储
    - 使用 LLM 进行实体和关系提取
"""

from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import networkx as nx
from pydantic import BaseModel, Field

from deeptutor.core.llm.client import LLMClient, get_llm_client
from deeptutor.integrations.supermemory.models import (
    EntityRelation,
    KnowledgeEntity,
    KnowledgeGraphResult,
    MemoryRecord,
    RelationType,
)

logger = logging.getLogger(__name__)


class EntityExtractionResult(BaseModel):
    """实体提取结果"""
    
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    text: str = Field(default="")
    extraction_time_ms: Optional[float] = Field(default=None)


class RelationExtractionResult(BaseModel):
    """关系提取结果"""
    
    relations: List[Dict[str, Any]] = Field(default_factory=list)
    source_text: str = Field(default="")
    extraction_time_ms: Optional[float] = Field(default=None)


class GraphTraversalResult(BaseModel):
    """图遍历结果"""
    
    entities: List[KnowledgeEntity] = Field(default_factory=list)
    relations: List[EntityRelation] = Field(default_factory=list)
    paths: List[List[str]] = Field(default_factory=list)  # 实体 ID 路径
    traversal_depth: int = Field(default=0)


class KnowledgeGraphService:
    """知识图谱服务
    
    提供完整的知识图谱管理功能，包括：
    - 从文本中提取实体和关系
    - 构建和维护知识图谱
    - 执行图查询和遍历
    - 实体消歧和关系推断
    - 导出图谱到多种格式
    
    Attributes:
        llm_client: LLM 客户端用于实体/关系提取
        graph: NetworkX 有向图用于内存操作
        neo4j_driver: Neo4j 驱动用于持久化存储
        entity_cache: 实体缓存用于消歧
    """
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
    ) -> None:
        """初始化知识图谱服务
        
        Args:
            llm_client: LLM 客户端，默认使用全局实例
            neo4j_uri: Neo4j 数据库 URI
            neo4j_user: Neo4j 用户名
            neo4j_password: Neo4j 密码
        
        Configuration is loaded from environment variables via KGConfig:
        - KG_NEO4J_URI, KG_NEO4J_USER, KG_NEO4J_PASSWORD
        """
        from deeptutor.tools.kg_config import get_kg_config, get_llm_settings
        
        # Get unified config
        kg_config = get_kg_config()
        llm_settings = get_llm_settings()
        
        self.llm_client = llm_client or get_llm_client()
        self.graph = nx.DiGraph()
        self.entity_cache: Dict[str, KnowledgeEntity] = {}
        self.relation_cache: Dict[str, EntityRelation] = {}
        
        # Neo4j 配置 - priority: params > env config > defaults
        self.neo4j_uri = neo4j_uri or kg_config.neo4j_uri
        self.neo4j_user = neo4j_user or kg_config.neo4j_user
        self.neo4j_password = neo4j_password or kg_config.neo4j_password
        self._neo4j_driver: Optional[Any] = None
        
        logger.info(f"Initialized KnowledgeGraphService with Neo4j: {self.neo4j_uri}")
    
    async def _get_neo4j_driver(self) -> Any:
        """获取 Neo4j 驱动（延迟初始化）"""
        if self._neo4j_driver is None:
            try:
                from neo4j import AsyncGraphDatabase
                self._neo4j_driver = AsyncGraphDatabase.driver(
                    self.neo4j_uri,
                    auth=(self.neo4j_user, self.neo4j_password),
                )
                logger.info("Connected to Neo4j database")
            except ImportError:
                logger.warning("Neo4j driver not installed, using in-memory storage only")
                return None
        return self._neo4j_driver
    
    async def close(self) -> None:
        """关闭服务连接"""
        if self._neo4j_driver:
            await self._neo4j_driver.close()
            self._neo4j_driver = None
            logger.info("Closed Neo4j connection")
    
    # ==================== 实体提取 ====================
    
    async def extract_entities(
        self,
        text: str,
        entity_types: Optional[List[str]] = None,
        language: str = "zh",
    ) -> EntityExtractionResult:
        """从文本中提取实体
        
        使用 LLM 进行命名实体识别（NER），提取文本中的关键实体。
        
        Args:
            text: 输入文本
            entity_types: 指定实体类型列表（如 ["人物", "组织", "地点"]）
            language: 文本语言
        
        Returns:
            实体提取结果
        
        Example:
            >>> result = await service.extract_entities(
            ...     "张三在北京大学工作",
            ...     entity_types=["人物", "组织", "地点"]
            ... )
            >>> print(result.entities)
            [{"name": "张三", "type": "人物"}, {"name": "北京大学", "type": "组织"}]
        """
        import time
        start_time = time.time()
        
        entity_types = entity_types or ["人物", "组织", "地点", "概念", "事件", "时间"]
        
        system_prompt = f"""你是一个专业的命名实体识别（NER）专家。
请从给定的文本中提取实体，并以 JSON 格式返回。

支持的实体类型：{', '.join(entity_types)}

返回格式：
{{
    "entities": [
        {{"name": "实体名称", "type": "实体类型", "description": "简要描述"}},
        ...
    ]
}}

只返回 JSON，不要其他解释。"""

        try:
            response = await self.llm_client.complete(
                prompt=f"请从以下文本中提取实体：\n\n{text}",
                system_prompt=system_prompt,
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            
            data = json.loads(response)
            entities = data.get("entities", [])
            
            extraction_time = (time.time() - start_time) * 1000
            
            logger.debug(f"Extracted {len(entities)} entities from text")
            
            return EntityExtractionResult(
                entities=entities,
                text=text,
                extraction_time_ms=extraction_time,
            )
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return EntityExtractionResult(
                entities=[],
                text=text,
                extraction_time_ms=(time.time() - start_time) * 1000,
            )
    
    async def extract_relations(
        self,
        text: str,
        entities: Optional[List[Dict[str, Any]]] = None,
        relation_types: Optional[List[str]] = None,
    ) -> RelationExtractionResult:
        """从文本中提取实体间的关系
        
        使用 LLM 进行关系抽取，识别实体之间的语义关系。
        
        Args:
            text: 输入文本
            entities: 预提取的实体列表（可选）
            relation_types: 指定关系类型列表
        
        Returns:
            关系提取结果
        
        Example:
            >>> result = await service.extract_relations(
            ...     "张三在北京大学工作，他是教授。"
            ... )
            >>> print(result.relations)
            [{"source": "张三", "target": "北京大学", "type": "工作于"}]
        """
        import time
        start_time = time.time()
        
        relation_types = relation_types or [
            "属于", "包含", "导致", "被导致", "相似", "矛盾",
            "支持", "示例", "实例", "子类", "超类", "相关"
        ]
        
        entity_context = ""
        if entities:
            entity_names = [e.get("name", "") for e in entities]
            entity_context = f"\n已识别实体：{', '.join(entity_names)}"
        
        system_prompt = f"""你是一个专业的关系抽取专家。
请从给定的文本中提取实体之间的关系，并以 JSON 格式返回。

支持的关系类型：{', '.join(relation_types)}

返回格式：
{{
    "relations": [
        {{
            "source": "源实体名称",
            "target": "目标实体名称",
            "type": "关系类型",
            "description": "关系描述"
        }},
        ...
    ]
}}

只返回 JSON，不要其他解释。"""

        try:
            response = await self.llm_client.complete(
                prompt=f"请从以下文本中提取实体关系：{entity_context}\n\n{text}",
                system_prompt=system_prompt,
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            
            data = json.loads(response)
            relations = data.get("relations", [])
            
            extraction_time = (time.time() - start_time) * 1000
            
            logger.debug(f"Extracted {len(relations)} relations from text")
            
            return RelationExtractionResult(
                relations=relations,
                source_text=text,
                extraction_time_ms=extraction_time,
            )
            
        except Exception as e:
            logger.error(f"Relation extraction failed: {e}")
            return RelationExtractionResult(
                relations=[],
                source_text=text,
                extraction_time_ms=(time.time() - start_time) * 1000,
            )
    
    async def extract_entities_and_relations(
        self,
        text: str,
    ) -> Tuple[EntityExtractionResult, RelationExtractionResult]:
        """同时提取实体和关系
        
        Args:
            text: 输入文本
        
        Returns:
            (实体提取结果, 关系提取结果)
        """
        # 先提取实体
        entity_result = await self.extract_entities(text)
        
        # 使用提取的实体进行关系抽取
        relation_result = await self.extract_relations(
            text,
            entities=entity_result.entities,
        )
        
        return entity_result, relation_result
    
    # ==================== 实体管理 ====================
    
    async def create_entity(
        self,
        name: str,
        entity_type: str = "concept",
        description: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
        source: str = "unknown",
        confidence: float = 1.0,
    ) -> KnowledgeEntity:
        """创建知识实体
        
        Args:
            name: 实体名称
            entity_type: 实体类型
            description: 实体描述
            properties: 实体属性
            embedding: 向量嵌入
            source: 数据来源
            confidence: 置信度
        
        Returns:
            创建的知识实体
        """
        entity = KnowledgeEntity(
            name=name,
            entity_type=entity_type,
            description=description,
            properties=properties or {},
            embedding=embedding,
            source=source,
            confidence=confidence,
        )
        
        # 添加到内存图
        self.graph.add_node(
            entity.id,
            name=entity.name,
            entity_type=entity.entity_type,
            description=entity.description,
            properties=entity.properties,
            source=entity.source,
            confidence=entity.confidence,
        )
        
        # 添加到缓存
        self.entity_cache[entity.id] = entity
        
        # 同步到 Neo4j
        await self._sync_entity_to_neo4j(entity)
        
        logger.debug(f"Created entity: {entity.name} ({entity.id})")
        
        return entity
    
    async def _sync_entity_to_neo4j(self, entity: KnowledgeEntity) -> None:
        """同步实体到 Neo4j"""
        driver = await self._get_neo4j_driver()
        if not driver:
            return
        
        try:
            async with driver.session() as session:
                await session.run(
                    """
                    MERGE (e:Entity {id: $id})
                    SET e.name = $name,
                        e.entity_type = $entity_type,
                        e.description = $description,
                        e.properties = $properties,
                        e.source = $source,
                        e.confidence = $confidence,
                        e.updated_at = datetime()
                    """,
                    id=entity.id,
                    name=entity.name,
                    entity_type=entity.entity_type,
                    description=entity.description or "",
                    properties=json.dumps(entity.properties),
                    source=entity.source,
                    confidence=entity.confidence,
                )
        except Exception as e:
            logger.error(f"Failed to sync entity to Neo4j: {e}")
    
    async def get_entity(self, entity_id: str) -> Optional[KnowledgeEntity]:
        """获取知识实体
        
        Args:
            entity_id: 实体 ID
        
        Returns:
            知识实体，不存在则返回 None
        """
        # 先从缓存查找
        if entity_id in self.entity_cache:
            return self.entity_cache[entity_id]
        
        # 从内存图查找
        if entity_id in self.graph:
            node_data = self.graph.nodes[entity_id]
            entity = KnowledgeEntity(
                id=entity_id,
                name=node_data.get("name", ""),
                entity_type=node_data.get("entity_type", "concept"),
                description=node_data.get("description"),
                properties=node_data.get("properties", {}),
                source=node_data.get("source", "unknown"),
                confidence=node_data.get("confidence", 1.0),
            )
            self.entity_cache[entity_id] = entity
            return entity
        
        # 从 Neo4j 查找
        return await self._get_entity_from_neo4j(entity_id)
    
    async def _get_entity_from_neo4j(self, entity_id: str) -> Optional[KnowledgeEntity]:
        """从 Neo4j 获取实体"""
        driver = await self._get_neo4j_driver()
        if not driver:
            return None
        
        try:
            async with driver.session() as session:
                result = await session.run(
                    "MATCH (e:Entity {id: $id}) RETURN e",
                    id=entity_id,
                )
                record = await result.single()
                
                if record:
                    node = record["e"]
                    entity = KnowledgeEntity(
                        id=entity_id,
                        name=node.get("name", ""),
                        entity_type=node.get("entity_type", "concept"),
                        description=node.get("description"),
                        properties=json.loads(node.get("properties", "{}")),
                        source=node.get("source", "unknown"),
                        confidence=node.get("confidence", 1.0),
                    )
                    self.entity_cache[entity_id] = entity
                    return entity
                    
        except Exception as e:
            logger.error(f"Failed to get entity from Neo4j: {e}")
        
        return None
    
    async def query_entities(
        self,
        entity_type: Optional[str] = None,
        name_pattern: Optional[str] = None,
        min_confidence: Optional[float] = None,
        limit: int = 50,
    ) -> List[KnowledgeEntity]:
        """查询知识实体
        
        Args:
            entity_type: 实体类型过滤
            name_pattern: 名称匹配模式
            min_confidence: 最小置信度
            limit: 返回数量限制
        
        Returns:
            知识实体列表
        """
        entities = []
        
        # 从内存图查询
        for node_id, node_data in self.graph.nodes(data=True):
            if entity_type and node_data.get("entity_type") != entity_type:
                continue
            if name_pattern and name_pattern.lower() not in node_data.get("name", "").lower():
                continue
            if min_confidence is not None and node_data.get("confidence", 1.0) < min_confidence:
                continue
            
            entity = KnowledgeEntity(
                id=node_id,
                name=node_data.get("name", ""),
                entity_type=node_data.get("entity_type", "concept"),
                description=node_data.get("description"),
                properties=node_data.get("properties", {}),
                source=node_data.get("source", "unknown"),
                confidence=node_data.get("confidence", 1.0),
            )
            entities.append(entity)
            
            if len(entities) >= limit:
                break
        
        return entities
    
    # ==================== 关系管理 ====================
    
    async def create_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        properties: Optional[Dict[str, Any]] = None,
        strength: float = 1.0,
        bidirectional: bool = False,
        source: str = "unknown",
        confidence: float = 1.0,
    ) -> EntityRelation:
        """创建实体关系
        
        Args:
            source_id: 源实体 ID
            target_id: 目标实体 ID
            relation_type: 关系类型
            properties: 关系属性
            strength: 关系强度
            bidirectional: 是否双向关系
            source: 数据来源
            confidence: 置信度
        
        Returns:
            创建的实体关系
        """
        relation = EntityRelation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            properties=properties or {},
            strength=strength,
            bidirectional=bidirectional,
            source=source,
            confidence=confidence,
        )
        
        # 添加到内存图
        self.graph.add_edge(
            source_id,
            target_id,
            id=relation.id,
            relation_type=relation_type.value,
            properties=relation.properties,
            strength=relation.strength,
            bidirectional=relation.bidirectional,
            source=relation.source,
            confidence=relation.confidence,
        )
        
        # 如果是双向关系，添加反向边
        if bidirectional:
            self.graph.add_edge(
                target_id,
                source_id,
                id=f"{relation.id}_reverse",
                relation_type=relation_type.value,
                properties=relation.properties,
                strength=relation.strength,
                bidirectional=True,
                source=relation.source,
                confidence=relation.confidence,
            )
        
        # 添加到缓存
        self.relation_cache[relation.id] = relation
        
        # 同步到 Neo4j
        await self._sync_relation_to_neo4j(relation)
        
        logger.debug(f"Created relation: {source_id} -> {target_id}")
        
        return relation
    
    async def _sync_relation_to_neo4j(self, relation: EntityRelation) -> None:
        """同步关系到 Neo4j"""
        driver = await self._get_neo4j_driver()
        if not driver:
            return
        
        try:
            async with driver.session() as session:
                await session.run(
                    """
                    MATCH (source:Entity {id: $source_id})
                    MATCH (target:Entity {id: $target_id})
                    MERGE (source)-[r:RELATES {id: $id}]->(target)
                    SET r.relation_type = $relation_type,
                        r.properties = $properties,
                        r.strength = $strength,
                        r.bidirectional = $bidirectional,
                        r.source = $source,
                        r.confidence = $confidence,
                        r.updated_at = datetime()
                    """,
                    source_id=relation.source_id,
                    target_id=relation.target_id,
                    id=relation.id,
                    relation_type=relation.relation_type.value,
                    properties=json.dumps(relation.properties),
                    strength=relation.strength,
                    bidirectional=relation.bidirectional,
                    source=relation.source,
                    confidence=relation.confidence,
                )
                
                # 如果是双向关系，创建反向关系
                if relation.bidirectional:
                    await session.run(
                        """
                        MATCH (source:Entity {id: $source_id})
                        MATCH (target:Entity {id: $target_id})
                        MERGE (target)-[r:RELATES {id: $reverse_id}]->(source)
                        SET r.relation_type = $relation_type,
                            r.properties = $properties,
                            r.strength = $strength,
                            r.bidirectional = true,
                            r.source = $source,
                            r.confidence = $confidence
                        """,
                        source_id=relation.source_id,
                        target_id=relation.target_id,
                        reverse_id=f"{relation.id}_reverse",
                        relation_type=relation.relation_type.value,
                        properties=json.dumps(relation.properties),
                        strength=relation.strength,
                        source=relation.source,
                        confidence=relation.confidence,
                    )
        except Exception as e:
            logger.error(f"Failed to sync relation to Neo4j: {e}")
    
    # ==================== 图谱查询 ====================
    
    async def query_graph(
        self,
        entity_name: Optional[str] = None,
        entity_type: Optional[str] = None,
        relation_type: Optional[RelationType] = None,
        depth: int = 1,
        limit: int = 50,
    ) -> KnowledgeGraphResult:
        """查询知识图谱
        
        Args:
            entity_name: 实体名称
            entity_type: 实体类型
            relation_type: 关系类型
            depth: 查询深度
            limit: 返回数量限制
        
        Returns:
            知识图谱查询结果
        """
        entities = []
        relations = []
        visited = set()
        
        # 找到起始实体
        start_entities = []
        for node_id, node_data in self.graph.nodes(data=True):
            if entity_name and entity_name.lower() not in node_data.get("name", "").lower():
                continue
            if entity_type and node_data.get("entity_type") != entity_type:
                continue
            start_entities.append(node_id)
        
        # BFS 遍历
        for start_id in start_entities[:limit]:
            visited.add(start_id)
            node_data = self.graph.nodes[start_id]
            entities.append(KnowledgeEntity(
                id=start_id,
                name=node_data.get("name", ""),
                entity_type=node_data.get("entity_type", "concept"),
                description=node_data.get("description"),
                properties=node_data.get("properties", {}),
            ))
            
            # 遍历邻居
            for neighbor_id in nx.bfs_tree(self.graph, start_id, depth_limit=depth):
                if neighbor_id in visited:
                    continue
                visited.add(neighbor_id)
                
                neighbor_data = self.graph.nodes[neighbor_id]
                entities.append(KnowledgeEntity(
                    id=neighbor_id,
                    name=neighbor_data.get("name", ""),
                    entity_type=neighbor_data.get("entity_type", "concept"),
                    description=neighbor_data.get("description"),
                    properties=neighbor_data.get("properties", {}),
                ))
                
                # 收集关系
                for u, v, edge_data in self.graph.edges(data=True):
                    if (u in visited and v in visited):
                        if relation_type and edge_data.get("relation_type") != relation_type.value:
                            continue
                        relations.append(EntityRelation(
                            id=edge_data.get("id", str(uuid4())),
                            source_id=u,
                            target_id=v,
                            relation_type=RelationType(edge_data.get("relation_type", "related_to")),
                            properties=edge_data.get("properties", {}),
                            strength=edge_data.get("strength", 1.0),
                            bidirectional=edge_data.get("bidirectional", False),
                        ))
        
        return KnowledgeGraphResult(
            entities=entities,
            relations=relations,
            total_entities=len(entities),
            total_relations=len(relations),
        )
    
    async def get_entity_neighbors(
        self,
        entity_id: str,
        relation_type: Optional[RelationType] = None,
        depth: int = 1,
    ) -> GraphTraversalResult:
        """获取实体的邻居节点
        
        Args:
            entity_id: 实体 ID
            relation_type: 关系类型过滤
            depth: 查询深度
        
        Returns:
            图遍历结果
        """
        if entity_id not in self.graph:
            return GraphTraversalResult(traversal_depth=depth)
        
        entities = []
        relations = []
        paths = []
        visited = {entity_id}
        
        # BFS 遍历
        for neighbor_id in nx.bfs_tree(self.graph, entity_id, depth_limit=depth):
            if neighbor_id == entity_id:
                continue
            
            visited.add(neighbor_id)
            neighbor_data = self.graph.nodes[neighbor_id]
            entities.append(KnowledgeEntity(
                id=neighbor_id,
                name=neighbor_data.get("name", ""),
                entity_type=neighbor_data.get("entity_type", "concept"),
                description=neighbor_data.get("description"),
                properties=neighbor_data.get("properties", {}),
            ))
            
            # 找到路径
            try:
                path = nx.shortest_path(self.graph, entity_id, neighbor_id)
                paths.append(path)
            except nx.NetworkXNoPath:
                pass
        
        # 收集关系
        for u, v, edge_data in self.graph.edges(data=True):
            if u in visited and v in visited:
                if relation_type and edge_data.get("relation_type") != relation_type.value:
                    continue
                relations.append(EntityRelation(
                    id=edge_data.get("id", str(uuid4())),
                    source_id=u,
                    target_id=v,
                    relation_type=RelationType(edge_data.get("relation_type", "related_to")),
                    properties=edge_data.get("properties", {}),
                    strength=edge_data.get("strength", 1.0),
                    bidirectional=edge_data.get("bidirectional", False),
                ))
        
        # 添加起始实体
        start_data = self.graph.nodes[entity_id]
        entities.insert(0, KnowledgeEntity(
            id=entity_id,
            name=start_data.get("name", ""),
            entity_type=start_data.get("entity_type", "concept"),
            description=start_data.get("description"),
            properties=start_data.get("properties", {}),
        ))
        
        return GraphTraversalResult(
            entities=entities,
            relations=relations,
            paths=paths,
            traversal_depth=depth,
        )
    
    async def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_length: int = 5,
    ) -> List[List[str]]:
        """查找两个实体间的路径
        
        Args:
            source_id: 源实体 ID
            target_id: 目标实体 ID
            max_length: 最大路径长度
        
        Returns:
            路径列表（每个路径是实体 ID 列表）
        """
        if source_id not in self.graph or target_id not in self.graph:
            return []
        
        try:
            # 使用 NetworkX 查找所有简单路径
            paths = list(nx.all_simple_paths(
                self.graph,
                source_id,
                target_id,
                cutoff=max_length,
            ))
            return paths
        except nx.NetworkXNoPath:
            return []
    
    # ==================== 实体消歧 ====================
    
    async def disambiguate_entity(
        self,
        entity_name: str,
        context: str,
        candidates: List[KnowledgeEntity],
    ) -> Optional[KnowledgeEntity]:
        """实体消歧
        
        在多个候选实体中选择最符合上下文的一个。
        
        Args:
            entity_name: 实体名称
            context: 上下文文本
            candidates: 候选实体列表
        
        Returns:
            最匹配的实体，无匹配则返回 None
        """
        if not candidates:
            return None
        
        if len(candidates) == 1:
            return candidates[0]
        
        # 构建候选描述
        candidate_descriptions = []
        for i, candidate in enumerate(candidates):
            desc = f"{i+1}. {candidate.name} ({candidate.entity_type}): {candidate.description or '无描述'}"
            candidate_descriptions.append(desc)
        
        system_prompt = """你是一个实体消歧专家。
根据给定的上下文，从候选实体中选择最匹配的一个。
只返回实体编号（1, 2, 3...），不要其他解释。"""

        candidates_text = "\n".join(candidate_descriptions)
        prompt = f"""上下文：{context}

实体：{entity_name}

候选实体：
{candidates_text}

请返回最匹配的实体编号："""

        try:
            response = await self.llm_client.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
            )
            
            # 解析响应
            import re
            match = re.search(r'\d+', response.strip())
            if match:
                index = int(match.group()) - 1
                if 0 <= index < len(candidates):
                    return candidates[index]
                    
        except Exception as e:
            logger.error(f"Entity disambiguation failed: {e}")
        
        # 默认返回第一个
        return candidates[0]
    
    async def merge_entities(
        self,
        entity_ids: List[str],
        merged_name: Optional[str] = None,
    ) -> Optional[KnowledgeEntity]:
        """合并多个实体
        
        Args:
            entity_ids: 要合并的实体 ID 列表
            merged_name: 合并后的名称（可选）
        
        Returns:
            合并后的实体
        """
        if len(entity_ids) < 2:
            return await self.get_entity(entity_ids[0]) if entity_ids else None
        
        entities = []
        for eid in entity_ids:
            entity = await self.get_entity(eid)
            if entity:
                entities.append(entity)
        
        if not entities:
            return None
        
        # 合并属性
        merged_properties = {}
        for entity in entities:
            merged_properties.update(entity.properties)
        
        # 创建新实体
        merged_entity = await self.create_entity(
            name=merged_name or entities[0].name,
            entity_type=entities[0].entity_type,
            description=" | ".join(filter(None, [e.description for e in entities])),
            properties=merged_properties,
            source="merged",
            confidence=min(e.confidence for e in entities),
        )
        
        # 迁移关系
        for entity in entities:
            if entity.id == merged_entity.id:
                continue
            
            # 获取邻居
            neighbors = await self.get_entity_neighbors(entity.id)
            for relation in neighbors.relations:
                # 重新连接到新实体
                if relation.source_id == entity.id:
                    await self.create_relation(
                        source_id=merged_entity.id,
                        target_id=relation.target_id,
                        relation_type=relation.relation_type,
                        properties=relation.properties,
                        strength=relation.strength,
                    )
                elif relation.target_id == entity.id:
                    await self.create_relation(
                        source_id=relation.source_id,
                        target_id=merged_entity.id,
                        relation_type=relation.relation_type,
                        properties=relation.properties,
                        strength=relation.strength,
                    )
            
            # 删除旧实体
            self.graph.remove_node(entity.id)
            if entity.id in self.entity_cache:
                del self.entity_cache[entity.id]
        
        logger.info(f"Merged {len(entities)} entities into {merged_entity.id}")
        
        return merged_entity
    
    # ==================== 关系推断 ====================
    
    async def infer_relations(
        self,
        entity_id: str,
        max_depth: int = 2,
    ) -> List[EntityRelation]:
        """推断实体间的隐含关系
        
        使用传递闭包推断间接关系。
        
        Args:
            entity_id: 起始实体 ID
            max_depth: 最大推断深度
        
        Returns:
            推断出的关系列表
        """
        inferred_relations = []
        
        if entity_id not in self.graph:
            return inferred_relations
        
        # 获取传递闭包
        descendants = nx.descendants(self.graph, entity_id)
        
        for descendant_id in descendants:
            # 找到路径
            try:
                path = nx.shortest_path(self.graph, entity_id, descendant_id)
                if len(path) <= max_depth + 1:
                    # 推断关系
                    relation = EntityRelation(
                        source_id=entity_id,
                        target_id=descendant_id,
                        relation_type=RelationType.RELATED_TO,
                        properties={"inferred": True, "path_length": len(path) - 1},
                        strength=0.5,  # 推断关系强度较低
                        source="inferred",
                        confidence=0.7,
                    )
                    inferred_relations.append(relation)
            except nx.NetworkXNoPath:
                continue
        
        return inferred_relations
    
    # ==================== 从记忆构建图谱 ====================
    
    async def build_graph_from_memories(
        self,
        memories: List[MemoryRecord],
        extract_relations: bool = True,
    ) -> KnowledgeGraphResult:
        """从记忆记录构建知识图谱
        
        Args:
            memories: 记忆记录列表
            extract_relations: 是否提取关系
        
        Returns:
            构建的知识图谱
        """
        entities = []
        relations = []
        
        for memory in memories:
            # 提取实体
            extraction_result = await self.extract_entities(memory.content)
            
            entity_map = {}  # name -> entity
            for entity_data in extraction_result.entities:
                entity = await self.create_entity(
                    name=entity_data.get("name", ""),
                    entity_type=entity_data.get("type", "concept"),
                    description=entity_data.get("description"),
                    source=memory.source,
                    confidence=memory.confidence,
                )
                entities.append(entity)
                entity_map[entity.name] = entity
            
            # 提取关系
            if extract_relations and entity_map:
                relation_result = await self.extract_relations(
                    memory.content,
                    entities=[{"name": name} for name in entity_map.keys()],
                )
                
                for relation_data in relation_result.relations:
                    source_name = relation_data.get("source", "")
                    target_name = relation_data.get("target", "")
                    
                    if source_name in entity_map and target_name in entity_map:
                        relation = await self.create_relation(
                            source_id=entity_map[source_name].id,
                            target_id=entity_map[target_name].id,
                            relation_type=RelationType(relation_data.get("type", "related_to")),
                            properties={"description": relation_data.get("description", "")},
                            source=memory.source,
                            confidence=memory.confidence,
                        )
                        relations.append(relation)
        
        return KnowledgeGraphResult(
            entities=entities,
            relations=relations,
            total_entities=len(entities),
            total_relations=len(relations),
        )
    
    # ==================== 图谱导出 ====================
    
    async def export_to_json(
        self,
        include_embeddings: bool = False,
    ) -> Dict[str, Any]:
        """导出图谱为 JSON 格式
        
        Args:
            include_embeddings: 是否包含向量嵌入
        
        Returns:
            JSON 格式的图谱数据
        """
        nodes = []
        edges = []
        
        for node_id, node_data in self.graph.nodes(data=True):
            node = {
                "id": node_id,
                "name": node_data.get("name", ""),
                "entity_type": node_data.get("entity_type", "concept"),
                "description": node_data.get("description"),
                "properties": node_data.get("properties", {}),
                "source": node_data.get("source", "unknown"),
                "confidence": node_data.get("confidence", 1.0),
            }
            if include_embeddings:
                entity = self.entity_cache.get(node_id)
                if entity and entity.embedding:
                    node["embedding"] = entity.embedding
            nodes.append(node)
        
        for u, v, edge_data in self.graph.edges(data=True):
            edge = {
                "id": edge_data.get("id", str(uuid4())),
                "source": u,
                "target": v,
                "relation_type": edge_data.get("relation_type", "related_to"),
                "properties": edge_data.get("properties", {}),
                "strength": edge_data.get("strength", 1.0),
                "bidirectional": edge_data.get("bidirectional", False),
                "source_data": edge_data.get("source", "unknown"),
                "confidence": edge_data.get("confidence", 1.0),
            }
            edges.append(edge)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "node_count": len(nodes),
                "edge_count": len(edges),
            },
        }
    
    async def export_to_gexf(self, filepath: str) -> bool:
        """导出图谱为 GEXF 格式（用于 Gephi 等可视化工具）
        
        Args:
            filepath: 输出文件路径
        
        Returns:
            是否导出成功
        """
        try:
            # 为 NetworkX 图添加节点属性
            for node_id, node_data in self.graph.nodes(data=True):
                self.graph.nodes[node_id]["label"] = node_data.get("name", node_id)
            
            nx.write_gexf(self.graph, filepath)
            logger.info(f"Exported graph to GEXF: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export to GEXF: {e}")
            return False
    
    async def export_to_graphml(self, filepath: str) -> bool:
        """导出图谱为 GraphML 格式
        
        Args:
            filepath: 输出文件路径
        
        Returns:
            是否导出成功
        """
        try:
            nx.write_graphml(self.graph, filepath)
            logger.info(f"Exported graph to GraphML: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export to GraphML: {e}")
            return False
    
    # ==================== 图谱分析 ====================
    
    async def get_graph_stats(self) -> Dict[str, Any]:
        """获取图谱统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "is_directed": self.graph.is_directed(),
        }
        
        # 连通分量
        if not self.graph.is_directed():
            stats["connected_components"] = nx.number_connected_components(self.graph.to_undirected())
        else:
            stats["weakly_connected_components"] = nx.number_weakly_connected_components(self.graph)
            stats["strongly_connected_components"] = nx.number_strongly_connected_components(self.graph)
        
        # 度分布
        degrees = [d for n, d in self.graph.degree()]
        if degrees:
            stats["avg_degree"] = sum(degrees) / len(degrees)
            stats["max_degree"] = max(degrees)
            stats["min_degree"] = min(degrees)
        
        # 实体类型分布
        type_counts = {}
        for node_id, node_data in self.graph.nodes(data=True):
            entity_type = node_data.get("entity_type", "unknown")
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        stats["entity_type_distribution"] = type_counts
        
        return stats
    
    async def get_centrality_measures(
        self,
        top_k: int = 10,
    ) -> Dict[str, List[Tuple[str, float]]]:
        """获取中心性度量
        
        Args:
            top_k: 返回前 K 个节点
        
        Returns:
            各种中心性度量结果
        """
        measures = {}
        
        # 度中心性
        degree_centrality = nx.degree_centrality(self.graph)
        measures["degree"] = sorted(
            degree_centrality.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]
        
        # 介数中心性
        betweenness_centrality = nx.betweenness_centrality(self.graph)
        measures["betweenness"] = sorted(
            betweenness_centrality.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]
        
        # 接近中心性
        closeness_centrality = nx.closeness_centrality(self.graph)
        measures["closeness"] = sorted(
            closeness_centrality.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]
        
        # PageRank
        pagerank = nx.pagerank(self.graph)
        measures["pagerank"] = sorted(
            pagerank.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]
        
        return measures
    
    # ==================== 批量操作 ====================
    
    async def batch_create_entities(
        self,
        entity_data_list: List[Dict[str, Any]],
    ) -> List[KnowledgeEntity]:
        """批量创建实体
        
        Args:
            entity_data_list: 实体数据列表
        
        Returns:
            创建的实体列表
        """
        entities = []
        for data in entity_data_list:
            entity = await self.create_entity(
                name=data.get("name", ""),
                entity_type=data.get("entity_type", "concept"),
                description=data.get("description"),
                properties=data.get("properties", {}),
                source=data.get("source", "unknown"),
                confidence=data.get("confidence", 1.0),
            )
            entities.append(entity)
        
        return entities
    
    async def batch_create_relations(
        self,
        relation_data_list: List[Dict[str, Any]],
    ) -> List[EntityRelation]:
        """批量创建关系
        
        Args:
            relation_data_list: 关系数据列表
        
        Returns:
            创建的关系列表
        """
        relations = []
        for data in relation_data_list:
            relation = await self.create_relation(
                source_id=data.get("source_id", ""),
                target_id=data.get("target_id", ""),
                relation_type=RelationType(data.get("relation_type", "related_to")),
                properties=data.get("properties", {}),
                strength=data.get("strength", 1.0),
                bidirectional=data.get("bidirectional", False),
                source=data.get("source", "unknown"),
                confidence=data.get("confidence", 1.0),
            )
            relations.append(relation)
        
        return relations
    
    async def clear_graph(self) -> None:
        """清空图谱"""
        self.graph.clear()
        self.entity_cache.clear()
        self.relation_cache.clear()
        
        # 清空 Neo4j
        driver = await self._get_neo4j_driver()
        if driver:
            try:
                async with driver.session() as session:
                    await session.run("MATCH (n) DETACH DELETE n")
                    logger.info("Cleared Neo4j graph")
            except Exception as e:
                logger.error(f"Failed to clear Neo4j graph: {e}")
        
        logger.info("Cleared knowledge graph")


# 全局服务实例
_kg_service: Optional[KnowledgeGraphService] = None


def get_knowledge_graph_service(
    llm_client: Optional[LLMClient] = None,
    neo4j_uri: Optional[str] = None,
    neo4j_user: Optional[str] = None,
    neo4j_password: Optional[str] = None,
) -> KnowledgeGraphService:
    """获取知识图谱服务实例
    
    Args:
        llm_client: LLM 客户端
        neo4j_uri: Neo4j URI
        neo4j_user: Neo4j 用户名
        neo4j_password: Neo4j 密码
    
    Returns:
        KnowledgeGraphService 实例
    """
    global _kg_service
    if _kg_service is None:
        _kg_service = KnowledgeGraphService(
            llm_client=llm_client,
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
        )
    return _kg_service


async def close_knowledge_graph_service() -> None:
    """关闭全局知识图谱服务"""
    global _kg_service
    if _kg_service is not None:
        await _kg_service.close()
        _kg_service = None

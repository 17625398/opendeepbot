#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
知识图谱构建Agent

基于graph-rag-agent的知识图谱构建能力，为DeepTutor的笔录分析系统提供知识图谱构建功能。
"""

import os
import time
from typing import Any, Dict, List, Optional

from deeptutor.agents.interrogation.data_structures import (
    AnalysisResult,
    ExtractedInfo,
    InterrogationRecord,
    RelationData,
)
from deeptutor.core.llm import get_llm_config
from deeptutor.logging import get_logger


class KnowledgeGraphAgent:
    """知识图谱构建Agent"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        binding: Optional[str] = None
    ):
        """
        初始化知识图谱构建Agent
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
            binding: 绑定类型
        
        Configuration:
            Uses unified KGConfig from deeptutor.tools.kg_config
            Priority: provided params > environment variables > defaults
        """
        from deeptutor.tools.kg_config import get_kg_config, get_llm_settings
        
        # Get unified knowledge graph configuration
        kg_config = get_kg_config()
        llm_settings = get_llm_settings()
        
        # Use unified config with parameter override
        self.api_key = api_key or llm_settings.get("api_key") or getattr(get_llm_config(), "api_key", None)
        self.base_url = base_url or llm_settings.get("base_url") or getattr(get_llm_config(), "base_url", None)
        self.model = model or llm_settings.get("model") or getattr(get_llm_config(), "model", "gpt-4")
        self.binding = binding or llm_settings.get("provider") or getattr(get_llm_config(), "binding", "openai")
        
        # Neo4j settings from KGConfig
        self.neo4j_uri = kg_config.neo4j_uri
        self.neo4j_user = kg_config.neo4j_user
        self.neo4j_password = kg_config.neo4j_password
        
        self.logger = get_logger("KnowledgeGraphAgent")
        self.logger.info(f"初始化KnowledgeGraphAgent: model={self.model}, binding={self.binding}, neo4j={self.neo4j_uri}")
        
        # 初始化缓存
        self.cache = {}
        self.cache_ttl = kg_config.extraction_timeout if kg_config.extraction_timeout else 3600  # 使用配置的超时时间
        
        # 延迟导入graph-rag-agent组件，避免循环依赖
        self._initialize_graph_components()
    
    def _initialize_graph_components(self):
        """初始化知识图谱构建组件"""
        try:
            # 导入graph-rag-agent的核心组件
            from graphrag_agent.config.neo4jdb import get_db_manager
            from graphrag_agent.config.prompts import (
                human_template_build_graph,
                system_template_build_graph,
            )
            from graphrag_agent.config.settings import (
                BATCH_SIZE,
                CHUNK_SIZE,
                MAX_WORKERS,
                OVERLAP,
                entity_types,
                relationship_types,
                theme,
            )
            from graphrag_agent.graph import (
                EntityRelationExtractor,
                GraphStructureBuilder,
                GraphWriter,
            )
            from graphrag_agent.models.get_models import get_embeddings_model, get_llm_model
            from graphrag_agent.pipelines.ingestion.document_processor import DocumentProcessor
            
            # 保存导入的组件
            self.get_llm_model = get_llm_model
            self.get_embeddings_model = get_embeddings_model
            self.system_template_build_graph = system_template_build_graph
            self.human_template_build_graph = human_template_build_graph
            self.entity_types = entity_types
            self.relationship_types = relationship_types
            self.theme = theme
            self.CHUNK_SIZE = CHUNK_SIZE
            self.OVERLAP = OVERLAP
            self.MAX_WORKERS = MAX_WORKERS
            self.BATCH_SIZE = BATCH_SIZE
            self.get_db_manager = get_db_manager
            self.DocumentProcessor = DocumentProcessor
            self.GraphStructureBuilder = GraphStructureBuilder
            self.EntityRelationExtractor = EntityRelationExtractor
            self.GraphWriter = GraphWriter
            
            self.logger.info("成功导入graph-rag-agent组件")
        except Exception as e:
            self.logger.error(f"导入graph-rag-agent组件失败: {e}")
            raise
    
    def _generate_cache_key(self, record: InterrogationRecord) -> str:
        """
        生成缓存键
        
        Args:
            record: 笔录记录
            
        Returns:
            缓存键字符串
        """
        import hashlib
        content_hash = hashlib.md5(record.content.encode('utf-8')).hexdigest()
        cache_key = f"kg_{record.case_id}_{content_hash}"
        return cache_key
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        从缓存获取结果
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存的结果，如果不存在或已过期则返回None
        """
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            timestamp = cached_data.get('timestamp', 0)
            if time.time() - timestamp < self.cache_ttl:
                self.logger.info(f"从缓存获取知识图谱构建结果: {cache_key}")
                return cached_data.get('result')
            else:
                # 缓存已过期，删除
                del self.cache[cache_key]
                self.logger.info(f"缓存已过期，删除: {cache_key}")
        return None
    
    def _set_to_cache(self, cache_key: str, result: Dict[str, Any]):
        """
        将结果存入缓存
        
        Args:
            cache_key: 缓存键
            result: 知识图谱构建结果
        """
        self.cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
        self.logger.info(f"知识图谱构建结果已存入缓存: {cache_key}")
    
    def _clear_cache(self):
        """
        清除所有缓存
        """
        self.cache.clear()
        self.logger.info("知识图谱构建缓存已清空")
    
    async def process(
        self,
        record: InterrogationRecord,
        extracted_info: ExtractedInfo,
        relations: RelationData
    ) -> Dict[str, Any]:
        """
        构建知识图谱
        
        Args:
            record: 笔录记录
            extracted_info: 提取的信息
            relations: 关联关系数据
            
        Returns:
            知识图谱构建结果
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(record)
        
        # 尝试从缓存获取结果
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        self.logger.info(f"开始构建知识图谱: {record.case_id}")
        
        try:
            # 1. 初始化模型
            llm = self.get_llm_model()
            embeddings = self.get_embeddings_model()
            
            # 2. 初始化图数据库连接
            db_manager = self.get_db_manager()
            graph = db_manager.graph
            
            # 3. 准备文档数据
            # 将笔录内容转换为graph-rag-agent期望的格式
            file_contents = [
                (
                    record.case_id,
                    record.content
                )
            ]
            
            # 4. 使用DocumentProcessor处理文件
            document_processor = self.DocumentProcessor(
                ".",  # 临时目录
                self.CHUNK_SIZE,
                self.OVERLAP
            )
            
            # 5. 初始化GraphStructureBuilder
            struct_builder = self.GraphStructureBuilder(batch_size=self.BATCH_SIZE)
            
            # 6. 初始化EntityRelationExtractor
            entity_extractor = self.EntityRelationExtractor(
                llm,
                self.system_template_build_graph,
                self.human_template_build_graph,
                self.entity_types,
                self.relationship_types,
                max_workers=self.MAX_WORKERS,
                batch_size=5  # LLM批处理大小保持小一些以确保质量
            )
            
            # 7. 初始化GraphWriter
            graph_writer = self.GraphWriter(
                graph,
                batch_size=50,
                max_workers=os.cpu_count() or 4
            )
            
            # 8. 处理文件和分块
            processed_documents = []
            for filename, content in file_contents:
                # 创建文档处理结果
                doc = {
                    "filepath": filename,
                    "filename": filename,
                    "extension": ".txt",
                    "content": content,
                    "content_length": len(content),
                    "chunks": None
                }
                
                # 对文本内容进行分块
                try:
                    # 使用document_processor的chunker进行分块
                    chunks = document_processor.chunker.chunk_text(content)
                    doc["chunks"] = chunks
                    doc["chunk_count"] = len(chunks)
                    
                    # 计算每个块的长度
                    chunk_lengths = [len(''.join(chunk)) for chunk in chunks]
                    doc["chunk_lengths"] = chunk_lengths
                    doc["average_chunk_length"] = sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0
                    
                except Exception as e:
                    doc["chunk_error"] = str(e)
                    self.logger.warning(f"分块错误 ({filename}): {str(e)}")
                
                processed_documents.append(doc)
            
            # 9. 构建图结构
            for doc in processed_documents:
                if "chunks" in doc and doc["chunks"]:  # 只处理成功分块的文档
                    # 清空并创建Document节点
                    struct_builder.clear_database()
                    struct_builder.create_document(
                        type="local",
                        uri=".",
                        file_name=doc["filename"],
                        domain=self.theme
                    )
                    
                    # 创建Chunk节点和关系
                    chunks = doc["chunks"]
                    if doc.get("chunk_count", 0) > 100:
                        # 对于大文件使用并行处理
                        result = struct_builder.parallel_process_chunks(
                            doc["filename"],
                            chunks,
                            max_workers=os.cpu_count() or 4
                        )
                    else:
                        # 对于小文件使用标准批处理
                        result = struct_builder.create_relation_between_chunks(
                            doc["filename"],
                            chunks
                        )
                    doc["graph_result"] = result
            
            # 10. 提取实体和关系
            file_contents_format = []
            for doc in processed_documents:
                if "chunks" in doc and doc["chunks"]:
                    file_contents_format.append([
                        doc["filename"],
                        doc["content"],
                        doc["chunks"]
                    ])
            
            # 根据数据集大小选择处理方法
            total_chunks = sum(doc.get("chunk_count", 0) for doc in processed_documents)
            if total_chunks > 100:
                # 对于大型数据集使用批处理模式
                processed_file_contents = entity_extractor.process_chunks_batch(
                    file_contents_format
                )
            else:
                # 对于小型数据集使用标准并行处理
                processed_file_contents = entity_extractor.process_chunks(
                    file_contents_format
                )
            
            # 11. 将处理结果合并回文档数据
            file_content_map = {}
            for processed_file in processed_file_contents:
                if len(processed_file) >= 4:  # 确保有足够的元素
                    filename = processed_file[0]
                    entity_data = processed_file[3]
                    file_content_map[filename] = entity_data
            
            # 使用映射将结果放回到原始文档中
            for doc in processed_documents:
                if "chunks" in doc and doc["chunks"]:
                    filename = doc["filename"]
                    if filename in file_content_map:
                        doc["entity_data"] = file_content_map[filename]
                    else:
                        self.logger.warning(f"警告: 文件 {filename} 的实体抽取结果未找到")
            
            # 12. 写入数据库
            graph_writer_data = []
            for doc in processed_documents:
                if "chunks" in doc and doc["chunks"] and "entity_data" in doc:
                    # 获取图构建结果（创建的chunk节点列表）
                    graph_result = doc.get("graph_result", [])
                    entity_data = doc.get("entity_data", [])
                    
                    # 确保graph_result和entity_data存在且长度相等
                    if not graph_result:
                        self.logger.warning(f"警告: 文件 {doc['filename']} 的图结构结果缺失")
                        continue
                        
                    if not entity_data or not isinstance(entity_data, list):
                        self.logger.warning(f"警告: 文件 {doc['filename']} 的实体数据缺失或格式不正确")
                        continue
                        
                    # 调整数据格式以匹配GraphWriter期望的结构
                    graph_writer_data.append([
                        doc["filename"],
                        doc["content"],
                        doc["chunks"],
                        graph_result,  # 这应该是chunks_with_hash数据
                        entity_data,    # 这应该是实体提取结果
                    ])
            
            # 使用GraphWriter写入数据
            if graph_writer_data:
                graph_writer.process_and_write_graph_documents(graph_writer_data)
                self.logger.info(f"成功写入 {len(graph_writer_data)} 个文档到数据库")
            
            # 13. 生成知识图谱构建结果
            result = {
                "success": True,
                "case_id": record.case_id,
                "total_documents": len(processed_documents),
                "total_chunks": total_chunks,
                "total_entities": sum(len(doc.get("entity_data", [])) for doc in processed_documents),
                "message": "知识图谱构建成功"
            }
            
            self.logger.info(f"知识图谱构建完成: {result}")
            
            # 将结果存入缓存
            self._set_to_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"知识图谱构建失败: {e}", exc_info=True)
            error_result = {
                "success": False,
                "case_id": record.case_id,
                "error": str(e),
                "message": "知识图谱构建失败"
            }
            
            # 错误结果也存入缓存，避免重复尝试失败的构建
            self._set_to_cache(cache_key, error_result)
            
            return error_result
    
    async def process_batch(
        self,
        records: List[InterrogationRecord],
        individual_results: List[AnalysisResult]
    ) -> Dict[str, Any]:
        """
        批量构建知识图谱
        
        Args:
            records: 笔录记录列表
            individual_results: 每份笔录的分析结果
            
        Returns:
            批量知识图谱构建结果
        """
        # 生成批量缓存键
        import hashlib
        combined_hash = hashlib.md5(
            ''.join(record.content for record in records).encode('utf-8')
        ).hexdigest()
        batch_cache_key = f"batch_kg_{combined_hash}"
        
        # 尝试从缓存获取批量结果
        cached_batch_result = self._get_from_cache(batch_cache_key)
        if cached_batch_result:
            return cached_batch_result
        
        self.logger.info(f"开始批量构建知识图谱: {len(records)} 份笔录")
        
        try:
            results = []
            for record, analysis_result in zip(records, individual_results):
                result = await self.process(
                    record,
                    analysis_result.extracted_info,
                    analysis_result.relations
                )
                results.append(result)
            
            # 汇总结果
            success_count = sum(1 for r in results if r.get("success", False))
            total_count = len(results)
            
            batch_result = {
                "success": success_count == total_count,
                "total_records": total_count,
                "success_count": success_count,
                "failure_count": total_count - success_count,
                "results": results,
                "message": f"批量知识图谱构建完成: {success_count}/{total_count} 成功"
            }
            
            # 将批量结果存入缓存
            self._set_to_cache(batch_cache_key, batch_result)
            
            self.logger.info(f"批量知识图谱构建完成: {batch_result}")
            return batch_result
            
        except Exception as e:
            self.logger.error(f"批量知识图谱构建失败: {e}", exc_info=True)
            batch_error_result = {
                "success": False,
                "total_records": len(records),
                "error": str(e),
                "message": "批量知识图谱构建失败"
            }
            
            # 错误结果也存入缓存
            self._set_to_cache(batch_cache_key, batch_error_result)
            
            return batch_error_result

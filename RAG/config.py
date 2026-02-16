"""
API Configuration and Client Initialization
配置 SiliconFlow API 和数据库客户端

Author: EV PM DSS Team
Date: 2026-02-15
"""

import os
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from chromadb.config import Settings
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# ==================== SiliconFlow API Client ====================
class SiliconFlowClient:
    """SiliconFlow API 客户端（OpenAI 兼容接口）"""
    
    def __init__(self):
        self.api_base = os.getenv("SILICONFLOW_API_BASE", "https://api.siliconflow.cn/v1")
        self.api_key = os.getenv("SILICONFLOW_API_KEY")
        
        if not self.api_key:
            raise ValueError("SILICONFLOW_API_KEY not found in environment variables")
        
        # Initialize OpenAI-compatible client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
        
        # Model configuration
        self.model_reasoning = os.getenv("MODEL_REASONING", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B")
        self.model_routing = os.getenv("MODEL_ROUTING", "Qwen/Qwen2.5-7B-Instruct")
        self.model_reranker = os.getenv("MODEL_RERANKER", "BAAI/bge-reranker-v2-m3")
    
    def chat(self, messages: list, model: Optional[str] = None, **kwargs):
        """调用聊天接口"""
        model = model or self.model_reasoning
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
        return response


# ==================== Vector Database Client ====================
class VectorDBClient:
    """ChromaDB 客户端"""
    
    def __init__(self):
        self.db_path = os.getenv("VECTOR_DB_PATH", "Data/Vector")
        
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Load embedding model
        embedding_model_name = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
        # Get collections
        self.ugc_collection = self.client.get_collection("ugc_reviews")
        self.specs_collection = self.client.get_collection("vehicle_specs")
        self.persona_collection = self.client.get_collection("user_personas")
    
    def query(self, collection_name: str, query_texts: list, n_results: int = 5, **kwargs):
        """查询向量集合"""
        collection = self.client.get_collection(collection_name)
        results = collection.query(
            query_texts=query_texts,
            n_results=n_results,
            **kwargs
        )
        return results


# ==================== Graph Database Client ====================
class GraphDBClient:
    """Neo4j 客户端"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        
        if not self.uri or not self.password:
            raise ValueError("NEO4J_URI or NEO4J_PASSWORD not found in environment variables")
        
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password)
        )
    
    def query(self, cypher: str, parameters: Optional[dict] = None):
        """执行 Cypher 查询"""
        with self.driver.session() as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]
    
    def close(self):
        """关闭连接"""
        self.driver.close()


# ==================== Singleton Instances ====================
# 全局客户端实例（延迟初始化）
_siliconflow_client: Optional[SiliconFlowClient] = None
_vector_client: Optional[VectorDBClient] = None
_graph_client: Optional[GraphDBClient] = None


def get_siliconflow_client() -> SiliconFlowClient:
    """获取 SiliconFlow 客户端单例"""
    global _siliconflow_client
    if _siliconflow_client is None:
        _siliconflow_client = SiliconFlowClient()
    return _siliconflow_client


def get_vector_client() -> VectorDBClient:
    """获取向量数据库客户端单例"""
    global _vector_client
    if _vector_client is None:
        _vector_client = VectorDBClient()
    return _vector_client


def get_graph_client() -> GraphDBClient:
    """获取图数据库客户端单例"""
    global _graph_client
    if _graph_client is None:
        _graph_client = GraphDBClient()
    return _graph_client

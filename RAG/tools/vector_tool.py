"""
Vector Retriever Tool - 向量检索工具
语义搜索 UGC 评论、车型规格和用户画像

Author: EV PM DSS Team
Date: 2026-02-15
"""

from typing import List, Dict, Optional
from RAG.config import get_vector_client


class VectorRetriever:
    """向量检索工具"""
    
    def __init__(self):
        self.client = get_vector_client()
        # 使用与构建时相同的嵌入模型
        self.embedding_model = self.client.embedding_model
    
    def _embed_query(self, query: str):
        """使用 SentenceTransformer 嵌入查询"""
        return self.embedding_model.encode([query])[0].tolist()
    
    def search_ugc_reviews(
        self,
        query: str,
        n_results: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        搜索 UGC 评论
        
        Args:
            query: 查询文本（如"Model Y 内饰怎么样"）
            n_results: 返回结果数量
            filters: 元数据过滤器（如 {"brand": "Tesla", "series": "Model Y"}）
        
        Returns:
            List of documents with metadata
        """
        where = filters if filters else None
        
        # 使用自定义嵌入
        query_embedding = self._embed_query(query)
        
        results = self.client.ugc_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        # Format results
        documents = []
        for i in range(len(results['ids'][0])):
            doc = {
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            }
            documents.append(doc)
        
        return documents
    
    def search_vehicle_specs(
        self,
        query: str,
        n_results: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        搜索车型规格
        
        Args:
            query: 查询文本（如"续航600km以上的SUV"）
            n_results: 返回结果数量
            filters: 元数据过滤器
        
        Returns:
            List of vehicle specs documents
        """
        where = filters if filters else None
        
        query_embedding = self._embed_query(query)
        
        results = self.client.specs_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        documents = []
        for i in range(len(results['ids'][0])):
            doc = {
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            }
            documents.append(doc)
        
        return documents
    
    def search_personas(
        self,
        query: str,
        n_results: int = 3
    ) -> List[Dict]:
        """
        搜索用户画像
        
        Args:
            query: 查询文本（如"关注智能化的用户"）
            n_results: 返回结果数量
        
        Returns:
            List of persona documents
        """
        query_embedding = self._embed_query(query)
        
        results = self.client.persona_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        documents = []
        for i in range(len(results['ids'][0])):
            doc = {
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            }
            documents.append(doc)
        
        return documents


# ==================== Utility Functions ====================
def format_ugc_context(documents: List[Dict], max_docs: int = 5) -> str:
    """
    格式化 UGC 文档为 LLM 上下文
    
    Args:
        documents: 检索到的文档列表
        max_docs: 最多使用的文档数量
    
    Returns:
        Formatted context string
    """
    context_parts = []
    
    for i, doc in enumerate(documents[:max_docs], 1):
        meta = doc['metadata']
        text = doc['text']
        
        # Extract key metadata
        brand = meta.get('brand', 'Unknown')
        series = meta.get('series', 'Unknown')
        model = meta.get('model', 'Unknown')
        dimension = meta.get('dimension', 'summary')
        
        context_parts.append(
            f"[评论 {i}] {brand} {series} {model} - {dimension}\n{text}\n"
        )
    
    return "\n".join(context_parts)


def format_specs_context(documents: List[Dict]) -> str:
    """格式化车型规格为 LLM 上下文"""
    context_parts = []
    
    for i, doc in enumerate(documents, 1):
        meta = doc['metadata']
        text = doc['text']
        
        brand = meta.get('brand', 'Unknown')
        series = meta.get('series', 'Unknown')
        model = meta.get('model', 'Unknown')
        
        context_parts.append(
            f"[车型 {i}] {brand} {series} {model}\n{text}\n"
        )
    
    return "\n".join(context_parts)

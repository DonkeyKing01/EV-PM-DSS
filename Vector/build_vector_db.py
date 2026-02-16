"""
ChromaDB Vector Database Builder for EV PM DSS
向量数据库构建脚本 - 处理并嵌入 UGC、车型规格和用户画像数据

Author: EV PM DSS Team
Date: 2026-02-15
"""

import os
import json
import pandas as pd
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== Configuration ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Data")
VECTOR_DB_PATH = os.path.join(DATA_DIR, "Vector")

# 数据文件路径
UGC_FILE = os.path.join(DATA_DIR, "Processed", "ugc.csv")
CONFIG_FILE = os.path.join(DATA_DIR, "Processed", "vehicles_config.json")
PERSONA_FILE = os.path.join(DATA_DIR, "Analyzed", "Persona", "step4_user_persona_full.csv")

# ==================== Logging ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vector_build.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class VectorDBBuilder:
    """ChromaDB 向量数据库构建器"""
    
    def __init__(self, embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        初始化构建器
        
        Args:
            embedding_model: SentenceTransformer 模型名称
                - 'all-MiniLM-L6-v2': 轻量级英文模型 (384维)
                - 'paraphrase-multilingual-MiniLM-L12-v2': 多语言模型 (384维)
                - 'distiluse-base-multilingual-cased-v2': 多语言高性能 (512维)
        """
        logger.info(f"Initializing VectorDBBuilder with model: {embedding_model}")
        
        # 初始化 Embedding 模型
        self.embedding_model = SentenceTransformer(embedding_model)
        logger.info(f"Embedding dimension: {self.embedding_model.get_sentence_embedding_dimension()}")
        
        # 初始化 ChromaDB 客户端
        self.client = chromadb.PersistentClient(
            path=VECTOR_DB_PATH,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        logger.info(f"ChromaDB initialized at: {VECTOR_DB_PATH}")
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """生成文本的向量嵌入"""
        return self.embedding_model.encode(texts, show_progress_bar=True).tolist()
    
    def build_ugc_collection(self, limit: int = None):
        """
        构建 UGC 评论向量集合
        
        Args:
            limit: 限制处理的评论数量（测试用），None 表示全部
        """
        logger.info("=" * 70)
        logger.info("Building UGC Reviews Vector Collection")
        logger.info("=" * 70)
        
        # 创建或获取集合
        collection = self.client.get_or_create_collection(
            name="ugc_reviews",
            metadata={"description": "User-generated content reviews"}
        )
        
        # 读取数据
        logger.info(f"Loading UGC data from {UGC_FILE}")
        df = pd.read_csv(UGC_FILE)
        
        if limit:
            df = df.head(limit)
            logger.info(f"Limited to {limit} reviews for testing")
        
        logger.info(f"Total reviews to process: {len(df)}")
        
        # 准备数据
        documents = []
        metadatas = []
        ids = []
        
        dimensions = ['appearance', 'interior', 'space', 'intelligence', 'driving', 'range', 'value']
        
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing reviews"):
            review_id = str(row['review_id'])
            row_idx = int(idx)  # 使用行索引确保唯一性
            
            # 1. 全文评论（如果有综合评论字段）
            # 这里我们组合最满意和最不满意作为摘要
            summary_parts = []
            if pd.notna(row.get('most_satisfied')):
                summary_parts.append(f"最满意: {row['most_satisfied']}")
            if pd.notna(row.get('least_satisfied')):
                summary_parts.append(f"最不满意: {row['least_satisfied']}")
            
            if summary_parts:
                full_text = " | ".join(summary_parts)
                documents.append(full_text)
                metadatas.append({
                    "review_id": review_id,
                    "type": "summary",
                    "brand": str(row['brand']) if pd.notna(row['brand']) else "",
                    "series": str(row['series']) if pd.notna(row['series']) else "",
                    "model": str(row['model']) if pd.notna(row['model']) else "",
                    "date": str(row['review_date']) if pd.notna(row['review_date']) else "",
                    "location": str(row['purchase_location']) if pd.notna(row['purchase_location']) else ""
                })
                ids.append(f"review_{row_idx}_summary")
            
            # 2. 分维度评论
            for dim in dimensions:
                review_col = f'{dim}_review'
                score_col = f'{dim}_score'
                
                review_text = row.get(review_col)
                if pd.notna(review_text) and str(review_text).strip():
                    documents.append(str(review_text))
                    metadatas.append({
                        "review_id": review_id,
                        "type": "dimension_review",
                        "dimension": dim,
                        "score": float(row[score_col]) if pd.notna(row.get(score_col)) else None,
                        "brand": str(row['brand']) if pd.notna(row['brand']) else "",
                        "series": str(row['series']) if pd.notna(row['series']) else "",
                        "model": str(row['model']) if pd.notna(row['model']) else ""
                    })
                    ids.append(f"review_{row_idx}_{dim}")
        
        logger.info(f"Prepared {len(documents)} text documents for embedding")
        
        # 批量嵌入和存储
        batch_size = 5000
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_meta = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            embeddings = self.embed_texts(batch_docs)
            
            collection.add(
                documents=batch_docs,
                embeddings=embeddings,
                metadatas=batch_meta,
                ids=batch_ids
            )
        
        logger.info(f"✅ UGC collection built successfully! Total documents: {collection.count()}")
    
    def build_vehicle_specs_collection(self):
        """构建车型规格向量集合"""
        logger.info("=" * 70)
        logger.info("Building Vehicle Specs Vector Collection")
        logger.info("=" * 70)
        
        collection = self.client.get_or_create_collection(
            name="vehicle_specs",
            metadata={"description": "Vehicle specifications and features"}
        )
        
        # 读取车型配置
        logger.info(f"Loading vehicle config from {CONFIG_FILE}")
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            vehicles = json.load(f)
        
        logger.info(f"Total vehicles to process: {len(vehicles)}")
        
        documents = []
        metadatas = []
        ids = []
        
        for vehicle in tqdm(vehicles, desc="Processing vehicles"):
            model_name = vehicle['model']
            
            # 构建描述性文本
            desc_parts = [
                f"车型: {model_name}",
                f"品牌: {vehicle['brand']}",
                f"车系: {vehicle['series']}",
                f"价格: {vehicle.get('price', 'N/A')}万元"
            ]
            
            # 添加关键配置
            if vehicle.get('battery'):
                battery = vehicle['battery']
                desc_parts.append(f"电池: {battery.get('capacity', 'N/A')}kWh {battery.get('type', '')}")
                desc_parts.append(f"续航: {battery.get('cltc_range', 'N/A')}km")
            
            if vehicle.get('intelligence'):
                intel = vehicle['intelligence']
                if intel.get('cockpit_system'):
                    desc_parts.append(f"座舱系统: {intel['cockpit_system']}")
                if intel.get('adas_system'):
                    desc_parts.append(f"智驾系统: {intel['adas_system']}")
                if intel.get('lidar_count', 0) > 0:
                    desc_parts.append(f"激光雷达: {intel['lidar_count']}个")
            
            if vehicle.get('performance'):
                perf = vehicle['performance']
                if perf.get('acceleration_0_100'):
                    desc_parts.append(f"百公里加速: {perf['acceleration_0_100']}秒")
            
            full_desc = " | ".join(desc_parts)
            
            documents.append(full_desc)
            metadatas.append({
                "model": model_name,
                "brand": vehicle['brand'],
                "series": vehicle['series'],
                "price": vehicle.get('price'),
                "category": vehicle.get('category', '')
            })
            ids.append(model_name.replace(' ', '_'))
        
        # 嵌入和存储
        logger.info("Generating embeddings...")
        embeddings = self.embed_texts(documents)
        
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"✅ Vehicle specs collection built successfully! Total documents: {collection.count()}")
    
    def build_persona_collection(self):
        """构建用户画像向量集合"""
        logger.info("=" * 70)
        logger.info("Building Persona Vector Collection")
        logger.info("=" * 70)
        
        collection = self.client.get_or_create_collection(
            name="user_personas",
            metadata={"description": "User persona descriptions"}
        )
        
        # 读取画像数据
        logger.info(f"Loading persona data from {PERSONA_FILE}")
        df = pd.read_csv(PERSONA_FILE)
        
        # 计算画像质心和统计
        weight_cols = [c for c in df.columns if c.startswith('w_')]
        persona_stats = df.groupby('persona_name').agg({
            'review_id': 'count',
            **{col: 'mean' for col in weight_cols}
        }).reset_index()
        
        logger.info(f"Total personas to process: {len(persona_stats)}")
        
        documents = []
        metadatas = []
        ids = []
        
        dimension_names = {
            'w_appearance': '外观',
            'w_interior': '内饰',
            'w_space': '空间',
            'w_intelligence': '智能化',
            'w_driving': '驾驶感受',
            'w_range': '续航',
            'w_value': '性价比'
        }
        
        for _, row in persona_stats.iterrows():
            persona_name = row['persona_name']
            user_count = int(row['review_id'])
            
            # 找出 Top 3 关注维度
            weights = {dim: row[col] for col, dim in dimension_names.items()}
            top_dims = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # 构建描述
            desc = f"用户画像: {persona_name} | 用户数量: {user_count} | "
            desc += "关注重点: " + ", ".join([f"{dim}({weight:.2f})" for dim, weight in top_dims])
            
            documents.append(desc)
            metadatas.append({
                "persona_name": persona_name,
                "user_count": user_count,
                **{f"centroid_{dim}": float(row[col]) for col, dim in dimension_names.items()}
            })
            ids.append(persona_name.replace(' ', '_'))
        
        # 嵌入和存储
        logger.info("Generating embeddings...")
        embeddings = self.embed_texts(documents)
        
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"✅ Persona collection built successfully! Total documents: {collection.count()}")
    
    def build_all(self, ugc_limit: int = None):
        """
        构建所有向量集合
        
        Args:
            ugc_limit: UGC 评论数量限制（测试用）
        """
        logger.info("🚀 Starting Vector Database Construction")
        logger.info(f"Database path: {VECTOR_DB_PATH}")
        
        try:
            # 1. UGC 评论
            self.build_ugc_collection(limit=ugc_limit)
            
            # 2. 车型规格
            self.build_vehicle_specs_collection()
            
            # 3. 用户画像
            self.build_persona_collection()
            
            logger.info("=" * 70)
            logger.info("✅ All vector collections built successfully!")
            logger.info("=" * 70)
            
            # 输出统计
            logger.info("\nCollection Statistics:")
            for coll_name in ["ugc_reviews", "vehicle_specs", "user_personas"]:
                coll = self.client.get_collection(coll_name)
                logger.info(f"  - {coll_name}: {coll.count()} documents")
            
        except Exception as e:
            logger.error(f"Error during vector DB construction: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build ChromaDB Vector Database")
    parser.add_argument(
        "--limit", 
        type=int, 
        default=None,
        help="Limit number of UGC reviews (for testing)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="paraphrase-multilingual-MiniLM-L12-v2",
        help="Embedding model name"
    )
    
    args = parser.parse_args()
    
    builder = VectorDBBuilder(embedding_model=args.model)
    builder.build_all(ugc_limit=args.limit)

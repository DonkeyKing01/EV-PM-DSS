"""
Neo4j Knowledge Graph Builder for EV PM DSS
构建新能源车决策支持系统的知识图谱

Author: EV PM DSS Team
Date: 2026-02-15
"""

import os
import json
import logging
import pandas as pd
from neo4j import GraphDatabase
from datetime import datetime
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# ==================== Configuration ====================
# 从环境变量读取配置（请在项目根目录创建 .env 文件）
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# ==================== Data Paths ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Data")

CONFIG_FILE = os.path.join(DATA_DIR, "Processed", "vehicles_config.json")
UGC_FILE = os.path.join(DATA_DIR, "Processed", "ugc.csv")
IPA_FILE = os.path.join(DATA_DIR, "Analyzed", "IPA", "step1_scores_matrix.csv")
PERSONA_FILE = os.path.join(DATA_DIR, "Analyzed", "Persona", "step4_user_persona_full.csv")

# ==================== Logging ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('graph_build.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Neo4jGraphBuilder:
    """Neo4j 知识图谱构建器"""
    
    def __init__(self, uri, user, password, database="neo4j"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password), database=database)
        logger.info("Connected to Neo4j Aura")

    def close(self):
        self.driver.close()
        logger.info("Connection closed")

    def run_query(self, query, parameters=None):
        """执行 Cypher 查询"""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return result

    def create_constraints(self):
        """创建唯一性约束"""
        logger.info("Creating constraints...")
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (b:Brand) REQUIRE b.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Series) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Model) REQUIRE m.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Persona) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Review) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Dimension) REQUIRE d.name IS UNIQUE"
        ]
        for constraint_query in constraints:
            self.run_query(constraint_query)
        logger.info("Constraints created successfully")

    def import_dimensions(self):
        """导入评价维度节点"""
        logger.info("Importing Dimensions...")
        dimensions = [
            {"name": "appearance", "name_cn": "外观"},
            {"name": "interior", "name_cn": "内饰"},
            {"name": "space", "name_cn": "空间"},
            {"name": "intelligence", "name_cn": "智能化"},
            {"name": "driving", "name_cn": "驾驶"},
            {"name": "range", "name_cn": "续航"},
            {"name": "value", "name_cn": "性价比"}
        ]
        query = """
        UNWIND $batch AS row
        MERGE (d:Dimension {name: row.name})
        SET d.name_cn = row.name_cn
        """
        self.run_query(query, {"batch": dimensions})
        logger.info(f"Imported {len(dimensions)} dimensions")

    def import_vehicles(self):
        """导入车型层级数据 (Brand -> Series -> Model)"""
        logger.info("Loading vehicle configuration...")
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            vehicles = json.load(f)

        brands = set()
        series_data = {}
        models = []

        # 加载 IPA 数据
        logger.info("Loading IPA scores...")
        ipa_df = pd.read_csv(IPA_FILE)
        ipa_lookup = ipa_df.set_index('series').to_dict('index')

        # 处理车型数据
        for v in vehicles:
            brands.add(v['brand'])
            
            # Series 数据
            if v['series'] not in series_data:
                series_data[v['series']] = {
                    "name": v['series'],
                    "brand": v['brand']
                }
                # 合并 IPA 分数
                if v['series'] in ipa_lookup:
                    series_data[v['series']].update(ipa_lookup[v['series']])

            # Model 数据 - 扁平化属性
            model = {
                "name": v['model'],
                "series": v['series'],
                "price": v.get('price'),
                "seats": v.get('seats'),
                "length_width_height": f"{v.get('dimensions', {}).get('length', 0)}×{v.get('dimensions', {}).get('width', 0)}×{v.get('dimensions', {}).get('height', 0)}",
                "wheelbase": v.get('dimensions', {}).get('wheelbase'),
                "acceleration_0_100": v.get('performance', {}).get('acceleration_0_100'),
                "battery_capacity": v.get('battery', {}).get('capacity'),
                "battery_type": v.get('battery', {}).get('type'),
                "range_cltc": v.get('battery', {}).get('cltc_range'),
                "suspension_front": v.get('chassis', {}).get('front_suspension'),
                "suspension_rear": v.get('chassis', {}).get('rear_suspension'),
                "cockpit_system": v.get('intelligence', {}).get('cockpit_system'),
                "adas_system": v.get('intelligence', {}).get('adas_system'),
                "lidar_count": v.get('intelligence', {}).get('lidar_count', 0)
            }
            models.append(model)

        # 导入 Brands
        logger.info(f"Importing {len(brands)} brands...")
        self.run_query(
            "UNWIND $batch AS name MERGE (b:Brand {name: name})",
            {"batch": list(brands)}
        )

        # 导入 Series
        logger.info(f"Importing {len(series_data)} series...")
        series_query = """
        UNWIND $batch AS row
        MERGE (s:Series {name: row.name})
        SET s += row
        WITH s, row
        MATCH (b:Brand {name: row.brand})
        MERGE (s)-[:BELONGS_TO_BRAND]->(b)
        """
        self.run_query(series_query, {"batch": list(series_data.values())})

        # 导入 Models
        logger.info(f"Importing {len(models)} models...")
        model_query = """
        UNWIND $batch AS row
        MERGE (m:Model {name: row.name})
        SET m.price = row.price,
            m.seats = row.seats,
            m.length_width_height = row.length_width_height,
            m.wheelbase = row.wheelbase,
            m.acceleration_0_100 = row.acceleration_0_100,
            m.battery_capacity = row.battery_capacity,
            m.battery_type = row.battery_type,
            m.range_cltc = row.range_cltc,
            m.suspension_front = row.suspension_front,
            m.suspension_rear = row.suspension_rear,
            m.cockpit_system = row.cockpit_system,
            m.adas_system = row.adas_system,
            m.lidar_count = row.lidar_count
        WITH m, row
        MATCH (s:Series {name: row.series})
        MERGE (m)-[:BELONGS_TO_SERIES]->(s)
        """
        self.run_query(model_query, {"batch": models})

        # 创建 Series 分析关系
        self._create_series_analytical_relationships(series_data)

    def _create_series_analytical_relationships(self, series_data):
        """创建 Series 的优劣势关系"""
        logger.info("Creating analytical relationships for Series...")
        dims = ["appearance", "interior", "space", "intelligence", "driving", "range", "value"]
        
        strength_rels = []
        weakness_rels = []
        
        for s_name, data in series_data.items():
            for d in dims:
                p_score = data.get(f'P_{d}')
                if p_score is not None:
                    try:
                        p_val = float(p_score)
                        if p_val > 0.8:
                            strength_rels.append({"series": s_name, "dimension": d, "score": p_val})
                        elif p_val < 0.6:
                            weakness_rels.append({"series": s_name, "dimension": d, "score": p_val})
                    except (ValueError, TypeError):
                        continue

        if strength_rels:
            self.run_query("""
                UNWIND $batch AS row
                MATCH (s:Series {name: row.series})
                MATCH (d:Dimension {name: row.dimension})
                MERGE (s)-[:HAS_STRENGTH {score: row.score}]->(d)
            """, {"batch": strength_rels})
            logger.info(f"Created {len(strength_rels)} HAS_STRENGTH relationships")
            
        if weakness_rels:
            self.run_query("""
                UNWIND $batch AS row
                MATCH (s:Series {name: row.series})
                MATCH (d:Dimension {name: row.dimension})
                MERGE (s)-[:HAS_WEAKNESS {score: row.score}]->(d)
            """, {"batch": weakness_rels})
            logger.info(f"Created {len(weakness_rels)} HAS_WEAKNESS relationships")

    def import_personas(self):
        """导入用户画像节点（增强版）"""
        logger.info("Processing personas...")
        df = pd.read_csv(PERSONA_FILE)
        
        # 计算画像质心
        weight_cols = [c for c in df.columns if c.startswith('w_')]
        centroids = df.groupby('persona_name')[weight_cols].mean().reset_index()
        
        # 计算画像统计元数据
        persona_stats = df.groupby('persona_name').agg({
            'review_id': 'count',  # 用户数量
            'purchase_price': 'mean',  # 平均购车价格
            'mileage': 'mean'  # 平均行驶里程
        }).reset_index()
        persona_stats.columns = ['persona_name', 'user_count', 'avg_purchase_price', 'avg_mileage']
        
        # 合并质心和统计数据
        centroids = centroids.merge(persona_stats, on='persona_name')
        
        personas = []
        priorities = []
        
        for _, row in centroids.iterrows():
            persona_name = row['persona_name']
            personas.append({
                'name': persona_name,
                'centroid_appearance': float(row.get('w_appearance', 0)),
                'centroid_interior': float(row.get('w_interior', 0)),
                'centroid_space': float(row.get('w_space', 0)),
                'centroid_intelligence': float(row.get('w_intelligence', 0)),
                'centroid_driving': float(row.get('w_driving', 0)),
                'centroid_range': float(row.get('w_range', 0)),
                'centroid_value': float(row.get('w_value', 0)),
                'user_count': int(row['user_count']),
                'avg_purchase_price': float(row['avg_purchase_price']) if pd.notna(row['avg_purchase_price']) else None,
                'avg_mileage': float(row['avg_mileage']) if pd.notna(row['avg_mileage']) else None
            })
            
            # PRIORITIZES 关系 (Top 3)
            weights = [(k.replace('w_', ''), v) for k, v in row.items() if k.startswith('w_')]
            top3 = sorted(weights, key=lambda x: x[1], reverse=True)[:3]
            
            for dim_name, weight_val in top3:
                priorities.append({
                    "persona": persona_name,
                    "dimension": dim_name,
                    "weight": float(weight_val)
                })

        # 导入 Persona 节点（增强版）
        logger.info(f"Importing {len(personas)} personas...")
        query = """
        UNWIND $batch AS row
        MERGE (p:Persona {name: row.name})
        SET p.centroid_appearance = row.centroid_appearance,
            p.centroid_interior = row.centroid_interior,
            p.centroid_space = row.centroid_space,
            p.centroid_intelligence = row.centroid_intelligence,
            p.centroid_driving = row.centroid_driving,
            p.centroid_range = row.centroid_range,
            p.centroid_value = row.centroid_value,
            p.user_count = row.user_count,
            p.avg_purchase_price = row.avg_purchase_price,
            p.avg_mileage = row.avg_mileage
        """
        self.run_query(query, {"batch": personas})
        
        # 导入 PRIORITIZES 关系
        logger.info(f"Creating {len(priorities)} PRIORITIZES relationships...")
        rel_query = """
        UNWIND $batch AS row
        MATCH (p:Persona {name: row.persona})
        MATCH (d:Dimension {name: row.dimension})
        MERGE (p)-[:PRIORITIZES {weight: row.weight}]->(d)
        """
        self.run_query(rel_query, {"batch": priorities})

    def import_reviews(self, limit=None, random_sample=False):
        """
        导入用户评论及其关系
        
        Args:
            limit: 限制导入的评论数量（用于测试），None 表示导入全部
            random_sample: 是否随机抽样（True=随机，False=顺序读取）
        """
        logger.info("Loading persona mapping...")
        p_df = pd.read_csv(PERSONA_FILE, usecols=['review_id', 'persona_name'])
        persona_map = p_df.set_index('review_id')['persona_name'].to_dict()
        
        if limit:
            if random_sample:
                logger.info(f"TEST MODE: Randomly sampling {limit} reviews...")
            else:
                logger.info(f"TEST MODE: Importing only first {limit} reviews...")
        else:
            logger.info("Importing all reviews in batches...")
        
        chunk_size = 5000
        dims = ["appearance", "interior", "space", "intelligence", "driving", "range", "value"]
        
        # 如果是随机抽样模式，先读取所有 review_id 并随机选择
        selected_ids = None
        if limit and random_sample:
            logger.info("Reading all review IDs for random sampling...")
            all_ids = pd.read_csv(UGC_FILE, usecols=['review_id'])['review_id'].tolist()
            total_available = len(all_ids)
            
            if limit > total_available:
                logger.warning(f"Requested {limit} reviews but only {total_available} available. Using all.")
                selected_ids = set(all_ids)
            else:
                import random
                selected_ids = set(random.sample(all_ids, limit))
                logger.info(f"Selected {len(selected_ids)} random reviews from {total_available} total")
        
        total_reviews = 0
        total_mentions = 0
        
        for chunk in pd.read_csv(UGC_FILE, chunksize=chunk_size):
            reviews_batch = []
            mentions_batch = []
            
            for _, row in chunk.iterrows():
                rid = str(row['review_id'])
                
                # 随机抽样模式：跳过不在选中集合的评论
                if selected_ids is not None and rid not in selected_ids:
                    continue
                
                # Review 节点数据（完整增强版）
                review_data = {
                    "id": rid,
                    "date": str(row['review_date']) if pd.notna(row['review_date']) else None,
                    "location": str(row['purchase_location']) if pd.notna(row['purchase_location']) else None,
                    "price": float(row['purchase_price']) if pd.notna(row['purchase_price']) else None,
                    "mileage": float(row['mileage']) if pd.notna(row['mileage']) else None,
                    "real_range": float(row['real_range']) if pd.notna(row['real_range']) else None,
                    "season": str(row['season_type']) if pd.notna(row['season_type']) else None,
                    "energy_consumption": float(row['energy_consumption']) if pd.notna(row['energy_consumption']) else None,
                    "model": str(row['model']) if pd.notna(row['model']) else None,
                    "series": str(row['series']) if pd.notna(row['series']) else None,
                    "persona": persona_map.get(rid),
                    # 评论文本内容
                    "appearance_review": str(row['appearance_review']) if pd.notna(row['appearance_review']) else None,
                    "interior_review": str(row['interior_review']) if pd.notna(row['interior_review']) else None,
                    "space_review": str(row['space_review']) if pd.notna(row['space_review']) else None,
                    "intelligence_review": str(row['intelligence_review']) if pd.notna(row['intelligence_review']) else None,
                    "driving_review": str(row['driving_review']) if pd.notna(row['driving_review']) else None,
                    "range_review": str(row['range_review']) if pd.notna(row['range_review']) else None,
                    "value_review": str(row['value_review']) if pd.notna(row['value_review']) else None,
                    "most_satisfied": str(row['most_satisfied']) if pd.notna(row['most_satisfied']) else None,
                    "least_satisfied": str(row['least_satisfied']) if pd.notna(row['least_satisfied']) else None,
                    # 评分数据
                    "appearance_score": float(row['appearance_score']) if pd.notna(row['appearance_score']) else None,
                    "interior_score": float(row['interior_score']) if pd.notna(row['interior_score']) else None,
                    "space_score": float(row['space_score']) if pd.notna(row['space_score']) else None,
                    "intelligence_score": float(row['intelligence_score']) if pd.notna(row['intelligence_score']) else None,
                    "driving_score": float(row['driving_score']) if pd.notna(row['driving_score']) else None,
                    "range_score": float(row['range_score']) if pd.notna(row['range_score']) else None,
                    "value_score": float(row['value_score']) if pd.notna(row['value_score']) else None
                }
                reviews_batch.append(review_data)
                
                # MENTIONS 关系（增强版：添加评分和文本元数据）
                for d in dims:
                    content_col = f'{d}_review'
                    score_col = f'{d}_score'
                    
                    content = row.get(content_col)
                    has_content = pd.notna(content) and str(content).strip() != ""
                    review_length = len(str(content)) if has_content else 0
                    
                    sentiment = 0.0
                    is_strong = False
                    score_val = None
                    
                    if pd.notna(row.get(score_col)):
                        try:
                            score_val = float(row[score_col])
                            # 评分显著性检查 (1-2 或 4-5)
                            if score_val >= 4 or score_val <= 2:
                                sentiment = (score_val - 3) / 2  # 标准化到 [-1, 1]
                                is_strong = (score_val >= 5 or score_val <= 1)
                                
                                if has_content or True:  # 有评分就创建关系
                                    mentions_batch.append({
                                        "review_id": rid,
                                        "dimension": d,
                                        "sentiment": sentiment,
                                        "is_strong": is_strong,
                                        "score": score_val,
                                        "has_text": has_content,
                                        "review_length": review_length
                                    })
                        except (ValueError, TypeError):
                            pass

            # 导入 Review 节点及关系（增强版）
            query = """
            UNWIND $batch AS row
            MERGE (r:Review {id: row.id})
            SET r.date = row.date,
                r.location = row.location,
                r.price = row.price,
                r.mileage = row.mileage,
                r.real_range = row.real_range,
                r.season = row.season,
                r.energy_consumption = row.energy_consumption,
                r.appearance_review = row.appearance_review,
                r.interior_review = row.interior_review,
                r.space_review = row.space_review,
                r.intelligence_review = row.intelligence_review,
                r.driving_review = row.driving_review,
                r.range_review = row.range_review,
                r.value_review = row.value_review,
                r.most_satisfied = row.most_satisfied,
                r.least_satisfied = row.least_satisfied,
                r.appearance_score = row.appearance_score,
                r.interior_score = row.interior_score,
                r.space_score = row.space_score,
                r.intelligence_score = row.intelligence_score,
                r.driving_score = row.driving_score,
                r.range_score = row.range_score,
                r.value_score = row.value_score
            
            WITH r, row
            FOREACH (_ IN CASE WHEN row.persona IS NOT NULL THEN [1] ELSE [] END |
                MERGE (p:Persona {name: row.persona})
                MERGE (r)-[:BELONGS_TO_PERSONA]->(p)
            )
            
            WITH r, row
            OPTIONAL MATCH (m:Model {name: row.model})
            FOREACH (_ IN CASE WHEN m IS NOT NULL THEN [1] ELSE [] END |
                MERGE (r)-[:EVALUATES]->(m)
            )
            FOREACH (_ IN CASE WHEN m IS NULL AND row.series IS NOT NULL THEN [1] ELSE [] END |
                MERGE (s:Series {name: row.series})
                MERGE (r)-[:EVALUATES]->(s)
            )
            """
            self.run_query(query, {"batch": reviews_batch})
            
            # 导入 MENTIONS 关系（增强版）
            if mentions_batch:
                m_query = """
                UNWIND $batch AS row
                MATCH (r:Review {id: row.review_id})
                MATCH (d:Dimension {name: row.dimension})
                MERGE (r)-[:MENTIONS {
                    sentiment: row.sentiment, 
                    is_strong_signal: row.is_strong,
                    score: row.score,
                    has_text: row.has_text,
                    review_length: row.review_length
                }]->(d)
                """
                self.run_query(m_query, {"batch": mentions_batch})
                total_mentions += len(mentions_batch)
            
            total_reviews += len(reviews_batch)
            logger.info(f"Processed {total_reviews} reviews, {total_mentions} mentions...")
            
            # 测试模式：达到限制后停止
            if limit and total_reviews >= limit:
                logger.info(f"Reached limit of {limit} reviews. Stopping import.")
                break

        logger.info(f"Import complete! Total: {total_reviews} reviews, {total_mentions} dimension mentions")

    def build(self, limit=None, random_sample=False):
        """
        执行完整的图谱构建流程
        
        Args:
            limit: 限制导入的评论数量（用于测试），None 表示导入全部
            random_sample: 是否随机抽样（True=随机，False=顺序读取）
        """
        try:
            logger.info("=" * 60)
            if limit:
                mode_text = "Random Sampling" if random_sample else "Sequential"
                logger.info(f"Starting Neo4j Knowledge Graph Construction (TEST MODE: {limit} reviews, {mode_text})")
            else:
                logger.info("Starting Neo4j Knowledge Graph Construction")
            logger.info("=" * 60)
            
            self.create_constraints()
            self.import_dimensions()
            self.import_vehicles()
            self.import_personas()
            self.import_reviews(limit=limit, random_sample=random_sample)
            
            logger.info("=" * 60)
            logger.info("Knowledge Graph Construction Completed Successfully!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error during graph construction: {e}", exc_info=True)
            raise
        finally:
            self.close()


if __name__ == "__main__":
    # 验证必需的环境变量
    if not NEO4J_URI:
        raise ValueError("NEO4J_URI environment variable is required")
    if not NEO4J_PASSWORD:
        raise ValueError("NEO4J_PASSWORD environment variable is required")
    
    logger.info(f"Connecting to Neo4j at {NEO4J_URI}")
    logger.info("执行完整数据导入（约 52,000+ 条评论）")
    logger.info("如需测试模式，请运行: python Graph/test_graph.py")
    
    builder = Neo4jGraphBuilder(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE
    )
    builder.build()

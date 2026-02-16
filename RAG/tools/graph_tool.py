"""
Graph Retriever Tool - 图谱检索工具
执行 Cypher 查询获取结构化数据

Author: EV PM DSS Team
Date: 2026-02-15
"""

from typing import List, Dict, Optional
from RAG.config import get_graph_client


class GraphRetriever:
    """图谱检索工具"""
    
    def __init__(self):
        self.client = get_graph_client()
    
    def get_vehicle_by_filters(
        self,
        brand: Optional[str] = None,
        series: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_range: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        根据过滤条件查询车型
        
        Args:
            brand: 品牌名称
            series: 车系名称
            min_price: 最低价格（万元）
            max_price: 最高价格（万元）
            min_range: 最低续航（km）
            limit: 返回结果数量
        
        Returns:
            List of vehicle nodes
        """
        # Build WHERE clauses
        where_clauses = []
        params = {}
        
        if brand:
            where_clauses.append("b.name = $brand")
            params["brand"] = brand
        if series:
            where_clauses.append("s.name = $series")
            params["series"] = series
        if min_price is not None:
            where_clauses.append("m.price >= $min_price")
            params["min_price"] = min_price
        if max_price is not None:
            where_clauses.append("m.price <= $max_price")
            params["max_price"] = max_price
        if min_range is not None:
            where_clauses.append("m.range_cltc >= $min_range")
            params["min_range"] = min_range
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        params["limit"] = limit
        
        cypher = f"""
        MATCH (m:Model)-[:BELONGS_TO_SERIES]->(s:Series)-[:BELONGS_TO_BRAND]->(b:Brand)
        WHERE {where_clause}
        RETURN b.name AS brand, s.name AS series, m.name AS model,
               m.price AS price, m.range_cltc AS range_cltc,
               m.battery_capacity AS battery_capacity,
               m.acceleration_0_100 AS acceleration,
               m.seats AS seats
        LIMIT $limit
        """
        
        try:
            print(f"\n📊 [图谱查询] 开始查询车型参数...")
            print(f"   Brand={brand}, Series={series}, Min_Price={min_price}, Max_Price={max_price}, Min_Range={min_range}")
            print(f"   Cypher: {cypher.strip()}")
            print(f"   Params: {params}")
            
            results = self.client.query(cypher, params)
            
            print(f"   ✅ 查询成功，返回 {len(results)} 个车型")
            if results:
                for i, r in enumerate(results[:3], 1):  # 只显示前3个
                    print(f"      {i}. {r.get('brand')} {r.get('series')} {r.get('model')} - ¥{r.get('price')}万")
            
            return results
        except Exception as e:
            print(f"   ❌ 图谱查询失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_competitor_comparison(
        self,
        model1_name: str,
        model2_name: str
    ) -> Dict:
        """
        对比两个车型的参数
        
        Args:
            model1_name: 车型1名称
            model2_name: 车型2名称
        
        Returns:
            Comparison data
        """
        cypher = """
        MATCH (m1:Model {name: $model1})-[:BELONGS_TO_SERIES]->(s1:Series)-[:BELONGS_TO_BRAND]->(b1:Brand)
        MATCH (m2:Model {name: $model2})-[:BELONGS_TO_SERIES]->(s2:Series)-[:BELONGS_TO_BRAND]->(b2:Brand)
        RETURN 
            b1.name AS brand1, s1.name AS series1, m1.name AS model1,
            m1.price AS price1, m1.range_cltc AS range1,
            m1.acceleration_0_100 AS accel1, m1.seats AS seats1,
            b2.name AS brand2, s2.name AS series2, m2.name AS model2,
            m2.price AS price2, m2.range_cltc AS range2,
            m2.acceleration_0_100 AS accel2, m2.seats AS seats2
        """
        
        results = self.client.query(cypher, {"model1": model1_name, "model2": model2_name})
        return results[0] if results else {}
    
    def get_all_personas(self) -> List[Dict]:
        """
        获取所有用户画像（
        
        Returns:
            List of all persona insights with top dimensions
        """
        cypher = """
        MATCH (p:Persona)
        OPTIONAL MATCH (p)-[r:PRIORITIZES]->(d:Dimension)
        WITH p, r, d
        ORDER BY r.weight DESC
        WITH p, collect({dimension: d.name_cn, weight: r.weight})[..3] AS top_dimensions
        RETURN p.name AS persona_name,
               p.user_count AS review_count,
               top_dimensions
        """
        
        try:
            print(f"🔍 正在查询所有用户画像")
            results = self.client.query(cypher)
            print(f"   ✅ 查询到 {len(results)} 个画像")
            
            # 为每个结果添加描述
            for result in results:
                result['description'] = f"用户画像: {result.get('persona_name', 'Unknown')}"
                
            return results
        except Exception as e:
            print(f"❌ Error querying personas: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return []


    
    def get_series_ipa_scores(self, series_name: str) -> Dict:
        """
        获取车系的 IPA 评分
        
        Args:
            series_name: 车系名称
        
        Returns:
            IPA scores for all dimensions
        """
        cypher = """
        MATCH (s:Series {name: $series})
        RETURN s.name AS series,
               s.I_appearance AS I_appearance, s.P_appearance AS P_appearance,
               s.I_interior AS I_interior, s.P_interior AS P_interior,
               s.I_space AS I_space, s.P_space AS P_space,
               s.I_intelligence AS I_intelligence, s.P_intelligence AS P_intelligence,
               s.I_driving AS I_driving, s.P_driving AS P_driving,
               s.I_range AS I_range, s.P_range AS P_range,
               s.I_value AS I_value, s.P_value AS P_value,
               s.sample_count AS sample_count
        """
        
        results = self.client.query(cypher, {"series": series_name})
        return results[0] if results else {}
    
    def get_review_statistics(
        self,
        brand: Optional[str] = None,
        series: Optional[str] = None,
        model: Optional[str] = None,
        dimension: Optional[str] = None
    ) -> Dict:
        """
        获取评论统计信息
        
        Args:
            brand: 品牌过滤
            series: 车系过滤
            model: 车型过滤
            dimension: 维度过滤
        
        Returns:
            Review statistics
        """
        # Build MATCH pattern
        match_pattern = "(r:Review)"
        where_clauses = []
        params = {}
        
        if model:
            match_pattern = "(r:Review)-[:EVALUATES]->(m:Model {name: $model})"
            params["model"] = model
        elif series:
            match_pattern = "(r:Review)-[:EVALUATES]->(m:Model)-[:BELONGS_TO_SERIES]->(s:Series {name: $series})"
            params["series"] = series
        elif brand:
            match_pattern = "(r:Review)-[:EVALUATES]->(m:Model)-[:BELONGS_TO_SERIES]->(:Series)-[:BELONGS_TO_BRAND]->(b:Brand {name: $brand})"
            params["brand"] = brand
        
        if dimension:
            match_pattern += f"-[men:MENTIONS]->(d:Dimension {{name: $dimension}})"
            params["dimension"] = dimension
        
        cypher = f"""
        MATCH {match_pattern}
        RETURN count(r) AS review_count,
               avg(r.sentiment_score) AS avg_sentiment
        """
        
        results = self.client.query(cypher, params)
        return results[0] if results else {}


# ==================== Utility Functions ====================
def format_vehicle_comparison(comparison: Dict) -> str:
    """格式化车型对比结果为表格"""
    if not comparison:
        return "未找到对比数据"
    
    table = f"""
| 维度 | {comparison['brand1']} {comparison['series1']} | {comparison['brand2']} {comparison['series2']} |
|------|------|------|
| 车型 | {comparison['model1']} | {comparison['model2']} |
| 价格 | {comparison.get('price1', 'N/A')} 万 | {comparison.get('price2', 'N/A')} 万 |
| 续航 | {comparison.get('range1', 'N/A')} km | {comparison.get('range2', 'N/A')} km |
| 加速 | {comparison.get('accel1', 'N/A')} s | {comparison.get('accel2', 'N/A')} s |
| 座位 | {comparison.get('seats1', 'N/A')} 座 | {comparison.get('seats2', 'N/A')} 座 |
"""
    return table


def format_ipa_scores(ipa_data: Dict) -> str:
    """格式化 IPA 评分数据"""
    if not ipa_data:
        return "未找到 IPA 数据"
    
    dimensions = ['appearance', 'interior', 'space', 'intelligence', 'driving', 'range', 'value']
    dim_cn = {
        'appearance': '外观', 'interior': '内饰', 'space': '空间',
        'intelligence': '智能化', 'driving': '驾驶', 'range': '续航', 'value': '价值'
    }
    
    lines = [f"**{ipa_data.get('series')}** IPA 评分 (样本数: {ipa_data.get('sample_count', 0)})\n"]
    
    for dim in dimensions:
        i_score = ipa_data.get(f'I_{dim}', 0)
        p_score = ipa_data.get(f'P_{dim}', 0)
        lines.append(f"- **{dim_cn[dim]}**: I={i_score:.2f}, P={p_score:.2f}")
    
    return "\n".join(lines)

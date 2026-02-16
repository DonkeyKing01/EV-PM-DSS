"""
Query Analyzer - 问题分析模块
判断用户问题的复杂度、类型和所需检索策略

Author: EV PM DSS Team
Date: 2026-02-15
"""

from typing import Dict, List, Optional
from openai import OpenAI


class QueryAnalyzer:
    """查询分析器 - 智能判断检索策略"""
    
    def __init__(self, llm_client: OpenAI):
        self.llm = llm_client
    
    def needs_retrieval(self, query: str, module: str = "User Insights") -> Dict:
        """
        判断问题是否需要检索（智能分流）
        
        Returns:
            {
                "requires_retrieval": bool,
                "query_category": "greeting|meta|domain",
                "direct_response": Optional[str],
                "reasoning": str
            }
        """
        
        # 使用 LLM 快速判断（轻量级模型）
        prompt = f"""判断以下用户问题是否需要检索数据库。

**用户问题**: {query}

**分类标准**:
- **greeting**: 纯问候语（如"你好"、"hi"、"早上好"）→ 不需要检索
- **meta**: 关于系统功能的问题（如"你能做什么"、"如何使用"、"这个系统是干什么的"）→ 不需要检索
- **domain**: 关于电动汽车领域的专业问题 → **必须检索**

**重要**: 以下问题属于 domain，需要检索：
- 询问用户类型、用户画像、用户需求（如"有哪些用户类型"）
- 询问车型参数、评价、对比（如"Model Y 怎么样"）
- 询问功能、场景、痛点（如"智能座舱评价"）
- 需要撰写文档、分析数据的任务

返回 JSON:
{{
    "category": "greeting|meta|domain",
    "requires_retrieval": true|false,
    "reasoning": "简短说明"
}}

只返回 JSON。"""
        
        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            category = result.get("category", "domain")
            requires_retrieval = result.get("requires_retrieval", True)
            
            # 二次验证：包含关键词的必须检索
            domain_keywords = ["用户", "车型", "评价", "对比", "分析", "画像", "需求", "痛点", "竞品", "PRD", "Model", "特斯拉", "比亚迪", "理想", "蔚来", "小鹏"]
            if any(kw in query for kw in domain_keywords):
                requires_retrieval = True
                category = "domain"
            
            # 生成直接回复（如果不需要检索）
            direct_response = None
            if not requires_retrieval:
                if category == "greeting":
                    direct_response = "你好！我是 EV PM DSS 智能助手。\n\n我可以帮您：\n- 📊 分析用户洞察和需求\n- ⚔️ 进行竞品对比分析\n- 📝 撰写产品需求文档\n\n请告诉我您想了解什么？"
                elif category == "meta":
                    # 使用 LLM 基于系统文档生成回答
                    direct_response = self._generate_meta_response(query, module)
            
            return {
                "requires_retrieval": requires_retrieval,
                "query_category": category,
                "direct_response": direct_response,
                "reasoning": result.get("reasoning", "")
            }
            
        except Exception as e:
            # 失败时保守策略：假设需要检索
            return {
                "requires_retrieval": True,
                "query_category": "domain",
                "direct_response": None,
                "reasoning": f"分类失败，默认需要检索: {str(e)}"
            }
    
    def _generate_meta_response(self, query: str, module: str = "User Insights") -> str:
        """
        基于系统文档生成 meta 问题的回答
        
        Args:
            query: 用户问题
            module: 当前模块
        
        Returns:
            LLM生成的回答
        """
        # 读取系统文档
        import os
        from pathlib import Path
        
        doc_path = Path(__file__).parent.parent / "SYSTEM_INTRO.md"
        
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                system_doc = f.read()
        except Exception as e:
            print(f"⚠️ 无法读取系统文档: {e}")
            # 降级到简单回复
            return f"我是 EV PM DSS 智能助手，当前在 {module} 模块。我可以帮您分析电动汽车用户需求、竞品对比和撰写 PRD。请问有什么可以帮您？"
        
        prompt = f"""你是 EV PM DSS 的智能助手，用户在 {module} 模块询问系统功能。

**系统文档**:
{system_doc}

**用户问题**: {query}

**回答要求**:
1. 基于系统文档回答，不要添加文档中没有的功能
2. 如果问题超出系统范围（非电动汽车领域），礼貌拒绝并说明系统定位
3. 突出当前模块 ({module}) 的能力
4. 简洁专业，2-3段即可
5. 使用 Markdown 格式，可以用列表和加粗

请回答用户的问题。"""

        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,  # 稍高温度，更自然
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"⚠️ LLM 生成 meta 回答失败: {e}")
            return f"我是 EV PM DSS 智能助手，当前在 **{module}** 模块。我可以帮您分析电动汽车用户需求、竞品对比和撰写 PRD。请具体告诉我您想了解什么？"
    
    def _get_module_help(self, module: str = "User Insights") -> str:
        """获取当前模块的帮助信息"""
        
        help_texts = {
            "User Insights": """**EV PM DSS 功能说明**

当前您在 **User Insights** 模块，可以：
- 分析特定用户群体的需求和痛点
- 了解用户对某个功能/车型的评价
- 识别用户画像和使用场景

**示例问题**:
- "有哪些用户类型？"
- "用户对智能座舱有什么评价？"
- "续航焦虑主要在哪些场景？"

切换到其他模块可查看更多功能。""",
            
            "Competitor Analysis": """**EV PM DSS 功能说明**

当前您在 **Competitor Analysis** 模块，可以：
- 对比不同车型的参数和性能
- 分析竞品的优势和劣势
- 基于真实用户评价生成 SWOT 分析

**示例问题**:
- "Model Y 和理想 L7 对比"
- "比亚迪海豹的竞争力如何？"
- "15-20万纯电 SUV 市场分析"

切换到其他模块可查看更多功能。""",
            
            "PRD Writer": """**EV PM DSS 功能说明**

当前您在 **PRD Writer** 模块，可以：
- 基于用户画像和市场数据撰写 PRD
- 自动生成功能需求和优先级
- 提供数据驱动的产品建议

**示例问题**:
- "撰写智能座舱 PRD"
- "针对年轻家庭用户的车型需求文档"
- "续航优化功能 PRD"

切换到其他模块可查看更多功能。"""
        }
    
    def extract_entities(self, query: str, module: str = "Competitor Analysis") -> Dict:
        """
        从用户问题中提取品牌和车型实体
        
        Args:
            query: 用户问题
            module: 当前模块
        
        Returns:
            {
                "brands": List[str],  # 提取的品牌列表
                "models": List[str],  # 提取的车型列表
                "series": List[str],  # 提取的车系列表
                "extraction_confidence": float  # 提取置信度
            }
        """
        
        prompt = f"""从以下用户问题中提取电动汽车相关的品牌、车系和车型信息。

**用户问题**: {query}

**数据库中的标准品牌名称**（你必须严格使用以下名称，不能使用简称或别名）:
- 特斯拉（Tesla）
- 比亚迪（BYD）
- 理想汽车（理想 / Li Auto）→ 必须输出"理想汽车"
- 蔚来（NIO）
- 小鹏（Xpeng）
- 小米汽车（小米 / Xiaomi）→ 必须输出"小米汽车"
- AITO 问界（问界 / AITO）→ 必须输出"AITO 问界"
- 极氪（Zeekr）
- 奥迪（Audi）
- 宝马（BMW）
- 奔驰（Benz / Mercedes）
- 沃尔沃（Volvo）

**车型/车系示例**:
- Model Y, Model 3, Model S, Model X
- 海豹, 汉, 唐, 元 Plus
- 理想 L7, 理想 L8, 理想 L9
- ES6, ES8, ET5, ET7
- P7, G9, P5
- SU7

返回 JSON 格式：
{{
    "brands": ["品牌1", "品牌2"],  // 必须使用上面列出的标准品牌名称
    "models": ["车型1", "车型2"],  // 提取的具体车型
    "series": ["车系1"],           // 提取的车系
    "extraction_confidence": 0.0-1.0  // 提取置信度
}}

**规则**:
1. brands 字段必须使用上面列出的标准品牌名称，例如用户说"小米"你必须输出"小米汽车"，用户说"理想"你必须输出"理想汽车"，用户说"问界"你必须输出"AITO 问界"
2. 车型要包含品牌前缀，如 "特斯拉 Model Y"
3. 如果问题中没有提到任何品牌或车型，返回空列表
4. 置信度: 明确提到品牌=1.0, 仅暗示=0.5, 未提到=0.0

只返回 JSON，不要其他内容。"""

        try:
            print(f"\n🔍 [实体提取] 开始提取品牌和车型...")
            print(f"   查询: {query}")
            
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # 验证和清理结果
            brands = result.get("brands", [])
            models = result.get("models", [])
            series = result.get("series", [])
            confidence = result.get("extraction_confidence", 0.0)
            
            # 去重
            normalized_brands = list(dict.fromkeys(brands))
            
            print(f"   ✅ 提取结果: brands={normalized_brands}, models={models}, series={series}, confidence={confidence:.2f}")
            
            return {
                "brands": normalized_brands,
                "models": models,
                "series": series,
                "extraction_confidence": confidence
            }
            
        except Exception as e:
            print(f"   ❌ 实体提取失败: {str(e)}")
            # 失败时返回空结果
            return {
                "brands": [],
                "models": [],
                "series": [],
                "extraction_confidence": 0.0
            }
    
    
    def analyze_query(self, query: str, module: str) -> Dict:
        """
        分析用户问题，返回检索策略
        
        Args:
            query: 用户问题
            module: 当前模块（User Insights / Competitor Analysis / PRD Writer）
        
        Returns:
            {
                "complexity": "simple|medium|complex",
                "query_type": "factual|analytical|creative",
                "data_sources": ["vector", "graph"],
                "n_results": int,
                "requires_rerank": bool,
                "reasoning": str
            }
        """
        
        # 使用轻量级模型（Routing Model）进行快速分析
        prompt = f"""你是一个智能的查询分析系统。分析以下用户问题，确定最优检索策略。

**当前模块**: {module}
**用户问题**: {query}

请分析并返回 JSON 格式的结果：

{{
    "complexity": "simple|medium|complex",  // 问题复杂度
    "query_type": "factual|analytical|creative",  // 问题类型
    "data_sources": ["vector", "graph"],  // 需要的数据源
    "n_results": 5-15,  // 建议检索结果数量
    "requires_rerank": true|false,  // 是否需要重排序
    "reasoning": "简短说明理由"
}}

**判断标准**:
- **simple**: 简单事实查询（如"Model Y 价格"）→ vector, n_results=5
- **medium**: 需要对比分析（如"Model Y 和理想L7 对比"）→ vector+graph, n_results=10
- **complex**: 需要深度分析（如"撰写智能座舱 PRD"）→ vector+graph+personas, n_results=15, rerank=true

只返回 JSON，不要其他内容。"""
        
        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
                response_format={"type": "json_object"}  # 强制 JSON 输出
            )
            
            import json
            analysis = json.loads(response.choices[0].message.content)
            
            # 验证和默认值
            analysis.setdefault("complexity", "medium")
            analysis.setdefault("query_type", "analytical")
            analysis.setdefault("data_sources", ["vector", "graph"])
            analysis.setdefault("n_results", 10)
            analysis.setdefault("requires_rerank", False)
            analysis.setdefault("reasoning", "自动分析")
            
            return analysis
            
        except Exception as e:
            # 失败时返回默认策略
            return {
                "complexity": "medium",
                "query_type": "analytical",
                "data_sources": ["vector", "graph"],
                "n_results": 10,
                "requires_rerank": False,
                "reasoning": f"分析失败，使用默认策略: {str(e)}"
            }
    
    def get_retrieval_config(self, analysis: Dict, module: str) -> Dict:
        """
        根据分析结果生成检索配置
        
        Returns:
            {
                "use_vector": bool,
                "use_graph": bool,
                "vector_n_results": int,
                "graph_queries": List[str],
                "enable_rerank": bool
            }
        """
        config = {
            "use_vector": "vector" in analysis["data_sources"],
            "use_graph": "graph" in analysis["data_sources"],
            "vector_n_results": analysis["n_results"],
            "enable_rerank": analysis["requires_rerank"],
            "complexity": analysis["complexity"]
        }
        
        # 根据模块调整配置
        if module == "User Insights":
            config["use_graph"] = True  # 始终使用 Persona
        elif module == "PRD Writer":
            config["use_vector"] = True
            config["use_graph"] = True
            config["vector_n_results"] = max(15, config["vector_n_results"])
        
        return config


class RetrievalQualityChecker:
    """检索质量把控模块"""
    
    def __init__(self, llm_client: OpenAI):
        self.llm = llm_client
    
    def check_relevance(
        self, 
        query: str, 
        retrieved_docs: List[Dict],
        min_relevant_ratio: float = 0.4
    ) -> Dict:
        """
        检查检索结果与问题的相关度
        
        Args:
            query: 用户问题
            retrieved_docs: 检索到的文档列表
            min_relevant_ratio: 最低相关文档比例阈值
        
        Returns:
            {
                "is_sufficient": bool,
                "relevant_count": int,
                "total_count": int,
                "relevance_ratio": float,
                "suggestion": str,
                "should_reretrieve": bool
            }
        """
        
        if not retrieved_docs:
            return {
                "is_sufficient": False,
                "relevant_count": 0,
                "total_count": 0,
                "relevance_ratio": 0.0,
                "suggestion": "未检索到任何文档，需要重新检索",
                "should_reretrieve": True
            }
        
        # 构建检查 prompt
        docs_preview = "\n\n".join([
            f"文档 {i+1}:\n{doc.get('text', '')[:200]}..."
            for i, doc in enumerate(retrieved_docs[:15])  # 检查前 15 个文档（适应更大数据集）
        ])
        
        prompt = f"""你是一个检索质量评估系统。判断检索到的文档与用户问题的相关性。

**用户问题**: {query}

**检索到的文档**:
{docs_preview}

请评估并返回 JSON：

{{
    "relevant_count": 0-5,  // 相关文档数量
    "relevance_scores": [0.0-1.0, ...],  // 每个文档的相关度评分
    "is_sufficient": true|false,  // 是否足够回答问题
    "suggestion": "评估说明"
}}

**判断标准**:
- 相关度 > 0.7: 高度相关
- 相关度 0.4-0.7: 中度相关
- 相关度 < 0.4: 不相关

只返回 JSON，不要其他内容。"""
        
        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            relevant_count = result.get("relevant_count", 0)
            total_count = len(retrieved_docs)
            relevance_ratio = relevant_count / total_count if total_count > 0 else 0.0
            
            is_sufficient = result.get("is_sufficient", False)
            should_reretrieve = relevance_ratio < min_relevant_ratio or not is_sufficient
            
            return {
                "is_sufficient": is_sufficient,
                "relevant_count": relevant_count,
                "total_count": total_count,
                "relevance_ratio": relevance_ratio,
                "suggestion": result.get("suggestion", ""),
                "should_reretrieve": should_reretrieve,
                "relevance_scores": result.get("relevance_scores", [])
            }
            
        except Exception as e:
            # 失败时保守策略：报告失败，要求重新检索
            return {
                "is_sufficient": False,  # 改为 False，不假设结果可用
                "relevant_count": 0,
                "total_count": len(retrieved_docs),
                "relevance_ratio": 0.0,
                "suggestion": f"质量检查失败，建议重新检索或扩大范围: {str(e)}",
                "should_reretrieve": True  # 改为 True，建议重新检索
            }
    
    def suggest_refinement(self, query: str, quality_result: Dict) -> str:
        """建议如何改进检索"""
        
        if quality_result["should_reretrieve"]:
            suggestions = []
            
            if quality_result["relevance_ratio"] < 0.2:
                suggestions.append("扩大检索范围（增加 n_results）")
                suggestions.append("尝试改写查询关键词")
            elif quality_result["relevance_ratio"] < 0.4:
                suggestions.append("调整检索策略（如增加图数据库查询）")
            
            return "; ".join(suggestions) if suggestions else "建议重新检索"
        
        return "检索质量良好"

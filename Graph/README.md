# EV PM DSS - Neo4j Knowledge Graph Module

新能源汽车决策支持系统的知识图谱模块，基于 Neo4j Aura 构建，支持 RAG (检索增强生成) 应用。

## 🚀 快速开始

### 1. 环境配置

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量（在项目根目录创建 .env 文件）
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
```

### 2. 测试导入（推荐）

```bash
# 导入 1000 条随机评论进行验证
python Graph/test_graph.py
```

### 3. 完整导入

```bash
# 导入全部 52,000+ 条评论
python Graph/build_graph.py
```

### 4. 数据清理

```bash
# 清空数据库（需要输入 YES 确认）
python Graph/clear_graph.py
```

---

## 📊 知识图谱结构

### 节点类型 (6 种)

| 节点类型 | 数量 | 核心属性 | 说明 |
|---------|------|---------|------|
| **Brand** | 12 | `name` | 汽车品牌 |
| **Series** | 113 | `name`, `sample_count`, IPA 分数 | 车系 + 市场表现分析 |
| **Model** | 580 | 配置详情（价格、电池、智能化等） | 具体车型配置 |
| **Persona** | 8 | `name`, 质心权重, 统计元数据 | 用户画像（如"性能追求者"） |
| **Review** ⭐ | ~52,000 | 文本内容 + 评分 + 元数据 | 用户真实评论 |
| **Dimension** | 7 | `name`, `name_cn` | 评价维度（外观、内饰等） |

### 关系类型 (8 种)

```
Brand <-[BELONGS_TO_BRAND]- Series <-[BELONGS_TO_SERIES]- Model
                                ↓
                          [HAS_STRENGTH/HAS_WEAKNESS]
                                ↓
                            Dimension
                                ↑
                         [MENTIONS] (score, has_text)
                                ↑
                             Review
                           ↙      ↘
              [BELONGS_TO_PERSONA]  [EVALUATES]
                     ↓                   ↓
                  Persona            Model/Series
                     ↓
              [PRIORITIZES]
                     ↓
                 Dimension
```

### Review 节点详细属性（增强版）

**元数据**：
- `id`, `date`, `location`, `price`, `mileage`, `real_range`, `season`, `energy_consumption`

**文本内容** (9 个字段)：
- `appearance_review`, `interior_review`, `space_review`
- `intelligence_review`, `driving_review`, `range_review`, `value_review`
- `most_satisfied`, `least_satisfied`

**评分数据** (7 个字段)：
- `appearance_score`, `interior_score`, `space_score`
- `intelligence_score`, `driving_score`, `range_score`, `value_score`

### MENTIONS 关系详细属性（增强版）

- `sentiment` - 情感倾向 (-1 到 1)
- `is_strong_signal` - 是否强信号
- `score` - 原始评分 (1-5)
- `has_text` - 是否有文本评论
- `review_length` - 评论文本长度

---

## 🎯 RAG 能力与应用场景

### 核心能力

| 能力 | 支持度 | 说明 |
|------|-------|------|
| **多维度检索** | ⭐⭐⭐⭐⭐ | 文本 + 评分 + 画像 + 车型关联 |
| **用户画像定向** | ⭐⭐⭐⭐⭐ | 精准定位特定用户群体反馈 |
| **产品对比分析** | ⭐⭐⭐⭐ | IPA 分数 + 用户评价综合对比 |
| **情感倾向分析** | ⭐⭐⭐⭐ | 正负面反馈统计与趋势分析 |
| **质量内容过滤** | ⭐⭐⭐⭐ | 区分详细评论和简单打分 |

### 典型查询示例

#### 1. 全文检索
```cypher
// 查找所有提到"智能座舱"的好评
MATCH (r:Review)-[m:MENTIONS]->(d:Dimension {name: 'intelligence'})
WHERE r.intelligence_review CONTAINS '智能座舱' 
  AND m.score >= 4
RETURN r.intelligence_review, r.most_satisfied, m.score
LIMIT 10
```

#### 2. 用户画像分析
```cypher
// 找到"性能追求者"最不满意的功能
MATCH (p:Persona {name: '性能追求者'})<-[:BELONGS_TO_PERSONA]-(r:Review)
WHERE r.least_satisfied IS NOT NULL
RETURN r.least_satisfied, count(*) as count
ORDER BY count DESC
LIMIT 5
```

#### 3. 车型对比
```cypher
// 对比两个车系的智能化表现
MATCH (s:Series)-[rel:HAS_STRENGTH|HAS_WEAKNESS]->(d:Dimension {name: 'intelligence'})
WHERE s.name IN ['Model Y', '问界M5']
RETURN s.name, s.I_intelligence, s.P_intelligence, type(rel) as relationship
```

#### 4. 高质量内容筛选
```cypher
// 找到有详细文本的高质量评论
MATCH (r:Review)-[m:MENTIONS]->(d:Dimension)
WHERE m.has_text = true AND m.review_length > 100
RETURN r, m, d
LIMIT 20
```

#### 5. 品牌整体洞察
```cypher
// 分析某品牌下所有正面评价的分布
MATCH (b:Brand {name: '特斯拉'})<-[:BELONGS_TO_BRAND]-(s:Series)
      <-[:BELONGS_TO_SERIES]-(m:Model)<-[:EVALUATES]-(r:Review)
      -[men:MENTIONS]->(d:Dimension)
WHERE men.sentiment > 0.5
RETURN d.name_cn, count(r) as positive_count
ORDER BY positive_count DESC
```

### 适配场景

✅ **高度适配**：
- 智能问答系统
- 用户画像分析
- 产品对比报告
- 情感倾向分析

⚠️ **需要增强**：
- 语义搜索（需要向量嵌入）
- 多轮对话上下文（需要会话管理）

---

## 📈 数据规模

| 项目 | 数量 | Aura Free Tier 占用率 |
|------|------|---------------------|
| **节点总数** | ~53,000 | 26% (上限 200,000) |
| **关系总数** | ~340,000 | 85% (上限 400,000) |
| **文本存储** | ~20MB | 可忽略 |

**结论**：在 Neo4j Aura Free Tier 限制内安全运行 ✅

---

## 🛠️ 脚本说明

### build_graph.py
主导入脚本，完整导入所有数据：
- 创建约束
- 导入车型层级（Brand → Series → Model）
- 导入用户画像（Persona）
- 导入评论及关系（Review + MENTIONS）

### test_graph.py
测试脚本，随机抽样 1000 条评论：
- 配置参数：`TEST_LIMIT = 1000`, `RANDOM_SAMPLE = True`
- 用于快速验证图谱构建逻辑

### clear_graph.py
数据清理脚本：
- 删除所有节点和关系
- 需要输入 `YES` 进行二次确认
- 用于重新导入前的数据清理

---

## 🔧 进阶优化建议

### 1. 创建全文索引（推荐）
```cypher
// 创建全文索引以提升中文搜索性能
CREATE FULLTEXT INDEX review_text FOR (r:Review)
ON EACH [r.intelligence_review, r.driving_review, r.range_review, 
         r.appearance_review, r.interior_review, r.space_review, r.value_review]

// 使用全文搜索
CALL db.index.fulltext.queryNodes("review_text", "智能座舱")
YIELD node, score
RETURN node.intelligence_review, score
LIMIT 10
```

### 2. 添加向量嵌入（语义搜索）
```cypher
// 创建向量索引
CREATE VECTOR INDEX review_embeddings FOR (r:Review)
ON (r.text_embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}}

// 向量检索
CALL db.index.vector.queryNodes('review_embeddings', 5, $query_vector)
YIELD node, score
RETURN node, score
```

### 3. 优化日期类型
```cypher
// 转换日期字符串为 DateTime 类型
MATCH (r:Review)
WHERE r.date IS NOT NULL
SET r.purchase_datetime = datetime(r.date)
```

---

## 📊 验证查询

登录 [Neo4j Browser](https://console.neo4j.io/) 后运行：

```cypher
// 1. 检查节点统计
MATCH (n) 
RETURN labels(n) as Type, count(n) as Count
ORDER BY Count DESC

// 2. 查看 Review 节点示例
MATCH (r:Review) 
RETURN r LIMIT 1

// 3. 检查 MENTIONS 关系属性
MATCH (r:Review)-[m:MENTIONS]->(d:Dimension) 
RETURN r.id, d.name, m.score, m.has_text, m.review_length 
LIMIT 5

// 4. 查看 Persona 统计
MATCH (p:Persona)
RETURN p.name, p.user_count, p.avg_purchase_price
ORDER BY p.user_count DESC
```

---

## 📝 数据来源

- `vehicles_config.json` - 车型配置数据
- `ugc.csv` - 用户评论数据
- `step1_scores_matrix.csv` - Series 级 IPA 分析
- `step4_user_persona_full.csv` - 用户画像映射

---

## 🤝 贡献指南

欢迎提交 Pull Request 或 Issue！

改进方向：
- 添加更多评价维度
- 优化查询性能
- 集成向量嵌入
- 添加时间序列分析

---

## 📄 License

EV PM DSS © 2026

---

**相关文档**：
- [Schema Enhancement Summary](schema_enhancement_summary.md) - 属性增强详细说明
- [Graph Structure Assessment](GRAPH_STRUCTURE_AND_RAG_ASSESSMENT.md) - 完整技术评估

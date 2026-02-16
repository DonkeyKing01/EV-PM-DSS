# Vector Database Module

向量数据库模块，基于 ChromaDB 构建，负责数据嵌入和入库。

**注**: 查询接口和 RAG 应用将在 `RAG/` 模块中实现。

---

## 🚀 快速开始

### 1. 环境配置

```bash
# 安装依赖
pip install -r requirements.txt
```

### 2. 测试构建（推荐）

```bash
# 测试模式（1000 条评论）
python Vector/test_vector_db.py
```

### 3. 完整构建

```bash
# 完整构建（所有数据）
python Vector/build_vector_db.py

# 使用不同的嵌入模型
python Vector/build_vector_db.py --model all-MiniLM-L6-v2
```

---

## 📊 数据内容

### 1. UGC 评论语义库
- **来源**: `Data/Processed/ugc.csv`
- **内容**: 
  - 评论摘要（最满意/不满意）
  - 分维度评价（7个维度）
- **元数据**: 品牌、车系、车型、画像、评分、日期等
- **预计文档数**: ~360,000 条

### 2. 车型规格说明书
- **来源**: `Data/Processed/vehicles_config.json`
- **内容**: 车型配置参数文本化描述
- **元数据**: 车系、品牌、价格、类别等
- **预计文档数**: ~580 条

### 3. 用户画像描述
- **来源**: `Data/Analyzed/Persona/step4_user_persona_full.csv`
- **内容**: 画像特征描述（Top 3 关注维度）
- **元数据**: 画像名称、用户数量、质心权重等
- **预计文档数**: 8 条

---

## 📈 数据规模

| 集合名称 | 文档数量 | 向量维度 | 存储位置 |
|---------|---------|---------|---------|
| `ugc_reviews` | ~360,000 | 384 | `Data/Vector/` |
| `vehicle_specs` | ~580 | 384 | `Data/Vector/` |
| `user_personas` | 8 | 384 | `Data/Vector/` |

**向量维度**: 默认使用 `paraphrase-multilingual-MiniLM-L12-v2` 模型（384维，支持中文）

---

## 🔧 嵌入模型选择

### 本地模型（推荐）

| 模型名称 | 维度 | 特点 | 适用场景 |
|---------|------|------|---------|
| `all-MiniLM-L6-v2` | 384 | 轻量级，英文优化 | 快速测试 |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | 多语言支持 | **推荐用于中文** |
| `distiluse-base-multilingual-cased-v2` | 512 | 高性能多语言 | 生产环境 |

### API 模型（可选）

需要在 `.env` 中配置 `OPENAI_API_KEY`：
```bash
python Vector/build_vector_db.py --model openai
```

---

## �️ 脚本说明

### build_vector_db.py
主构建脚本，功能：
- 读取并清洗数据（UGC、车型、画像）
- 生成文本嵌入向量（使用 SentenceTransformer）
- 批量存储到 ChromaDB
- 支持断点续传（自动跳过已存在的集合）

**参数**：
- `--limit`: 限制 UGC 评论数量（测试用）
- `--model`: 指定嵌入模型名称

---

## 📝 输出说明

### 数据库位置
- **路径**: `Data/Vector/`
- **格式**: ChromaDB 持久化存储

### 日志文件
- **路径**: `vector_build.log`
- **内容**: 构建过程详细日志

---

## 🤝 与其他模块协同

- **Graph/**: Neo4j 图数据库，负责结构化关系
- **Vector/**: ChromaDB 向量数据库，负责语义嵌入
- **RAG/** (待开发): 混合检索和生成应用

---

## ⚠️ 注意事项

1. **首次运行**: 需要下载嵌入模型（约 100-500MB）
2. **内存需求**: 建议至少 8GB RAM（处理全量 UGC 数据）
3. **时间估算**: 完整构建约需 30-60 分钟（取决于硬件）
4. **存储空间**: 向量数据库约占用 2-3GB 磁盘空间

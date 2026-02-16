# Process 模块 - 数据处理

## 功能说明

负责清洗、标准化和结构化原始采集数据，输出可用于分析的高质量数据集。

## 核心脚本

### 1. Para_process.py
- 处理车型参数 JSON 文件
- 标准化字段名称和数据格式
- 输出：`Data/Processed/vehicles_config.json`

### 2. UGC_process.py
- 清洗用户评论数据
- 提取真实续航、成交价、地理位置等关键信息
- 统一评分维度（外观、内饰、空间、操控、智能、续航、性价比）
- 输出：`Data/Processed/ugc.csv`（黄金数据集，包含 20+ 个分析字段）

### 3. Pic_process.py
- 处理车型图片
- 生成图片索引映射
- 输出：`Data/Processed/image_map.json`

## 数据质量

处理后的 `ugc.csv` 包含以下核心字段：
- 基本信息：brand, series, model, user_id, review_date
- 评分数据：appearance_score, interior_score, space_score, control_score, intelligence_score, endurance_score, cost_performance_score
- 文本数据：appearance_text, interior_text, space_text, control_text, intelligence_text, endurance_text, cost_performance_text, overall_comment, purchase_reason
- 扩展信息：real_endurance, deal_price, province, city, usage_frequency

## 使用方法

```bash
# 处理车型参数
python Process/Para_process.py

# 处理用户评论
python Process/UGC_process.py

# 处理图片
python Process/Pic_process.py
```

## 输出数据

所有处理后的数据存储在 `Data/Processed/` 目录下，可直接用于后续分析和知识图谱构建。

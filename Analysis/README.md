# Analysis 模块 - 智能分析

## 功能说明

基于处理后的数据，进行用户画像聚类和 IPA 战略分析，为产品决策提供量化依据。

## 子模块

### Persona - 用户画像聚类

基于 K-Means 聚类算法，从用户评论行为中提取注意力向量，识别典型用户群体。

**核心脚本**
- `step1_extract_attention.py` - 提取用户在7个维度的注意力向量
- `step2a_initial_k_test.py` - 初步测试最优 K 值（3-15）
- `step2b_k_range_eval.py` - 精细化 K 值评估
- `step2c_k_visualization.py` - 可视化不同 K 值的聚类效果
- `step3_final_clustering.py` - 执行最终聚类（K=8）
- `step4_merge_external_attributes.py` - 合并地理、价格、用车频率等外部属性

**输出结果**
- `Data/Analyzed/Persona/step1_attention_vectors.csv` - 用户注意力向量
- `Data/Analyzed/Persona/step4_user_persona_full.csv` - 完整用户画像数据
- `Data/Analyzed/Persona/clustering_report.json` - 聚类评估报告
- `Data/Analyzed/Persona/expert_cluster_profile.md` - 8个画像的详细描述

**8 类用户画像**
1. 全能均衡型 - 关注各维度均衡
2. 传统务实型 - 重视性价比和实用性
3. 品质体验型 - 追求高品质和驾驶体验
4. 内饰舒适型 - 专注内饰和舒适性
5. 极致空间型 - 对空间有极高要求
6. 极致操控型 - 追求驾驶操控感
7. 颜值至上型 - 外观设计优先
8. 续航焦虑型 - 续航里程是首要考虑

### IPA - 重要性-表现分析

构建"用户关注度-产品表现力"二维矩阵，识别产品优势区、改进区和机会区。

**核心脚本**
- `step1_compute_scores.py` - 计算各维度的重要性（I）和表现力（P）分数
- `step2_generate_ipa_reports.py` - 生成品牌、车系和维度分析报告

**输出结果**
- `Data/Analyzed/IPA/step1_scores_matrix.csv` - IPA 分数矩阵
- `Data/Analyzed/IPA/brand_analysis_report.md` - 品牌级分析报告
- `Data/Analyzed/IPA/dimension_analysis_report.md` - 维度级分析报告
- `Data/Analyzed/IPA/top20_series_analysis_report.md` - Top 20 车系分析
- `Data/Analyzed/IPA/brands_charts/` - 品牌 IPA 散点图
- `Data/Analyzed/IPA/series_charts/` - 车系 IPA 散点图

## 使用方法

```bash
# 运行用户画像分析全流程
cd Analysis/Persona
python step1_extract_attention.py
python step3_final_clustering.py
python step4_merge_external_attributes.py

# 运行 IPA 战略分析
cd ../IPA
python step1_compute_scores.py
python step2_generate_ipa_reports.py
```

## 技术栈

- 聚类算法：K-Means (Scikit-learn)
- 评估指标：Silhouette Score, Davies-Bouldin Index, Calinski-Harabasz Index
- 可视化：Matplotlib, Seaborn
- 数据处理：Pandas, NumPy

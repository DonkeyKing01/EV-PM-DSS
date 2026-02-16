# RAG 模块 - 检索增强生成应用

## 功能说明

基于 Chainlit 框架的智能问答系统，结合知识图谱和向量数据库，为电动汽车产品经理提供三大核心功能。

## 三大核心功能

### 1. User Insights - 用户洞察分析
- 基于真实用户评论和权威用户画像
- 分析用户需求、痛点和期望
- 支持对话式追问，深入理解用户群体特征

### 2. Competitor Analysis - 竞品分析
- 对比多个品牌和车型的关键参数
- 整合用户口碑和官方规格数据
- 客观呈现优劣势对比，辅助市场定位决策

### 3. PRD Writer - PRD 文档撰写
- 基于用户画像、市场数据和竞品分析自动生成产品需求文档
- 所有需求点均可溯源到具体数据来源
- 支持导出为 Markdown 格式

## 技术架构

### 核心组件

```
RAG/
├── app.py                    # Chainlit 主程序
├── config.py                 # 配置管理
├── chainlit.md              # 欢迎页面
├── tools/                    # 工具模块
│   ├── __init__.py
│   ├── query_analyzer.py    # 查询分析和路由
│   ├── hybrid_retriever.py  # 混合检索（图谱+向量）
│   ├── graph_tool.py        # Neo4j 图谱查询
│   └── vector_tool.py       # ChromaDB 向量检索
└── chains/                   # LangChain 链（预留）
```

### 关键特性

**对话记忆**
- 支持多轮对话，自动理解上下文
- 最近 3 轮对话自动注入 LLM 推理过程
- 处理指代消解（"它"、"这个车"、"刚才那个用户"）

**智能检索**
- 分层检索策略：快速检索（15条）→ 标准检索（50条）→ 深度检索（100条）
- 自动根据向量距离调整检索深度
- 混合检索：知识图谱（结构化数据）+ 向量库（语义检索）

**数据溯源**
- 每个洞察都标注具体来源（画像、评论、规格）
- 可折叠的数据源展示，方便验证和审查
- 防止幻觉：严格限制 LLM 仅基于提供的数据回答

**智能路由**
- 自动判断问题类型（需要检索 vs 可直接回答）
- 实体提取：自动识别品牌和车型名称
- 查询复杂度评估：动态调整检索数量

## 技术栈

- 前端框架：Chainlit
- 大语言模型：SiliconFlow API (DeepSeek-R1-Distill-Qwen-32B)
- 路由模型：Qwen2.5-7B-Instruct
- 知识图谱：Neo4j
- 向量数据库：ChromaDB
- 嵌入模型：paraphrase-multilingual-MiniLM-L12-v2

## 环境配置

需要在根目录 `.env` 文件中配置：

```bash
# Neo4j 数据库
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# SiliconFlow API
SILICONFLOW_API_KEY=your-api-key
```

## 使用方法

```bash
# 启动应用
chainlit run RAG/app.py

# 指定端口
chainlit run RAG/app.py --port 8100
```

访问 http://localhost:8000 开始使用。

## 使用指南

1. 从左侧选择功能模块（User Insights / Competitor Analysis / PRD Writer）
2. 输入您的问题或需求
3. 系统将自动执行：查询路由 → 实体提取 → 混合检索 → AI 分析
4. 查看分析结果和数据来源
5. 继续追问以深入探索

## 工作流程

### User Insights 流程
```
用户输入 → 查询路由 → 问题分析 → 混合检索（画像+评论）→ LLM 分析 → 结果展示
```

### Competitor Analysis 流程
```
用户输入 → 查询路由 → 实体提取 → 混合检索（车型+评论+规格）→ LLM 对比分析 → 结果展示
```

### PRD Writer 流程
```
用户输入 → 查询路由 → 实体提取 → 全栈检索（画像+车型+评论）→ LLM 生成 PRD → 结果展示 + 导出
```

## 注意事项

- DeepSeek R1 推理模型响应时间 30-60 秒，请耐心等待
- 系统已添加心跳机制防止 WebSocket 超时
- 所有分析结果均基于已有数据，数据不足时会明确说明
- 建议从简单问题开始，逐步追问深入细节

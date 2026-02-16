# 欢迎使用 EV PM DSS

电动车产品经理决策支持系统（Electric Vehicle Product Manager Decision Support System）

## 系统简介

本系统是一个基于 RAG（检索增强生成）架构的智能决策辅助工具，专为电动汽车产品经理设计。通过整合知识图谱和向量数据库，结合大语言模型的推理能力，为产品决策提供数据驱动的洞察。

## 核心功能

**用户洞察分析（User Insights）**
- 基于真实用户评论和权威用户画像
- 分析用户需求、痛点和期望
- 支持对话式追问，深入理解用户群体特征

**竞品分析（Competitor Analysis）**
- 对比多个品牌和车型的关键参数
- 整合用户口碑和官方规格数据
- 客观呈现优劣势对比，辅助市场定位决策

**PRD 文档撰写（PRD Writer）**
- 基于用户画像、市场数据和竞品分析自动生成产品需求文档
- 所有需求点均可溯源到具体数据来源
- 支持导出为 Markdown 格式，直接用于产品规划

## 技术亮点

**对话记忆**
- 支持多轮对话，自动理解上下文和指代关系
- 最近 3 轮对话自动注入 LLM 推理过程

**智能检索**
- 分层检索策略：快速检索（15条）→ 标准检索（50条）→ 深度检索（100条）
- 自动根据向量距离调整检索深度
- 混合检索：知识图谱（结构化数据）+ 向量库（语义检索）

**数据溯源**
- 每个洞察都标注具体来源（画像、评论、规格）
- 可折叠的数据源展示，方便验证和审查
- 防止幻觉：严格限制 LLM 仅基于提供的数据回答

## 使用指南

1. 从左侧选择功能模块（User Insights / Competitor Analysis / PRD Writer）
2. 输入您的问题或需求
3. 系统将自动执行：查询路由 → 实体提取 → 混合检索 → AI 分析
4. 查看分析结果和数据来源
5. 继续追问以深入探索

## 技术栈

- 前端框架：Chainlit
- 知识图谱：Neo4j
- 向量数据库：ChromaDB
- 嵌入模型：paraphrase-multilingual-MiniLM-L12-v2
- 大语言模型：SiliconFlow API（DeepSeek-R1-Distill-Qwen-32B）

## 数据说明

当前系统包含：
- 12 个电动车品牌（AITO 问界、奔驰、奥迪、宝马、小米汽车、小鹏、极氪、比亚迪、沃尔沃、特斯拉、理想汽车、蔚来）
- 8 个权威用户画像（基于真实用户评论聚类生成）
- 数千条真实用户口碑评论
- 完整的车型参数和规格数据

---

# Welcome to EV PM DSS

Electric Vehicle Product Manager Decision Support System

## About

An intelligent decision support tool for EV product managers, built on RAG (Retrieval-Augmented Generation) architecture. Combines knowledge graphs and vector databases with LLM reasoning to provide data-driven insights for product decisions.

## Core Features

**User Insights Analysis**
- Based on real user reviews and authoritative personas
- Analyze user needs, pain points, and expectations
- Support conversational follow-ups for deeper understanding

**Competitor Analysis**
- Compare key parameters across multiple brands and models
- Integrate user feedback with official specifications
- Objective presentation of strengths and weaknesses

**PRD Writer**
- Auto-generate Product Requirement Documents based on user personas, market data, and competitive analysis
- All requirements traceable to specific data sources
- Export as Markdown for direct use in product planning

## Technical Highlights

**Conversation Memory**
- Multi-turn dialogue with automatic context understanding
- Last 3 rounds of conversation automatically injected into LLM reasoning

**Smart Retrieval**
- Layered retrieval strategy: Quick (15) → Standard (50) → Deep (100)
- Automatic depth adjustment based on vector distance
- Hybrid retrieval: Knowledge graph (structured) + Vector DB (semantic)

**Data Traceability**
- Every insight annotated with specific sources (personas, reviews, specs)
- Collapsible data source display for verification
- Hallucination prevention: LLM strictly limited to provided data

## Tech Stack

Frontend: Chainlit | Knowledge Graph: Neo4j | Vector DB: ChromaDB | Embedding: paraphrase-multilingual-MiniLM-L12-v2 | LLM: SiliconFlow (DeepSeek-R1-Distill-Qwen-32B)

## Data Coverage

12 EV brands | 8 user personas | Thousands of real user reviews | Complete vehicle specifications

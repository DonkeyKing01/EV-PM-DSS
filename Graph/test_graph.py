"""
Neo4j Knowledge Graph Builder - Test Mode
小规模数据测试脚本（导入前 1000 条评论用于验证）

Author: EV PM DSS Team
Date: 2026-02-15
"""

import os
import sys

# 添加父目录到路径以便导入 build_graph 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_graph import Neo4jGraphBuilder, logger

# ==================== Test Configuration ====================
# 测试模式配置
TEST_LIMIT = 1000  # 仅导入 1000 条评论
RANDOM_SAMPLE = True  # 使用随机抽样
ENABLE_FULL_VEHICLE_IMPORT = True  # 是否导入完整的车型数据（建议保持 True）

# Neo4j 配置（从环境变量读取）
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def run_test_import():
    """执行测试导入"""
    # 验证必需的环境变量
    if not NEO4J_URI:
        raise ValueError("NEO4J_URI environment variable is required")
    if not NEO4J_PASSWORD:
        raise ValueError("NEO4J_PASSWORD environment variable is required")
    
    logger.info("=" * 70)
    logger.info("🧪 TEST MODE - Knowledge Graph Construction")
    logger.info(f"   Limit: {TEST_LIMIT} reviews")
    logger.info(f"   Sampling: {'Random' if RANDOM_SAMPLE else 'Sequential'}")
    logger.info(f"   Full vehicle data: {'Yes' if ENABLE_FULL_VEHICLE_IMPORT else 'No'}")
    logger.info("=" * 70)
    
    # 创建构建器实例
    builder = Neo4jGraphBuilder(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE
    )
    
    # 执行测试导入
    builder.build(limit=TEST_LIMIT, random_sample=RANDOM_SAMPLE)
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ Test import completed successfully!")
    logger.info("=" * 70)
    logger.info("\n建议验证步骤:")
    logger.info("1. 登录 Neo4j Browser: https://console.neo4j.io/")
    logger.info("2. 运行验证查询:")
    logger.info("   MATCH (n) RETURN labels(n) as Type, count(n) as Count")
    logger.info("3. 检查节点和关系数量是否符合预期")
    logger.info("4. 如果测试正常，运行 build_graph.py 执行完整导入")
    logger.info("=" * 70)


if __name__ == "__main__":
    try:
        run_test_import()
    except Exception as e:
        logger.error(f"Test import failed: {e}", exc_info=True)
        sys.exit(1)

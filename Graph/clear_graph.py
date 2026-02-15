"""
Neo4j Knowledge Graph - Clear All Data
清空知识图谱所有数据（用于重新导入前清理）

Author: EV PM DSS Team
Date: 2026-02-15
"""

import os
import sys
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_graph import Neo4jGraphBuilder, logger

# Neo4j 配置
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def clear_all_data():
    """清空数据库中的所有节点和关系"""
    # 验证环境变量
    if not NEO4J_URI or not NEO4J_PASSWORD:
        raise ValueError("NEO4J_URI and NEO4J_PASSWORD are required")
    
    # 连接数据库
    builder = Neo4jGraphBuilder(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE
    )
    
    logger.info("=" * 70)
    logger.info("⚠️  WARNING: Clearing ALL data from Neo4j database")
    logger.info("=" * 70)
    
    # 删除所有节点和关系
    logger.info("Deleting all nodes and relationships...")
    with builder.driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        
        # 验证删除（在同一个 session 中）
        result = session.run("MATCH (n) RETURN count(n) as count")
        count = result.single()["count"]
    
    logger.info("=" * 70)
    if count == 0:
        logger.info("✅ Database cleared successfully!")
    else:
        logger.warning(f"⚠️  Warning: {count} nodes still remain")
    logger.info("=" * 70)
    
    builder.close()


if __name__ == "__main__":
    try:
        # 二次确认
        print("\n" + "=" * 70)
        print("⚠️  WARNING: This will DELETE ALL data from your Neo4j database!")
        print("=" * 70)
        confirm = input("Type 'YES' to confirm deletion: ")
        
        if confirm == "YES":
            clear_all_data()
        else:
            print("Operation cancelled.")
            sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to clear database: {e}", exc_info=True)
        sys.exit(1)

"""
Vector Database Test Script
测试脚本 - 小规模数据验证向量数据库构建逻辑

Author: EV PM DSS Team
Date: 2026-02-15
"""

import sys
import logging
from build_vector_db import VectorDBBuilder

# ==================== Test Configuration ====================
TEST_LIMIT = 1000  # 限制 UGC 评论数量
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"  # 多语言模型

# ==================== Logging ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_test():
    """运行测试导入"""
    logger.info("=" * 70)
    logger.info("🧪 TEST MODE - Vector Database Construction")
    logger.info(f"   UGC Limit: {TEST_LIMIT} reviews")
    logger.info(f"   Embedding Model: {EMBEDDING_MODEL}")
    logger.info("=" * 70)
    
    try:
        # 创建构建器
        builder = VectorDBBuilder(embedding_model=EMBEDDING_MODEL)
        
        # 仅构建 UGC 集合（测试模式）
        logger.info("Building UGC reviews collection (test mode)...")
        builder.build_ugc_collection(limit=TEST_LIMIT)
        
        logger.info("=" * 70)
        logger.info("✅ Test completed successfully!")
        logger.info("=" * 70)
        logger.info("\n建议验证步骤:")
        logger.info("1. 检查 Vector/chroma_db/ 目录是否已创建")
        logger.info("2. 查看 vector_build.log 日志文件")
        logger.info("3. 如果测试正常，运行完整构建:")
        logger.info("   python Vector/build_vector_db.py")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run_test()

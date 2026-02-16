"""
Vector Database Verification Script
验证向量数据库完整性

Author: EV PM DSS Team
Date: 2026-02-15
"""

import chromadb
from chromadb.config import Settings

# 连接到向量数据库
client = chromadb.PersistentClient(
    path="D:/code/EV PM DSS/Data/Vector",
    settings=Settings(anonymized_telemetry=False)
)

# 列出所有集合
collections = client.list_collections()

print("=" * 70)
print("Vector Database Verification Report")
print("=" * 70)
print(f"\nTotal Collections: {len(collections)}\n")

for collection in collections:
    print(f"📦 Collection: {collection.name}")
    print(f"   Documents: {collection.count():,}")
    print(f"   Metadata: {collection.metadata}")
    print()

print("=" * 70)
print("✅ Database verification complete!")
print("=" * 70)

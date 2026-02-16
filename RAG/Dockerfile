# EV PM DSS - ModelScope 部署 Dockerfile
# 优化：预下载 Embedding 模型到镜像，避免冷启动下载

FROM python:3.10-slim

WORKDIR /app

# 1. 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. 复制依赖文件
COPY requirements.txt .

# 3. 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 4. 【关键】预下载 Embedding 模型到镜像
# 这样每次冷启动时无需重新下载，瞬间启动
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
import chromadb; \
print('⬇️ Downloading SentenceTransformer model...'); \
SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2'); \
print('⬇️ Downloading ChromaDB ONNX model...'); \
client = chromadb.Client(); \
print('✅ Models cached in image!'); \
"

# 5. 复制应用代码
COPY RAG/ ./RAG/
COPY Graph/ ./Graph/
COPY Vector/ ./Vector/
COPY .env.example .env

# 6. 暴露端口
EXPOSE 7860

# 7. 启动命令
CMD ["chainlit", "run", "RAG/app.py", "--host", "0.0.0.0", "--port", "7860"]

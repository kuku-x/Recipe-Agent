# Recipe Agent Docker 配置
# 支持 FastAPI 后端 + Vue 前端

FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# 复制后端 requirements 并安装
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# 复制源代码
COPY src/ ./src/
COPY backend/ ./backend/

# 复制前端（如果需要构建）
COPY frontend/package.json ./frontend/
RUN pip install npm && cd frontend && npm install

# 设置环境变量
ENV PYTHONPATH=/app/src

# 暴露端口
# 8000: FastAPI 后端
# 5173: Vite 开发服务器
EXPOSE 8000 5173

# 启动命令（开发模式）
# 使用 docker-compose.yml 中的 command 覆盖
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port 8000"]

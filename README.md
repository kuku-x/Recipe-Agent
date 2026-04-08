# Recipe Agent - 智能烹饪助手

基于图数据库的 RAG (Retrieval-Augmented Generation) 智能烹饪助手，支持 Neo4j 图数据库和 Milvus 向量数据库。

## 功能特性

- **混合检索**: 结合向量检索和 BM25 关键词检索
- **图 RAG**: 基于 Neo4j 的知识图谱，支持多跳推理
- **智能路由**: 自动分析查询复杂度，选择最优检索策略
- **流式输出**: 支持 LLM 流式生成回答
- **可爱 UI**: Vue 3 + TailwindCSS 打造的温馨界面

## 技术栈

### 后端
- **Python**: FastAPI + uvicorn
- **LLM**: Moonshot/Kimi (OpenAI 兼容 API)
- **向量数据库**: Milvus
- **图数据库**: Neo4j
- **Embedding**: BAAI/bge-small-zh-v1.5

### 前端
- **框架**: Vue 3 + Vite
- **样式**: TailwindCSS
- **状态管理**: Pinia
- **样式风格**: 可爱、温暖的生活风格

## 项目结构

```
recipe_agent/
├── src/recipe_agent/    # RAG 核心模块
│   ├── rag/             # RAG 检索模块
│   ├── agent/           # Agent 模块
│   └── common/          # 公共组件
├── backend/             # FastAPI 后端
│   ├── main.py
│   └── routers/
├── frontend/            # Vue 前端
│   ├── src/
│   │   ├── components/  # Vue 组件
│   │   ├── stores/      # Pinia 状态管理
│   │   └── views/       # 页面视图
│   └── ...
├── web/                 # 旧版 Web 服务 (已废弃)
└── tests/               # 测试
```

## 快速开始

### 前置条件

- Python 3.12+
- Node.js 18+
- Docker (用于 Neo4j 和 Milvus)

### 1. 启动依赖服务

```bash
docker start milvus-etcd milvus-minio milvus-standalone
docker start neo4j-db
```

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
```

### 4. 配置

复制 `.env.example` 为 `.env`，填入你的 API Key：

```bash
MOONSHOT_API_KEY=your_api_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=all-in-rag
```

### 5. 启动

```bash
# 终端 1: 启动后端
cd backend
uvicorn main:app --reload --port 8000

# 终端 2: 启动前端
cd frontend
npm run dev
```

访问 http://localhost:5173 即可使用！

## 开发

```bash
# 后端代码格式化
ruff check src/

# 前端构建
cd frontend
npm run build
```

## License

MIT

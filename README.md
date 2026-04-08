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
│   │   ├── data_preparation.py  # 图形数据准备
│   │   ├── vector_index.py      # Milvus 向量索引
│   │   ├── hybrid_retrieval.py  # 混合检索
│   │   ├── graph_rag.py        # 图 RAG 检索
│   │   ├── query_router.py     # 智能查询路由
│   │   └── generation.py       # 答案生成
│   ├── agent/            # Agent 模块
│   │   ├── recipe_agent.py     # Kimi 菜谱解析 Agent
│   │   └── amount_normalizer.py # 食材量标准化
│   └── common/           # 公共组件
│       ├── neo4j_client.py  # Neo4j 连接池
│       ├── llm_service.py   # LLM 服务
│       └── cache.py       # 缓存工具
├── backend/              # FastAPI 后端
│   ├── main.py           # FastAPI 入口
│   └── routers/
│       └── chat.py       # 聊天路由 (SSE 流式)
├── frontend/             # Vue 前端
│   ├── src/
│   │   ├── components/  # Vue 组件
│   │   │   ├── ChatMessage.vue   # 消息气泡
│   │   │   ├── ChatInput.vue     # 输入框
│   │   │   ├── QuickActions.vue  # 快捷问题
│   │   │   └── ChatHistory.vue  # 历史记录
│   │   └── stores/
│   │       └── chat.ts   # Pinia 状态管理
│   └── ...
├── web/                 # 旧版 Web 服务 (已废弃)
└── tests/               # 测试目录
```

## 快速开始

### 前置条件

- Python 3.12+
- Node.js 18+
- Docker (用于 Neo4j 和 Milvus)

### 1. 克隆项目

```bash
git clone https://github.com/kuku-x/Recipe-Agent.git
cd Recipe-Agent
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填入你的 API Key：

```bash
MOONSHOT_API_KEY=your_api_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=all-in-rag
```

### 3. 使用 Docker 启动依赖服务 (推荐)

```bash
docker-compose up -d
```

或手动启动：

```bash
docker start milvus-etcd milvus-minio milvus-standalone neo4j-db
```

### 4. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 即可使用！

## API 文档

后端启动后访问：
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 主要接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | 聊天接口 (SSE 流式) |
| `/api/status` | GET | 获取 RAG 系统状态 |
| `/api/history` | GET | 获取对话历史 |
| `/api/history/{id}` | DELETE | 删除对话 |

### 聊天接口示例

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "红烧肉怎么做？"}'
```

## Docker 部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend

# 停止服务
docker-compose down
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 后端代码检查
ruff check src/

# 前端构建
cd frontend
npm run build
```

## 架构说明

```
用户提问
    │
    ▼
┌─────────────────┐
│  FastAPI 后端    │
│  /api/chat      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Intelligent     │
│ QueryRouter     │ ← 分析查询复杂度
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐  ┌───────┐
│Hybrid │  │Graph  │
│Retrieval│ │RAG   │
└───┬───┘  └───┬───┘
    │          │
    └────┬─────┘
         ▼
┌─────────────────┐
│  Moonshot/Kimi  │ ← LLM 生成回答
└────────┬────────┘
         │
         ▼
    SSE 流式响应
         │
         ▼
┌─────────────────┐
│   Vue 前端      │ ← 实时显示
└─────────────────┘
```

## License

MIT

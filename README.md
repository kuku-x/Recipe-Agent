# Recipe Agent - 智能烹饪助手

基于图数据库的 RAG (Retrieval-Augmented Generation) 智能烹饪助手，支持 Neo4j 图数据库和 Milvus 向量数据库。

## 功能特性

- **混合检索**: 结合向量检索和 BM25 关键词检索
- **图 RAG**: 基于 Neo4j 的知识图谱，支持多跳推理
- **智能路由**: 自动分析查询复杂度，选择最优检索策略
- **流式输出**: 支持 LLM 流式生成回答

## 技术栈

- **LLM**: Moonshot/Kimi (OpenAI 兼容 API)
- **向量数据库**: Milvus
- **图数据库**: Neo4j
- **Embedding**: BAAI/bge-small-zh-v1.5
- **框架**: LangChain, Flask

## 项目结构

```
src/recipe_agent/
├── rag/            # RAG 核心模块
├── agent/          # Agent 模块
└── common/         # 公共组件
web/                # Web 服务
tests/              # 测试
```

## 快速开始

### 环境要求

- Python 3.12+
- Neo4j 5.x
- Milvus 2.5.x

### 安装

```bash
pip install -r requirements.txt
```

### 配置

复制 `.env.example` 为 `.env`，填入你的 API Key 和数据库配置。

### 运行

```bash
# 启动依赖服务
docker-compose up -d

# 运行主程序
python -m recipe_agent.main
```

### Web 服务

```bash
cd web
python server.py
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 代码格式化
black src/
ruff check src/
```

## License

MIT

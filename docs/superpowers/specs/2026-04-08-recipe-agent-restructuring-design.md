# Recipe Agent 项目架构重构设计

**日期**: 2026-04-08
**状态**: 已批准

## 1. 背景

这是一个用于学习和求职的 Graph RAG 烹饪助手项目。原项目结构存在以下问题：
- 目录名含中文和特殊字符 (`agent(代码系ai生成)/`)
- 模块组织不清晰，`rag_modules/` 和 `agent/` 分离
- 缺少标准 Python 项目文件 (`pyproject.toml`、`.gitignore`)
- 无 Docker 配置和测试目录

## 2. 目标

将项目重构为专业的 Python 项目结构，便于：
- 面试时展示架构思维
- 团队协作
- 部署和运维

## 3. 目标目录结构

```
recipe_agent/
├── src/
│   └── recipe_agent/
│       ├── __init__.py
│       ├── main.py                 # 主入口
│       ├── config.py               # 配置类
│       │
│       ├── rag/                     # RAG 核心模块
│       │   ├── __init__.py
│       │   ├── data_preparation.py # 图形数据准备
│       │   ├── vector_index.py     # Milvus 向量索引
│       │   ├── hybrid_retrieval.py # 混合检索
│       │   ├── graph_rag.py        # 图 RAG 检索
│       │   ├── query_router.py     # 智能查询路由
│       │   └── generation.py       # 答案生成
│       │
│       ├── agent/                   # Agent 模块
│       │   ├── __init__.py
│       │   ├── recipe_agent.py     # Kimi 菜谱解析 Agent
│       │   ├── batch_manager.py    # 批处理管理
│       │   └── amount_normalizer.py # 食材量标准化
│       │
│       └── common/                  # 公共模块
│           ├── __init__.py
│           ├── neo4j_client.py     # Neo4j 连接池
│           ├── llm_service.py       # LLM 服务
│           └── cache.py             # 缓存工具
│
├── tests/                          # 测试目录
│   ├── rag/
│   └── agent/
├── docs/                           # 文档目录
├── web/                            # Web 服务（独立）
│   ├── server.py
│   ├── static/
│   └── templates/
│
├── pyproject.toml                  # 项目配置
├── .gitignore
├── requirements.txt
├── Dockerfile
└── README.md
```

## 4. 文件迁移映射

| 原有位置 | 新位置 |
|---------|-------|
| `main.py` | `src/recipe_agent/main.py` |
| `config.py` | `src/recipe_agent/config.py` |
| `rag_modules/graph_data_preparation.py` | `src/recipe_agent/rag/data_preparation.py` |
| `rag_modules/milvus_index_construction.py` | `src/recipe_agent/rag/vector_index.py` |
| `rag_modules/hybrid_retrieval.py` | `src/recipe_agent/rag/hybrid_retrieval.py` |
| `rag_modules/graph_rag_retrieval.py` | `src/recipe_agent/rag/graph_rag.py` |
| `rag_modules/intelligent_query_router.py` | `src/recipe_agent/rag/query_router.py` |
| `rag_modules/generation_integration.py` | `src/recipe_agent/rag/generation.py` |
| `rag_modules/common.py` | `src/recipe_agent/common/` (拆分) |
| `rag_modules/graph_indexing.py` | `src/recipe_agent/rag/data_preparation.py` |
| `agent(代码系ai生成)/recipe_ai_agent.py` | `src/recipe_agent/agent/recipe_agent.py` |
| `agent(代码系ai生成)/batch_manager.py` | `src/recipe_agent/agent/batch_manager.py` |
| `agent(代码系ai生成)/amount_normalizer.py` | `src/recipe_agent/agent/amount_normalizer.py` |
| `agent(代码系ai生成)/web_server.py` | `web/server.py` |

## 5. 新增文件

### pyproject.toml
- 项目元数据 (name, version, description)
- 依赖声明 (参考原有 requirements.txt)
- 开发依赖 (pytest, black, ruff, mypy)

### .gitignore
- Python 缓存 (`__pycache__/`, `*.pyc`)
- 虚拟环境 (`.venv/`, `venv/`)
- 环境变量文件 (`.env`)
- IDE 配置 (`.vscode/`, `.idea/`)
- 测试覆盖率 (`htmlcov/`, `.coverage`)
- Docker 相关 (`*.egg-info/`)

### Dockerfile
- 基于 Python 3.12
- 安装系统依赖
- 复制项目文件
- 安装 Python 依赖
- 启动命令

### docker-compose.yml
- Neo4j 服务
- Milvus 服务
- Zookeeper (Milvus 依赖)

### tests/
- `tests/rag/` - RAG 模块单元测试
- `tests/agent/` - Agent 模块单元测试
- 使用 pytest 框架

## 6. 设计原则

1. **单一职责**: 每个模块只做一件事
2. **清晰导入**: `from recipe_agent.rag import HybridRetrieval`
3. **可测试性**: 依赖注入，方便 mock 测试
4. **可扩展性**: 清晰接口，易于添加新功能

## 7. 实施步骤

1. 创建目录结构
2. 创建 `pyproject.toml`
3. 创建 `.gitignore`
4. 移动并重构 `rag_modules/` → `src/recipe_agent/rag/`
5. 移动并重构 `agent/` → `src/recipe_agent/agent/`
6. 重构 `common.py` → `src/recipe_agent/common/`
7. 移动 Web 服务 → `web/`
8. 创建测试目录结构
9. 创建 Dockerfile 和 docker-compose.yml
10. 更新 `requirements.txt` (仅保留运行时依赖)
11. 创建 README.md
12. 删除原目录

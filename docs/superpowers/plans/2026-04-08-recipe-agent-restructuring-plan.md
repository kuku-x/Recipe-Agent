# Recipe Agent 项目架构重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 recipe-agent 项目重构为专业的 Python 项目结构，包含清晰模块划分、标准配置文件和 Docker 支持。

**Architecture:** 采用 `src/` 布局模式，将 RAG 核心模块、Agent 模块和公共模块分离到 `src/recipe_agent/` 包中，Web 服务独立于 `web/` 目录。

**Tech Stack:** Python 3.12+, Neo4j, Milvus, Flask, PyTorch, LangChain

---

## 文件结构映射

```
原始位置                                    → 新位置
───────────────────────────────────────────────────────────────────
main.py                                    → src/recipe_agent/main.py
config.py                                  → src/recipe_agent/config.py
rag_modules/graph_data_preparation.py      → src/recipe_agent/rag/data_preparation.py
rag_modules/milvus_index_construction.py  → src/recipe_agent/rag/vector_index.py
rag_modules/hybrid_retrieval.py            → src/recipe_agent/rag/hybrid_retrieval.py
rag_modules/graph_rag_retrieval.py         → src/recipe_agent/rag/graph_rag.py
rag_modules/intelligent_query_router.py     → src/recipe_agent/rag/query_router.py
rag_modules/generation_integration.py       → src/recipe_agent/rag/generation.py
rag_modules/common.py                       → src/recipe_agent/common/ (拆分)
rag_modules/graph_indexing.py              → src/recipe_agent/rag/data_preparation.py
rag_modules/__init__.py                    → src/recipe_agent/rag/__init__.py
agent(代码系ai生成)/recipe_ai_agent.py     → src/recipe_agent/agent/recipe_agent.py
agent(代码系ai生成)/batch_manager.py        → src/recipe_agent/agent/batch_manager.py
agent(代码系ai生成)/amount_normalizer.py    → src/recipe_agent/agent/amount_normalizer.py
agent(代码系ai生成)/web_server.py           → web/server.py
agent(代码系ai生成)/static/                 → web/static/
agent(代码系ai生成)/templates/              → web/templates/
agent(代码系ai生成)/config.json             → web/config.json
agent(代码系ai生成)/requirements.txt        → (合并到根 requirements.txt)
```

---

## 任务列表

### Task 1: 创建项目基础结构和配置文件

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `requirements.txt` (清理版)
- Create: `Dockerfile`
- Create: `docker-compose.yml`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[project]
name = "recipe-agent"
version = "0.1.0"
description = "基于图数据库的智能烹饪助手 RAG 系统"
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }

dependencies = [
    "transformers>=4.40.0",
    "torch==2.6.0",
    "sentence-transformers>=3.0.0",
    "langchain-core>=0.3.0",
    "langchain-community>=0.3.0",
    "langchain-huggingface>=0.3.0",
    "neo4j>=5.0.0",
    "pymilvus>=2.5.0",
    "rank-bm25>=0.2.2",
    "openai>=1.86.0,<2.0.0",
    "tiktoken>=0.4.0",
    "python-dotenv>=1.0.0",
    "numpy>=1.24.0",
    "pandas>=2.0.0",
    "scikit-learn>=1.3.0",
    "tqdm>=4.64.0",
    "pydantic>=2.0.0",
    "requests>=2.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "black>=24.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/recipe_agent"]

[tool.black]
line-length = 100
target-version = ["py312"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
```

- [ ] **Step 2: 创建 .gitignore**

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg
*.egg-info/
dist/
build/

# Virtual environments
.venv/
venv/
ENV/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# OS
.DS_Store
Thumbs.db

# Project specific
*.log
milvus_data/
neo4j_data/
```

- [ ] **Step 3: 创建 requirements.txt (清理版)**

```
# Core ML
transformers>=4.40.0
torch==2.6.0
sentence-transformers>=3.0.0

# LangChain
langchain-core>=0.3.0
langchain-community>=0.3.0
langchain-huggingface>=0.3.0

# Databases
neo4j>=5.0.0
pymilvus>=2.5.0

# LLM
openai>=1.86.0,<2.0.0
tiktoken>=0.4.0

# Utils
python-dotenv>=1.0.0
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
tqdm>=4.64.0
pydantic>=2.0.0
requests>=2.28.0
rank-bm25>=0.2.2
```

- [ ] **Step 4: 创建 Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY src/ ./src/
COPY web/ ./web/
COPY pyproject.toml .
COPY .env.example .

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "recipe_agent.main"]
```

- [ ] **Step 5: 创建 docker-compose.yml**

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5.20
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/all-in-rag
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - neo4j_data:/data

  milvus:
    image: milvusdb/milvus:v2.5.11
    ports:
      - "19530:19530"
      - "9091:9091"
    environment:
      - ETCD_ENDPOINTS=etcd:2379
      - MINIO_ADDRESS=minio:9000
    depends_on:
      - etcd
      - minio
    volumes:
      - milvus_data:/var/lib/milvus

  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - etcd_data:/etcd

  minio:
    image: minio/minio:latest
    ports:
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/minio_data
    command: server /minio_data --console-address ":9001"

volumes:
  neo4j_data:
  milvus_data:
  etcd_data:
  minio_data:
```

- [ ] **Step 6: 创建 .env.example**

```
# API Keys
MOONSHOT_API_KEY=your_api_key_here

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=all-in-rag
NEO4J_DATABASE=neo4j

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Models
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
LLM_MODEL=kimi-k2-0711-preview
```

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .gitignore requirements.txt Dockerfile docker-compose.yml .env.example
git commit -m "chore: add project configuration files"
```

---

### Task 2: 创建项目目录结构

**Files:**
- Create: `src/recipe_agent/__init__.py`
- Create: `src/recipe_agent/rag/__init__.py`
- Create: `src/recipe_agent/agent/__init__.py`
- Create: `src/recipe_agent/common/__init__.py`
- Create: `tests/rag/__init__.py`
- Create: `tests/agent/__init__.py`
- Create: `tests/common/__init__.py`
- Create: `web/static/`
- Create: `web/templates/`

- [ ] **Step 1: 创建所有目录和 __init__.py 文件**

```bash
mkdir -p src/recipe_agent/rag
mkdir -p src/recipe_agent/agent
mkdir -p src/recipe_agent/common
mkdir -p tests/rag
mkdir -p tests/agent
mkdir -p tests/common
mkdir -p web/static
mkdir -p web/templates
touch src/recipe_agent/__init__.py
touch src/recipe_agent/rag/__init__.py
touch src/recipe_agent/agent/__init__.py
touch src/recipe_agent/common/__init__.py
touch tests/__init__.py
touch tests/rag/__init__.py
touch tests/agent/__init__.py
touch tests/common/__init__.py
```

- [ ] **Step 2: 创建 src/recipe_agent/__init__.py**

```python
"""
Recipe Agent - 基于图数据库的智能烹饪助手
"""

__version__ = "0.1.0"
```

- [ ] **Step 3: Commit**

```bash
git add src/ tests/
git commit -m "structure: create project directory structure"
```

---

### Task 3: 迁移并重构 rag/ 模块

**Files:**
- Create: `src/recipe_agent/rag/data_preparation.py` (合并 graph_data_preparation.py + graph_indexing.py)
- Create: `src/recipe_agent/rag/vector_index.py` (原 milvus_index_construction.py)
- Create: `src/recipe_agent/rag/hybrid_retrieval.py`
- Create: `src/recipe_agent/rag/graph_rag.py` (原 graph_rag_retrieval.py)
- Create: `src/recipe_agent/rag/query_router.py` (原 intelligent_query_router.py)
- Create: `src/recipe_agent/rag/generation.py` (原 generation_integration.py)
- Modify: `src/recipe_agent/rag/__init__.py`

**注意**: 需要更新所有文件内的 import 路径，从 `from rag_modules.xxx import xxx` 改为 `from recipe_agent.rag.xxx import xxx` 或 `from recipe_agent.common import xxx`

- [ ] **Step 1: 读取并分析原 rag_modules 文件**

读取以下文件了解具体实现：
- `rag_modules/graph_data_preparation.py`
- `rag_modules/graph_indexing.py`
- `rag_modules/milvus_index_construction.py`
- `rag_modules/hybrid_retrieval.py`
- `rag_modules/graph_rag_retrieval.py`
- `rag_modules/intelligent_query_router.py`
- `rag_modules/generation_integration.py`

- [ ] **Step 2: 创建 src/recipe_agent/rag/data_preparation.py**

将 graph_data_preparation.py 和 graph_indexing.py 的内容合并，注意：
- 更新 import 路径
- class 名保持不变 `GraphDataPreparationModule`

- [ ] **Step 3: 创建 src/recipe_agent/rag/vector_index.py**

将 milvus_index_construction.py 重命名为 vector_index.py：
- 更新 import 路径
- class 名保持不变 `MilvusIndexConstructionModule`

- [ ] **Step 4: 创建 src/recipe_agent/rag/hybrid_retrieval.py**

复制原文件，更新 import 路径

- [ ] **Step 5: 创建 src/recipe_agent/rag/graph_rag.py**

复制原文件，重命名 class `GraphRAGRetrieval`，更新 import 路径

- [ ] **Step 6: 创建 src/recipe_agent/rag/query_router.py**

复制原文件，更新 import 路径

- [ ] **Step 7: 创建 src/recipe_agent/rag/generation.py**

复制原文件，更新 import 路径

- [ ] **Step 8: 更新 src/recipe_agent/rag/__init__.py**

```python
"""RAG 核心模块"""

from .data_preparation import GraphDataPreparationModule
from .vector_index import MilvusIndexConstructionModule
from .hybrid_retrieval import HybridRetrievalModule
from .graph_rag import GraphRAGRetrieval
from .query_router import IntelligentQueryRouter
from .generation import GenerationIntegrationModule

__all__ = [
    "GraphDataPreparationModule",
    "MilvusIndexConstructionModule",
    "HybridRetrievalModule",
    "GraphRAGRetrieval",
    "IntelligentQueryRouter",
    "GenerationIntegrationModule",
]
```

- [ ] **Step 9: Commit**

```bash
git add src/recipe_agent/rag/
git commit -m "refactor: migrate rag_modules to src/recipe_agent/rag/"
```

---

### Task 4: 迁移并重构 common/ 模块

**Files:**
- Create: `src/recipe_agent/common/neo4j_client.py` (从 common.py 提取)
- Create: `src/recipe_agent/common/llm_service.py` (从 common.py 提取)
- Create: `src/recipe_agent/common/cache.py` (从 common.py 提取)
- Create: `src/recipe_agent/common/__init__.py`

**注意**: 需要分析 common.py 的内容，按功能拆分为三个文件

- [ ] **Step 1: 读取 rag_modules/common.py 分析结构**

确定以下 class 和 function 的归属：
- `Neo4jConnectionPool` → neo4j_client.py
- `Neo4jConnectionConfig` → neo4j_client.py
- `LLMService` → llm_service.py
- `LRUCache` → cache.py
- `QueryAnalysisCache` → cache.py
- `parallel_execute` → 归属视情况
- `initialize_services` → llm_service.py

- [ ] **Step 2: 创建 src/recipe_agent/common/neo4j_client.py**

```python
"""Neo4j 客户端和连接池"""

from .neo4j_client import Neo4jConnectionPool, Neo4jConnectionConfig

__all__ = ["Neo4jConnectionPool", "Neo4jConnectionConfig"]
```

- [ ] **Step 3: 创建 src/recipe_agent/common/llm_service.py**

```python
"""LLM 服务"""

from .llm_service import LLMService, initialize_services

__all__ = ["LLMService", "initialize_services"]
```

- [ ] **Step 4: 创建 src/recipe_agent/common/cache.py**

```python
"""缓存工具"""

from .cache import LRUCache, QueryAnalysisCache, parallel_execute

__all__ = ["LRUCache", "QueryAnalysisCache", "parallel_execute"]
```

- [ ] **Step 5: 更新 src/recipe_agent/common/__init__.py**

```python
"""公共模块"""

from .neo4j_client import Neo4jConnectionPool, Neo4jConnectionConfig
from .llm_service import LLMService, initialize_services
from .cache import LRUCache, QueryAnalysisCache, parallel_execute

__all__ = [
    "Neo4jConnectionPool",
    "Neo4jConnectionConfig",
    "LLMService",
    "LRUCache",
    "QueryAnalysisCache",
    "parallel_execute",
    "initialize_services",
]
```

- [ ] **Step 6: Commit**

```bash
git add src/recipe_agent/common/
git commit -m "refactor: split common.py into separate modules"
```

---

### Task 5: 迁移 agent/ 模块

**Files:**
- Create: `src/recipe_agent/agent/recipe_agent.py` (原 recipe_ai_agent.py)
- Create: `src/recipe_agent/agent/batch_manager.py`
- Create: `src/recipe_agent/agent/amount_normalizer.py`
- Create: `src/recipe_agent/agent/__init__.py`

- [ ] **Step 1: 读取原 agent 文件**

读取 `agent(代码系ai生成)/recipe_ai_agent.py`, `batch_manager.py`, `amount_normalizer.py`

- [ ] **Step 2: 创建 src/recipe_agent/agent/recipe_agent.py**

复制 recipe_ai_agent.py 内容，更新 import 路径

- [ ] **Step 3: 创建 src/recipe_agent/agent/batch_manager.py**

复制 batch_manager.py 内容，更新 import 路径

- [ ] **Step 4: 创建 src/recipe_agent/agent/amount_normalizer.py**

复制 amount_normalizer.py 内容

- [ ] **Step 5: 更新 src/recipe_agent/agent/__init__.py**

```python
"""Agent 模块 - 菜谱知识图谱构建"""

from .recipe_agent import KimiRecipeAgent, RecipeInfo, IngredientInfo, CookingStep
from .batch_manager import BatchManager
from .amount_normalizer import AmountNormalizer

__all__ = [
    "KimiRecipeAgent",
    "RecipeInfo",
    "IngredientInfo",
    "CookingStep",
    "BatchManager",
    "AmountNormalizer",
]
```

- [ ] **Step 6: Commit**

```bash
git add src/recipe_agent/agent/
git commit -m "refactor: migrate agent module to src/recipe_agent/agent/"
```

---

### Task 6: 迁移主入口和配置

**Files:**
- Create: `src/recipe_agent/main.py` (原 main.py)
- Create: `src/recipe_agent/config.py` (原 config.py)
- Modify: `src/recipe_agent/__init__.py`

- [ ] **Step 1: 读取原 main.py 和 config.py**

- [ ] **Step 2: 创建 src/recipe_agent/config.py**

复制 config.py 内容

- [ ] **Step 3: 创建 src/recipe_agent/main.py**

复制 main.py 内容，更新 import 路径：
```python
# 旧
from rag_modules import (...)

# 新
from recipe_agent.rag import (...)
from recipe_agent.config import DEFAULT_CONFIG, GraphRAGConfig
```

- [ ] **Step 4: 更新 src/recipe_agent/__init__.py**

```python
"""Recipe Agent - 基于图数据库的智能烹饪助手"""

__version__ = "0.1.0"

from .config import GraphRAGConfig, DEFAULT_CONFIG
from .main import AdvancedGraphRAGSystem

__all__ = ["GraphRAGConfig", "DEFAULT_CONFIG", "AdvancedGraphRAGSystem"]
```

- [ ] **Step 5: Commit**

```bash
git add src/recipe_agent/main.py src/recipe_agent/config.py src/recipe_agent/__init__.py
git commit -m "refactor: migrate main.py and config.py to src/recipe_agent/"
```

---

### Task 7: 迁移 Web 服务

**Files:**
- Create: `web/server.py` (原 web_server.py)
- Move: `agent(代码系ai生成)/static/` → `web/static/`
- Move: `agent(代码系ai生成)/templates/` → `web/templates/`
- Create: `web/config.json`
- Create: `web/__init__.py`

- [ ] **Step 1: 读取原 web_server.py**

- [ ] **Step 2: 创建 web/server.py**

复制 web_server.py 内容，更新 import 路径：
```python
# 旧
from rag_modules import (...)

# 新 (需要从 src 导入)
import sys
sys.path.insert(0, 'src')
from recipe_agent.rag import (...)
```

- [ ] **Step 3: 移动 static/ 和 templates/ 目录**

```bash
mv "agent(代码系ai生成)/static/" web/
mv "agent(代码系ai生成)/templates/" web/
```

- [ ] **Step 4: 创建 web/config.json**

复制 `agent(代码系ai生成)/config.json` 到 `web/config.json`

- [ ] **Step 5: 创建 web/__init__.py**

```python
"""Web 服务模块"""
```

- [ ] **Step 6: Commit**

```bash
git add web/
git commit -m "refactor: migrate web server to web/ directory"
```

---

### Task 8: 创建 README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: 创建 README.md**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README.md"
```

---

### Task 9: 清理原目录

**Files:**
- Delete: `rag_modules/` (整个目录)
- Delete: `agent(代码系ai生成)/` (整个目录)

**注意**: 确保所有迁移完成后再执行此步骤

- [ ] **Step 1: 确认迁移完成**

检查以下文件/目录是否都已迁移：
- [ ] `src/recipe_agent/rag/` 存在且完整
- [ ] `src/recipe_agent/agent/` 存在且完整
- [ ] `src/recipe_agent/common/` 存在且完整
- [ ] `src/recipe_agent/main.py` 存在
- [ ] `src/recipe_agent/config.py` 存在
- [ ] `web/server.py` 存在
- [ ] `web/static/` 存在
- [ ] `web/templates/` 存在

- [ ] **Step 2: 删除原目录**

```bash
rm -rf rag_modules/
rm -rf "agent(代码系ai生成)/"
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove old directory structure"
```

---

### Task 10: 验证项目可运行

**Files:**
- Modify: `pyproject.toml` (如需要调整)

- [ ] **Step 1: 验证 Python 路径设置**

确保 `PYTHONPATH=/app/src` 或等效配置正确

- [ ] **Step 2: 验证导入语句**

```bash
python -c "from recipe_agent.rag import HybridRetrieval; print('OK')"
python -c "from recipe_agent.agent import KimiRecipeAgent; print('OK')"
python -c "from recipe_agent.common import Neo4jConnectionPool; print('OK')"
```

- [ ] **Step 3: Commit (如有修复)**

```bash
git add -A
git commit -m "fix: resolve import path issues"
```

---

## 实施检查清单

完成所有任务后，确认：

- [ ] `src/recipe_agent/` 目录结构正确
- [ ] `web/` 目录独立存在
- [ ] `tests/` 目录结构正确
- [ ] `pyproject.toml` 包含所有依赖
- [ ] `.gitignore` 正确配置
- [ ] `Dockerfile` 和 `docker-compose.yml` 存在
- [ ] `README.md` 文档完整
- [ ] 原 `rag_modules/` 和 `agent(代码系ai生成)/` 已删除
- [ ] 所有 import 路径已更新
- [ ] Python 导入验证通过

"""
Recipe Agent - FastAPI Backend
连接 AdvancedGraphRAGSystem，提供智能问答 API
"""

import sys
import os
from pathlib import Path

# 添加 src 路径以便导入 recipe_agent
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from recipe_agent.config import DEFAULT_CONFIG
from recipe_agent.main import AdvancedGraphRAGSystem
from .routers import chat

# 加载环境变量
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化 RAG 系统
    print("正在初始化 RAG 系统...")
    try:
        rag_system = AdvancedGraphRAGSystem()
        rag_system.initialize_system()
        rag_system.build_knowledge_base()
        app.state.rag_system = rag_system
        print("RAG 系统初始化完成！")
    except Exception as e:
        print(f"RAG 系统初始化失败: {e}")
        app.state.rag_system = None

    yield

    # 关闭时清理资源
    if app.state.rag_system:
        app.state.rag_system._cleanup()


app = FastAPI(
    title="Recipe Agent API",
    description="智能烹饪助手 - 基于 Graph RAG 的问答系统",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router, prefix="/api", tags=["chat"])


@app.get("/")
async def root():
    return {"message": "Recipe Agent API", "status": "running"}


@app.get("/health")
async def health():
    rag_system = getattr(app.state, "rag_system", None)
    return {
        "status": "healthy",
        "rag_system_ready": rag_system is not None and rag_system.system_ready
    }

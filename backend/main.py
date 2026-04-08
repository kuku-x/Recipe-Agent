"""
Recipe Agent - FastAPI Backend
连接 AdvancedGraphRAGSystem，提供智能问答 API
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加 src 路径以便导入 recipe_agent
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers import chat

# 加载环境变量
load_dotenv()

# 创建 FastAPI 应用
app = FastAPI(
    title="Recipe Agent API",
    description="智能烹饪助手 - 基于 Graph RAG 的问答系统",
    version="1.0.0"
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

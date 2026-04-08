"""
聊天路由 - 支持 SSE 流式输出
懒加载 RAG 系统，按需初始化
"""

import json
from typing import List, Dict, AsyncGenerator
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

# 导入放在函数内部，避免启动时加载
RAGSystem = None


def get_rag_system(app):
    """懒加载获取 RAG 系统"""
    global RAGSystem

    if not hasattr(app.state, 'rag_system') or app.state.rag_system is None:
        if RAGSystem is None:
            from recipe_agent.main import AdvancedGraphRAGSystem
            RAGSystem = AdvancedGraphRAGSystem()
            print("正在初始化 RAG 系统...")
            RAGSystem.initialize_system()
            RAGSystem.build_knowledge_base()
            print("RAG 系统初始化完成！")
            app.state.rag_system = RAGSystem

    return getattr(app.state, 'rag_system', None)


class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []


async def generate_stream(req: Request, question: str) -> AsyncGenerator[str, None]:
    """生成流式响应"""
    rag_system = get_rag_system(req.app)

    if not rag_system or not rag_system.system_ready:
        yield json.dumps({"error": "RAG 系统初始化中，请稍候...", "done": True}) + "\n"
        return

    try:
        # 执行智能路由检索
        relevant_docs, analysis = rag_system.query_router.route_query(
            question,
            rag_system.config.top_k
        )

        if not relevant_docs:
            yield json.dumps({"content": "抱歉，没有找到相关的烹饪信息。", "done": True}) + "\n"
            return

        # 使用流式生成
        strategy_info = ""
        if analysis and hasattr(analysis, 'recommended_strategy'):
            strategy_info = f" [使用策略: {analysis.recommended_strategy.value}]"

        for chunk_text in rag_system.generation_module.generate_adaptive_answer_stream(
            question, relevant_docs
        ):
            yield json.dumps({"content": chunk_text, "done": False}) + "\n"

        # 发送完成信号
        yield json.dumps({
            "content": "",
            "done": True,
            "strategy": strategy_info if strategy_info else "unknown"
        }) + "\n"

    except Exception as e:
        yield json.dumps({"error": f"生成回答时出错: {str(e)}", "done": True}) + "\n"


@router.post("/chat")
async def chat(request: ChatRequest, req: Request):
    """
    聊天接口 - 流式响应

    请求:
    {
        "message": "红烧肉怎么做？",
        "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    }

    响应: SSE 流式数据
    """
    return StreamingResponse(
        generate_stream(req, request.message),
        media_type="application/x-ndjson"
    )


@router.get("/status")
async def get_status(req: Request):
    """获取 RAG 系统状态"""
    rag_system = getattr(req.app.state, "rag_system", None)
    is_ready = rag_system is not None and rag_system.system_ready

    return {
        "ready": is_ready,
        "message": "RAG 系统就绪" if is_ready else "RAG 系统初始化中..."
    }


@router.get("/history")
async def get_history():
    """获取对话历史"""
    return {"history": []}


@router.delete("/history/{session_id}")
async def delete_history(session_id: str):
    """删除指定对话历史"""
    return {"success": True, "message": f"对话 {session_id} 已删除"}

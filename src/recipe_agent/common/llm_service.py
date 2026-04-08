"""LLM服务模块"""

import os
import logging
import time
import threading
from typing import Dict, Any, Optional, List

from openai import OpenAI

from .neo4j_client import Neo4jConnectionPool, Neo4jConnectionConfig

logger = logging.getLogger(__name__)


class LLMService:
    """
    统一LLM服务
    封装LLM调用，提供重试、超时、缓存等功能
    """
    _instance: Optional['LLMService'] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = "kimi-k2-0711-preview",
                 temperature: float = 0.1, max_tokens: int = 2048,
                 max_retries: int = 3, timeout: float = 60.0):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.timeout = timeout

        api_key = os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")
        if not api_key:
            raise ValueError("请设置 MOONSHOT_API_KEY 或 KIMI_API_KEY 环境变量")

        self._client = OpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1"
        )
        self._initialized = True
        logger.info(f"LLM服务初始化完成，模型: {model_name}")

    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None,
             temperature: Optional[float] = None, max_tokens: Optional[int] = None,
             retry_times: Optional[int] = None) -> str:
        """
        统一的聊天接口（带重试机制）

        Args:
            messages: 消息列表
            model: 模型名称（可选，默认使用配置的模型）
            temperature: 温度参数
            max_tokens: 最大token数
            retry_times: 重试次数

        Returns:
            模型生成的文本内容
        """
        model = model or self.model_name
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens or self.max_tokens
        retry_times = retry_times or self.max_retries

        last_error = None
        for attempt in range(retry_times):
            try:
                response = self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=self.timeout
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                last_error = e
                logger.warning(f"LLM调用失败 (尝试 {attempt + 1}/{retry_times}): {e}")
                if attempt < retry_times - 1:
                    time.sleep(1.0 * (attempt + 1))

        raise last_error or Exception("LLM调用失败")

    def chat_with_json(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        调用LLM并期望返回JSON格式的结果
        """
        import json
        content = self.chat(messages, **kwargs)
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 内容: {content[:200]}")
            raise ValueError(f"LLM返回的不是有效的JSON格式: {content[:200]}")


def initialize_services(config: Dict[str, Any]) -> tuple:
    """
    初始化所有共享服务

    Returns:
        (Neo4jConnectionPool, LLMService)
    """
    neo4j_config = Neo4jConnectionConfig(
        uri=config.get('neo4j_uri', 'bolt://localhost:7687'),
        user=config.get('neo4j_user', 'neo4j'),
        password=config.get('neo4j_password', 'all-in-rag'),
        database=config.get('neo4j_database', 'neo4j'),
        max_connection_pool_size=config.get('neo4j_pool_size', 50)
    )
    neo4j_pool = Neo4jConnectionPool().initialize(neo4j_config)

    llm_service = LLMService(
        model_name=config.get('llm_model', 'kimi-k2-0711-preview'),
        temperature=config.get('temperature', 0.1),
        max_tokens=config.get('max_tokens', 2048)
    )

    return neo4j_pool, llm_service
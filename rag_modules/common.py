"""
共享工具模块
提供Neo4j连接池管理、LLM统一调用、缓存等公共功能
"""

import os
import logging
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from functools import lru_cache
from dataclasses import dataclass
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed

from neo4j import GraphDatabase
from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class Neo4jConnectionConfig:
    """Neo4j连接配置"""
    uri: str
    user: str
    password: str
    database: str = "neo4j"
    max_connection_pool_size: int = 50
    connection_acquisition_timeout: int = 60


class Neo4jConnectionPool:
    """
    Neo4j连接池管理器
    单例模式，确保全局共享一个连接池
    """
    _instance: Optional['Neo4jConnectionPool'] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[Neo4jConnectionConfig] = None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._config = config
        self._driver = None
        self._initialized = True
        self._health_ok = False

    def initialize(self, config: Neo4jConnectionConfig) -> 'Neo4jConnectionPool':
        """初始化连接池"""
        if self._driver:
            return self
        self._config = config
        try:
            self._driver = GraphDatabase.driver(
                config.uri,
                auth=(config.user, config.password),
                max_connection_pool_size=config.max_connection_pool_size,
                connection_acquisition_timeout=config.connection_acquisition_timeout
            )
            self._health_ok = True
            logger.info(f"Neo4j连接池初始化完成: {config.uri}")
        except Exception as e:
            logger.error(f"Neo4j连接池初始化失败: {e}")
            self._health_ok = False
        return self

    @property
    def driver(self):
        """获取驱动实例"""
        return self._driver

    @property
    def is_healthy(self) -> bool:
        """检查连接健康状态"""
        if not self._driver:
            return False
        try:
            with self._driver.session() as session:
                session.run("RETURN 1")
            self._health_ok = True
            return True
        except Exception as e:
            logger.warning(f"Neo4j健康检查失败: {e}")
            self._health_ok = False
            return False

    def health_check_and_reconnect(self) -> bool:
        """健康检查并在必要时重连"""
        if self.is_healthy:
            return True
        logger.info("尝试重新连接Neo4j...")
        try:
            if self._driver:
                self._driver.close()
            self._driver = GraphDatabase.driver(
                self._config.uri,
                auth=(self._config.user, self._config.password),
                max_connection_pool_size=self._config.max_connection_pool_size
            )
            self._health_ok = True
            logger.info("Neo4j重连成功")
            return True
        except Exception as e:
            logger.error(f"Neo4j重连失败: {e}")
            self._health_ok = False
            return False

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None,
                     retry_times: int = 3, retry_delay: float = 1.0) -> List[Dict[str, Any]]:
        """
        执行Cypher查询（带重试机制）

        Args:
            query: Cypher查询语句
            parameters: 查询参数
            retry_times: 重试次数
            retry_delay: 重试延迟（秒）

        Returns:
            查询结果列表
        """
        if not self._driver:
            if not self.health_check_and_reconnect():
                raise ConnectionError("Neo4j连接不可用")

        last_error = None
        for attempt in range(retry_times):
            try:
                with self._driver.session() as session:
                    result = session.run(query, parameters or {})
                    return [record.data() for record in result]
            except Exception as e:
                last_error = e
                logger.warning(f"Neo4j查询失败 (尝试 {attempt + 1}/{retry_times}): {e}")
                if attempt < retry_times - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    if not self.health_check_and_reconnect():
                        break

        raise last_error or Exception("Neo4j查询失败")

    def close(self):
        """关闭连接池"""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j连接池已关闭")


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


class LRUCache:
    """
    LRU缓存实现
    用于缓存查询分析结果等
    """
    def __init__(self, max_size: int = 128):
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                return None
            self._cache.move_to_end(key)
            return self._cache[key]

    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self._max_size:
                    self._cache.popitem(last=False)
            self._cache[key] = value

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)


class QueryAnalysisCache:
    """查询分析结果缓存"""
    _instance: Optional['QueryAnalysisCache'] = None
    _lock = threading.Lock()

    def __new__(cls, max_size: int = 256):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache = LRUCache(max_size)
        return cls._instance

    def get(self, query: str) -> Optional[Any]:
        """获取缓存的查询分析结果"""
        normalized_query = query.strip().lower()
        return self._cache.get(normalized_query)

    def set(self, query: str, analysis: Any) -> None:
        """缓存查询分析结果"""
        normalized_query = query.strip().lower()
        self._cache.set(normalized_query, analysis)

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()


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


def parallel_execute(tasks: List[Callable], max_workers: int = 4) -> List[Any]:
    """
    并行执行多个任务

    Args:
        tasks: 可调用任务列表
        max_workers: 最大工作线程数

    Returns:
        任务结果列表（按顺序）
    """
    if not tasks:
        return []

    results = [None] * len(tasks)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {
            executor.submit(task): i
            for i, task in enumerate(tasks)
        }
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                results[index] = future.result()
            except Exception as e:
                logger.error(f"任务 {index} 执行失败: {e}")
                results[index] = None
    return results
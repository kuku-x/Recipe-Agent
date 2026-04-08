"""Neo4j连接池管理模块"""

import os
import logging
import time
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from neo4j import GraphDatabase

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
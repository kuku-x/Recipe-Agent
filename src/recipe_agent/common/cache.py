"""缓存模块"""

import logging
import threading
from typing import Any, Optional, List, Callable
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


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
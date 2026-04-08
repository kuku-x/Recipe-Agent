"""Recipe Agent - 基于图数据库的智能烹饪助手"""

__version__ = "0.1.0"

from .config import GraphRAGConfig, DEFAULT_CONFIG
from .main import AdvancedGraphRAGSystem

__all__ = ["GraphRAGConfig", "DEFAULT_CONFIG", "AdvancedGraphRAGSystem"]
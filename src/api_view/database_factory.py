"""
数据库工厂
根据环境变量动态选择 PostgreSQL 或 MongoDB 存储
"""
from typing import Optional
from .postgres_store import PostgreSQLStore
from .mongodb_store import MongoDBStore
from ..agent.env_utils import get_env
from ..agent.log_utils import web_logger


def get_database_store():
    """
    根据 POSTGRES_URI 环境变量决定使用 PostgreSQL 还是 MongoDB

    Returns:
        BaseStore: 数据库存储实例
    """
    postgres_uri = get_env("POSTGRES_URI", None)

    if postgres_uri and postgres_uri.startswith("postgresql://"):
        web_logger.info("使用 PostgreSQL 数据库存储")
        return PostgreSQLStore(uri=postgres_uri)
    else:
        web_logger.info("使用 MongoDB 数据库存储")
        return MongoDBStore(
            uri=get_env("MONGODB_URI", "mongodb://localhost:27017"),
            db_name=get_env("MONGODB_DB_NAME", "erp_agent")
        )
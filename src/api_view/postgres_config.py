"""
PostgreSQL 连接配置
AsyncPG 连接.
"""
import os
from asyncpg import create_pool, Pool
from ..agent.env_utils import get_env

POSTGRES_URI = get_env("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/erp_agent")
POSTGRES_DB_NAME = get_env("POSTGRES_DB_NAME", "erp_agent")

# 全局连接池
_pool: Pool = None


async def get_postgres_pool() -> Pool:
    """获取 PostgreSQL 连接池"""
    global _pool
    if _pool is None:
        _pool = await create_pool(POSTGRES_URI)
    return _pool


async def get_db():
    """获取数据库连接"""
    pool = await get_postgres_pool()
    return pool.acquire()


async def close_postgres_pool():
    """关闭 PostgreSQL 连接池"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
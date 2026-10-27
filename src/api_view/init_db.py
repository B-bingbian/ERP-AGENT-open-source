"""
数据库初始化脚本
为 PostgreSQL 创建必要的表结构
"""
import asyncio
import sys
import os
from pathlib import Path

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from postgres_config import get_postgres_pool
from postgres_store import PostgreSQLStore
from postgres_checkpointer import PostgresCheckpointSaver
from agent.log_utils import web_logger


async def init_database():
    """初始化数据库表"""
    try:
        web_logger.info("开始初始化数据库...")

        # 初始化 Store
        store = PostgreSQLStore()
        await store._init_db()
        web_logger.info("✓ LangGraph Store 表已创建")

        # 初始化 Checkpoint 表
        checkpointer = PostgresCheckpointSaver(
            uri="postgresql://postgres:postgres@localhost:5432/erp_agent"
        )
        await checkpointer.setup_table()
        web_logger.info("✓ Checkpoint 表已创建")

        # 创建额外的业务表（如果需要）
        await create_business_tables()

        web_logger.info("数据库初始化完成！")

    except Exception as e:
        web_logger.error(f"数据库初始化失败: {e}")
        raise


async def create_business_tables():
    """创建业务相关的表"""
    pool = await get_postgres_pool()

    async with pool.acquire() as conn:
        # 创建 display_messages 表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS display_messages (
                thread_id UUID PRIMARY KEY,
                messages JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

        # 创建 conversations 表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                thread_id UUID NOT NULL UNIQUE,
                user_id UUID NOT NULL,
                title TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                metadata JSONB DEFAULT '{}'
            )
        """)

        # 创建 harness_traces 表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS harness_traces (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                thread_id UUID NOT NULL UNIQUE,
                trace JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

        # 创建索引
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_updated ON conversations (user_id, updated_at DESC)")

        web_logger.info("✓ 业务表已创建")


if __name__ == "__main__":
    asyncio.run(init_database())
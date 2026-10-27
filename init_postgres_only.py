"""
仅初始化PostgreSQL数据库脚本
"""
import sys
import os
import asyncio
import asyncpg
from pathlib import Path

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(__file__))

async def init_database():
    """初始化PostgreSQL数据库"""
    try:
        print("正在初始化PostgreSQL数据库...")

        # 创建连接池
        pool = await asyncpg.create_pool(
            "postgresql://postgres:postgres@localhost:5432/postgres"
        )

        async with pool.acquire() as conn:
            # 创建数据库
            await conn.execute("CREATE DATABASE erp_agent;")
            print("✓ 数据库 erp_agent 创建成功")

            # 连接到新数据库

            pool = await asyncpg.create_pool(
                "postgresql://postgres:postgres@localhost:5432/erp_agent"
            )

            async with pool.acquire() as conn:
                # 创建langgraph_store表
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS langgraph_store (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        namespace JSONB NOT NULL,
                        key TEXT NOT NULL,
                        value JSONB NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)

                # 创建索引
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_langgraph_store_namespace_key
                    ON langgraph_store (namespace, key)
                """)

                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_langgraph_store_updated_at
                    ON langgraph_store (updated_at)
                """)

                print("✓ langgraph_store 表创建成功")

                # 创建checkpoints表
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS checkpoints (
                        thread_id UUID NOT NULL,
                        checkpoint_id UUID NOT NULL,
                        checkpoint JSONB NOT NULL,
                        writes JSONB,
                        parent_checkpoint_id UUID,
                        metadata JSONB DEFAULT '{}',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        PRIMARY KEY (thread_id, checkpoint_id)
                    )
                """)

                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_created
                    ON checkpoints (thread_id, created_at)
                """)

                print("✓ checkpoints 表创建成功")

                # 创建业务表
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS display_messages (
                        thread_id UUID PRIMARY KEY,
                        messages JSONB NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)

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

                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS harness_traces (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        thread_id UUID NOT NULL UNIQUE,
                        trace JSONB NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)

                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conversations_user_updated
                    ON conversations (user_id, updated_at DESC)
                """)

                print("✓ 业务表创建成功")

        await pool.close()
        print("✓ 数据库初始化完成!")

    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        print("\n可能的原因:")
        print("1. PostgreSQL 服务未启动")
        print("2. 密码不正确")
        print("3. 数据库已存在")
        raise

if __name__ == "__main__":
    asyncio.run(init_database())
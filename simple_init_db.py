"""
简化版PostgreSQL数据库初始化
"""
import asyncio
import asyncpg

async def init_database():
    print("开始初始化PostgreSQL数据库...")

    # 连接到postgres数据库
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/postgres')

    try:
        # 创建数据库
        await conn.execute('CREATE DATABASE erp_agent;')
        print("✓ 数据库 erp_agent 创建成功")

        # 连接到新数据库
        await conn.close()
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/erp_agent')

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
        print("✓ display_messages 表创建成功")

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
        print("✓ conversations 表创建成功")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS harness_traces (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                thread_id UUID NOT NULL UNIQUE,
                trace JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        print("✓ harness_traces 表创建成功")

    finally:
        await conn.close()

    print("✓ 数据库初始化完成!")

if __name__ == "__main__":
    asyncio.run(init_database())
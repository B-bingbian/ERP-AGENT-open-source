"""
PostgreSQL 连接验证脚本
"""
import sys
import os
import asyncio
import asyncpg

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from src.api_view.postgres_config import get_postgres_pool

async def test_connection():
    """测试PostgreSQL连接"""
    try:
        print("正在测试PostgreSQL连接...")

        # 尝试连接
        pool = await get_postgres_pool()
        async with pool.acquire() as conn:
            # 测试基本查询
            result = await conn.fetch("SELECT version()")
            version = result[0]['version']
            print(f"✓ 连接成功！PostgreSQL版本: {version}")

            # 检查数据库是否存在
            result = await conn.fetch("SELECT datname FROM pg_database WHERE datname = $1", "erp_agent")
            if not result:
                print("创建数据库 erp_agent...")
                await conn.execute("CREATE DATABASE erp_agent")
                print("✓ 数据库创建成功")
            else:
                print("✓ 数据库 erp_agent 已存在")

            # 关闭连接
            await pool.close()

        print("✓ 所有测试通过！")

    except Exception as e:
        print(f"✗ 连接失败: {e}")
        print("\n请确保：")
        print("1. PostgreSQL 已安装并运行")
        print("2. 用户名是 postgres")
        print("3. 密码是 postgres")
        print("4. 端口是 5432")

if __name__ == "__main__":
    asyncio.run(test_connection())
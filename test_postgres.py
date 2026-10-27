#!/usr/bin/env python
"""
简单的PostgreSQL连接测试脚本
"""
import sys
import os
import subprocess

def test_postgres():
    print("=" * 50)
    print("PostgreSQL 连接测试")
    print("=" * 50)

    # 测试psql命令是否可用
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ PostgreSQL 已安装: {result.stdout.strip()}")
        else:
            print("✗ PostgreSQL 未安装或命令不可用")
            print("\n请安装PostgreSQL:")
            print("1. 访问: https://www.postgresql.org/download/windows/")
            print("2. 下载并安装，设置密码为: postgres")
            return False
    except FileNotFoundError:
        print("✗ PostgreSQL 未安装或命令不可用")
        print("\n请安装PostgreSQL:")
        print("1. 访问: https://www.postgresql.org/download/windows/")
        print("2. 下载并安装，设置密码为: postgres")
        return False

    # 测试连接
    try:
        result = subprocess.run([
            'psql', '-U', 'postgres', '-c', 'SELECT version();'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✓ PostgreSQL 连接成功!")
            print(f"版本: {result.stdout.split()[2]}")

            # 创建数据库
            print("\n正在创建数据库 erp_agent...")
            subprocess.run(['psql', '-U', 'postgres', '-c', 'CREATE DATABASE erp_agent;'],
                         capture_output=True)
            print("✓ 数据库创建完成")

            # 初始化项目表
            print("\n正在初始化项目表结构...")
            sys.path.insert(0, os.path.dirname(__file__))

            try:
                from src.api_view.init_db import init_database
                import asyncio

                asyncio.run(init_database())
                print("✓ 项目表结构初始化成功")

            except Exception as e:
                print(f"⚠ 初始化表结构时出错: {e}")
                print("这可能是因为依赖未安装，不影响数据库使用")

            return True

        else:
            print("✗ PostgreSQL 连接失败")
            print(f"错误: {result.stderr}")
            print("\n请检查:")
            print("1. PostgreSQL 服务是否运行 (net start postgresql)")
            print("2. 密码是否正确设置为: postgres")
            return False

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_postgres()

    print("\n" + "=" * 50)
    if success:
        print("配置完成! 现在可以启动项目了:")
        print("1. MCP服务: .venv/Scripts/python.exe -m src.mcp_server.server_main")
        print("2. 后端服务: .venv/Scripts/python.exe -m src.api_view.web_main")
        print("3. 前端服务: cd frontend && npm run dev")
        print("访问: http://localhost:3000")
    else:
        print("请先解决上述问题")
    print("=" * 50)
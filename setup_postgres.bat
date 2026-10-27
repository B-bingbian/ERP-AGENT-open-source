@echo off
echo ========================================
echo   ERP Agent - PostgreSQL 配置脚本
echo ========================================
echo.

echo 步骤 1: 检查PostgreSQL是否已安装...
where psql >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [错误] PostgreSQL未安装!
    echo.
    echo 请先安装PostgreSQL:
    echo 1. 访问: https://www.postgresql.org/download/windows/
    echo 2. 下载安装程序
    echo 3. 安装时设置密码为: postgres
    echo 4. 安装完成后重新运行此脚本
    echo.
    pause
    exit /b 1
)

echo [✓] PostgreSQL 已安装
psql --version

echo.
echo 步骤 2: 检查PostgreSQL服务...
net stop postgresql >nul 2>&1
net start postgresql
if %errorlevel% neq 0 (
    echo.
    echo [错误] 无法启动PostgreSQL服务
    echo 请检查PostgreSQL是否正确安装
    pause
    exit /b 1
)

echo [✓] PostgreSQL 服务运行中

echo.
echo 步骤 3: 测试连接...
psql -U postgres -c "SELECT version();" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [错误] 无法连接到PostgreSQL
    echo 请检查密码是否设置为: postgres
    pause
    exit /b 1
)

echo [✓] PostgreSQL 连接成功

echo.
echo 步骤 4: 创建数据库...
psql -U postgres -c "CREATE DATABASE erp_agent;" 2>nul
if %errorlevel% equ 0 (
    echo [✓] 数据库 erp_agent 创建成功
) else (
    echo [信息] 数据库 erp_agent 已存在
)

echo.
echo 步骤 5: 初始化项目表结构...
cd /d "%~dp0"
.venv\Scripts\python.exe src\api_view\init_db.py
if %errorlevel% equ 0 (
    echo [✓] 项目表结构初始化成功
) else (
    echo [警告] 表结构初始化失败
    echo 请检查Python环境和依赖
)

echo.
echo ========================================
echo   PostgreSQL 配置完成!
echo ========================================
echo.
echo 现在您可以启动项目服务:
echo 1. MCP服务: .venv\Scripts\python.exe -m src.mcp_server.server_main
echo 2. 后端服务: .venv\Scripts\python.exe -m src.api_view.web_main
echo 3. 前端服务: cd frontend ^&^& npm run dev
echo.
echo 访问地址: http://localhost:3000
echo.
pause
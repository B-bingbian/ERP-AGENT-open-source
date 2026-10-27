# ============================================================
# ERP-AGENT-open-source 一键启动脚本
# 功能：合并启动 MCP(:9000) / 后端(:8000) / 前端(:3000) + 自动自检
# 用法：PowerShell 中执行  .\start.ps1
#       跳过前端：.\start.ps1 -SkipFrontend
# 说明：已占用端口会自动跳过对应服务；日志输出到 startup-logs\
# 适用版本：2026-09-26 修复后的代码基线
# ============================================================
param(
    [switch]$SkipFrontend
)

$ErrorActionPreference = 'Stop'
$root = 'D:\myProject\ai_project\ERP-AGENT-open-source'
$python = Join-Path $root '.venv\Scripts\python.exe'
$frontendDir = Join-Path $root 'frontend'
$logDir = Join-Path $root 'startup-logs'

function Write-Step($msg) { Write-Host "[step] $msg" -ForegroundColor Cyan }
function Write-Pass($msg)  { Write-Host "[PASS] $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Fail($msg)  { Write-Host "[FAIL] $msg" -ForegroundColor Red }

function Test-Port([int]$port) {
    try { return (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop | Measure-Object).Count -gt 0 }
    catch { return $false }
}

# ---------- 0. 前置检查 ----------
Write-Step "前置检查"
if (-not (Test-Path $python)) { Write-Fail "缺少虚拟环境: $python"; exit 1 }
$envFile = Join-Path $root '.env'
if (-not (Test-Path $envFile)) { Write-Warn "缺少 .env 文件，LLM/数据库配置可能缺失" }
else {
    $envContent = Get-Content $envFile -Raw -Encoding UTF8
    if ($envContent -notmatch 'DOCKER_HOST') { Write-Warn ".env 未配置 DOCKER_HOST，沙箱将无法连接虚拟机 Docker" }
}
$vmTcp = Test-NetConnection -ComputerName '192.168.159.168' -Port 2375 -WarningAction SilentlyContinue
if ($vmTcp.TcpTestSucceeded) { Write-Pass "虚拟机 Docker 2375 连通" }
else { Write-Warn "虚拟机 Docker 2375 未连通，沙箱执行将失败" }

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

# ---------- 1. 启动 MCP (:9000) ----------
if (Test-Port 9000) { Write-Pass "MCP :9000 已在运行，跳过" }
else {
    Write-Step "启动 MCP :9000"
    Start-Process -FilePath $python -ArgumentList '-m','src.mcp_server.server_main' `
        -WorkingDirectory $root -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir 'mcp.out.log') `
        -RedirectStandardError (Join-Path $logDir 'mcp.err.log')
    Write-Pass "MCP 已启动，日志: $logDir\mcp.out.log"
}

# ---------- 2. 启动后端 (:8000) ----------
if (Test-Port 8000) { Write-Pass "后端 :8000 已在运行，跳过" }
else {
    Write-Step "启动后端 :8000"
    Start-Process -FilePath $python -ArgumentList '-m','src.api_view.web_main' `
        -WorkingDirectory $root -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir 'backend.out.log') `
        -RedirectStandardError (Join-Path $logDir 'backend.err.log')
    Write-Pass "后端已启动，日志: $logDir\backend.out.log"
}

# ---------- 3. 启动前端 (:3000) ----------
if (-not $SkipFrontend) {
    if (Test-Port 3000) { Write-Pass "前端 :3000 已在运行，跳过" }
    else {
        Write-Step "启动前端 :3000"
        Start-Process -FilePath 'npm.cmd' -ArgumentList 'run','dev' `
            -WorkingDirectory $frontendDir -WindowStyle Hidden `
            -RedirectStandardOutput (Join-Path $logDir 'frontend.out.log') `
            -RedirectStandardError (Join-Path $logDir 'frontend.err.log')
        Write-Pass "前端已启动，日志: $logDir\frontend.out.log"
    }
}

# ---------- 4. 自检 ----------
Write-Step "自检"
$healthOk = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    try {
        $r = Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) { $healthOk = $true; break }
    } catch { }
}
if ($healthOk) { Write-Pass "后端 health 返回 200" }
else { Write-Fail "后端 health 未就绪，请查看 $logDir\backend.err.log" }

Start-Sleep -Seconds 5
$backendLog = ''
if (Test-Path (Join-Path $logDir 'backend.out.log')) {
    $backendLog = Get-Content (Join-Path $logDir 'backend.out.log') -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
}
if ($backendLog -match 'Warm pool container created') { Write-Pass "沙箱预热成功（Warm pool container created）" }
elseif (Test-Port 8000) { Write-Warn "后端日志未发现预热记录，可能已在更早启动（日志在旧终端）" }
else { Write-Warn "未发现沙箱预热记录，请查看后端日志" }

Write-Host ""
Write-Step "完成。端到端冒烟测试命令："
Write-Host '  curl.exe -N -X POST http://localhost:8000/api/chat/stream -H "Content-Type: application/json" --data-binary "@chat_body.json"' -ForegroundColor Gray
Write-Host "日志目录: $logDir"

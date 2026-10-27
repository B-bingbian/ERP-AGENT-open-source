# 自动安装PostgreSQL脚本
Write-Host "PostgreSQL 自动安装脚本" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green

# 检查管理员权限
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "需要管理员权限运行此脚本" -ForegroundColor Red
    Write-Host "请右键点击PowerShell，选择'以管理员身份运行'" -ForegroundColor Yellow
    exit 1
}

# 检查是否已安装
if (Get-Command psql -ErrorAction SilentlyContinue) {
    Write-Host "PostgreSQL 已安装!" -ForegroundColor Green
    psql --version
    exit 0
}

# 下载安装程序
Write-Host "下载PostgreSQL安装程序..." -ForegroundColor Yellow
$downloadUrl = "https://get.enterprisedb.com/postgresql/postgresql-16.2-1-windows-x64.exe"
$outputFile = "$env:TEMP\postgresql-installer.exe"

try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $outputFile -UseBasicParsing
    Write-Host "下载完成" -ForegroundColor Green
} catch {
    Write-Host "下载失败: $_" -ForegroundColor Red
    exit 1
}

# 安装PostgreSQL
Write-Host "启动安装程序..." -ForegroundColor Yellow
Write-Host "在安装过程中，请设置密码为: postgres" -ForegroundColor Cyan
Write-Host "点击Next继续安装..." -ForegroundColor Cyan

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $outputFile
$psi.Arguments = "/S"
$psi.UseShellExecute = $true
$psi.WindowStyle = "Hidden"

$process = [System.Diagnostics.Process]::Start($psi)
$process.WaitForExit()

# 清理安装文件
Remove-Item $outputFile -Force

# 验证安装
if (Get-Command psql -ErrorAction SilentlyCreate) {
    Write-Host "PostgreSQL 安装成功!" -ForegroundColor Green
    psql --version

    # 启动服务
    Write-Host "启动PostgreSQL服务..." -ForegroundColor Yellow
    net start postgresql

    # 验证连接
    psql -U postgres -c "SELECT version();" | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "PostgreSQL 连接测试成功!" -ForegroundColor Green
    } else {
        Write-Host "PostgreSQL 连接测试失败!" -ForegroundColor Red
    }
} else {
    Write-Host "PostgreSQL 安装失败!" -ForegroundColor Red
}

Write-Host "安装完成!" -ForegroundColor Green
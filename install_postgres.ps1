# PostgreSQL 自动安装脚本
# 需要以管理员权限运行

Write-Host "正在准备安装PostgreSQL..." -ForegroundColor Yellow

# 检查是否已安装
if (Get-Command psql -ErrorAction SilentlyContinue) {
    Write-Host "PostgreSQL 已安装!" -ForegroundColor Green
    psql --version
    exit 0
}

# 检查PowerShell版本
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Host "需要PowerShell 5.0或更高版本" -ForegroundColor Red
    exit 1
}

# 检查管理员权限
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "请以管理员身份运行此脚本!" -ForegroundColor Red
    Write-Host "右键点击PowerShell，选择'以管理员身份运行'" -ForegroundColor Yellow
    exit 1
}

# 下载PostgreSQL安装程序
Write-Host "下载PostgreSQL安装程序..." -ForegroundColor Yellow
$downloadUrl = "https://get.enterprisedb.com/postgresql/postgresql-16.2-1-windows-x64.exe"
$outputFile = "$env:TEMP\postgresql-installer.exe"

Invoke-WebRequest -Uri $downloadUrl -OutFile $outputFile

# 运行安装程序
Write-Host "启动PostgreSQL安装程序..." -ForegroundColor Yellow
Write-Host "请在安装过程中设置密码为: postgres" -ForegroundColor Cyan
Write-Host "点击Next继续..." -ForegroundColor Cyan

Start-Process $outputFile -Wait

# 清理
Remove-Item $outputFile

# 验证安装
Write-Host "验证安装..." -ForegroundColor Yellow
if (Get-Command psql -ErrorAction SilentlyContinue) {
    Write-Host "PostgreSQL 安装成功!" -ForegroundColor Green
    psql --version

    # 启动服务
    Write-Host "启动PostgreSQL服务..." -ForegroundColor Yellow
    net start postgresql

    # 测试连接
    psql -U postgres -c "SELECT version();" | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "PostgreSQL 连接测试成功!" -ForegroundColor Green
    } else {
        Write-Host "PostgreSQL 连接测试失败!" -ForegroundColor Red
    }
} else {
    Write-Host "PostgreSQL 安装失败!" -ForegroundColor Red
}

Write-Host "安装完成！" -ForegroundColor Green
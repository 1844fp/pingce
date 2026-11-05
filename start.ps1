$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$localPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $localPython)) { throw '请先按 README 创建 .venv 并安装 requirements.txt。' }
if (-not (Test-Path -LiteralPath 'apps/web/dist/index.html')) { throw '请先在 apps/web 运行 npm ci 和 npm run build。' }
& $localPython run.py

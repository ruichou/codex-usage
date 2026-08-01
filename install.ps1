$ErrorActionPreference = "Stop"

$installDir = Join-Path $env:LOCALAPPDATA "CodexUsageWidget"
$exePath = Join-Path $installDir "CodexUsageWidget.exe"
$downloadUrl = "https://raw.githubusercontent.com/ruichou/codex-usage/main/dist/CodexUsageWidget.exe"

New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Write-Host "正在下载 Codex usage widget..."
Invoke-WebRequest -Uri $downloadUrl -OutFile $exePath
Write-Host "已安装到 $installDir"
Start-Process -FilePath $exePath

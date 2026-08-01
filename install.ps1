$ErrorActionPreference = "Stop"

$installDir = Join-Path $env:LOCALAPPDATA "CodexUsageWidget"
$exePath = Join-Path $installDir "CodexUsageWidget.exe"
$downloadUrl = "https://raw.githubusercontent.com/ruichou/codex-usage/main/dist/CodexUsageWidget.exe"

New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Write-Host "正在下载 Codex usage widget..."
Invoke-WebRequest -Uri $downloadUrl -OutFile $exePath

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "Codex usage widget.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = $installDir
$shortcut.Description = "显示 Codex 当前套餐剩余用量"
$shortcut.Save()

Write-Host "已安装到 $installDir"
Write-Host "桌面快捷方式已创建"
Start-Process -FilePath $exePath

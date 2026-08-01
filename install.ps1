$ErrorActionPreference = "Stop"

$installDir = Join-Path $env:LOCALAPPDATA "CodexUsageWidget"
$exePath = Join-Path $installDir "CodexUsageWidget.exe"
$iconPath = Join-Path $installDir "codex-usage.ico"
$downloadUrl = "https://raw.githubusercontent.com/ruichou/codex-usage/main/dist/CodexUsageWidget.exe"
$iconUrl = "https://raw.githubusercontent.com/ruichou/codex-usage/main/assets/codex-usage.ico"
$tempExePath = Join-Path $env:TEMP ("CodexUsageWidget-" + [Guid]::NewGuid().ToString("N") + ".exe")
$tempIconPath = Join-Path $env:TEMP ("CodexUsageWidget-" + [Guid]::NewGuid().ToString("N") + ".ico")

New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Write-Host "正在下载 Codex usage widget..."
Invoke-WebRequest -Uri $downloadUrl -OutFile $tempExePath
Invoke-WebRequest -Uri $iconUrl -OutFile $tempIconPath

$oldProcesses = Get-Process -Name "CodexUsageWidget" -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $exePath }
foreach ($process in $oldProcesses) {
    Stop-Process -Id $process.Id -Force
}
Start-Sleep -Milliseconds 500
Move-Item -LiteralPath $tempExePath -Destination $exePath -Force
Move-Item -LiteralPath $tempIconPath -Destination $iconPath -Force

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "Codex usage widget.lnk"
if (Test-Path -LiteralPath $shortcutPath) {
    Remove-Item -LiteralPath $shortcutPath -Force
}
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exePath
$shortcut.IconLocation = "$iconPath,0"
$shortcut.WorkingDirectory = $installDir
$shortcut.Description = "显示 Codex 当前套餐剩余用量"
$shortcut.Save()

$iconRefresh = Join-Path $env:WINDIR "System32\ie4uinit.exe"
if (Test-Path -LiteralPath $iconRefresh) {
    Start-Process -FilePath $iconRefresh -ArgumentList "-show" -WindowStyle Hidden -Wait
}

Write-Host "已安装到 $installDir"
Write-Host "桌面快捷方式已创建"
Start-Process -FilePath $exePath

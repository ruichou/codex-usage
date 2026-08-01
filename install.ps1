$ErrorActionPreference = "Stop"

$installDir = Join-Path $env:LOCALAPPDATA "CodexUsageWidget"
$exePath = Join-Path $installDir "CodexUsageWidget.exe"
$iconPath = Join-Path $installDir "codex-usage.ico"
$downloadUrl = "https://github.com/ruichou/codex-usage/raw/refs/heads/main/dist/CodexUsageWidget.exe"
$iconUrl = "https://github.com/ruichou/codex-usage/raw/refs/heads/main/assets/codex-usage.ico"
$tempExePath = Join-Path $env:TEMP ("CodexUsageWidget-" + [Guid]::NewGuid().ToString("N") + ".exe")
$tempIconPath = Join-Path $env:TEMP ("CodexUsageWidget-" + [Guid]::NewGuid().ToString("N") + ".ico")

New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Write-Host "Downloading Codex usage widget..."
Invoke-WebRequest -Uri $downloadUrl -OutFile $tempExePath
Invoke-WebRequest -Uri $iconUrl -OutFile $tempIconPath

$oldProcesses = Get-Process -Name "CodexUsageWidget" -ErrorAction SilentlyContinue
if ($oldProcesses) {
    try {
        $oldProcesses | Stop-Process -Force -ErrorAction Stop
    } catch {
        throw "CodexUsageWidget is running with elevated permissions. Close it with the X button, then run the installer again."
    }
}
Start-Sleep -Milliseconds 500

$replaced = $false
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    try {
        Move-Item -LiteralPath $tempExePath -Destination $exePath -Force
        $replaced = $true
        break
    } catch {
        Start-Sleep -Milliseconds 250
    }
}
if (-not $replaced) {
    throw "无法替换正在使用的 CodexUsageWidget.exe，请关闭程序后重试。"
}
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
$shortcut.Description = "Show current Codex usage"
$shortcut.Save()

$windowsDir = [Environment]::GetEnvironmentVariable("WINDIR")
if (-not $windowsDir) { $windowsDir = "C:\Windows" }
$iconRefresh = Join-Path $windowsDir "System32\ie4uinit.exe"
if (Test-Path -LiteralPath $iconRefresh) {
    Start-Process -FilePath $iconRefresh -ArgumentList "-show" -WindowStyle Hidden -Wait
}

Write-Host "Installed to $installDir"
Write-Host "Desktop shortcut created"
Start-Process -FilePath $exePath

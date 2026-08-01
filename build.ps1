$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $python) {
    throw "未找到 Python，请先安装 Python 3。"
}

& $python.Source -m PyInstaller --noconfirm --clean --onefile --windowed --icon assets\codex-usage.ico --name CodexUsageWidget usage_widget.py
if ($LASTEXITCODE -ne 0) {
    throw "打包失败。请先运行：python -m pip install pyinstaller"
}

Write-Host "已生成 dist\CodexUsageWidget.exe"

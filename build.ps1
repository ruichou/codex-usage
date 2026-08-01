$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $python) {
    throw "Python was not found. Install Python 3 first."
}

& $python.Source -m PyInstaller --noconfirm --clean --onefile --windowed --icon assets\codex-usage.ico --name CodexUsageWidget usage_widget.py
if ($LASTEXITCODE -ne 0) {
    throw "Build failed. Install PyInstaller with: python -m pip install pyinstaller"
}

Write-Host "Built dist\CodexUsageWidget.exe"

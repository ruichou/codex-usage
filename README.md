# Codex usage widget

一个轻量的 Windows / macOS 悬浮窗，用来显示当前 Codex 套餐周期的剩余用量。

## 普通用户安装

### Windows

请在 PowerShell 中运行：

```powershell
irm https://raw.githubusercontent.com/ruichou/codex-usage/main/install.ps1 | iex
```

脚本会自动下载、创建桌面快捷方式并启动程序。程序需要你的电脑已经登录过 Codex，但不需要先打开 Codex 桌面端。

### macOS

macOS 安装包会在 GitHub Release 中自动生成，包含 Intel 和 Apple Silicon 两个版本：

[下载 macOS 版本](https://github.com/ruichou/codex-usage/releases)

下载对应架构的 `.zip`，解压后将 `CodexUsageWidget.app` 拖到“应用程序”文件夹，再双击启动。首次启动如遇到安全提示，请在“系统设置 → 隐私与安全性”中允许打开。

## 使用说明

- 横向 3D 胶囊样式
- 突出显示剩余百分比和粗进度条
- 用量越低，进度条和百分比颜色越偏橙/红
- 每 30 秒自动刷新
- 支持拖动、缩小和关闭
- 每个人运行后读取的是自己电脑上的 Codex 登录状态和套餐余量

## 从源码运行

```powershell
python usage_widget.py
```

## 本地打包

Windows：

```powershell
python -m pip install pyinstaller
.\build.ps1
```

macOS：

```bash
python3 -m pip install pyinstaller
python3 -m PyInstaller --noconfirm --clean --windowed --icon assets/codex-usage.icns --name CodexUsageWidget usage_widget.py
```

推送版本标签后，GitHub Actions 会自动构建 Windows、Intel macOS 和 Apple Silicon macOS 包，并发布到 GitHub Release：

```bash
git tag v1.0.0
git push origin v1.0.0
```

## 隐私和安全

程序只读取当前用户目录下的 Codex 登录状态，并向 Codex 用量接口请求当前账号的用量。认证信息不会写入项目文件，也不会上传到第三方服务。

这是 Codex 客户端当前使用的内部用量接口，未来可能随客户端更新而变化。

## 开源协议

[MIT License](LICENSE)

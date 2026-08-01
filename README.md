# Codex usage widget

一个轻量的 Windows 悬浮窗，用来显示当前 Codex 套餐周期的剩余用量。

## 普通用户安装

请在 PowerShell 中运行下面这一行：

```powershell
irm https://raw.githubusercontent.com/ruichou/codex-usage/main/install.ps1 | iex
```

脚本会把程序安装到：

```text
%LOCALAPPDATA%\CodexUsageWidget\CodexUsageWidget.exe
```

然后自动启动悬浮窗。程序需要你的电脑已经登录 Codex。

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

```powershell
python -m pip install pyinstaller
.\build.ps1
```

生成的文件位于 `dist\CodexUsageWidget.exe`。

## 隐私和安全

程序只读取当前 Windows 用户目录下的 Codex 登录状态，并向 Codex 用量接口请求当前账号的用量。认证信息不会写入项目文件，也不会上传到第三方服务。

这是 Codex 客户端当前使用的内部用量接口，未来可能随客户端更新而变化。

## 开源协议

[MIT License](LICENSE)

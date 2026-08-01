# Codex usage widget

一个轻量的 Windows 悬浮窗，用来显示当前 Codex 套餐周期的剩余用量。

## 功能

- 横向 3D 胶囊样式
- 突出显示剩余百分比和粗进度条
- 用量较低时自动变为橙色/红色
- 每 30 秒自动刷新
- 支持拖动、缩小和关闭
- 读取本机 Codex 登录状态，不需要重新输入 API Key

## 运行

双击 `dist\\CodexUsageWidget.exe` 即可运行。使用者需要先在本机登录 Codex。

也可以直接运行源码：

```powershell
python usage_widget.py
```

重新打包：

```powershell
.\\build.ps1
```

## 隐私和安全

程序只读取当前 Windows 用户目录下的 Codex 登录状态，并向 Codex 用量接口请求当前账号的用量。认证信息不会写入项目文件，也不会上传到第三方服务。

这是 Codex 客户端当前使用的内部用量接口，未来可能随客户端更新而变化。

## 开源协议

[MIT License](LICENSE)
